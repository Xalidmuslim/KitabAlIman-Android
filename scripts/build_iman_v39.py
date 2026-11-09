"""v0.39: consistent calligraphy, permanent embossed reminder, card-matched app icon.

Apply only native UI/resource changes on verified v0.38.0; preserve all source
texts, reader, saved notes/bookmarks, quiz engine and five-tab navigation.
"""
from pathlib import Path
import argparse
import hashlib
import re

import numpy as np
from PIL import Image, ImageFilter, ImageOps

from scripts.build_iman_v38 import build_v38
from scripts.build_iman_v20 import APP, NAV, replace_one

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_embossed_reminder(drawable: Path) -> None:
    """Prepare crisp aged-paper bas relief; mask the painted halo out entirely."""
    # Use the sharper approved graphic instead of v38's twice-faded derivative.
    with Image.open(drawable/"iman_v35_reminder.webp") as source:
        art=source.convert("RGBA")
    gray=ImageOps.grayscale(art)
    light=np.asarray(gray,dtype=np.float32)
    relief=np.asarray(gray.filter(ImageFilter.EMBOSS),dtype=np.float32)-128.
    highpass=light-np.asarray(gray.filter(ImageFilter.GaussianBlur(2)),dtype=np.float32)
    shade=np.clip(relief*.33+highpass*.14,-40.,40.)
    depth=np.clip((240.-light)/125.,0.,1.)
    pigment=np.zeros((art.height,art.width,4),dtype=np.uint8)
    for channel,base in enumerate((186,156,125)):
        pigment[:,:,channel]=np.uint8(np.clip(base+shade*(1.0-channel*.09),0,255))
    # Ink's light areas become transparent; preserve paper-engraved contours.
    original=np.asarray(art.getchannel("A"),dtype=np.float32)
    x=np.arange(art.width,dtype=np.float32)[None,:]
    fade_left=np.clip((x-art.width*.035)/max(1.,art.width*.30),0.,1.)
    fade_right=np.clip((art.width-x)/max(1.,art.width*.055),0.,1.)
    engraved=np.clip(original*(.05+.95*depth**.72)*fade_left*fade_right,0.,255)
    pigment[:,:,3]=np.uint8(engraved)
    out=Image.fromarray(pigment,"RGBA")
    out.save(drawable/"iman_v39_relief.webp","WEBP",quality=95,method=6)
    if (drawable/"iman_v39_relief.webp").stat().st_size < 1000:
        raise RuntimeError("Embossed reminder artwork unexpectedly small")


def create_matching_launcher(dest: Path) -> None:
    """Reuse approved library book artwork for BOTH Android launcher and Home header."""
    res=dest/"app/src/main/res"
    drawable=res/"drawable-nodpi"
    original=drawable/"iman_v35_bookmarks.webp"
    with Image.open(original) as source:
        art=source.convert("RGBA")
    alpha=art.getchannel("A")
    bbox=alpha.point(lambda a:255 if a>135 else 0).getbbox()
    if bbox is None:
        raise RuntimeError("Approved library book is invisible")
    art=art.crop(bbox)

    def fitting_image(size, fraction):
        fg=Image.new("RGBA",(size,size),(0,0,0,0))
        subject=art.copy()
        subject.thumbnail((int(size*fraction),int(size*fraction)),
                          Image.Resampling.LANCZOS)
        fg.alpha_composite(subject,((size-subject.width)//2,(size-subject.height)//2))
        return fg

    # Unframed image matching the visible Contents/Collections/Glossary drawings.
    header=fitting_image(320,1.08)
    header.save(drawable/"iman_v39_header.webp","WEBP",quality=95,method=6)

    # Android's adaptive icon mask retains the book safely in its centre area.
    foreground=fitting_image(512,.84)
    foreground.save(drawable/"iman_v39_launcher_foreground.webp",
                    "WEBP",quality=94,method=6)

    # Legacy launchers still receive the same artwork on matte parchment.
    with Image.open(drawable/"iman_v38_flat_paper.webp") as wallpaper:
        paper=wallpaper.convert("RGB")
    w,h=paper.size
    patch=paper.crop((int(w*.26),int(h*.37),int(w*.74),int(h*.60)))
    background=patch.resize((512,512),Image.Resampling.BICUBIC).convert("RGBA")
    subtle=Image.new("RGBA",(512,512),(247,234,214,255))
    legacy=Image.blend(background,subtle,.76)
    legacy.alpha_composite(foreground)
    legacy=legacy.convert("RGB")
    (res/"mipmap-anydpi").mkdir(parents=True,exist_ok=True)
    legacy.save(res/"mipmap-anydpi/iman_v39_launcher.webp","WEBP",
                quality=93,method=6)

    (res/"mipmap-anydpi-v26").mkdir(parents=True,exist_ok=True)
    (res/"mipmap-anydpi-v26/iman_v39_launcher.xml").write_text(
        '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
        '  <background android:drawable="@color/iman_v39_icon_background"/>\n'
        '  <foreground android:drawable="@drawable/iman_v39_launcher_foreground"/>\n'
        '</adaptive-icon>\n',encoding="utf-8")
    (res/"values").mkdir(parents=True,exist_ok=True)
    (res/"values/iman_v39_icon_colors.xml").write_text(
        '<resources><color name="iman_v39_icon_background">#F7EAD7</color></resources>\n',
        encoding="utf-8")

    # Do not change activity launch flags, exported state, theme or app ID.
    manifest=dest/"app/src/main/AndroidManifest.xml"
    before=manifest.read_text("utf-8")
    tag=re.search(r"<application\b[^>]*>",before,re.DOTALL)
    if tag is None:
        raise RuntimeError("Android application element missing")
    replacement=tag.group()
    for attr in ("android:icon","android:roundIcon"):
        value=f'{attr}="@mipmap/iman_v39_launcher"'
        if re.search(r'\b'+re.escape(attr)+r'\s*=\s*"[^"]*"',replacement):
            replacement=re.sub(r'\b'+re.escape(attr)+r'\s*=\s*"[^"]*"',
                               value,replacement,count=1)
        else:
            replacement=replacement[:-1]+" "+value+">"
    updated=before[:tag.start()]+replacement+before[tag.end():]
    if updated.replace(replacement,tag.group(),1)!=before:
        raise RuntimeError("Launcher manifest update altered unrelated XML")
    manifest.write_text(updated,"utf-8")


def build_v39(kit: Path, dest: Path) -> None:
    build_v38(kit,dest)
    java=dest/APP
    assets=dest/"app/src/main/assets"
    drawable=dest/"app/src/main/res/drawable-nodpi"
    app=java/"App.kt"
    reader=java/"Reader.kt"
    app_before=digest(app)
    reader_before=digest(reader)
    book_hashes={f.name:digest(f) for f in assets.iterdir() if f.is_file()}
    if NAV not in app.read_text("utf-8"):
        raise RuntimeError("v39 expected native five-tab navigation")

    gradle=dest/"app/build.gradle"
    g=gradle.read_text("utf-8")
    for old,new in (
        ("versionCode 39","versionCode 41"),
        ("versionName '0.38.0'","versionName '0.39.1'"),
        ("applicationIdSuffix '.preview38'","applicationIdSuffix '.preview39'"),
    ):
        g=replace_one(g,old,new,"v39 isolated icon and quote preview")
    gradle.write_text(g,"utf-8")

    create_embossed_reminder(drawable)
    create_matching_launcher(dest)

    home=(kit/"scripts/ReferenceHomeV39.kt").read_text("utf-8")
    for name in ("contents","collections","glossary"):
        home=replace_one(home,f"R.drawable.iman_v32_{name}",
                         f"R.drawable.iman_v35_{name}",
                         "keep approved library drawings")
    if 'EditorialBookSection("Заметки"' not in home:
        raise RuntimeError("v39 lost user-approved Notes tile")
    (java/"ModernEditorialHome.kt").write_text(home,"utf-8")

    quote_file=java/"ImanQuoteCarousel.kt"
    existing=quote_file.read_text("utf-8")
    marker="@Composable\ninternal fun ImanFeaturedQuoteCarousel("
    if existing.count(marker)!=1 or existing.count('FeaturedExcerpt("iman-chapter-')!=79:
        raise RuntimeError("v39 source reminder inventory changed")
    q=(kit/"scripts/ReferenceQuoteV39.kt").read_text("utf-8")
    if ('fontFamily = ImanCaveatFont' not in q or
        'fontFamily = if (length' in q or
        'if (showIllustration)' in q or
        'R.drawable.iman_v39_relief' not in q):
        raise RuntimeError("v39 reminder lost constant font or illustration")
    quote_file.write_text(existing[:existing.index(marker)]+q,"utf-8")

    preloader=java/"MedicineHomeArtwork.kt"
    pre=preloader.read_text("utf-8")
    pre=replace_one(pre,
        "        R.drawable.iman_v38_reminder,",
        "        R.drawable.iman_v38_reminder,\n"
        "        R.drawable.iman_v39_header,\n"
        "        R.drawable.iman_v39_relief,",
        "preload new identity and bas-relief without frame work")
    preloader.write_text(pre,"utf-8")

    # Protected: books, audio reader, chapter state, notes, 5 routes and wallpaper.
    if digest(reader)!=reader_before or digest(app)!=app_before or NAV not in app.read_text("utf-8"):
        raise RuntimeError("v39 altered native reader or bottom navigation")
    for name,before in book_hashes.items():
        if digest(assets/name)!=before:
            raise RuntimeError("v39 changed source book or quiz/notes data: "+name)
    if quote_file.read_text("utf-8").count('FeaturedExcerpt("iman-chapter-')!=79:
        raise RuntimeError("v39 lost a source quote")
    if "@mipmap/iman_v39_launcher" not in (dest/"app/src/main/AndroidManifest.xml").read_text("utf-8"):
        raise RuntimeError("v39 system app icon not installed")
    print("PASS v39.1: 79 stable handwriting+permanent relief, matching header and launcher; reading/state preserved")


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--dest",type=Path,required=True)
    args=parser.parse_args()
    build_v39(Path(__file__).resolve().parents[1],args.dest)
