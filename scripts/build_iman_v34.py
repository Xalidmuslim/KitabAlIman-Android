"""Reference v0.34: precisely scoped art-size corrections over verified v0.33.

No new root background; one continuous parchment, five original tab actions,
existing reader, 131 chapters, 242 notes, 524 quizzes, 79 excerpts retained.
"""
from pathlib import Path
import argparse, hashlib, json
from PIL import Image
from scripts.build_iman_v33 import build_v33
from scripts.build_iman_v20 import APP, replace_one, NAV
from scripts.build_iman_v23 import install_variant4_quote
from scripts.iman_v28_scale import fill_artwork

ART=("contents","collections","glossary","bookmarks","reminder")

def build_v34(kit:Path,dest:Path):
    build_v33(kit,dest)
    gradle=dest/"app/build.gradle"
    g=gradle.read_text("utf-8")
    for before,after in (
        ("versionCode 33","versionCode 34"),
        ("versionName '0.33.0'","versionName '0.34.0'"),
        ("applicationIdSuffix '.preview33'","applicationIdSuffix '.preview34'"),
    ):
        g=replace_one(g,before,after,"v34 package identity")
    gradle.write_text(g,"utf-8")

    java=dest/APP
    app=java/"App.kt"
    reader=java/"Reader.kt"
    home=java/"ModernEditorialHome.kt"
    quote=java/"ImanQuoteCarousel.kt"
    preload=java/"MedicineHomeArtwork.kt"
    res=dest/"app/src/main/res"
    drawable=res/"drawable-nodpi"
    assets=dest/"app/src/main/assets"

    app_before=app.read_bytes()
    reader_before=reader.read_bytes()
    immutable={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
               for p in java.glob("*.kt")
               if p.name not in ("ModernEditorialHome.kt","ImanQuoteCarousel.kt","MedicineHomeArtwork.kt")}
    book_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in assets.iterdir() if p.is_file()}
    nav_sha={p.relative_to(res).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
             for p in res.rglob("*") if p.is_file()
             and (p.name.startswith("nav_") or p.name.startswith("ic_nav_"))}
    paper=drawable/"iman_v29_unified_home.webp"
    paper_sha=hashlib.sha256(paper.read_bytes()).hexdigest()

    # Reframe the five original illustrations off the UI thread at build time.
    for name in ART:
        source=drawable/f"iman_v32_{name}.webp"
        with Image.open(source) as im:
            artwork=fill_artwork(im,pad=0.0 if name=="reminder" else 0.012)
        dst=drawable/f"iman_v34_{name}.webp"
        artwork.save(dst,"WEBP",quality=96,method=6)
        if artwork.getpixel((0,0))[3]!=0 or dst.stat().st_size<3000:
            raise RuntimeError("v34: broken alpha edge or missing artwork "+name)
        high=artwork.getchannel("A").point(lambda value:255 if value>=180 else 0).getbbox()
        if high is None:
            raise RuntimeError("v34: missing opaque subject "+name)

    home_source=(kit/"scripts/ReferenceHomeV34.kt").read_text("utf-8")
    quote_source=(kit/"scripts/ReferenceQuoteV34.kt").read_text("utf-8")
    for token in (
        "book.collections.take(2)","height(78.dp)",
        "modifier.fillMaxSize().padding(bottom = 76.dp).clipToBounds()",
        "Route.Book","Route.Collections","Route.Glossary","Route.Bookmarks",
        "Route.Progress","Route.CollectionDetail(entry.id)",
        "Route.Reader(it.id, resume = last != null)",
        *("R.drawable.iman_v34_"+key for key in ART[:4]),
    ):
        if token not in home_source:
            raise RuntimeError("v34: Home route/layout lost "+token)
    if "R.drawable.iman_v29_unified_home" in home_source or "BorderStroke(" in home_source:
        raise RuntimeError("v34: unwanted second wallpaper or border")
    for token in (
        "width(290.dp).height(183.dp)","R.drawable.iman_v34_reminder",
        "Modifier.fillMaxWidth(0.62f)","q.text.length <= 120",
        "Crossfade(", "tween(180)", "maxLines = 5",
        "Route.Reader(q.chapterId, q.blockId)",
    ):
        if token not in quote_source:
            raise RuntimeError("v34: excerpt control changed "+token)
    home.write_text(home_source,"utf-8")
    quote.write_text(
        install_variant4_quote(quote.read_text("utf-8"),quote_source),
        "utf-8",
    )

    preload_before=preload.read_text("utf-8")
    for name in ART:
        preload_before=replace_one(
            preload_before,f"R.drawable.iman_v32_{name}",f"R.drawable.iman_v34_{name}",
            "v34 native IO bitmap preloader "+name,
        )
    preload.write_text(preload_before,"utf-8")

    if app.read_bytes()!=app_before or reader.read_bytes()!=reader_before:
        raise RuntimeError("v34 native app navigation or reader altered")
    for name,digest in immutable.items():
        if hashlib.sha256((java/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError("v34 unrelated Kotlin modified "+name)
    for name,digest in book_hashes.items():
        if hashlib.sha256((assets/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError("v34 book or saved content altered "+name)
    for path,digest in nav_sha.items():
        if hashlib.sha256((res/path).read_bytes()).hexdigest()!=digest:
            raise RuntimeError("v34 original five-tab icons modified "+path)
    if hashlib.sha256(paper.read_bytes()).hexdigest()!=paper_sha:
        raise RuntimeError("v34 continuous parchment changed")
    shell=app.read_text("utf-8")
    if (shell.count("R.drawable.iman_v29_unified_home")!=1 or NAV not in shell
        or ".background(if (seamlessHome) Color.Transparent" not in shell.split(NAV,1)[1]):
        raise RuntimeError("v34 bottom navigation introduced separate background")
    featured=json.loads((assets/"featured_quotes.json").read_text("utf-8"))
    if len(featured)!=79:
        raise RuntimeError("v34 source excerpts lost")
    print("PASS v34: original art at reference-scale, navigation seamless, protected source text")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dest",type=Path,required=True)
    build_v34(Path(__file__).resolve().parents[1],p.parse_args().dest)
