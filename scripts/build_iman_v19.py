"""v0.19: premium compact homepage with book art.

Baseline: verified v0.18. Changes limited to homepage + reminder presentation.
Android bottom navigation, quiz, reading progress, TTS and source content
are strictly unchanged. Each build uses a separate preview package.
"""
from pathlib import Path
import argparse
import hashlib
import json

from scripts.build_iman_v18 import build_v18

JAVA = Path("app/src/main/java/com/xalid/meditsinaproroka/nativeapp")
NAV = "@Composable\nprivate fun StandaloneBottomNav("
QUOTE_MARKER = "@Composable\ninternal fun ImanFeaturedQuoteCarousel("

def replace_once(source, old, new, what):
    n = source.count(old)
    if n != 1:
        raise RuntimeError(f"Unexpected {what}: {n} matching anchors")
    return source.replace(old, new, 1)

def install_quote(source, implementation):
    if source.count(QUOTE_MARKER) != 1:
        raise RuntimeError("Reference quote composable changed")
    original_quotes = source[:source.index(QUOTE_MARKER)]
    if original_quotes.count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("Missing one of the 79 source-backed excerpts")
    for text in ("Route.Reader(q.chapterId, q.blockId)",
                 "Text(\"Другая ↻\"",
                 "R.drawable.iman_v17_quote",
                 "maxLines = 4",
                 "ContentScale.Fit",
                 "heightIn(min = 40.dp)"):
        if text not in implementation:
            raise RuntimeError("Missing quote interaction: " + text)
    source = replace_once(source,
        "import androidx.compose.foundation.clickable",
        "import androidx.compose.foundation.background\nimport androidx.compose.foundation.clickable",
        "brush background import")
    source = replace_once(source,
        "import androidx.compose.ui.graphics.Color",
        "import androidx.compose.ui.graphics.Brush\nimport androidx.compose.ui.graphics.Color",
        "brush color import")
    return source[:source.index(QUOTE_MARKER)] + implementation

def build_v19(kit: Path, dest: Path):
    build_v18(kit, dest)
    gradle = dest/"app/build.gradle"
    g = gradle.read_text(encoding="utf-8")
    for a,b in (
        ("versionCode 18", "versionCode 19"),
        ("versionName '0.18.0'", "versionName '0.19.0'"),
        ("applicationIdSuffix '.preview18'", "applicationIdSuffix '.preview19'"),
    ):
        g = replace_once(g, a, b, "version")
    gradle.write_text(g, encoding="utf-8")

    src = dest/JAVA
    res = dest/"app/src/main/res"
    protected_nav = (src/"App.kt").read_bytes()
    if NAV not in protected_nav.decode("utf-8"):
        raise RuntimeError("Original bottom navigation not found")
    protected_icons = {
        p.relative_to(res).as_posix(): p.read_bytes()
        for p in res.rglob("*")
        if p.is_file() and (p.name.startswith("nav_") or p.name.startswith("ic_nav_"))
    }
    protected_java = {
        p.name: p.read_bytes()
        for p in src.glob("*.kt")
        if p.name not in ("ModernEditorialHome.kt", "ImanQuoteCarousel.kt")
    }
    assets_dir = dest/"app/src/main/assets"
    protected_data = {
        name: hashlib.sha256((assets_dir/name).read_bytes()).hexdigest()
        for name in ("book.json", "quiz.json", "featured_quotes.json")
    }

    new_home = (kit/"scripts/PremiumEditorialHome.kt").read_text(encoding="utf-8")
    required = ("ModernEditorialHomeScreen(", "EditorialBookSection(",
                "EditorialResumeCard(", "ImanFeaturedQuoteCarousel(navigate)",
                "Route.Progress", "Route.Bookmarks", "Route.Glossary",
                "Route.Reader(it.id, resume = last != null)",
                "R.drawable.iman_v17_contents",
                "R.drawable.iman_v17_bookmarks",
                "heightIn(min = 76.dp)")
    for anchor in required:
        if anchor not in new_home:
            raise RuntimeError("Home feature missing: " + anchor)
    if "StandaloneBottomNav(" in new_home or "WebView(" in new_home:
        raise RuntimeError("Homepage attempts to replace native navigation")
    (src/"ModernEditorialHome.kt").write_text(new_home, encoding="utf-8")

    old_quote = (src/"ImanQuoteCarousel.kt").read_text(encoding="utf-8")
    new_quote = (kit/"scripts/PremiumEditorialQuote.kt").read_text(encoding="utf-8")
    (src/"ImanQuoteCarousel.kt").write_text(
        install_quote(old_quote, new_quote), encoding="utf-8")

    if (src/"App.kt").read_bytes() != protected_nav:
        raise RuntimeError("Bottom navigation route/state modified")
    for relative,content in protected_icons.items():
        if (res/relative).read_bytes() != content:
            raise RuntimeError("Bottom navigation icon changed: " + relative)
    for filename,content in protected_java.items():
        if (src/filename).read_bytes() != content:
            raise RuntimeError("Reader, TTS or unrelated code changed: " + filename)
    for filename,digest in protected_data.items():
        if hashlib.sha256((assets_dir/filename).read_bytes()).hexdigest() != digest:
            raise RuntimeError("Book/quiz/quotes changed: " + filename)
    quotes = json.loads((assets_dir/"featured_quotes.json").read_text(encoding="utf-8"))
    if len(quotes) != 79:
        raise RuntimeError("Lost source-backed reminders")
    if list((dest/"app/src/main").rglob("*.pdf")):
        raise RuntimeError("PDF unexpectedly packaged in app")
    print("v0.19 complete: premium compact editorial home, 79 source quotes, immutable bottom navigation")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dest", required=True, type=Path)
    args = p.parse_args()
    build_v19(Path(__file__).resolve().parents[1], args.dest)
