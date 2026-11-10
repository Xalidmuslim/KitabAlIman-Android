"""v0.45.9 – integrate the user-approved seamless manuscript illustration into the native reader.

Keeps v0.45.8 frame-free UI and CTA. Changes ONLY the reminder composable and
adds a single alpha-aware WebP, decoded from the checked-in data source.
"""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
from PIL import Image

from scripts.build_iman_v458 import build_v458
from scripts.build_iman_v20 import APP, NAV, replace_one

APPROVED_HASH = "c82dd7e55f74ffa322daba9ca25918fd4489927cd63316be69e4582cc80a5965"


def checksum(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build_v459(kit: Path, dest: Path):
    build_v458(kit, dest)
    java = dest / APP
    assets = dest / "app/src/main/assets"
    drawable = dest / "app/src/main/res/drawable-nodpi"
    gradle = dest / "app/build.gradle"
    quote_file = java / "ImanQuoteCarousel.kt"
    original_quote = quote_file.read_text("utf-8")
    original_nav = (java / "App.kt").read_text("utf-8")
    protected = {p.name: checksum(p) for p in java.glob("*.kt") if p != quote_file}
    assets_before = {p.name: checksum(p) for p in assets.iterdir() if p.is_file()}

    version = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 58", "versionCode 59"),
        ("versionName '0.45.8'", "versionName '0.45.9'"),
        ("applicationIdSuffix '.preview458'", "applicationIdSuffix '.preview459'"),
    ):
        version = replace_one(version, old, new, "v459 isolated release")
    gradle.write_text(version, "utf-8")

    # Only the two old artwork layers are replaced; all 79 excerpts,
    # navigation actions, handwriting and responsive text widths remain untouched.
    marker = "@Composable\ninternal fun ImanFeaturedQuoteCarousel("
    if original_quote.count(marker) != 1:
        raise RuntimeError("v459 missing existing quote composable")
    source = (kit/"scripts/ReferenceQuoteV459.kt").read_text("utf-8")
    previous = (kit/"scripts/ReferenceQuoteV456.kt").read_text("utf-8")
    before_tag = "                    // Background relief is transparent"
    after_tag = "\n                }\n                HorizontalDivider("
    if (source.split("                    // Approved integrated")[0]
            != previous.split(before_tag)[0]):
        raise RuntimeError("v459 altered responsive reminder text or header")
    if source.split(after_tag)[1] != previous.split(after_tag)[1]:
        raise RuntimeError("v459 altered reminder actions or following UI")
    quote_file.write_text(original_quote.split(marker)[0]+source, "utf-8")

    from scripts.iman_v459_art_data import APPROVED_WEBP_BASE64
    art = base64.b64decode(APPROVED_WEBP_BASE64, validate=True)
    if hashlib.sha256(art).hexdigest() != APPROVED_HASH:
        raise RuntimeError("v459 approved artwork binary digest mismatch")
    target = drawable/"iman_v459_integrated_manuscript.webp"
    with Image.open(io.BytesIO(art)) as img:
        if img.size != (240, 162) or img.mode != "RGBA":
            raise RuntimeError("v459 artwork lost RGBA transparency")
        rgba = img.getchannel("A")
        if rgba.getextrema()[0] != 0 or max(rgba.crop((0,0,240,1)).getextrema()) > 2:
            raise RuntimeError("v459 top edge not feathered")
        if any(rgba.getpixel(c) != 0 for c in ((0,0),(239,0),(0,161),(239,161))):
            raise RuntimeError("v459 rectangular outline on corners")
    target.write_bytes(art)
    if checksum(target) != APPROVED_HASH:
        raise RuntimeError("v459 artwork was damaged when written to drawable")

    for file, prev in protected.items():
        if checksum(java/file) != prev:
            raise RuntimeError("v459 unrelated Kotlin code changed: "+file)
    for file, prev in assets_before.items():
        if checksum(assets/file) != prev:
            raise RuntimeError("v459 altered book/quiz/bookmark source: "+file)
    if NAV not in original_nav or (java/"App.kt").read_text("utf-8") != original_nav:
        raise RuntimeError("v459 altered native navigation")
    if quote_file.read_text("utf-8").count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v459 lost an excerpt")
    if len(json.loads((assets/"book.json").read_text("utf-8"))["chapters"]) != 131:
        raise RuntimeError("v459 book chapters changed")
    if len(json.loads((assets/"quiz.json").read_text("utf-8"))["chapters"]) != 131:
        raise RuntimeError("v459 quiz chapters changed")
    print("PASS v459: approved transparent manuscript applied, 131 chapters and 79 quotes preserved")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", type=Path, required=True)
    args = ap.parse_args()
    build_v459(Path(__file__).resolve().parents[1], args.dest)
