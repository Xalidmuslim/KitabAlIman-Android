"""v0.22: reuse exact installed reader paper presets in native main UI.

Build from tested v0.21. Only the modern home and reminder composables change.
The reader, five tabs, Kotlin engine, source book, quizzes and user storage
remain byte-for-byte unchanged; v0.22 is an isolated preview installation.
"""
from pathlib import Path
import argparse
import hashlib
import json

from scripts.build_iman_v21 import build_v21
from scripts.build_iman_v20 import replace_one, APP, NAV, QUOTE as QUOTE_MARKER


def install_paper_quote(source: str, implementation: str) -> str:
    if source.count(QUOTE_MARKER) != 1:
        raise RuntimeError("Unexpected quote composable entry point")
    prefix = source[:source.index(QUOTE_MARKER)]
    if prefix.count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("Missing one or more source-anchored quotations")
    for required in (
        "R.drawable.reader_parchment_source",
        "ContentScale.Crop", "Crossfade(", "tween(180)",
        'Text("Другая ↻"', "Route.Reader(q.chapterId, q.blockId)",
        "maxLines = 5", "shadowElevation = 0.dp",
    ):
        if required not in implementation:
            raise RuntimeError("v0.22 reminder lost behavior: " + required)
    if "R.drawable.iman_v17_quote" in implementation:
        raise RuntimeError("v0.22 reminder still contains obsolete right-side illustration")
    if 'readerPaperOverlay("light")' in implementation:
        raise RuntimeError("Reminder must use antique original, without light wash")
    return prefix + implementation


def build_v22(kit: Path, dest: Path) -> None:
    build_v21(kit, dest)
    gradle = dest / "app/build.gradle"
    g = gradle.read_text("utf-8")
    for a, b in (
        ("versionCode 21", "versionCode 22"),
        ("versionName '0.21.0'", "versionName '0.22.0'"),
        ("applicationIdSuffix '.preview21'", "applicationIdSuffix '.preview22'"),
    ):
        g = replace_one(g, a, b, "v22 version")
    gradle.write_text(g, "utf-8")

    src = dest / APP
    assets = dest / "app/src/main/assets"
    res = dest / "app/src/main/res"
    original_reader = (src / "Reader.kt").read_bytes()
    original_app = (src / "App.kt").read_bytes()
    original_java = {
        p.name: p.read_bytes() for p in src.glob("*.kt")
        if p.name not in ("ModernEditorialHome.kt", "ImanQuoteCarousel.kt")
    }
    icon_hashes = {
        p.relative_to(res).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in res.rglob("*") if p.is_file() and
        (p.name.startswith("nav_") or p.name.startswith("ic_nav_"))
    }
    protected = {
        name: hashlib.sha256((assets / name).read_bytes()).hexdigest()
        for name in ("book.json", "quiz.json", "featured_quotes.json")
    }
    paper = res / "drawable-nodpi/reader_parchment_source.png"
    if not paper.is_file() or paper.stat().st_size < 5000:
        raise RuntimeError("The verified original reader paper image was not present")
    original_paper = hashlib.sha256(paper.read_bytes()).hexdigest()
    reader = original_reader.decode("utf-8")
    if ('"original" -> null' not in reader or
        'Color(0xFFFFFCF6).copy(alpha = 0.42f)' not in reader or
        'R.drawable.reader_parchment_source' not in reader):
        raise RuntimeError("Reader paper presets changed; refuse to approximate")

    home = (kit / "scripts/ReadingPaperHomeV22.kt").read_text("utf-8")
    quote = (kit / "scripts/ReadingPaperQuoteV22.kt").read_text("utf-8")
    for anchor in ('readerPaperOverlay("light")', "R.drawable.reader_parchment_source",
                   "ContentScale.FillBounds", "width = 58.dp, height = 60.dp",
                   "0.74f", "ModernEditorialHomeScreen(", "EditorialResumeCard(",
                   "ImanFeaturedQuoteCarousel(navigate)", "EditorialBookSection(",
                   "Route.Book", "Route.Collections", "Route.Glossary",
                   "Route.Bookmarks", "Route.Progress",
                   "Route.CollectionDetail(entry.id)",
                   "Route.Reader(it.id, resume = last != null)",
                   "R.drawable.iman_v17_contents", "R.drawable.iman_v17_collections",
                   "R.drawable.iman_v17_glossary", "R.drawable.iman_v17_bookmarks"):
        if anchor not in home:
            raise RuntimeError("v0.22 home missing design or route: " + anchor)
    if "Brush.horizontalGradient" in home or "BorderStroke(" in home:
        raise RuntimeError("Old library backgrounds/frames reappeared")
    (src / "ModernEditorialHome.kt").write_text(home, "utf-8")
    quotes_path = src / "ImanQuoteCarousel.kt"
    quotes_path.write_text(
        install_paper_quote(quotes_path.read_text("utf-8"), quote), "utf-8")

    for name, blob in original_java.items():
        if (src / name).read_bytes() != blob:
            raise RuntimeError("Unrelated Kotlin file was modified: " + name)
    if (src / "Reader.kt").read_bytes() != original_reader:
        raise RuntimeError("Reader appearance or user settings altered")
    if (src / "App.kt").read_bytes() != original_app or NAV not in original_app.decode("utf-8"):
        raise RuntimeError("Bottom navigation/state changed")
    if hashlib.sha256(paper.read_bytes()).hexdigest() != original_paper:
        raise RuntimeError("Original paper bitmap was modified")
    for path, digest in icon_hashes.items():
        if hashlib.sha256((res / path).read_bytes()).hexdigest() != digest:
            raise RuntimeError("A navigation icon was modified")
    for name, digest in protected.items():
        if hashlib.sha256((assets / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError("Book, quizzes or sourced quotes changed")
    data = json.loads((assets / "featured_quotes.json").read_text("utf-8"))
    if len(data) != 79 or len({x["text"] for x in data}) != 79:
        raise RuntimeError("79 unique original reminders not retained")
    if list((dest / "app/src/main").rglob("*.pdf")):
        raise RuntimeError("PDF unexpectedly bundled")
    print("PASS v0.22: exact light and antique reader paper, small icons, 79 quotes safe")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dest", type=Path, required=True)
    args = p.parse_args()
    build_v22(Path(__file__).resolve().parents[1], args.dest)
