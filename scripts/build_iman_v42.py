"""v0.42: replace the reminder engraving with a transparent manuscript and reed qalam.

This builds on verified v0.41 (week chart/spacing). Only the quote artwork and
its placement change. Preserve the book, 79 source excerpts, quizzes and routes.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from PIL import Image

from scripts.build_iman_v41 import build_v41
from scripts.build_iman_v20 import APP, NAV, replace_one


def digest(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build_v42(kit: Path, dest: Path) -> None:
    build_v41(kit, dest)
    java = dest / APP
    assets = dest / "app/src/main/assets"
    drawables = dest / "app/src/main/res/drawable-nodpi"
    app = java / "App.kt"
    reader = java / "Reader.kt"
    app_before = digest(app)
    reader_before = digest(reader)
    book_hashes = {f.name: digest(f) for f in assets.iterdir() if f.is_file()}
    if NAV not in app.read_text("utf-8"):
        raise RuntimeError("v42 changed native navigation")

    gradle = dest / "app/build.gradle"
    config = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 43", "versionCode 44"),
        ("versionName '0.41.0'", "versionName '0.42.0'"),
        ("applicationIdSuffix '.preview41'", "applicationIdSuffix '.preview42'"),
    ):
        config = replace_one(config, old, new, "isolated v42 preview build")
    gradle.write_text(config, "utf-8")

    # A generated matte-sepia manuscript and actual reed pen. Source image was
    # isolated to a transparent alpha illustration offline, not a rectangular
    # mockup screenshot. No runtime blur or bitmap filtering is performed.
    source = kit / "assets/ui/v42/iman_v42_manuscript_qalam.webp"
    if not source.is_file() or source.stat().st_size < 1000:
        raise RuntimeError("v42 transparent illustration missing")
    with Image.open(source) as im:
        if im.mode != "RGBA" or im.getpixel((0, 0))[3] != 0:
            raise RuntimeError("v42 manuscript is not transparent")
        lo, hi = im.getchannel("A").getextrema()
        if lo != 0 or hi < 90:
            raise RuntimeError("v42 manuscript has no visible fade")
    shutil.copyfile(source, drawables / "iman_v42_manuscript_qalam.webp")

    quote_path = java / "ImanQuoteCarousel.kt"
    previous = quote_path.read_text("utf-8")
    marker = "@Composable\\ninternal fun ImanFeaturedQuoteCarousel("
    if previous.count(marker) != 1 or previous.count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v42 reminder inventory changed")
    snippet = (kit / "scripts/ReferenceQuoteV42.kt").read_text("utf-8")
    if ("R.drawable.iman_v42_manuscript_qalam" not in snippet or
            "R.drawable.iman_v41_engraving" in snippet or
            "fontFamily = ImanCaveatFont" not in snippet or
            "ImanQuoteAnimatedText(current, ink)" not in snippet):
        raise RuntimeError("v42 quote lost the new drawing or handwriting")
    quote_path.write_text(previous[:previous.index(marker)] + snippet, "utf-8")

    preloader = java / "MedicineHomeArtwork.kt"
    before = preloader.read_text("utf-8")
    before = replace_one(
        before, "        R.drawable.iman_v41_engraving,",
        "        R.drawable.iman_v41_engraving,\\n"
        "        R.drawable.iman_v42_manuscript_qalam,",
        "preload new illustration exactly once",
    )
    preloader.write_text(before, "utf-8")

    # No change to the dashboard, chart, header, five bottom tabs or storage.
    statistics = (java / "ReadingStatisticsV36.kt").read_text("utf-8")
    if 'Text("$minutes"' not in statistics or "height(22.dp)" not in statistics:
        raise RuntimeError("v42 lost improved weekly graph")
    home = (java / "ModernEditorialHome.kt").read_text("utf-8")
    if 'EditorialBookSection("Хадисы", "Источники"' not in home:
        raise RuntimeError("v42 lost fourth Hadith tile")
    more = (java / "ImanV38More.kt").read_text("utf-8")
    if "Route.Notes" not in more or "Route.Hadiths" not in more:
        raise RuntimeError("v42 lost Notes or Hadith sources")
    if digest(app) != app_before or digest(reader) != reader_before or NAV not in app.read_text("utf-8"):
        raise RuntimeError("v42 modified reader or navigation")
    for name, old_hash in book_hashes.items():
        if digest(assets / name) != old_hash:
            raise RuntimeError("v42 altered book, notes or quiz: " + name)
    if quote_path.read_text("utf-8").count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v42 source quote count changed")
    book = json.loads((assets / "book.json").read_text("utf-8"))
    if len(book["chapters"]) != 131:
        raise RuntimeError("v42 chapter inventory changed")
    print("PASS v42: right-edge transparent manuscript/qalam; 79 quotes, 131 chapters, stats and routes intact")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args()
    build_v42(Path(__file__).resolve().parents[1], args.dest)
