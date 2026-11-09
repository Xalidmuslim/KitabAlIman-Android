"""v0.41: enhance ONLY sparse engraved strokes and fix the weekly-reading layout.

Keep the approved parchment, four library illustrations, 79 reminders, 131 chapters,
reader and existing five-tab navigation exactly as in verified v0.40.
"""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from PIL import Image

from scripts.build_iman_v40 import build_v40
from scripts.build_iman_v20 import APP, NAV, replace_one


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def strengthen_engraving(drawable: Path) -> None:
    """Increase existing contour alpha 23%; never fill non-outline pixels."""
    original = drawable / "iman_v40_engraving.webp"
    result = drawable / "iman_v41_engraving.webp"
    with Image.open(original) as image:
        art = image.convert("RGBA")
    alpha = np.asarray(art.getchannel("A"), dtype=np.uint8)
    visible = alpha > 0
    # The alpha-only operation keeps every transparent pixel transparent,
    # preventing the return of the large painted brown haze.
    stronger = np.uint8(np.clip(alpha.astype(np.float32) * 1.23, 0, 255))
    if np.any((alpha == 0) & (stronger != 0)):
        raise RuntimeError("v41 engraving filled transparent pixels")
    coverage = float(np.mean(stronger >= 20))
    if not (0.008 < coverage <= 0.34):
        raise RuntimeError(f"v41 engraving unexpectedly dense: {coverage:.3f}")
    if int(stronger.max()) <= int(alpha.max()):
        raise RuntimeError("v41 did not strengthen any engraved contour")
    art.putalpha(Image.fromarray(stronger, "L"))
    art.save(result, "WEBP", quality=97, method=6)
    if result.stat().st_size < 1000:
        raise RuntimeError("v41 engraving output missing")


def build_v41(kit: Path, dest: Path) -> None:
    build_v40(kit, dest)
    java = dest / APP
    drawable = dest / "app/src/main/res/drawable-nodpi"
    assets = dest / "app/src/main/assets"
    app = java / "App.kt"
    reader = java / "Reader.kt"
    app_before = sha(app)
    reader_before = sha(reader)
    book_hashes = {f.name: sha(f) for f in assets.iterdir() if f.is_file()}
    if NAV not in app.read_text("utf-8"):
        raise RuntimeError("v41 expected unchanged native navigation")

    gradle = dest / "app/build.gradle"
    config = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 42", "versionCode 43"),
        ("versionName '0.40.0'", "versionName '0.41.0'"),
        ("applicationIdSuffix '.preview40'", "applicationIdSuffix '.preview41'"),
    ):
        config = replace_one(config, old, new, "isolated v41 test package")
    gradle.write_text(config, "utf-8")

    strengthen_engraving(drawable)

    h = (kit / "scripts/ReferenceHomeV41.kt").read_text("utf-8")
    for name in ("contents", "collections", "glossary"):
        h = replace_one(h, f"R.drawable.iman_v32_{name}",
                        f"R.drawable.iman_v35_{name}", "approved library artwork")
    library = h.split('item(key = "library-four")', 1)[1].split('item(key = "reading-stats")', 1)[0]
    if library.count("EditorialBookSection(") != 4 or "navigate(Route.Hadiths)" not in library:
        raise RuntimeError("v41 changed approved four-section library")
    (java / "ModernEditorialHome.kt").write_text(h, "utf-8")

    stats = (kit / "scripts/ReadingStatisticsV41.kt").read_text("utf-8")
    if ('dayNames[index]' not in stats or 'Text("$minutes"' not in stats
            or 'height(22.dp)' not in stats
            or 'screenHeightDp >= 740' not in stats
            or 'ledger.daysAgo(it)' not in stats):
        raise RuntimeError("v41 missing aligned real-time weekly reading minutes")
    (java / "ReadingStatisticsV36.kt").write_text(stats, "utf-8")

    quote_file = java / "ImanQuoteCarousel.kt"
    original = quote_file.read_text("utf-8")
    marker = "@Composable\ninternal fun ImanFeaturedQuoteCarousel("
    if original.count(marker) != 1 or original.count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v41 reminder source data changed")
    quote = (kit / "scripts/ReferenceQuoteV41.kt").read_text("utf-8")
    if "R.drawable.iman_v41_engraving" not in quote or "fontFamily = ImanCaveatFont" not in quote:
        raise RuntimeError("v41 lost engraved quote or consistent handwritten font")
    quote_file.write_text(original[:original.index(marker)] + quote, "utf-8")

    preloader = java / "MedicineHomeArtwork.kt"
    pre = preloader.read_text("utf-8")
    pre = replace_one(pre,
        "        R.drawable.iman_v40_engraving,",
        "        R.drawable.iman_v40_engraving,\n"
        "        R.drawable.iman_v41_engraving,",
        "preload already-rendered engraving")
    preloader.write_text(pre, "utf-8")

    more = (java / "ImanV38More.kt").read_text("utf-8")
    if not all(route in more for route in ("Route.Notes", "Route.Hadiths")):
        raise RuntimeError("v41 lost original notes or hadith sources")
    if sha(app) != app_before or sha(reader) != reader_before or NAV not in app.read_text("utf-8"):
        raise RuntimeError("v41 changed the reader or bottom navigation")
    for name, original_sha in book_hashes.items():
        if sha(assets / name) != original_sha:
            raise RuntimeError("v41 changed book, notes or quiz data: " + name)
    if quote_file.read_text("utf-8").count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v41 changed any of the 79 sourced excerpts")
    book = json.loads((assets / "book.json").read_text("utf-8"))
    if len(book["chapters"]) != 131:
        raise RuntimeError("v41 book chapter inventory changed")
    print("PASS v41: +23% contour alpha, aligned compact weekly chart, adaptive stats gaps, untouched reader/book/routes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args()
    build_v41(Path(__file__).resolve().parents[1], args.dest)
