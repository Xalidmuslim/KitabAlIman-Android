"""v0.26: small, fail-closed native Android change over successful v0.25.

All six illustrations remain individual images. The background is still owned by
the same root Box behind Home and the native bottom navigation, never a Card.
No runtime blur or changes to reader, route state, bookmarks or book data.
"""
from pathlib import Path
import argparse
import hashlib
import json

from scripts.build_iman_v25 import build_v25, ARTWORK_NAMES
from scripts.build_iman_v20 import APP, NAV, replace_one
from scripts.iman_v26_finish import generate_assets

def build_v26(kit:Path,dest:Path)->None:
    build_v25(kit,dest)
    gradle=dest/"app/build.gradle"
    data=gradle.read_text("utf-8")
    for old,new in (
        ("versionCode 25","versionCode 26"),
        ("versionName '0.25.0'","versionName '0.26.0'"),
        ("applicationIdSuffix '.preview25'","applicationIdSuffix '.preview26'"),
    ):
        data=replace_one(data,old,new,"v26 isolated version")
    gradle.write_text(data,"utf-8")

    java=dest/APP
    assets=dest/"app/src/main/assets"
    res=dest/"app/src/main/res"
    drawable=res/"drawable-nodpi"
    app_path=java/"App.kt"
    home_path=java/"ModernEditorialHome.kt"
    quote_path=java/"ImanQuoteCarousel.kt"
    preload_path=java/"MedicineHomeArtwork.kt"
    reader_before=(java/"Reader.kt").read_bytes()
    app_before=app_path.read_text("utf-8")
    all_other={p.name:p.read_bytes() for p in java.glob("*.kt")
               if p.name not in ("App.kt","ModernEditorialHome.kt",
                                 "ImanQuoteCarousel.kt","MedicineHomeArtwork.kt")}
    protected_assets={name:hashlib.sha256((assets/name).read_bytes()).hexdigest()
                      for name in ("book.json","quiz.json","featured_quotes.json")}
    protected_nav={
        p.relative_to(res).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for p in res.rglob("*") if p.is_file() and
        (p.name.startswith("nav_") or p.name.startswith("ic_nav_"))
    }
    original_reading_paper=drawable/"reader_parchment_source.png"
    reading_paper_sha=hashlib.sha256(original_reading_paper.read_bytes()).hexdigest()

    # Graphics are rendered once during build; Compose only draws cached bitmaps.
    generate_assets(kit/"assets/ui/v25",drawable)

    app=replace_one(app_before,
        "R.drawable.iman_v25_unified_home","R.drawable.iman_v26_unified_home",
        "v26 one root background")
    if app.replace("R.drawable.iman_v26_unified_home",
                   "R.drawable.iman_v25_unified_home")!=app_before:
        raise RuntimeError("v26: navigation, other screens or app state changed")
    if (app.count("R.drawable.iman_v26_unified_home")!=1 or
        "seamlessHome = seamlessHome" not in app or NAV not in app):
        raise RuntimeError("v26: one-background-five-tabs invariant broken")
    app_path.write_text(app,"utf-8")

    for file in (home_path,quote_path):
        source=file.read_text("utf-8")
        original=source
        names=(("contents","collections","glossary","bookmarks")
               if file==home_path else ("reminder",))
        for name in names:
            source=replace_one(source,
                f"R.drawable.iman_v25_{name}",
                f"R.drawable.iman_v26_{name}",
                "v26 independent image "+name)
        restored=source
        for name in names:
            restored=restored.replace(f"R.drawable.iman_v26_{name}",
                                     f"R.drawable.iman_v25_{name}")
        if restored!=original:
            raise RuntimeError("v26: unrelated composable behavior changed")
        file.write_text(source,"utf-8")

    preload_before=preload_path.read_text("utf-8")
    preload=preload_before
    for name in ARTWORK_NAMES:
        preload=replace_one(preload,
            f"R.drawable.iman_v25_{name}",
            f"R.drawable.iman_v26_{name}",
            "v26 IO bitmap preloading "+name)
    preload_path.write_text(preload,"utf-8")

    for name,bytes_before in all_other.items():
        if (java/name).read_bytes()!=bytes_before:
            raise RuntimeError("v26: protected Kotlin file changed "+name)
    if (java/"Reader.kt").read_bytes()!=reader_before:
        raise RuntimeError("v26: existing reader or storage changed")
    for name,digest in protected_assets.items():
        if hashlib.sha256((assets/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError("v26: content of book/quiz/reminders changed")
    for path,digest in protected_nav.items():
        if hashlib.sha256((res/path).read_bytes()).hexdigest()!=digest:
            raise RuntimeError("v26: native navigation icon changed")
    if hashlib.sha256(original_reading_paper.read_bytes()).hexdigest()!=reading_paper_sha:
        raise RuntimeError("v26: reading paper preferences changed")
    for name in ARTWORK_NAMES:
        path=drawable/f"iman_v26_{name}.webp"
        if not path.is_file() or path.stat().st_size<=2000:
            raise RuntimeError("v26: processed artwork missing "+name)
        if f"R.drawable.iman_v26_{name}" not in preload:
            raise RuntimeError("v26: off-main-thread icon preload missing "+name)
    home=home_path.read_text("utf-8")
    quote=quote_path.read_text("utf-8")
    if ("Column(modifier.fillMaxSize())" not in home or
        "R.drawable.iman_v26_unified_home" in home or
        "R.drawable.iman_v26_unified_home" in quote or
        ".background(if (seamlessHome) Color.Transparent" not in app.split(NAV,1)[1]):
        raise RuntimeError("v26: second paper panel or opaque navigation discovered")
    entries=json.loads((assets/"featured_quotes.json").read_text("utf-8"))
    if len(entries)!=79 or len({q["text"] for q in entries})!=79:
        raise RuntimeError("v26: quote inventory changed")
    if list((dest/"app/src/main").rglob("*.pdf")):
        raise RuntimeError("v26: unexpected bundled source PDF")
    print("PASS v0.26: one textured page under all five tabs, pre-baked matte artwork, protected book and user state")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--dest",type=Path,required=True)
    args=parser.parse_args()
    build_v26(Path(__file__).resolve().parents[1],args.dest)
