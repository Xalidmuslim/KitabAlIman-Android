"""v0.18 Modern Editorial homepage; no change to book, reader, routes or lower nav."""
from pathlib import Path
import argparse, json
from scripts.build_iman_v17 import build_v17

ROOT=Path("app/src/main/java/com/xalid/meditsinaproroka/nativeapp")
NAV="@Composable\nprivate fun StandaloneBottomNav("
START="@Composable\ninternal fun IbnStyleHomeScreen("
END="@Composable\nprivate fun IbnHomeLink("

def once(s,old,new,label):
    count=s.count(old)
    if count!=1:raise RuntimeError(f"{label}: {count} expected anchors")
    return s.replace(old,new,1)

def patch_style(s):
    if s.count(START)!=1 or s.count(END)!=1:
        raise RuntimeError("Existing home component anchors missing")
    i,j=s.index(START),s.index(END)
    if i>=j:raise RuntimeError("Incorrect home anchors")
    delegate="""@Composable
internal fun IbnStyleHomeScreen(
    book: BookData, store: AppStore, modifier: Modifier,
    navigate: (Route) -> Unit, onGlobalSearch: () -> Unit,
    onToggleTheme: () -> Unit,
) {
    ModernEditorialHomeScreen(book, store, modifier, navigate, onGlobalSearch, onToggleTheme)
}

"""
    return s[:i]+delegate+s[j:]

def patch_quote(s):
    replacements=[
        ("Color(0xFFF9ECD9)","Color(0xFFFFFCF7)"),
        ("Color(0xFFC69C6D)","Color(0xFFDDD0BE)"),
        ("width = 174.dp, height = 200.dp","width = 98.dp, height = 96.dp"),
        ("Modifier.fillMaxWidth(0.70f)","Modifier.fillMaxWidth(0.88f)"),
        ("fontSize = 16.5.sp, lineHeight = 23.sp","fontSize = 16.sp, lineHeight = 22.sp"),
        ("maxLines = 8, overflow = TextOverflow.Ellipsis",
         "maxLines = 4, overflow = TextOverflow.Ellipsis"),
        ("padding(horizontal = 15.dp, vertical = 14.dp)",
         "padding(horizontal = 14.dp, vertical = 10.dp)"),
        ("shape = RoundedCornerShape(19.dp)","shape = RoundedCornerShape(15.dp)"),
    ]
    for old,new in replacements:s=once(s,old,new,"compact reminder")
    for anchor in ('Text("Другая ↻"','Route.Reader(q.chapterId, q.blockId)',
                   'private val imanExcerpts = listOf(','Alignment.BottomEnd'):
        if anchor not in s:raise RuntimeError("Lost existing reminder behavior: "+anchor)
    if s.count('FeaturedExcerpt("iman-chapter-')!=79:
        raise RuntimeError("79 source-verified excerpts not preserved")
    return s

def build_v18(kit,dest):
    build_v17(kit,dest)
    gradle=dest/"app/build.gradle"
    text=gradle.read_text("utf-8")
    for a,b in (("versionCode 17","versionCode 18"),
                ("versionName '0.17.0'","versionName '0.18.0'"),
                ("applicationIdSuffix '.preview17'","applicationIdSuffix '.preview18'")):
        text=once(text,a,b,"version")
    gradle.write_text(text,"utf-8")
    java=dest/ROOT
    original_app=(java/"App.kt").read_bytes()
    if NAV not in original_app.decode("utf-8"):
        raise RuntimeError("Original bottom navigation missing")
    res=dest/"app/src/main/res"
    nav_icons={str(p.relative_to(res)):p.read_bytes() for p in res.rglob("*")
        if p.is_file() and (p.name.startswith("nav_") or p.name.startswith("ic_nav_"))}
    protected={p.name:p.read_bytes() for p in java.glob("*.kt")
        if p.name not in ("IbnQayyimStyle.kt","ImanQuoteCarousel.kt")}
    style=java/"IbnQayyimStyle.kt"
    style.write_text(patch_style(style.read_text("utf-8")),"utf-8")
    modern=(kit/"scripts/ModernEditorialHome.kt").read_text("utf-8")
    for anchor in ("ModernEditorialHomeScreen","ImanFeaturedQuoteCarousel(navigate)",
                   "Route.Progress","Route.Glossary","Route.Bookmarks",
                   "Route.CollectionDetail(collection.id)","EditorialReadingCard"):
        if anchor not in modern:raise RuntimeError("Modern home missing "+anchor)
    (java/"ModernEditorialHome.kt").write_text(modern,"utf-8")
    quote=java/"ImanQuoteCarousel.kt"
    quote.write_text(patch_quote(quote.read_text("utf-8")),"utf-8")
    for filename,content in protected.items():
        if (java/filename).read_bytes()!=content:
            raise RuntimeError("Unrelated Kotlin/reader changed: "+filename)
    if (java/"App.kt").read_bytes()!=original_app:
        raise RuntimeError("Bottom nav/routes modified")
    for filename,content in nav_icons.items():
        if (res/filename).read_bytes()!=content:
            raise RuntimeError("Bottom nav icon changed: "+filename)
    data=json.loads((dest/"app/src/main/assets/featured_quotes.json").read_text("utf-8"))
    assert len(data)==79
    assert not list((dest/"app/src/main").rglob("*.pdf"))
    print("PASS v0.18: compact editorial home, 79 quotes, preserved reader, navigation, assets")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dest",type=Path,required=True)
    args=p.parse_args()
    build_v18(Path(__file__).resolve().parents[1],args.dest)
