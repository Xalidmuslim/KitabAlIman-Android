"""v0.33: compact Material3 text controls to eliminate navbar overlap.

Derived from signed v0.32; no changes to single wallpaper, five native tab
actions, book reader or any user content/data. Entire UI still uses Compose.
"""
from pathlib import Path
import argparse,hashlib,json
from scripts.build_iman_v32 import build_v32
from scripts.build_iman_v23 import install_variant4_quote
from scripts.build_iman_v20 import APP,replace_one,NAV

def build_v33(kit:Path,dest:Path):
    build_v32(kit,dest)
    gradle=dest/"app/build.gradle"
    g=gradle.read_text("utf-8")
    for old,new in (
        ("versionCode 32","versionCode 33"),
        ("versionName '0.32.0'","versionName '0.33.0'"),
        ("applicationIdSuffix '.preview32'","applicationIdSuffix '.preview33'"),
    ):
        g=replace_one(g,old,new,"v33 package")
    gradle.write_text(g,"utf-8")
    java=dest/APP
    home=java/"ModernEditorialHome.kt"
    quote=java/"ImanQuoteCarousel.kt"
    app=java/"App.kt"
    reader=java/"Reader.kt"
    app_before=app.read_bytes()
    reader_before=reader.read_bytes()
    preserved={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
               for p in java.glob("*.kt")
               if p.name not in ("ModernEditorialHome.kt","ImanQuoteCarousel.kt")}
    assets=dest/"app/src/main/assets"
    book_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in assets.iterdir() if p.is_file()}
    res=dest/"app/src/main/res"
    nav_sha={p.relative_to(res).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
             for p in res.rglob("*") if p.is_file() and
             (p.name.startswith("nav_") or p.name.startswith("ic_nav_"))}

    target_home=(kit/"scripts/ReferenceHomeV33.kt").read_text("utf-8")
    target_quote=(kit/"scripts/ReferenceQuoteV33.kt").read_text("utf-8")
    if ("modifier.fillMaxSize().padding(bottom = 76.dp).clipToBounds()" not in target_home or
        ".statusBarsPadding()" in target_home or
        "book.collections.take(2)" not in target_home or
        "Route.Reader(it.id, resume = last != null)" not in target_home or
        "height(36.dp)" not in target_home):
        raise RuntimeError("v33 Home viewport or native routes corrupted")
    if target_quote.count("modifier = Modifier.height(36.dp)")!=2:
        raise RuntimeError("v33 reminder top/footer controls are not compact")
    for token in ("Crossfade(","tween(180)","maxLines = 5",
                  "Route.Reader(q.chapterId, q.blockId)",
                  "R.drawable.iman_v32_reminder","q.text.length <= 120"):
        if token not in target_quote:
            raise RuntimeError("v33 excerpt lost "+token)
    home.write_text(target_home,"utf-8")
    quote.write_text(install_variant4_quote(quote.read_text("utf-8"),target_quote),"utf-8")

    if app.read_bytes()!=app_before or reader.read_bytes()!=reader_before:
        raise RuntimeError("v33 native navigation or book reader changed")
    for name,sha in preserved.items():
        if hashlib.sha256((java/name).read_bytes()).hexdigest()!=sha:
            raise RuntimeError("v33 unrelated Kotlin modified "+name)
    for name,sha in book_hashes.items():
        if hashlib.sha256((assets/name).read_bytes()).hexdigest()!=sha:
            raise RuntimeError("v33 book data modified "+name)
    for name,sha in nav_sha.items():
        if hashlib.sha256((res/name).read_bytes()).hexdigest()!=sha:
            raise RuntimeError("v33 nav icon asset modified "+name)
    a=app.read_text("utf-8")
    if (a.count("R.drawable.iman_v29_unified_home")!=1 or NAV not in a or
        ".background(if (seamlessHome) Color.Transparent" not in a.split(NAV,1)[1]):
        raise RuntimeError("v33 continuous paper lost")
    data=json.loads((assets/"featured_quotes.json").read_text("utf-8"))
    if len(data)!=79:
        raise RuntimeError("v33 original quotes modified")
    print("PASS v33: compressed reminder/progress control chrome, intact 131 chapters and five native navigation actions")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--dest",required=True,type=Path)
    build_v33(Path(__file__).resolve().parents[1],parser.parse_args().dest)
