"""v0.32: screenshot-driven native Home correction with fail-closed regressions.

Source: signed v31. One original wallpaper is shared with five-tab navbar.
All 131 chapters, 242 notes, 524 tests, 79 quotes and user settings intact.
"""
from pathlib import Path
import argparse, hashlib, json
from PIL import Image
from scripts.build_iman_v31 import build_v31
from scripts.build_iman_v20 import APP,replace_one,NAV
from scripts.build_iman_v23 import install_variant4_quote
from scripts.iman_v28_scale import fill_artwork

ICONS=("contents","collections","glossary","bookmarks")

def build_v32(kit:Path,dest:Path):
    build_v31(kit,dest)
    gradle=dest/"app/build.gradle"
    text=gradle.read_text("utf-8")
    for before,after in (
        ("versionCode 31","versionCode 32"),
        ("versionName '0.31.0'","versionName '0.32.0'"),
        ("applicationIdSuffix '.preview31'","applicationIdSuffix '.preview32'"),
    ):
        text=replace_one(text,before,after,"v32 version")
    gradle.write_text(text,"utf-8")

    java=dest/APP
    res=dest/"app/src/main/res"
    drawable=res/"drawable-nodpi"
    assets=dest/"app/src/main/assets"
    app=java/"App.kt"
    reader=java/"Reader.kt"
    home=java/"ModernEditorialHome.kt"
    quote=java/"ImanQuoteCarousel.kt"
    preload=java/"MedicineHomeArtwork.kt"
    app_before=app.read_bytes()
    reader_before=reader.read_bytes()
    others={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
            for p in java.glob("*.kt")
            if p.name not in ("ModernEditorialHome.kt","ImanQuoteCarousel.kt",
                              "MedicineHomeArtwork.kt")}
    book_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in assets.iterdir() if p.is_file()}
    protected_nav={
        p.relative_to(res).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for p in res.rglob("*") if p.is_file() and
        (p.name.startswith("nav_") or p.name.startswith("ic_nav_"))
    }
    wall=drawable/"iman_v29_unified_home.webp"
    wall_digest=hashlib.sha256(wall.read_bytes()).hexdigest()

    # Pre-bake a slightly fuller visual silhouette, preserving transparent
    # outer pixels and no runtime filter/blur.
    for name in (*ICONS,"reminder"):
        previous=drawable/f"iman_v28_{name}.webp" if name!="reminder" else drawable/"iman_v30_reminder.webp"
        with Image.open(previous) as original:
            corrected=fill_artwork(original,pad=0.015 if name!="reminder" else 0.0)
        new=drawable/f"iman_v32_{name}.webp"
        corrected.save(new,"WEBP",quality=95,method=6)
        if new.stat().st_size<3000 or corrected.getpixel((0,0))[3]!=0:
            raise RuntimeError("v32 corrected artwork invalid: "+name)

    candidate_home=(kit/"scripts/ReferenceHomeV32.kt").read_text("utf-8")
    for required in (
        "ModernEditorialHomeScreen(", "EditorialBookSection(",
        "EditorialResumeCard(", "LinearProgressIndicator(",
        ".clipToBounds()", ".padding(bottom = 76.dp)",
        "Route.Book", "Route.Collections", "Route.Glossary",
        "Route.Bookmarks", "Route.Progress",
        "Route.Reader(it.id, resume = last != null)",
        "Route.CollectionDetail(entry.id)",
        'item(key = "library-four")', "book.collections.take(2)",
        *("R.drawable.iman_v32_"+key for key in ICONS),
    ):
        if required not in candidate_home:
            raise RuntimeError("v32 Home missing "+required)
    if ".statusBarsPadding()" in candidate_home:
        raise RuntimeError("v32 double system bar inset was reintroduced")
    if "BorderStroke(" in candidate_home or "R.drawable.iman_v29_unified_home" in candidate_home:
        raise RuntimeError("v32 added a second background or frame")
    home.write_text(candidate_home,"utf-8")

    candidate_quote=(kit/"scripts/ReferenceQuoteV32.kt").read_text("utf-8")
    for required in ("Crossfade(","tween(180)","maxLines = 5",
                     'Text("Другая ↻"',"q.text.length <= 120",
                     "R.drawable.iman_v32_reminder",
                     "Route.Reader(q.chapterId, q.blockId)",
                     "Modifier.fillMaxWidth(0.62f)",
                     "width(239.dp).height(153.dp)"):
        if required not in candidate_quote:
            raise RuntimeError("v32 quote behavior lost "+required)
    quote.write_text(install_variant4_quote(quote.read_text("utf-8"),candidate_quote),"utf-8")

    pre=preload.read_text("utf-8")
    for name in ICONS:
        pre=replace_one(pre,f"R.drawable.iman_v28_{name}",
                        f"R.drawable.iman_v32_{name}",
                        "v32 original background IO preloading")
    pre=replace_one(pre,"R.drawable.iman_v30_reminder",
                    "R.drawable.iman_v32_reminder","v32 hero preloading")
    preload.write_text(pre,"utf-8")

    if app.read_bytes()!=app_before or reader.read_bytes()!=reader_before:
        raise RuntimeError("v32 native app navigation or book reader altered")
    for name,sha in others.items():
        if hashlib.sha256((java/name).read_bytes()).hexdigest()!=sha:
            raise RuntimeError("v32 unrelated Kotlin changed "+name)
    for name,sha in book_hashes.items():
        if hashlib.sha256((assets/name).read_bytes()).hexdigest()!=sha:
            raise RuntimeError("v32 data changed "+name)
    for path,sha in protected_nav.items():
        if hashlib.sha256((res/path).read_bytes()).hexdigest()!=sha:
            raise RuntimeError("v32 navigation art changed "+path)
    if hashlib.sha256(wall.read_bytes()).hexdigest()!=wall_digest:
        raise RuntimeError("v32 textured reference paper changed")
    a=app.read_text("utf-8")
    if (a.count("R.drawable.iman_v29_unified_home")!=1 or NAV not in a or
        ".background(if (seamlessHome) Color.Transparent" not in a.split(NAV,1)[1]):
        raise RuntimeError("v32 one wallpaper and tab bar not preserved")
    featured=json.loads((assets/"featured_quotes.json").read_text("utf-8"))
    book=json.loads((assets/"book.json").read_text("utf-8"))
    quiz=json.loads((assets/"quiz.json").read_text("utf-8"))
    if (len(book["chapters"]),len(featured),sum(len(q) for q in quiz["chapters"].values()))!=(131,79,524):
        raise RuntimeError("v32 content inventory changed")
    if any((dest/"app/src/main").rglob("*.pdf")):
        raise RuntimeError("v32 unexpectedly includes PDF")
    print("PASS v32: one background, no double status inset, clipped home content, 5 enlarged original artworks, native data/routes intact")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--dest",required=True,type=Path)
    build_v32(Path(__file__).resolve().parents[1],parser.parse_args().dest)
