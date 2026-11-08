"""v0.24 visual implementation of user's approved screen in native Compose.

Builds on verified v0.23. Exact reader Light paper, four original vector-drawn
matte WebP library icons, one separately extracted reminder illustration.
No user library, chapter text, quiz, preference, route or TTS change.
"""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import io
from PIL import Image

from scripts.build_iman_v23 import build_v23, install_variant4_quote, ICON_NAMES
from scripts.build_iman_v20 import APP, NAV, replace_one
from scripts.iman_v24_artwork import install as create_original_icons

def build_v24(kit:Path, dest:Path):
    build_v23(kit,dest)
    gradle=dest/"app/build.gradle"
    text=gradle.read_text("utf-8")
    for old,new in (
        ("versionCode 23", "versionCode 24"),
        ("versionName '0.23.0'", "versionName '0.24.0'"),
        ("applicationIdSuffix '.preview23'", "applicationIdSuffix '.preview24'"),
    ):
        text=replace_one(text,old,new,"v24 version")
    gradle.write_text(text,"utf-8")

    java=dest/APP
    res=dest/"app/src/main/res"
    drawable=res/"drawable-nodpi"
    assets=dest/"app/src/main/assets"
    original_reader=(java/"Reader.kt").read_bytes()
    original_nav=(java/"App.kt").read_bytes()
    old_files={p.name:p.read_bytes() for p in java.glob("*.kt")
               if p.name not in ("ModernEditorialHome.kt",
                                 "ImanQuoteCarousel.kt",
                                 "MedicineHomeArtwork.kt")}
    book_hashes={name:hashlib.sha256((assets/name).read_bytes()).hexdigest()
                 for name in ("book.json","quiz.json","featured_quotes.json")}
    nav_icon_hashes={
        p.relative_to(res).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for p in res.rglob("*") if p.is_file() and
        (p.name.startswith("nav_") or p.name.startswith("ic_nav_"))
    }
    original_paper=drawable/"reader_parchment_source.png"
    original_paper_hash=hashlib.sha256(original_paper.read_bytes()).hexdigest()

    home=(kit/"scripts/EditorialLightHomeV24.kt").read_text("utf-8")
    quote=(kit/"scripts/EditorialLightQuoteV24.kt").read_text("utf-8")
    required_home=(
        'readerPaperOverlay("light")',
        'R.drawable.reader_parchment_source',
        "ContentScale.FillBounds",
        "Modifier.matchParentSize()",
        "ModernEditorialHomeScreen(",
        "EditorialResumeCard(",
        "LinearProgressIndicator(",
        "EditorialBookSection(",
        "Route.Book",
        "Route.Collections",
        "Route.Glossary",
        "Route.Bookmarks",
        "Route.Progress",
        "Route.Reader(it.id, resume = last != null)",
        "Route.CollectionDetail(entry.id)",
        'item(key = "library-four")',
    )
    for token in required_home:
        if token not in home:
            raise RuntimeError("v24 home feature missing: "+token)
    for name in ICON_NAMES:
        if f"R.drawable.iman_v24_{name}" not in home:
            raise RuntimeError("v24 independent library icon not wired: "+name)
        if f"R.drawable.iman_v17_{name}" not in home:
            raise RuntimeError("v24 dark-theme fallback changed: "+name)
        if f"R.drawable.iman_v23_{name}" in home:
            raise RuntimeError("v24 still uses prior atlas icon: "+name)
    if "BorderStroke(" in home or "StandaloneBottomNav(" in home:
        raise RuntimeError("v24 introduced framed UI or duplicate navigation")
    for token in (
        "R.drawable.iman_v24_reminder", "Crossfade(", "tween(180)",
        'Text("Другая ↻"', "Route.Reader(q.chapterId, q.blockId)",
        "maxLines = 5", "border = null",
    ):
        if token not in quote:
            raise RuntimeError("v24 reminder missing or changed: "+token)

    (java/"ModernEditorialHome.kt").write_text(home,"utf-8")
    quote_path=java/"ImanQuoteCarousel.kt"
    quote_path.write_text(
        install_variant4_quote(quote_path.read_text("utf-8"),quote),
        "utf-8",
    )

    # Four separately drawn illustrations; never cut out of a screenshot.
    create_original_icons(drawable)
    for name in ICON_NAMES:
        path=drawable/f"iman_v24_{name}.webp"
        with Image.open(path) as img:
            img.load()
            if img.size!=(240,180) or img.mode!="RGBA":
                raise RuntimeError("v24 original library illustration invalid: "+name)

    # User-approved reminder artwork is an independent drawable. Only this
    # asset is taken from the reference; no UI labels are rasterized into it.
    encoded=(kit/"assets/ui/v24/iman_v24_reminder.b64").read_text("ascii")
    data=base64.b64decode(encoded.strip(),validate=True)
    with Image.open(io.BytesIO(data)) as img:
        img.load()
        if img.size!=(248,131) or img.mode!="RGBA":
            raise RuntimeError("v24 reminder art size/alpha invalid")
    (drawable/"iman_v24_reminder.webp").write_bytes(data)

    preload=java/"MedicineHomeArtwork.kt"
    source=preload.read_text("utf-8")
    source=replace_one(source,
        "        R.drawable.iman_v23_bookmarks,",
        """        R.drawable.iman_v23_bookmarks,
        R.drawable.reader_parchment_source,
        R.drawable.iman_v24_contents,
        R.drawable.iman_v24_collections,
        R.drawable.iman_v24_glossary,
        R.drawable.iman_v24_bookmarks,
        R.drawable.iman_v24_reminder,""",
        "preload all v24 raster drawables on background IO thread")
    preload.write_text(source,"utf-8")

    for name,data_before in old_files.items():
        if (java/name).read_bytes()!=data_before:
            raise RuntimeError("v24 unrelated Kotlin source changed: "+name)
    if (java/"Reader.kt").read_bytes()!=original_reader:
        raise RuntimeError("v24 modified Reader or its existing paper presets")
    if (java/"App.kt").read_bytes()!=original_nav or NAV not in original_nav.decode("utf-8"):
        raise RuntimeError("v24 modified five-tab navigation or app state")
    for path,digest in nav_icon_hashes.items():
        if hashlib.sha256((res/path).read_bytes()).hexdigest()!=digest:
            raise RuntimeError("v24 altered navigation icon: "+path)
    if hashlib.sha256(original_paper.read_bytes()).hexdigest()!=original_paper_hash:
        raise RuntimeError("v24 modified reader paper bitmap")
    for name,digest in book_hashes.items():
        if hashlib.sha256((assets/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError("v24 edited book, quotes or quiz data")
    quotes=json.loads((assets/"featured_quotes.json").read_text("utf-8"))
    if len(quotes)!=79 or len({q["text"] for q in quotes})!=79:
        raise RuntimeError("v24 missing quotations")
    if list((dest/"app/src/main").rglob("*.pdf")):
        raise RuntimeError("v24 unexpectedly bundles source PDF")
    print("PASS v0.24 original four book icons, exact Light reader paper, linked quote image and 131 chapters")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--dest",type=Path,required=True)
    args=parser.parse_args()
    build_v24(Path(__file__).resolve().parents[1],args.dest)
