"""v0.45.6: fix grainy hovering rug without touching book or scroll artwork."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

from scripts.build_iman_v455 import build_v455
from scripts.build_iman_v20 import APP, NAV, replace_one
from scripts.iman_v456_ground import make_ground, verify_ground


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_v456(kit: Path, dest: Path) -> None:
    build_v455(kit, dest)
    java = dest / APP
    assets = dest / "app/src/main/assets"
    drawable = dest / "app/src/main/res/drawable-nodpi"
    gradle = dest / "app/build.gradle"
    quote_file = java / "ImanQuoteCarousel.kt"
    ground_file = drawable / "iman_v455_ground_rug.webp"
    scroll_file = drawable / "iman_v43_approved_scroll.webp"

    protected = {p.name: sha(p) for p in java.glob("*.kt")
                 if p.name != "ImanQuoteCarousel.kt"}
    book_hashes = {p.name: sha(p) for p in assets.iterdir() if p.is_file()}
    original_scroll_hash = sha(scroll_file)
    original_nav = (java / "App.kt").read_text("utf-8")
    before_quote = quote_file.read_text("utf-8")
    marker = "@Composable\ninternal fun ImanFeaturedQuoteCarousel("
    if before_quote.count(marker) != 1 or before_quote.count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v456 original quote source unexpectedly changed")

    config = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 55", "versionCode 56"),
        ("versionName '0.45.5'", "versionName '0.45.6'"),
        ("applicationIdSuffix '.preview455'", "applicationIdSuffix '.preview456'"),
    ):
        config = replace_one(config, old, new, "v456 isolated preview metadata")
    gradle.write_text(config, "utf-8")

    old = (kit / "scripts/ReferenceQuoteV455.kt").read_text("utf-8")
    revised = (kit / "scripts/ReferenceQuoteV456.kt").read_text("utf-8")
    expected = old.replace(
        ".requiredWidth(if (compactScreen) 119.dp else 147.dp)",
        ".requiredWidth(if (compactScreen) 133.dp else 174.dp)"
    )
    if expected == old or revised != expected:
        raise RuntimeError("v456 may only widen the transparent ornament behind the scroll")
    updated = before_quote[:before_quote.index(marker)] + revised
    quote_file.write_text(updated, "utf-8")

    ground = make_ground()
    verify_ground(ground)
    ground.save(ground_file, "WEBP", lossless=True, method=6, exact=True)
    with Image.open(ground_file) as saved:
        verify_ground(saved.convert("RGBA"))

    if sha(scroll_file) != original_scroll_hash:
        raise RuntimeError("v456 modified the approved scroll colors or shape")
    for name, checksum in protected.items():
        if sha(java / name) != checksum:
            raise RuntimeError("v456 modified unrelated Kotlin file: " + name)
    for name, checksum in book_hashes.items():
        if sha(assets / name) != checksum:
            raise RuntimeError("v456 modified source book or quizzes: " + name)
    if (java / "App.kt").read_text("utf-8") != original_nav or NAV not in original_nav:
        raise RuntimeError("v456 modified navigation")
    if updated.count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v456 lost reminders")
    if len(json.loads((assets / "book.json").read_text("utf-8"))["chapters"]) != 131:
        raise RuntimeError("v456 modified book chapters")
    if len(json.loads((assets / "quiz.json").read_text("utf-8"))["chapters"]) != 131:
        raise RuntimeError("v456 modified quiz chapters")
    print("PASS v456: ornament no longer grainy, edges transparent, same 20% scroll size, 131 chapters, 79 quotes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args()
    build_v456(Path(__file__).resolve().parents[1], args.dest)
