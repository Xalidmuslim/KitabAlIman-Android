"""v0.45.1 follow-up: preserve single-screen dashboard on compact displays."""
import argparse
import hashlib
import json
from pathlib import Path

from scripts.build_iman_v45 import build_v45
from scripts.build_iman_v20 import APP, NAV, replace_one


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_v451(kit: Path, dest: Path) -> None:
    build_v45(kit, dest)
    java = dest / APP
    assets = dest / "app/src/main/assets"
    gradle = dest / "app/build.gradle"
    original = (java / "ImanQuoteCarousel.kt").read_text("utf-8")
    marker = "@Composable\ninternal fun ImanFeaturedQuoteCarousel("
    if original.count(marker) != 1 or original.count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v451 expected original 79 quotes")
    protected = {p.name: sha(p) for p in java.glob("*.kt") if p.name != "ImanQuoteCarousel.kt"}
    book_hashes = {p.name: sha(p) for p in assets.iterdir() if p.is_file()}
    app_before = (java / "App.kt").read_text("utf-8")

    config = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 50", "versionCode 51"),
        ("versionName '0.45.0'", "versionName '0.45.1'"),
        ("applicationIdSuffix '.preview45'", "applicationIdSuffix '.preview451'"),
    ):
        config = replace_one(config, old, new, "v451 isolated preview metadata")
    gradle.write_text(config, "utf-8")

    source = (kit / "scripts/ReferenceQuoteV451.kt").read_text("utf-8")
    required = (
        "ImanQuoteAnimatedText(current, ink, compactScreen)",
        ".width(if (compactScreen) 100.dp else 124.dp)",
        ".height(if (compactScreen) 98.dp else 118.dp)",
        "alpha = 1f",
        "Modifier.weight(1f)",
        "ContentScale.Fit",
        "preferences.edit().putInt(\"last_shown\", current).apply()",
    )
    if any(value not in source for value in required):
        raise RuntimeError("v451 lost compact visual treatment")
    if "maxLines =" in source or "TextOverflow.Ellipsis" in source:
        raise RuntimeError("v451 must not truncate reminder text")
    updated = original[:original.index(marker)] + source
    (java / "ImanQuoteCarousel.kt").write_text(updated, "utf-8")
    if updated.count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v451 changed curated reminder data")

    for name, before in protected.items():
        if sha(java / name) != before:
            raise RuntimeError("v451 changed unrelated Kotlin code: " + name)
    for name, before in book_hashes.items():
        if sha(assets / name) != before:
            raise RuntimeError("v451 changed saved chapter source: " + name)
    app_after = (java / "App.kt").read_text("utf-8")
    if NAV not in app_after or app_after[app_after.index(NAV):] != app_before[app_before.index(NAV):]:
        raise RuntimeError("v451 changed bottom navigation")
    book = json.loads((assets / "book.json").read_text("utf-8"))
    quiz = json.loads((assets / "quiz.json").read_text("utf-8"))
    if len(book["chapters"]) != 131 or len(quiz["chapters"]) != 131:
        raise RuntimeError("v451 changed chapter or quiz inventory")
    print("PASS v451: compact quote contrast, 79 reminders, 131 chapters, no unrelated changes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args()
    build_v451(Path(__file__).resolve().parents[1], args.dest)
