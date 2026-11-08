"""v0.35: apply approved matte artwork grading without altering native app behavior.

The existing verified v34 (one paper, status-safe header, clipped bottom nav)
is the base. Five independently generated WebP drawables are toned offline,
then substituted in Home and reminder. All source book data and user state are
protected by exact SHA-256 comparisons.
"""
from pathlib import Path
import argparse,hashlib,json
from scripts.build_iman_v34 import build_v34
from scripts.build_iman_v20 import APP,replace_one,NAV
from scripts.iman_v35_art import install,ICONS

def build_v35(kit:Path,dest:Path):
    build_v34(kit,dest)
    gradle=dest/"app/build.gradle"
    text=gradle.read_text("utf-8")
    for old,new in (
        ("versionCode 34","versionCode 35"),
        ("versionName '0.34.0'","versionName '0.35.0'"),
        ("applicationIdSuffix '.preview34'","applicationIdSuffix '.preview35'"),
    ):
        text=replace_one(text,old,new,"v35 package")
    gradle.write_text(text,"utf-8")

    java=dest/APP
    home=java/"ModernEditorialHome.kt"
    quote=java/"ImanQuoteCarousel.kt"
    preload=java/"MedicineHomeArtwork.kt"
    app=java/"App.kt"
    reader=java/"Reader.kt"
    app_before=app.read_bytes()
    reader_before=reader.read_bytes()
    other_sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in java.glob("*.kt")
                   if p.name not in ("ModernEditorialHome.kt",
                                     "ImanQuoteCarousel.kt","MedicineHomeArtwork.kt")}
    assets=dest/"app/src/main/assets"
    book_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in assets.iterdir() if p.is_file()}
    res=dest/"app/src/main/res"
    drawable=res/"drawable-nodpi"
    nav_icon_hashes={p.relative_to(res).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in res.rglob("*") if p.is_file() and
                     (p.name.startswith("nav_") or p.name.startswith("ic_nav_"))}
    wallpaper=drawable/"iman_v29_unified_home.webp"
    wallpaper_hash=hashlib.sha256(wallpaper.read_bytes()).hexdigest()

    install(drawable,drawable)

    home_before=home.read_text("utf-8")
    home_after=home_before
    for name in ICONS:
        home_after=replace_one(home_after,f"R.drawable.iman_v32_{name}",
                               f"R.drawable.iman_v35_{name}","softened library "+name)
    home.write_text(home_after,"utf-8")

    quote_before=quote.read_text("utf-8")
    target_quote=replace_one(quote_before,
        "R.drawable.iman_v32_reminder","R.drawable.iman_v35_reminder",
        "softened hero artwork")
    target_quote=replace_one(target_quote,
        ".width(239.dp).height(153.dp)",
        ".width(249.dp).height(163.dp)",
        "hero size closer to approved reference")
    target_quote=replace_one(target_quote,
        ".offset(y = (-3).dp)",
        ".offset(y = (2).dp)",
        "hero baseline closer to chapter divider")
    if target_quote.count("maxLines = 5")!=1 or "q.text.length <= 120" not in target_quote:
        raise RuntimeError("v35 long-quote protection changed")
    quote.write_text(target_quote,"utf-8")

    preload_before=preload.read_text("utf-8")
    pre=preload_before
    for name in (*ICONS,"reminder"):
        pre=replace_one(pre,f"R.drawable.iman_v32_{name}",
                        f"R.drawable.iman_v35_{name}",
                        "preload toned reference "+name+" on original IO path")
    preload.write_text(pre,"utf-8")

    if reader.read_bytes()!=reader_before or app.read_bytes()!=app_before:
        raise RuntimeError("v35 unexpectedly changed reader/router/bottom navigation")
    for name,sha in other_sources.items():
        if hashlib.sha256((java/name).read_bytes()).hexdigest()!=sha:
            raise RuntimeError("v35 unrelated native Kotlin source changed: "+name)
    for name,sha in book_hashes.items():
        if hashlib.sha256((assets/name).read_bytes()).hexdigest()!=sha:
            raise RuntimeError("v35 text/quiz/quotes changed: "+name)
    for name,sha in nav_icon_hashes.items():
        if hashlib.sha256((res/name).read_bytes()).hexdigest()!=sha:
            raise RuntimeError("v35 original nav artwork changed: "+name)
    if hashlib.sha256(wallpaper.read_bytes()).hexdigest()!=wallpaper_hash:
        raise RuntimeError("v35 introduced second background or modified paper")
    a=app.read_text("utf-8")
    if a.count("R.drawable.iman_v29_unified_home")!=1 or NAV not in a:
        raise RuntimeError("v35 did not preserve the original shared background")
    h=home.read_text("utf-8")
    if h.count(".statusBarsPadding()")!=1 or ".clipToBounds()" not in h:
        raise RuntimeError("v35 status/navigation safe-area regression")
    if "Crossfade(" not in target_quote or "Route.Reader(q.chapterId, q.blockId)" not in target_quote:
        raise RuntimeError("v35 quote transitions or source link lost")
    quotes=json.loads((assets/"featured_quotes.json").read_text("utf-8"))
    chapters=json.loads((assets/"book.json").read_text("utf-8"))
    if (len(quotes),len(chapters["chapters"]))!=(79,131):
        raise RuntimeError("v35 original book inventory changed")
    print("PASS v35: five softened matte icons, original wallpaper/reader/navigation and protected 131 chapters /79 excerpts")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--dest",type=Path,required=True)
    build_v35(Path(__file__).resolve().parents[1],parser.parse_args().dest)
