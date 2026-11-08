"""v0.27: approved independent book artwork integrated into existing native UI.

Only changes six resource drawables and their references; protected chapter data,
reader, tab actions, user preferences and motion code remain unchanged.
Artwork is committed permanently under assets/ui/v27 after one-time import.
"""
from pathlib import Path
from PIL import Image
import argparse, hashlib, json, shutil

from scripts.build_iman_v26 import build_v26
from scripts.build_iman_v20 import APP, NAV, replace_one
from scripts.build_iman_v25 import ARTWORK_NAMES

def install_v27_art(kit:Path,drawable:Path)->None:
    originals=kit/"assets/ui/v27"
    for name in ARTWORK_NAMES:
        source=originals/f"iman_v27_{name}.webp"
        if not source.is_file():
            raise RuntimeError("v27: missing generated source image "+str(source))
        with Image.open(source) as im:
            im.load()
            if name=="unified_home":
                if im.mode!="RGB" or im.size!=(648,1152):
                    raise RuntimeError("v27: reference paper size or color invalid")
            else:
                if im.mode!="RGBA" or im.getchannel("A").getextrema()[0]>0:
                    raise RuntimeError("v27: illustration does not blend to transparent page")
            if source.stat().st_size<=3300:
                raise RuntimeError("v27: generated asset is too small")
        shutil.copyfile(source,drawable/source.name)

def build_v27(kit:Path,dest:Path)->None:
    build_v26(kit,dest)
    gradle=dest/"app/build.gradle"
    text=gradle.read_text("utf-8")
    for old,new in (
        ("versionCode 26","versionCode 27"),
        ("versionName '0.26.0'","versionName '0.27.0'"),
        ("applicationIdSuffix '.preview26'","applicationIdSuffix '.preview27'"),
    ):
        text=replace_one(text,old,new,"v27 version identity")
    gradle.write_text(text,"utf-8")

    java=dest/APP
    app=java/"App.kt"
    home=java/"ModernEditorialHome.kt"
    quote=java/"ImanQuoteCarousel.kt"
    preload=java/"MedicineHomeArtwork.kt"
    reader_before=(java/"Reader.kt").read_bytes()
    app_before=app.read_text("utf-8")
    files_before={p.name:p.read_bytes() for p in java.glob("*.kt")
                  if p.name not in ("App.kt","ModernEditorialHome.kt",
                                    "ImanQuoteCarousel.kt","MedicineHomeArtwork.kt")}
    assets=dest/"app/src/main/assets"
    book_hashes={name:hashlib.sha256((assets/name).read_bytes()).hexdigest()
                 for name in ("book.json","quiz.json","featured_quotes.json")}
    res=dest/"app/src/main/res"
    nav_icons={p.relative_to(res).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
               for p in res.rglob("*") if p.is_file() and
               (p.name.startswith("nav_") or p.name.startswith("ic_nav_"))}
    old_reading_paper=res/"drawable-nodpi/reader_parchment_source.png"
    original_paper=hashlib.sha256(old_reading_paper.read_bytes()).hexdigest()

    install_v27_art(kit,res/"drawable-nodpi")

    a=replace_one(app_before,"R.drawable.iman_v26_unified_home",
                  "R.drawable.iman_v27_unified_home","v27 one root page background")
    if a.replace("R.drawable.iman_v27_unified_home",
                 "R.drawable.iman_v26_unified_home")!=app_before:
        raise RuntimeError("v27: changed router, navigation or app state")
    if (a.count("R.drawable.iman_v27_unified_home")!=1 or NAV not in a or
        ".background(if (seamlessHome) Color.Transparent" not in a.split(NAV,1)[1]):
        raise RuntimeError("v27: unified page background invariant violated")
    app.write_text(a,"utf-8")

    for source_path,names in (
        (home,("contents","collections","glossary","bookmarks")),
        (quote,("reminder",))
    ):
        before=source_path.read_text("utf-8")
        after=before
        for name in names:
            after=replace_one(after,f"R.drawable.iman_v26_{name}",
                              f"R.drawable.iman_v27_{name}",f"v27 icon {name}")
        restored=after
        for name in names:
            restored=restored.replace(f"R.drawable.iman_v27_{name}",
                                     f"R.drawable.iman_v26_{name}")
        if restored!=before:
            raise RuntimeError("v27: unrelated UI behavior change")
        source_path.write_text(after,"utf-8")

    p=preload.read_text("utf-8")
    for name in ARTWORK_NAMES:
        p=replace_one(p,f"R.drawable.iman_v26_{name}",
                      f"R.drawable.iman_v27_{name}","v27 preload "+name)
    preload.write_text(p,"utf-8")

    for path,content in files_before.items():
        if (java/path).read_bytes()!=content:
            raise RuntimeError("v27: modified non-UI Kotlin code "+path)
    if (java/"Reader.kt").read_bytes()!=reader_before:
        raise RuntimeError("v27: reader or preferences mutated")
    for name,digest in book_hashes.items():
        if hashlib.sha256((assets/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError("v27: book/quiz/source reminders changed")
    for path,digest in nav_icons.items():
        if hashlib.sha256((res/path).read_bytes()).hexdigest()!=digest:
            raise RuntimeError("v27: existing navigation icon overwritten")
    if hashlib.sha256(old_reading_paper.read_bytes()).hexdigest()!=original_paper:
        raise RuntimeError("v27: reader appearance unexpectedly changed")
    excerpts=json.loads((assets/"featured_quotes.json").read_text("utf-8"))
    if len(excerpts)!=79 or len({x["text"] for x in excerpts})!=79:
        raise RuntimeError("v27: original source reminders changed")
    if len(list((res/"drawable-nodpi").glob("iman_v27_*.webp")))!=6:
        raise RuntimeError("v27: six generated drawables not installed")
    if list((dest/"app/src/main").rglob("*.pdf")):
        raise RuntimeError("v27: source PDF accidentally bundled")
    print("PASS: six approved reference images, native seamless paper, and protected 131 chapters")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dest",type=Path,required=True)
    args=p.parse_args()
    build_v27(Path(__file__).resolve().parents[1],args.dest)
