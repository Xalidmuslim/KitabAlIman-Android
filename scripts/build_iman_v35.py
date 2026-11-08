"""v35: final reference-scale book and quill, no other Android UI or state changes."""
from pathlib import Path
import argparse,hashlib,json
from scripts.build_iman_v34 import build_v34
from scripts.build_iman_v20 import APP,NAV,replace_one
from scripts.build_iman_v23 import install_variant4_quote

def build_v35(kit:Path,dest:Path):
    build_v34(kit,dest)
    gradle=dest/"app/build.gradle"
    g=gradle.read_text("utf-8")
    for old,new in (
        ("versionCode 34","versionCode 35"),
        ("versionName '0.34.0'","versionName '0.35.0'"),
        ("applicationIdSuffix '.preview34'","applicationIdSuffix '.preview35'"),
    ):
        g=replace_one(g,old,new,"v35 version")
    gradle.write_text(g,"utf-8")

    java=dest/APP
    quote=java/"ImanQuoteCarousel.kt"
    app=java/"App.kt"
    reader=java/"Reader.kt"
    app_before=app.read_bytes()
    reader_before=reader.read_bytes()
    protected={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
               for p in java.glob("*.kt") if p.name!="ImanQuoteCarousel.kt"}
    assets=dest/"app/src/main/assets"
    book_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in assets.iterdir() if p.is_file()}
    res=dest/"app/src/main/res"
    nav_sha={p.relative_to(res).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
             for p in res.rglob("*") if p.is_file()
             and (p.name.startswith("nav_") or p.name.startswith("ic_nav_"))}
    paper=res/"drawable-nodpi/iman_v29_unified_home.webp"
    paper_sha=hashlib.sha256(paper.read_bytes()).hexdigest()
    candidate=(kit/"scripts/ReferenceQuoteV35.kt").read_text("utf-8")
    for term in (
        "width(380.dp).height(240.dp)","offset(x = 100.dp, y = 24.dp)",
        "Modifier.fillMaxWidth(0.62f)","q.text.length <= 120",
        "Crossfade(","tween(180)","maxLines = 5",
        "R.drawable.iman_v34_reminder",
        "Route.Reader(q.chapterId, q.blockId)",
    ):
        if term not in candidate:raise RuntimeError("v35 missing "+term)
    quote.write_text(install_variant4_quote(quote.read_text("utf-8"),candidate),"utf-8")

    for name,oldhash in protected.items():
        if hashlib.sha256((java/name).read_bytes()).hexdigest()!=oldhash:
            raise RuntimeError("v35 unrelated Kotlin edited "+name)
    if app.read_bytes()!=app_before or reader.read_bytes()!=reader_before:
        raise RuntimeError("v35 changed app navigation or reader")
    for name,oldhash in book_hashes.items():
        if hashlib.sha256((assets/name).read_bytes()).hexdigest()!=oldhash:
            raise RuntimeError("v35 book content changed "+name)
    for name,oldhash in nav_sha.items():
        if hashlib.sha256((res/name).read_bytes()).hexdigest()!=oldhash:
            raise RuntimeError("v35 navigation artwork changed "+name)
    if hashlib.sha256(paper.read_bytes()).hexdigest()!=paper_sha:
        raise RuntimeError("v35 continuous parchment changed")
    source=app.read_text("utf-8")
    if (source.count("R.drawable.iman_v29_unified_home")!=1 or NAV not in source
        or ".background(if (seamlessHome) Color.Transparent" not in source.split(NAV,1)[1]):
        raise RuntimeError("v35 second background appeared")
    snippets=json.loads((assets/"featured_quotes.json").read_text("utf-8"))
    if len(snippets)!=79:raise RuntimeError("v35 quotes missing")
    print("PASS v35 reference hero, original data and 5 tab routes")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--dest",type=Path,required=True)
    build_v35(Path(__file__).resolve().parents[1],parser.parse_args().dest)
