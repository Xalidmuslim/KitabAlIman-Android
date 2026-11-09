"""v0.45.5: seamlessly grounded manuscript relief, the approved image stays intact.

Builds on verified v0.45.4. Only adds a transparent, four-times-resolution
background ornament and a single Box overlay in the reminder composable.
All 131 chapters, 79 excerpts, user state and navigation are immutable.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

from scripts.build_iman_v454 import build_v454
from scripts.build_iman_v20 import APP, NAV, replace_one
from scripts.iman_v455_ground import make_ground, verify_ground


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_v455(kit: Path, dest: Path) -> None:
    build_v454(kit, dest)
    java = dest / APP
    assets = dest / "app/src/main/assets"
    drawable = dest / "app/src/main/res/drawable-nodpi"
    gradle = dest / "app/build.gradle"
    quote_file = java / "ImanQuoteCarousel.kt"
    original_scroll = drawable / "iman_v43_approved_scroll.webp"
    original_scroll_hash = sha(original_scroll)
    protected = {
        p.name: sha(p) for p in java.glob("*.kt") if p.name != "ImanQuoteCarousel.kt"
    }
    book_hashes = {
        p.name: sha(p) for p in assets.iterdir() if p.is_file()
    }
    app_before = (java / "App.kt").read_text("utf-8")
    quote_before = quote_file.read_text("utf-8")
    marker = "@Composable\ninternal fun ImanFeaturedQuoteCarousel("
    if quote_before.count(marker) != 1:
        raise RuntimeError("v455 quote structure unexpectedly changed")

    config = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 54", "versionCode 55"),
        ("versionName '0.45.4'", "versionName '0.45.5'"),
        ("applicationIdSuffix '.preview454'", "applicationIdSuffix '.preview455'"),
    ):
        config = replace_one(config, old, new, "v455 isolated preview")
    gradle.write_text(config, "utf-8")

    source = (kit / "scripts/ReferenceQuoteV455.kt").read_text("utf-8")
    baseline = (kit / "scripts/ReferenceQuoteV453.kt").read_text("utf-8")
    old_start = "                    Image(\n                        painter = MedicineHomeArtwork.painter(R.drawable.iman_v43_approved_scroll),"
    tail = "\n                }\n                HorizontalDivider("
    if baseline.count(old_start) != 1 or baseline.count(tail) != 1:
        raise RuntimeError("v455 approved reminder anchor changed")
    if source.split("                    // Background relief is transparent", 1)[0] != baseline.split(old_start, 1)[0]:
        raise RuntimeError("v455 modified text, quote text flow or unrelated composables")
    if source.split(tail, 1)[1] != baseline.split(tail, 1)[1]:
        raise RuntimeError("v455 modified actions, stats or navigation")
    if ".width(if (compactScreen) 80.dp else 99.dp)" not in source:
        raise RuntimeError("v455 changed approved scroll dimensions")
    if ".requiredWidth(if (compactScreen) 119.dp else 147.dp)" not in source:
        raise RuntimeError("v455 did not reserve transparent relief width")
    for required in (
        "R.drawable.iman_v43_approved_scroll",
        "R.drawable.iman_v455_ground_rug",
        "ImanQuoteAnimatedText(current, ink, compactScreen)",
        "Modifier.weight(1f)",
        "navigate(Route.Reader(q.chapterId, q.blockId))",
    ):
        if required not in source:
            raise RuntimeError("v455 missing approved reminder contract: " + required)
    updated = quote_before[:quote_before.index(marker)] + source
    quote_file.write_text(updated, "utf-8")

    ground = make_ground()
    verify_ground(ground)
    ornament = drawable / "iman_v455_ground_rug.webp"
    ground.save(ornament, "WEBP", lossless=True, method=6, exact=True)
    with Image.open(ornament) as stored:
        verify_ground(stored.convert("RGBA"))
        if stored.mode != "RGBA":
            raise RuntimeError("v455 lost transparent artifact")

    if sha(original_scroll) != original_scroll_hash:
        raise RuntimeError("v455 modified the approved scroll colors or drawing")
    for name, before in protected.items():
        if sha(java / name) != before:
            raise RuntimeError("v455 altered unrelated Kotlin file: " + name)
    for name, before in book_hashes.items():
        if sha(assets / name) != before:
            raise RuntimeError("v455 altered book or quiz data: " + name)
    app_after = (java / "App.kt").read_text("utf-8")
    if NAV not in app_after or app_before != app_after:
        raise RuntimeError("v455 altered navigation or root application")
    if updated.count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v455 changed reminder inventory")
    if len(json.loads((assets / "book.json").read_text("utf-8"))["chapters"]) != 131:
        raise RuntimeError("v455 changed book content")
    if len(json.loads((assets / "quiz.json").read_text("utf-8"))["chapters"]) != 131:
        raise RuntimeError("v455 changed quizzes")
    print("PASS v455: transparent relief, original scroll unchanged, 79 quotes and 131 chapters")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args()
    build_v455(Path(__file__).resolve().parents[1], args.dest)
