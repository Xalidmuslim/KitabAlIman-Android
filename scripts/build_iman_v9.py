"""v0.9: coherent sepia hero + six individually generated main-screen illustrations.

Keeps existing native engine / book data / reader motions. No image content crops:
the header is precisely 3:1 and icons are fitted into their on-screen slots.
"""
from pathlib import Path
import argparse
import hashlib
import shutil

# dest = native Android drawable filename, source = approved image within GitHub.
RESOURCE_MAP = (
    ('antique_hero_refined.webp','iman_home_banner_v9.webp',
     'fee08ca48cccd8fd05641ed8113bbe9f2e48e576b90ede8b9e5499badba65263',(1200,400)),
    ('antique_open_book_detail.webp','iman_reading_v9.webp',
     '7ee1956661ab3a41f8ee6b16a74cc2d4dc70f859dff8380f6a8c4758561b63b9',(360,270)),
    ('antique_search_detail.webp','iman_search_v9.webp',
     'f33244f9cfbf1b3672b150c067b370a850d612c41f524d25a0919059f788dd09',(360,270)),
    ('antique_books_detail.webp','iman_contents_v9.webp',
     'b8ff1a25c7a26be1dc48ef28ed8ed48fad0178d66bf4c3998e745c72e1b07bb6',(360,270)),
    ('antique_scroll_detail.webp','iman_collections_v9.webp',
     'ea8e799012131a50ffad36f9482f354a24c13479c0660c119d3a0c8af62d22e4',(360,270)),
    ('iman_glossary_detail.webp','iman_glossary_v9.webp',
     '6170b8cbc279b71b29eb5303e304ebfff08a4664fccf678d9687818fe62f162a',(360,270)),
    ('antique_bookmark_detail.webp','iman_bookmarks_v9.webp',
     '1c8cae2e51af2c8a04ee8507dadcc7a659302a3bed7afaf246ee5b703505b410',(360,270)),
)


def one(source, old, new, why):
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f'Pinned v0.8 source changed: {why}; matches={count}')
    return source.replace(old, new, 1)


def patch_header(source):
    # Dark layout already uses a native book title; only the light banner changes.
    source = one(source,
        'contentDescription = book.title + " — " + book.author,',
        'contentDescription = null,', 'old image description')
    original = '''                Box(
                    Modifier.fillMaxWidth().height(25.dp)
                        .align(Alignment.TopCenter)
                        .background(Color(0xFFF5E9DA).copy(alpha = 0.42f)),
                )'''
    replacement = '''                // Native title on the pale left half; source illustration has no lettering.
                // This scales with Android's text settings and is never raster-cropped.
                Text(
                    book.title,
                    modifier = Modifier.align(Alignment.CenterStart)
                        .fillMaxWidth(0.51f)
                        .padding(start = 22.dp, top = 25.dp),
                    fontFamily = WebLiterataFont,
                    fontSize = 23.sp,
                    lineHeight = 27.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF49321F),
                )'''
    source = one(source,original,replacement,'replace opaque header strip with native book title')
    if 'val bannerHeight = maxWidth / 3f' not in source or 'ContentScale.FillBounds' not in source:
        raise RuntimeError('Hero must preserve 3:1 scale without cropping')
    return source


def patch_icons(source):
    source = one(source,
        'AntiqueIcon(R.drawable.antique_open_book_detail, Modifier.size(width = 52.dp, height = 36.dp), scale = ContentScale.Fit)',
        'AntiqueIcon(R.drawable.antique_open_book_detail, Modifier.size(width = 68.dp, height = 46.dp), scale = ContentScale.Fit)',
        'reading icon visibility')
    source = one(source,
        'AntiqueIcon(R.drawable.antique_search_detail, Modifier.size(39.dp))',
        'AntiqueIcon(R.drawable.antique_search_detail, Modifier.size(width = 58.dp, height = 42.dp))',
        'search illustration fit')
    source = one(source,
        'AntiqueIcon(icon, Modifier.size(width = 70.dp, height = 48.dp))',
        'AntiqueIcon(icon, Modifier.size(width = 84.dp, height = 56.dp))',
        'quick cards preserve aspect')
    source = one(source,
        'AntiqueQuickCard(R.drawable.antique_scroll_detail, "Понятия",',
        'AntiqueQuickCard(R.drawable.iman_glossary_detail, "Понятия",',
        'glossary separate from collections')
    return source


def patch_preload(source):
    return one(source,
        '        R.drawable.antique_scroll_detail,',
        '        R.drawable.antique_scroll_detail,\n        R.drawable.iman_glossary_detail,',
        'warm new concept drawable off main UI thread')


def build_v9(kit, destination):
    from scripts.build_iman_v8 import build_v8
    from PIL import Image
    build_v8(kit,destination)
    gradle = destination / 'app/build.gradle'
    data=gradle.read_text(encoding='utf-8')
    for old,new in [('versionCode 8','versionCode 9'),
                    ("versionName '0.8.0'","versionName '0.9.0'"),
                    ("applicationIdSuffix '.preview8'","applicationIdSuffix '.preview9'")]:
        data=one(data,old,new,'version update')
    gradle.write_text(data,encoding='utf-8')
    main=destination/'app/src/main'
    java=main/'java/com/xalid/meditsinaproroka/nativeapp'
    home=java/'AntiqueDesign.kt'
    source=home.read_text(encoding='utf-8')
    source=patch_header(source)
    source=patch_icons(source)
    home.write_text(source,encoding='utf-8')
    preload=java/'MedicineHomeArtwork.kt'
    preload.write_text(patch_preload(preload.read_text(encoding='utf-8')),encoding='utf-8')
    images=kit/'assets/ui/v9'
    drawables=main/'res/drawable-nodpi'
    for target, filename, expected_hash, target_size in RESOURCE_MAP:
        src=images/filename
        raw=src.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected_hash:
            raise RuntimeError('Unexpected visual asset SHA: '+filename)
        with Image.open(src) as art:
            if art.format!='WEBP' or art.size!=target_size:
                raise RuntimeError(f'Incorrect resource size/format: {filename}')
        shutil.copy2(src,drawables/target)
    if list(main.rglob('*.pdf')):
        raise RuntimeError('Source PDF must not appear in app')
    print('v0.9 sepia UI: 3:1 hero, six unique fit-mode card icons, launcher unchanged')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--dest',type=Path,required=True)
    arg=parser.parse_args()
    build_v9(Path(__file__).resolve().parents[1],arg.dest)
