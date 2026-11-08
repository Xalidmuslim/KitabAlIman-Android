"""v0.30: screenshot-driven correction of real-device spacing and hero image size.

Based on signed v0.29. The *only* behavior changes are presentation of the
existing home and existing 79 rotating excerpts. App shell, wallpaper, reader,
quizzes, navigation and user data remain byte-for-byte unchanged.
"""
from pathlib import Path
import argparse, hashlib, json

from PIL import Image

from scripts.build_iman_v29 import build_v29
from scripts.build_iman_v20 import APP, NAV, replace_one
from scripts.build_iman_v23 import install_variant4_quote
from scripts.iman_v28_scale import fill_artwork


def build_v30(kit:Path,dest:Path):
    build_v29(kit,dest)
    gradle=dest/"app/build.gradle"
    text=gradle.read_text("utf-8")
    for before,after in (
        ("versionCode 29","versionCode 30"),
        ("versionName '0.29.0'","versionName '0.30.0'"),
        ("applicationIdSuffix '.preview29'","applicationIdSuffix '.preview30'"),
    ):
        text=replace_one(text,before,after,"v30 package identity")
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
    original_files={
        p.name:p.read_bytes() for p in java.glob("*.kt")
        if p.name not in ("ModernEditorialHome.kt",
                          "ImanQuoteCarousel.kt","MedicineHomeArtwork.kt")
    }
    book_hashes={
        name:hashlib.sha256((assets/name).read_bytes()).hexdigest()
        for name in ("book.json","quiz.json","featured_quotes.json")
    }
    protected_nav={
        p.relative_to(res).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for p in res.rglob("*") if p.is_file() and
        (p.name.startswith("nav_") or p.name.startswith("ic_nav_"))
    }
    wallpaper=drawable/"iman_v29_unified_home.webp"
    wallpaper_sha=hashlib.sha256(wallpaper.read_bytes()).hexdigest()

    # Reframe the already approved subject. Keep its soft alpha perimeter.
    with Image.open(drawable/"iman_v28_reminder.webp") as src:
        framed=fill_artwork(src,pad=0.0)
    if framed.size!=(380,245) or framed.getpixel((0,0))[3]!=0:
        raise RuntimeError("v30 damaged original feathered reminder subject")
    framed.save(drawable/"iman_v30_reminder.webp","WEBP",quality=96,method=6)

    candidate_home=(kit/"scripts/ReferenceHomeV30.kt").read_text("utf-8")
    for required in (
        "book.collections.take(2)","LinearProgressIndicator(",
        "Route.Book", "Route.Collections", "Route.Glossary","Route.Bookmarks",
        "Route.Progress","Route.CollectionDetail(entry.id)",
        "Route.Reader(it.id, resume = last != null)",
        "verticalArrangement = Arrangement.spacedBy(3.dp)",
        "Color.Transparent","R.drawable.iman_v28_contents",
    ):
        if required not in candidate_home:
            raise RuntimeError("v30 lost functional home route: "+required)
    if "R.drawable.iman_v29_unified_home" in candidate_home or "BorderStroke(" in candidate_home:
        raise RuntimeError("v30 created an unwanted paper layer / frame")
    home.write_text(candidate_home,"utf-8")

    candidate_quote=(kit/"scripts/ReferenceQuoteV30.kt").read_text("utf-8")
    for required in (
        "Box(", "height(120.dp)", "width(220.dp).height(142.dp)",
        "fillMaxWidth(0.66f)","R.drawable.iman_v30_reminder",
        "q.text.length <= 120", "Crossfade(", "tween(180)",
        "maxLines = 5", 'Text("Другая ↻"',
        "Route.Reader(q.chapterId, q.blockId)",
    ):
        if required not in candidate_quote:
            raise RuntimeError("v30 quote dynamic behavior missing: "+required)
    quote.write_text(
        install_variant4_quote(quote.read_text("utf-8"),candidate_quote),
        "utf-8",
    )
    original_preload=preload.read_text("utf-8")
    preload.write_text(replace_one(
        original_preload,
        "R.drawable.iman_v28_reminder",
        "R.drawable.iman_v30_reminder",
        "v30 off-main-thread preloading"),
        "utf-8",
    )

    if app.read_bytes()!=app_before or reader.read_bytes()!=reader_before:
        raise RuntimeError("v30 altered native tab routing / reader / user state")
    for name,blob in original_files.items():
        if (java/name).read_bytes()!=blob:
            raise RuntimeError("v30 touched protected Kotlin file "+name)
    for name,digest in book_hashes.items():
        if hashlib.sha256((assets/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError("v30 modified source book, quizzes or quotes")
    for name,digest in protected_nav.items():
        if hashlib.sha256((res/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError("v30 replaced navigation artwork")
    if hashlib.sha256(wallpaper.read_bytes()).hexdigest()!=wallpaper_sha:
        raise RuntimeError("v30 changed approved uninterrupted parchment")
    nav=app.read_text("utf-8")
    if nav.count("R.drawable.iman_v29_unified_home")!=1 or NAV not in nav:
        raise RuntimeError("v30 did not preserve shared root wallpaper")
    if ".background(if (seamlessHome) Color.Transparent" not in nav.split(NAV,1)[1]:
        raise RuntimeError("v30 created a separate bottom navbar")
    reminders=json.loads((assets/"featured_quotes.json").read_text("utf-8"))
    if len(reminders)!=79 or len({a["text"] for a in reminders})!=79:
        raise RuntimeError("v30 quotes lost source anchors")
    if list((dest/"app/src/main").rglob("*.pdf")):
        raise RuntimeError("v30 accidentally bundled a source PDF")
    print("PASS v30: actual-emulator screenshot-driven spacing/art correction; intact reader/book/settings")


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--dest",type=Path,required=True)
    args=parser.parse_args()
    build_v30(Path(__file__).resolve().parents[1],args.dest)
