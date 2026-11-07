"""Install the approved reminder-card artwork with no changes to books or navigation."""
from pathlib import Path
import argparse
import hashlib
from PIL import Image
from scripts.build_iman_v14 import build_v14, one

ART_SHA256 = "71274d42ab4f8a2f390607f01b83ce1e0a4828466223236b6636c2e57732539f"
ART_SIZE = (850,425)
JAVA = Path("app/src/main/java/com/xalid/meditsinaproroka/nativeapp")

def validate_card_source(source):
    for expected in (
        'R.drawable.iman_quote_v15',
        'ContentScale.FillBounds',
        'Route.Reader(q.chapterId, q.blockId)',
        'remember(prefs)',
        'mutableIntStateOf(initial)',
        'Text("Другая ↻"',
        'Modifier.fillMaxWidth(0.70f)',
    ):
        if expected not in source:
            raise RuntimeError("Reminder-card regression: " + expected)
    if source.count('Text("Другая ↻"') != 1:
        raise RuntimeError("Duplicate or missing quote rotation control")
    if source.index('Text("Другая ↻"') > source.index('Text(q.text'):
        raise RuntimeError("Rotation control overlaps book artwork")
    if source.count('FeaturedExcerpt("iman-chapter-') != 7:
        raise RuntimeError("Original source-verified quotations must remain")

def install_artwork(kit, dest):
    src = kit/"assets/ui/iman_quote_v15.webp"
    data = src.read_bytes()
    if hashlib.sha256(data).hexdigest()!=ART_SHA256:
        raise RuntimeError("Approved artwork does not match checksum")
    with Image.open(src) as art:
        if art.format!="WEBP" or art.size!=ART_SIZE:
            raise RuntimeError("Unexpected background format/dimensions")
    drawable = dest/"app/src/main/res/drawable-nodpi"
    drawable.mkdir(parents=True,exist_ok=True)
    (drawable/"iman_quote_v15.webp").write_bytes(data)
    return len(data)

def build_v15(kit,dest):
    build_v14(kit,dest)
    gradle=dest/"app/build.gradle"
    version=gradle.read_text("utf-8")
    for before,after in [
        ("versionCode 14","versionCode 15"),
        ("versionName '0.14.0'","versionName '0.15.0'"),
        ("applicationIdSuffix '.preview14'","applicationIdSuffix '.preview15'"),
    ]:
        version=one(version,before,after,"version")
    gradle.write_text(version,"utf-8")
    java=dest/JAVA
    quote=(java/"ImanQuoteCarousel.kt").read_text("utf-8")
    validate_card_source(quote)
    android=java/"MedicineHomeArtwork.kt"
    preload=android.read_text("utf-8")
    preload=one(preload,'        R.drawable.iman_quote_background,',
        '        R.drawable.iman_quote_background,\n        R.drawable.iman_quote_v15,',
        "preload one efficient WebP off the main thread")
    android.write_text(preload,"utf-8")
    size=install_artwork(kit,dest)
    if list((dest/"app/src/main").rglob("*.pdf")):
        raise RuntimeError("PDF resource forbidden")
    print(f"v0.15 verified reminder artwork installed ({size} bytes), "
          "old book, quote mappings and bottom navigation preserved")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dest",type=Path,required=True)
    args=p.parse_args()
    build_v15(Path(__file__).resolve().parents[1],args.dest)
