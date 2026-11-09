"""v0.45.4: repair clipped shadow without changing approved drawing or layout.

Starts from the verified v0.45.3 app. Regenerates the precise v0.45.2
matte sprite (no previous shadow) and applies a bounded contact shadow.
Only the drawable and the isolated test-version metadata are different.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

from scripts.build_iman_v453 import build_v453
from scripts.build_iman_v20 import APP, NAV, replace_one
from scripts.iman_v452_style import build_matte_artwork
from scripts.iman_v454_bounded_shadow import add_contact_shadow, assert_shadow_boundaries


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_v454(kit: Path, dest: Path) -> None:
    build_v453(kit, dest)
    java = dest / APP
    assets = dest / "app/src/main/assets"
    drawable = dest / "app/src/main/res/drawable-nodpi"
    gradle = dest / "app/build.gradle"
    quote_file = java / "ImanQuoteCarousel.kt"
    image_file = drawable / "iman_v43_approved_scroll.webp"

    protected = {p.name: sha(p) for p in java.glob("*.kt")}
    book_hashes = {p.name: sha(p) for p in assets.iterdir() if p.is_file()}
    app_before = (java / "App.kt").read_text("utf-8")
    quote_before = quote_file.read_text("utf-8")

    config = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 53", "versionCode 54"),
        ("versionName '0.45.3'", "versionName '0.45.4'"),
        ("applicationIdSuffix '.preview453'", "applicationIdSuffix '.preview454'"),
    ):
        config = replace_one(config, old, new, "v454 isolated preview metadata")
    gradle.write_text(config, "utf-8")

    # Crucial: NEVER blur the already clipped v0.45.3 shadow.
    # Recreate the earlier approved matte artwork from the original pixels.
    source = kit / "assets/ui/v43/iman_v43_approved_scroll_inkwell_quill.webp"
    build_matte_artwork(source, drawable, image_file)
    with Image.open(image_file) as image:
        approved = image.convert("RGBA")
    final = add_contact_shadow(approved)
    assert_shadow_boundaries(approved, final)
    final.save(image_file, "WEBP", lossless=True, method=6, exact=True)
    with Image.open(image_file) as saved:
        assert_shadow_boundaries(approved, saved.convert("RGBA"))

    for name, before in protected.items():
        if sha(java / name) != before:
            raise RuntimeError("v454 modified Kotlin source outside approved asset work: " + name)
    for name, before in book_hashes.items():
        if sha(assets / name) != before:
            raise RuntimeError("v454 modified book, quizzes or user data: " + name)
    app_after = (java / "App.kt").read_text("utf-8")
    if NAV not in app_after or app_after != app_before:
        raise RuntimeError("v454 modified app navigation")
    if quote_file.read_text("utf-8") != quote_before:
        raise RuntimeError("v454 modified prior quote layout, wrapping or scale")
    if quote_before.count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v454 lost 79 reminders")
    if len(json.loads((assets / "book.json").read_text("utf-8"))["chapters"]) != 131:
        raise RuntimeError("v454 modified book chapters")
    if len(json.loads((assets / "quiz.json").read_text("utf-8"))["chapters"]) != 131:
        raise RuntimeError("v454 modified chapter quizzes")
    print("PASS v454: no clipped shadow boundaries, matte artwork and 20% scale preserved; 131 chapters, 79 reminders")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args()
    build_v454(Path(__file__).resolve().parents[1], args.dest)
