"""v0.28 minimal correction: increase visible subject fill, not UI cards.

Verified parent v0.27. Root wallpaper and bottom nav remain bit-for-bit;
Reader, source text, quizzes and persisted preferences are protected.
"""
from pathlib import Path
import argparse, hashlib, json, shutil

from scripts.build_iman_v27 import build_v27
from scripts.build_iman_v20 import APP, NAV, replace_one
from scripts.iman_v28_scale import install

PICTURES=("contents","collections","glossary","bookmarks","reminder")

def build_v28(kit:Path,dest:Path):
    build_v27(kit,dest)
    gradle=dest/"app/build.gradle"
    before=gradle.read_text("utf-8")
    result=before
    for old,new in (
        ("versionCode 27","versionCode 28"),
        ("versionName '0.27.0'","versionName '0.28.0'"),
        ("applicationIdSuffix '.preview27'","applicationIdSuffix '.preview28'"),
    ):
        result=replace_one(result,old,new,"v28 version")
    gradle.write_text(result,"utf-8")

    java=dest/APP
    res=dest/"app/src/main/res"
    drawable=res/"drawable-nodpi"
    home=java/"ModernEditorialHome.kt"
    quote=java/"ImanQuoteCarousel.kt"
    preload=java/"MedicineHomeArtwork.kt"
    app_path=java/"App.kt"
    app_before=app_path.read_bytes()
    reader_before=(java/"Reader.kt").read_bytes()
    other_java={p.name:p.read_bytes() for p in java.glob("*.kt") if
                p.name not in ("ModernEditorialHome.kt","ImanQuoteCarousel.kt",
                               "MedicineHomeArtwork.kt")}
    protected_nav={
        p.relative_to(res).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for p in res.rglob("*") if p.is_file() and
        (p.name.startswith("nav_") or p.name.startswith("ic_nav_"))
    }
    assets=dest/"app/src/main/assets"
    book_hashes={name:hashlib.sha256((assets/name).read_bytes()).hexdigest()
                 for name in ("book.json","quiz.json","featured_quotes.json")}
    wallpaper=drawable/"iman_v27_unified_home.webp"
    wallpaper_sha=hashlib.sha256(wallpaper.read_bytes()).hexdigest()

    install(kit/"assets/ui/v27",drawable)
    home_before=home.read_text("utf-8")
    home_after=home_before
    for name in PICTURES[:-1]:
        home_after=replace_one(home_after,
            f"R.drawable.iman_v27_{name}",f"R.drawable.iman_v28_{name}",
            "v28 library visible content scale "+name)
    home.write_text(home_after,"utf-8")
    quote_before=quote.read_text("utf-8")
    quote_after=replace_one(quote_before,"R.drawable.iman_v27_reminder",
                            "R.drawable.iman_v28_reminder","v28 reminder drawing")
    quote_after=replace_one(quote_after,
        "Column(Modifier.weight(0.61f))",
        "Column(Modifier.weight(0.57f))","v28 more hero art space")
    quote_after=replace_one(quote_after,
        "modifier = Modifier.weight(0.39f).height(128.dp)",
        "modifier = Modifier.weight(0.43f).height(152.dp)",
        "v28 restore illustrated quote proportions")
    quote.write_text(quote_after,"utf-8")
    preload_before=preload.read_text("utf-8")
    preload_after=preload_before
    for name in PICTURES:
        preload_after=replace_one(preload_after,
            f"R.drawable.iman_v27_{name}",f"R.drawable.iman_v28_{name}",
            "v28 use original IO cache "+name)
    preload.write_text(preload_after,"utf-8")

    # The old and new app shells are byte identical by construction.
    if (app_path.read_bytes()!=app_before or
        (java/"Reader.kt").read_bytes()!=reader_before):
        raise RuntimeError("v28 modified navigation, preference or reading UI")
    for k,v in other_java.items():
        if (java/k).read_bytes()!=v:
            raise RuntimeError("v28 changed unrelated Kotlin: "+k)
    for name,digest in book_hashes.items():
        if hashlib.sha256((assets/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError("v28 edited user-facing book content: "+name)
    for name,digest in protected_nav.items():
        if hashlib.sha256((res/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError("v28 changed original navigation artwork: "+name)
    if hashlib.sha256(wallpaper.read_bytes()).hexdigest()!=wallpaper_sha:
        raise RuntimeError("v28 changed the approved continuous paper backdrop")
    q=quote.read_text("utf-8")
    if ("q.text.length <= 120" not in q or "maxLines = 5" not in q or
        "Route.Reader(q.chapterId, q.blockId)" not in q):
        raise RuntimeError("v28 quote text safety lost")
    a=app_path.read_text("utf-8")
    if (a.count("R.drawable.iman_v27_unified_home")!=1 or NAV not in a or
        ".background(if (seamlessHome) Color.Transparent" not in a.split(NAV,1)[1]):
        raise RuntimeError("v28 seamless nav background changed")
    quotes=json.loads((assets/"featured_quotes.json").read_text("utf-8"))
    if len(quotes)!=79:
        raise RuntimeError("v28 changed reminder inventory")
    print("PASS v0.28 subject size fixed, one paper under bottom nav, 131 chapters unchanged")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--dest",type=Path,required=True)
    options=parser.parse_args()
    build_v28(Path(__file__).resolve().parents[1],options.dest)
