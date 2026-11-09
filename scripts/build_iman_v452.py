"""v0.45.2: matte library-matched reminder image, 20% smaller.

Starts from verified v0.45.1; only reminder illustration color, width/height,
and isolated preview version change. Preserves all source books and user data.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

from scripts.build_iman_v451 import build_v451
from scripts.build_iman_v20 import APP, NAV, replace_one
from scripts.iman_v452_style import build_matte_artwork


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_v452(kit: Path, dest: Path) -> None:
    build_v451(kit, dest)
    java = dest / APP
    assets = dest / "app/src/main/assets"
    drawable = dest / "app/src/main/res/drawable-nodpi"
    gradle = dest / "app/build.gradle"
    quote_file = java / "ImanQuoteCarousel.kt"
    original_quote = quote_file.read_text("utf-8")
    marker = "@Composable\ninternal fun ImanFeaturedQuoteCarousel("
    if original_quote.count(marker) != 1:
        raise RuntimeError("v452 quote anchor missing")

    protected = {p.name: sha(p) for p in java.glob("*.kt") if p.name != "ImanQuoteCarousel.kt"}
    book_hashes = {p.name: sha(p) for p in assets.iterdir() if p.is_file()}
    app_before = (java / "App.kt").read_text("utf-8")
    art_before = sha(drawable / "iman_v43_approved_scroll.webp")

    conf = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 51", "versionCode 52"),
        ("versionName '0.45.1'", "versionName '0.45.2'"),
        ("applicationIdSuffix '.preview451'", "applicationIdSuffix '.preview452'"),
    ):
        conf = replace_one(conf, old, new, "v452 isolated preview")
    gradle.write_text(conf, "utf-8")

    updated_quote = (kit / "scripts/ReferenceQuoteV452.kt").read_text("utf-8")
    previous_quote = (kit / "scripts/ReferenceQuoteV451.kt").read_text("utf-8")
    expected_quote = previous_quote.replace(
        ".width(if (compactScreen) 100.dp else 124.dp)",
        ".width(if (compactScreen) 80.dp else 99.dp)"
    ).replace(
        ".height(if (compactScreen) 98.dp else 118.dp)",
        ".height(if (compactScreen) 78.dp else 94.dp)"
    )
    if updated_quote != expected_quote:
        raise RuntimeError("v452 modified reminder logic instead of just 20% artwork size")
    quote_file.write_text(original_quote[:original_quote.index(marker)] + updated_quote, "utf-8")

    # Only re-grade the approved drawable; preserve alpha, shape and identifiers.
    output = drawable / "iman_v43_approved_scroll.webp"
    source = kit / "assets/ui/v43/iman_v43_approved_scroll_inkwell_quill.webp"
    build_matte_artwork(source, drawable, output)
    with Image.open(output) as result:
        if result.mode != "RGBA" or result.getpixel((0, 0))[3] != 0:
            raise RuntimeError("v452 lost the transparent corner")
    if sha(output) == art_before or output.stat().st_size < 3000:
        raise RuntimeError("v452 matte artwork not applied")

    for name, before in protected.items():
        if sha(java / name) != before:
            raise RuntimeError("v452 touched unrelated Kotlin file: " + name)
    for name, before in book_hashes.items():
        if sha(assets / name) != before:
            raise RuntimeError("v452 touched book or user asset: " + name)
    app_after = (java / "App.kt").read_text("utf-8")
    if NAV not in app_after or app_after[app_after.index(NAV):] != app_before[app_before.index(NAV):]:
        raise RuntimeError("v452 navigation changed")
    quote_after = quote_file.read_text("utf-8")
    if quote_after.count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v452 reminder source inventory changed")
    if len(json.loads((assets / "book.json").read_text("utf-8"))["chapters"]) != 131:
        raise RuntimeError("v452 book lost chapters")
    if len(json.loads((assets / "quiz.json").read_text("utf-8"))["chapters"]) != 131:
        raise RuntimeError("v452 quiz inventory changed")
    print("PASS v452: original relief alpha, matte-library palette, 20% smaller art, 79 quotes and 131 chapters")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args()
    build_v452(Path(__file__).resolve().parents[1], args.dest)
