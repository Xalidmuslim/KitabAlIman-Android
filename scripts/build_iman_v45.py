"""v0.45: full-contrast reminder, text wrapping without artwork overlap.

Build on verified v0.44.1. Change only the reminder composable and isolated
preview metadata; never change book/quiz content, the other Home widgets,
navigation, bookmarks, reading progress, notes, or the original v44 release.
"""
import argparse
import hashlib
import json
from pathlib import Path

from scripts.build_iman_v44 import build_v44
from scripts.build_iman_v20 import APP, NAV, replace_one


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_v45(kit: Path, dest: Path) -> None:
    build_v44(kit, dest)
    java = dest / APP
    assets = dest / "app/src/main/assets"
    gradle = dest / "app/build.gradle"
    quote_file = java / "ImanQuoteCarousel.kt"
    marker = "@Composable\ninternal fun ImanFeaturedQuoteCarousel("

    original = quote_file.read_text(encoding="utf-8")
    if original.count(marker) != 1 or original.count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v45 expected exactly the approved 79-quote source")
    protected = {
        path.name: sha(path)
        for path in java.glob("*.kt") if path.name != "ImanQuoteCarousel.kt"
    }
    book_hashes = {path.name: sha(path) for path in assets.iterdir() if path.is_file()}
    app_before = (java / "App.kt").read_text(encoding="utf-8")
    if NAV not in app_before:
        raise RuntimeError("v45 missing original navigation")

    config = gradle.read_text(encoding="utf-8")
    for old, new in (
        ("versionCode 48", "versionCode 50"),
        ("versionName '0.44.1'", "versionName '0.45.0'"),
        ("applicationIdSuffix '.preview44'", "applicationIdSuffix '.preview45'"),
    ):
        config = replace_one(config, old, new, "v45 isolated preview metadata")
    gradle.write_text(config, encoding="utf-8")

    replacement = (kit / "scripts/ReferenceQuoteV45.kt").read_text(encoding="utf-8")
    required = (
        "// v45: independent text and artwork columns.",
        "Modifier.weight(1f)", "Arrangement.spacedBy(",
        "ImanQuoteAnimatedText(current, ink)", "ContentScale.Fit",
        "R.drawable.iman_v43_approved_scroll", "alpha = 1f",
        "preferences.edit().putInt(\"last_shown\", current).apply()",
        "navigate(Route.Reader(q.chapterId, q.blockId))",
    )
    if any(token not in replacement for token in required):
        raise RuntimeError("v45 reminder layout or interaction is incomplete")
    forbidden = ("alpha = if (q.text.length", ".fillMaxWidth(if (q.text.length",
                 ".offset(x =", "TextOverflow.Ellipsis", "maxLines =")
    if any(token in replacement for token in forbidden):
        raise RuntimeError("v45 reminder still contains faded art, overlapping text, or truncation")
    updated = original[:original.index(marker)] + replacement
    quote_file.write_text(updated, encoding="utf-8")

    for name, expected in protected.items():
        if sha(java / name) != expected:
            raise RuntimeError("v45 altered unrelated Kotlin code: " + name)
    for name, expected in book_hashes.items():
        if sha(assets / name) != expected:
            raise RuntimeError("v45 altered book, quiz, or source data: " + name)
    app_after = (java / "App.kt").read_text(encoding="utf-8")
    if NAV not in app_after or app_after[app_after.index(NAV):] != app_before[app_before.index(NAV):]:
        raise RuntimeError("v45 changed navigation")
    if updated.count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v45 changed the number of reminders")
    book = json.loads((assets / "book.json").read_text(encoding="utf-8"))
    quiz = json.loads((assets / "quiz.json").read_text(encoding="utf-8"))
    if len(book["chapters"]) != 131 or len(quiz["chapters"]) != 131:
        raise RuntimeError("v45 modified the source book or chapter quizzes")
    print("PASS v45: original 79 quotes, separate columns, opaque matte artwork, 131 chapters, preserved navigation")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args()
    build_v45(Path(__file__).resolve().parents[1], args.dest)
