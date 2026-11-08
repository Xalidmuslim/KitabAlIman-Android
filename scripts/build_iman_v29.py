"""v0.29: reference calibrated seamless paper and carefully measured home proportions.

Starts with tested v0.28 Kotlin/Compose implementation. No replacement app,
no changes to reader, user preferences, quizzes, 131 chapter contents or nav.
"""
from pathlib import Path
import argparse, hashlib, json, shutil
from PIL import Image, ImageFilter
import numpy as np

from scripts.build_iman_v28 import build_v28
from scripts.build_iman_v20 import APP, NAV, replace_one
from scripts.build_iman_v23 import install_variant4_quote

def build_v29(kit:Path,dest:Path):
    build_v28(kit,dest)
    gradle=dest/"app/build.gradle"
    g=gradle.read_text("utf-8")
    for old,new in (
        ("versionCode 28","versionCode 29"),
        ("versionName '0.28.0'","versionName '0.29.0'"),
        ("applicationIdSuffix '.preview28'","applicationIdSuffix '.preview29'"),
    ):
        g=replace_one(g,old,new,"v29 isolated native app version")
    gradle.write_text(g,"utf-8")

    java=dest/APP
    res=dest/"app/src/main/res"
    assets=dest/"app/src/main/assets"
    drawable=res/"drawable-nodpi"
    app=java/"App.kt"
    reader=java/"Reader.kt"
    home=java/"ModernEditorialHome.kt"
    quote=java/"ImanQuoteCarousel.kt"
    preload=java/"MedicineHomeArtwork.kt"

    app_before=app.read_text("utf-8")
    reader_before=reader.read_bytes()
    protected_files={
        p.name:p.read_bytes() for p in java.glob("*.kt")
        if p.name not in ("App.kt","ModernEditorialHome.kt",
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
    reading_paper=drawable/"reader_parchment_source.png"
    reading_paper_sha=hashlib.sha256(reading_paper.read_bytes()).hexdigest()
    original_assets={
        p.name:hashlib.sha256(p.read_bytes()).hexdigest()
        for p in drawable.glob("iman_v28_*.webp")
    }

    # The texture is generated from the TEXTURE-ONLY reference region once,
    # saved into the repo, and reused without network calls during normal builds.
    reference_paper=kit/"assets/ui/v29/iman_v29_unified_home.webp"
    if not reference_paper.is_file():
        raise RuntimeError("v29 source parchment must be committed before build")
    with Image.open(reference_paper) as original:
        im=original.convert("RGB")
        if im.size!=(648,1152):
            raise RuntimeError("v29 parchment must fit exact root wallpaper dimensions")
        sample=im.crop((150,750,485,830))
        delta=np.asarray(sample,dtype=np.float32)-np.asarray(
            sample.filter(ImageFilter.GaussianBlur(9)),dtype=np.float32)
        sigma=delta.std(axis=(0,1))
        if float(sigma.min())<3.1 or float(sigma.max())>7.0:
            raise RuntimeError(f"v29 reference grain mismatches target: {sigma}")
    shutil.copyfile(reference_paper,drawable/reference_paper.name)

    # The wallpaper is a SINGLE bitmap behind Home and native bottom navigation.
    patched_app=replace_one(app_before,
        "R.drawable.iman_v27_unified_home",
        "R.drawable.iman_v29_unified_home",
        "v29 shared reference paper")
    if patched_app.replace("R.drawable.iman_v29_unified_home",
                           "R.drawable.iman_v27_unified_home")!=app_before:
        raise RuntimeError("v29 unexpectedly mutated navigation or app state")
    app.write_text(patched_app,"utf-8")

    # The approved 4 book illustrations from v28 already have no framing,
    # keep them; adapt the layout only to real reference proportions.
    home_text=(kit/"scripts/ReferenceHomeV29.kt").read_text("utf-8")
    old_home=home.read_text("utf-8")
    for token in (
        "book.collections.take(2)", "item(key = \"library-four\")",
        "R.drawable.iman_v28_contents","R.drawable.iman_v28_collections",
        "R.drawable.iman_v28_glossary","R.drawable.iman_v28_bookmarks",
        "Route.Reader(it.id, resume = last != null)",
        "Route.CollectionDetail(entry.id)",
        "LinearProgressIndicator(",
        "color = Color.Transparent",
    ):
        if token not in home_text:
            raise RuntimeError("v29 home lost approved feature "+token)
    if ("R.drawable.iman_v27_unified_home" in home_text or
        "R.drawable.iman_v29_unified_home" in home_text):
        raise RuntimeError("v29 home must not add a second paper layer")
    home.write_text(home_text,"utf-8")

    quote_text=(kit/"scripts/ReferenceQuoteV29.kt").read_text("utf-8")
    for token in (
        "Modifier.weight(0.54f)","Modifier.weight(0.46f)",
        "height(174.dp)","heightIn(min = 148.dp)",
        "q.text.length <= 120","maxLines = 5",
        "Crossfade(", "tween(180)", "Route.Reader(q.chapterId, q.blockId)",
        "R.drawable.iman_v28_reminder",
    ):
        if token not in quote_text:
            raise RuntimeError("v29 quote lost animated reading or content safety: "+token)
    quote.write_text(
        install_variant4_quote(quote.read_text("utf-8"),quote_text),
        "utf-8")

    pre=preload.read_text("utf-8")
    pre=replace_one(pre,
        "R.drawable.iman_v27_unified_home",
        "R.drawable.iman_v29_unified_home",
        "preload root paper off UI thread")
    preload.write_text(pre,"utf-8")

    # Fail closed: source book, reader, user data and bottom tabs are unchanged.
    for name,data_before in protected_files.items():
        if (java/name).read_bytes()!=data_before:
            raise RuntimeError("v29 altered protected Kotlin file "+name)
    if reader.read_bytes()!=reader_before or NAV not in app_before:
        raise RuntimeError("v29 modified reader or native tab router")
    for name,expected in book_hashes.items():
        if hashlib.sha256((assets/name).read_bytes()).hexdigest()!=expected:
            raise RuntimeError("v29 altered source book/quiz/quotes: "+name)
    for name,expected in protected_nav.items():
        if hashlib.sha256((res/name).read_bytes()).hexdigest()!=expected:
            raise RuntimeError("v29 altered existing navigation icon")
    if hashlib.sha256(reading_paper.read_bytes()).hexdigest()!=reading_paper_sha:
        raise RuntimeError("v29 modified reading style assets")
    for name,expected in original_assets.items():
        if hashlib.sha256((drawable/name).read_bytes()).hexdigest()!=expected:
            raise RuntimeError("v29 modified approved book artwork: "+name)
    if (patched_app.count("R.drawable.iman_v29_unified_home")!=1 or
        ".background(if (seamlessHome) Color.Transparent" not in patched_app.split(NAV,1)[1]):
        raise RuntimeError("v29 introduced opaque bottom-nav panel")
    if len(json.loads((assets/"featured_quotes.json").read_text("utf-8")))!=79:
        raise RuntimeError("v29 altered 79 source-backed excerpts")
    if list((dest/"app/src/main").rglob("*.pdf")):
        raise RuntimeError("v29 unexpectedly bundles source PDF")
    print("PASS v0.29: reference-calibrated textured wallpaper, larger quote illustration, two topic previews and all book data protected")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--dest",type=Path,required=True)
    opt=parser.parse_args()
    build_v29(Path(__file__).resolve().parents[1],opt.dest)
