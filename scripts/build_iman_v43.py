"""v0.43: approved compact scroll, feather and inkpot in the reminder background.

Only the transparent illustration and its layout are changed on top of
verified v0.42. Book, reader, quiz, notes, statistics and navigation stay intact.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from PIL import Image

from scripts.build_iman_v42 import build_v42
from scripts.build_iman_v20 import APP, NAV, replace_one


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_v43(kit: Path, dest: Path) -> None:
    build_v42(kit, dest)
    java = dest / APP
    assets = dest / "app/src/main/assets"
    drawable = dest / "app/src/main/res/drawable-nodpi"
    app = java / "App.kt"
    reader = java / "Reader.kt"
    app_before = digest(app)
    reader_before = digest(reader)
    book_hashes = {p.name: digest(p) for p in assets.iterdir() if p.is_file()}
    if NAV not in app.read_text("utf-8"):
        raise RuntimeError("v43 five-tab navigation missing")

    gradle = dest / "app/build.gradle"
    conf = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 44", "versionCode 46"),
        ("versionName '0.42.0'", "versionName '0.43.1'"),
        ("applicationIdSuffix '.preview42'", "applicationIdSuffix '.preview43'"),
    ):
        conf = replace_one(conf, old, new, "v43 separate preview")
    gradle.write_text(conf, "utf-8")

    # Use the approved real asset, not a screenshot and not a different rendering.
    source = kit / "assets/ui/v43/iman_v43_approved_scroll_inkwell_quill.webp"
    if not source.is_file() or source.stat().st_size < 3000:
        raise RuntimeError("approved v43 illustration is missing")
    with Image.open(source) as original:
        if original.mode != "RGBA":
            raise RuntimeError("approved source must have transparent alpha")
        w, h = original.size
        if not (0.83 < h / w < 1.12) or original.getpixel((0, 0))[3] != 0:
            raise RuntimeError("approved art dimensions or background corrupted")
        if original.getchannel("A").getextrema()[1] < 220:
            raise RuntimeError("approved art lost transparency or definition")
    shutil.copyfile(source, drawable / "iman_v43_approved_scroll.webp")

    quote_file = java / "ImanQuoteCarousel.kt"
    q_before = quote_file.read_text("utf-8")
    marker = "@Composable\ninternal fun ImanFeaturedQuoteCarousel("
    if q_before.count(marker) != 1 or q_before.count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v43 changed quote anchor or excerpt inventory")
    quote = (kit / "scripts/ReferenceQuoteV43.kt").read_text("utf-8")
    if (
        "R.drawable.iman_v43_approved_scroll" not in quote
        or "R.drawable.iman_v42_manuscript_qalam" in quote
        or "ImanQuoteAnimatedText(current, ink)" not in quote
        or "fontFamily = ImanCaveatFont" not in quote
        or ".width(if (compactScreen) 112.dp else 148.dp)" not in quote
        or ".height(if (compactScreen) 103.dp else 137.dp)" not in quote
        or "ContentScale.Fit" not in quote
    ):
        raise RuntimeError("v43 quote lost approved source or aspect-safe layout")
    quote_file.write_text(q_before[:q_before.index(marker)] + quote, "utf-8")

    preload = java / "MedicineHomeArtwork.kt"
    src = preload.read_text("utf-8")
    src = replace_one(
        src,
        "        R.drawable.iman_v42_manuscript_qalam,",
        "        R.drawable.iman_v42_manuscript_qalam,\n"
        "        R.drawable.iman_v43_approved_scroll,",
        "register approved scroll with artwork preloader"
    )
    preload.write_text(src, "utf-8")

    # No touching anything beyond the illustration, reminder layout and preloader.
    more = (java / "ImanV38More.kt").read_text("utf-8")
    if "Route.Hadiths" not in more or "Route.Notes" not in more:
        raise RuntimeError("v43 lost existing Hadiths or Notes")
    home = (java / "ModernEditorialHome.kt").read_text("utf-8")
    if 'EditorialBookSection("Хадисы", "Источники"' not in home:
        raise RuntimeError("v43 lost fourth library section")
    stats = (java / "ReadingStatisticsV36.kt").read_text("utf-8")
    if 'Text("$minutes"' not in stats or "height(22.dp)" not in stats:
        raise RuntimeError("v43 lost aligned week chart")
    if digest(app) != app_before or digest(reader) != reader_before or NAV not in app.read_text("utf-8"):
        raise RuntimeError("v43 changed reader or navigation")
    for name, original_hash in book_hashes.items():
        if digest(assets / name) != original_hash:
            raise RuntimeError("v43 changed book or user data: " + name)
    if quote_file.read_text("utf-8").count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v43 changed 79 original quotations")
    if len(json.loads((assets / "book.json").read_text("utf-8"))["chapters"]) != 131:
        raise RuntimeError("v43 changed 131 chapters")
    print("PASS v43: approved scroll/right edge/aspect safe, 131 chapters, 79 quotes, routes intact")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args()
    build_v43(Path(__file__).resolve().parents[1], args.dest)
