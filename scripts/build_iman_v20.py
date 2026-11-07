"""v0.20: targeted illustrated redesign with source data and navigation protected.

Only ModernEditorialHome.kt and ImanQuoteCarousel.kt are changed relative
to v0.19. The original lower navigation, chapter reader, audio, exams,
bookmarks, saved progress and all source text are not modified.
"""
from pathlib import Path
import argparse, hashlib, json
from scripts.build_iman_v19 import build_v19

APP=Path("app/src/main/java/com/xalid/meditsinaproroka/nativeapp")
NAV="@Composable\nprivate fun StandaloneBottomNav("
QUOTE="@Composable\ninternal fun ImanFeaturedQuoteCarousel("

def replace_one(source,old,new,label):
    n=source.count(old)
    if n!=1:
        raise RuntimeError(f"Unexpected {label} anchor count {n}")
    return source.replace(old,new,1)

def patch_quote(source,implementation):
    if source.count(QUOTE)!=1:
        raise RuntimeError("Unknown quote component version")
    original=source[:source.index(QUOTE)]
    if original.count('FeaturedExcerpt("iman-chapter-')!=79:
        raise RuntimeError("Not all 79 sourced reminders are present")
    for anchor in ("q.chapterId", "Route.Reader(q.chapterId, q.blockId)",
                   'Text("Другая ↻"', "Crossfade(",
                   "ContentScale.Fit", "maxLines = 5",
                   "R.drawable.iman_v17_quote"):
        if anchor not in implementation:
            raise RuntimeError("New design lost quote behavior: "+anchor)
    return original+implementation

def build_v20(kit,dest):
    build_v19(kit,dest)
    gradle=dest/"app/build.gradle"
    g=gradle.read_text("utf-8")
    for a,b in (
        ("versionCode 19","versionCode 20"),
        ("versionName '0.19.0'","versionName '0.20.0'"),
        ("applicationIdSuffix '.preview19'","applicationIdSuffix '.preview20'"),
    ):
        g=replace_one(g,a,b,"version")
    gradle.write_text(g,"utf-8")
    java=dest/APP
    res=dest/"app/src/main/res"
    before_app=(java/"App.kt").read_bytes()
    if NAV not in before_app.decode("utf-8"):
        raise RuntimeError("Bottom navigation source missing")
    icons={p.relative_to(res).as_posix():p.read_bytes()
           for p in res.rglob("*") if p.is_file() and
           (p.name.startswith("nav_") or p.name.startswith("ic_nav_"))}
    protected={p.name:p.read_bytes() for p in java.glob("*.kt") if
               p.name not in ("ModernEditorialHome.kt","ImanQuoteCarousel.kt")}
    assets=dest/"app/src/main/assets"
    book_assets={n:hashlib.sha256((assets/n).read_bytes()).hexdigest()
                 for n in ("book.json","quiz.json","featured_quotes.json")}
    home=(kit/"scripts/ArtDirectedHomeV20.kt").read_text("utf-8")
    for anchor in ("ModernEditorialHomeScreen","EditorialBookSection",
                   "ImanFeaturedQuoteCarousel(navigate)", "Route.Book",
                   "Route.Glossary","Route.Collections","Route.Bookmarks",
                   "Route.Progress","Route.Reader(it.id, resume = last != null)",
                   "heightIn(min = 88.dp)","Brush.horizontalGradient",
                   "width = 70.dp, height = 74.dp"):
        if anchor not in home:
            raise RuntimeError("Home lost function or design: "+anchor)
    if "StandaloneBottomNav(" in home or "WebView(" in home:
        raise RuntimeError("Home incorrectly changes navigation technology")
    (java/"ModernEditorialHome.kt").write_text(home,"utf-8")
    quote=java/"ImanQuoteCarousel.kt"
    quote.write_text(patch_quote(
        quote.read_text("utf-8"),
        (kit/"scripts/ArtDirectedQuoteV20.kt").read_text("utf-8")),"utf-8")
    for n,content in protected.items():
        if (java/n).read_bytes()!=content:
            raise RuntimeError("Unrelated Kotlin file changed: "+n)
    if (java/"App.kt").read_bytes()!=before_app:
        raise RuntimeError("Bottom tab navigation changed")
    for n,content in icons.items():
        if (res/n).read_bytes()!=content:
            raise RuntimeError("Bottom nav icon mutated: "+n)
    for n,digest in book_assets.items():
        if hashlib.sha256((assets/n).read_bytes()).hexdigest()!=digest:
            raise RuntimeError("Book / quiz / quotes content changed: "+n)
    quoted=json.loads((assets/"featured_quotes.json").read_text("utf-8"))
    if len(quoted)!=79 or len({e["text"] for e in quoted})!=79:
        raise RuntimeError("Broken quote inventory")
    if list((dest/"app/src/main").rglob("*.pdf")):
        raise RuntimeError("PDF unexpectedly bundled")
    print("v0.20 complete: illustrated editorial home, 79 preserved quotes, native shell safe")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dest",required=True,type=Path)
    args=p.parse_args()
    build_v20(Path(__file__).resolve().parents[1],args.dest)
