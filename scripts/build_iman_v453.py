"""v0.45.3: soft contact shadow under the existing reminder illustration.

Extends verified v0.45.2 with only a shadow layer and transparent lower space.
The original rendered scroll stays the same size, palette, position and artwork.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

from scripts.build_iman_v452 import build_v452
from scripts.build_iman_v20 import APP, NAV, replace_one
from scripts.iman_v453_contact_shadow import add_contact_shadow


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_v453(kit: Path, dest: Path) -> None:
    build_v452(kit, dest)
    java = dest / APP
    assets = dest / "app/src/main/assets"
    drawable = dest / "app/src/main/res/drawable-nodpi"
    quote_file = java / "ImanQuoteCarousel.kt"
    gradle = dest / "app/build.gradle"
    marker = "@Composable\ninternal fun ImanFeaturedQuoteCarousel("
    original_quote = quote_file.read_text("utf-8")
    if original_quote.count(marker) != 1 or original_quote.count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v453 quote structure or source count changed")
    protected = {p.name: sha(p) for p in java.glob("*.kt") if p.name != "ImanQuoteCarousel.kt"}
    book_hashes = {p.name: sha(p) for p in assets.iterdir() if p.is_file()}
    app_before = (java / "App.kt").read_text("utf-8")
    image_file = drawable / "iman_v43_approved_scroll.webp"

    configuration = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 52", "versionCode 53"),
        ("versionName '0.45.2'", "versionName '0.45.3'"),
        ("applicationIdSuffix '.preview452'", "applicationIdSuffix '.preview453'"),
    ):
        configuration = replace_one(configuration, old, new, "v453 isolated preview")
    gradle.write_text(configuration, "utf-8")

    previous = (kit / "scripts/ReferenceQuoteV452.kt").read_text("utf-8")
    new_quote = (kit / "scripts/ReferenceQuoteV453.kt").read_text("utf-8")
    expected = previous.replace(
        ".height(if (compactScreen) 78.dp else 94.dp)",
        ".height(if (compactScreen) 86.dp else 103.dp)"
    )
    if new_quote != expected:
        raise RuntimeError("v453 changed quote layout beyond extra shadow room")
    if ".width(if (compactScreen) 80.dp else 99.dp)" not in new_quote:
        raise RuntimeError("v453 lost approved 20 percent image size")
    quote_file.write_text(original_quote[:original_quote.index(marker)] + new_quote, "utf-8")

    with Image.open(image_file) as existing:
        original_image = existing.convert("RGBA")
    enhanced = add_contact_shadow(original_image)
    if enhanced.width != original_image.width or enhanced.height <= original_image.height:
        raise RuntimeError("v453 altered image width or omitted lower shadow room")
    if enhanced.size[1] != original_image.height + max(10, round(original_image.height * 0.12)):
        raise RuntimeError("v453 shadow margin does not preserve visual scale")
    if enhanced.getpixel((0, 0))[3] != 0:
        raise RuntimeError("v453 added a background rather than transparent shadow")
    enhanced.save(image_file, "WEBP", lossless=True, method=6, exact=True)
    with Image.open(image_file) as saved:
        if saved.mode != "RGBA" or saved.size != enhanced.size:
            raise RuntimeError("v453 damaged final WebP artwork")
        if saved.getpixel((0, 0))[3] != 0:
            raise RuntimeError("v453 lost transparent background")

    for name, before in protected.items():
        if sha(java / name) != before:
            raise RuntimeError("v453 modified unrelated Kotlin code: " + name)
    for name, before in book_hashes.items():
        if sha(assets / name) != before:
            raise RuntimeError("v453 modified book, quizzes or user assets: " + name)
    app_after = (java / "App.kt").read_text("utf-8")
    if NAV not in app_after or app_after[app_after.index(NAV):] != app_before[app_before.index(NAV):]:
        raise RuntimeError("v453 changed navigation")
    if quote_file.read_text("utf-8").count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v453 modified reminders")
    if len(json.loads((assets / "book.json").read_text("utf-8"))["chapters"]) != 131:
        raise RuntimeError("v453 modified the book")
    if len(json.loads((assets / "quiz.json").read_text("utf-8"))["chapters"]) != 131:
        raise RuntimeError("v453 modified the quizzes")
    print("PASS v453: soft bottom contact shadow, unchanged 20% object size, 79 quotes and 131 chapters")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args()
    build_v453(Path(__file__).resolve().parents[1], args.dest)
