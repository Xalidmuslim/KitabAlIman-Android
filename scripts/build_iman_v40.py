"""v0.40: fourth library tile Hadiths, larger handwritten excerpts and haze-free engraving.

Patch only approved Compose Home / quote drawing / pre-rendered WebP resources
on the validated v0.39.1 base. Book, notes, stored progress and navigation
must remain byte-for-byte unchanged.
"""
from pathlib import Path
import argparse
import hashlib

import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageChops

from scripts.build_iman_v39 import build_v39
from scripts.build_iman_v20 import APP, NAV, replace_one


def digest(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def make_fine_engraving(drawable: Path) -> None:
    """Discard low-frequency brown fog, retaining ONLY book/quill/arch contours.

    Offline artifact: three overlapping thin alpha silhouettes imitate the
    directional highlight/shadow of a shallow emboss in old paper. There is no
    on-device ImageFilter and no solid rectangular region.
    """
    with Image.open(drawable / "iman_v35_reminder.webp") as src:
        rgba = src.convert("RGBA")
    gray = ImageOps.grayscale(rgba)
    edges = np.asarray(gray.filter(ImageFilter.FIND_EDGES), dtype=np.float32)
    source_alpha = np.asarray(rgba.getchannel("A"), dtype=np.float32) / 255.0
    h, w = edges.shape
    # Edge energy, not source brightness/opacity, drives visibility. This
    # eliminates the large filled oval from v0.39.1 even on long excerpts.
    strength = np.clip((edges - 17.0) / 90.0, 0.0, 1.0) ** 0.75
    x = np.arange(w, dtype=np.float32)[None, :]
    fade = np.clip((x - 0.06 * w) / max(1.0, 0.31 * w), 0.0, 1.0)
    intensity = strength * source_alpha * fade
    stroke_alpha = np.uint8(np.clip(intensity * 118.0, 0, 255))
    coverage = float(np.mean(stroke_alpha >= 20))
    if not (0.008 < coverage <= 0.34):
        raise RuntimeError(f"Engraving alpha coverage {coverage:.3f} indicates haze or missing outlines")

    core = Image.fromarray(stroke_alpha, "L")
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    def overlay(color, mask):
        layer = Image.new("RGBA", (w, h), color)
        layer.putalpha(mask)
        canvas.alpha_composite(layer)

    # A 1-pixel pair of translucent displaced outlines produces a matte
    # embossed direction without an opaque paper-colored rectangle.
    highlight = core.point(lambda v: min(255, round(v * 0.75)))
    shadow = core.point(lambda v: min(255, round(v * 0.72)))
    overlay((255, 249, 234, 255), ImageChops.offset(highlight, -1, -1))
    overlay((118, 90, 61, 255), ImageChops.offset(shadow, 1, 1))
    overlay((171, 139, 105, 255), core.point(lambda v: min(255, round(v * 0.28))))
    canvas.putpixel((0, 0), (0, 0, 0, 0))
    output = drawable / "iman_v40_engraving.webp"
    canvas.save(output, "WEBP", quality=96, method=6)
    if output.stat().st_size < 1000:
        raise RuntimeError("Engraving output too small")
    with Image.open(output) as saved:
        if saved.mode != "RGBA" or saved.getchannel("A").getextrema()[1] < 40:
            raise RuntimeError("Engraving has no visible transparent outlines")


def build_v40(kit: Path, dest: Path) -> None:
    build_v39(kit, dest)
    java = dest / APP
    drawable = dest / "app/src/main/res/drawable-nodpi"
    assets = dest / "app/src/main/assets"
    app = java / "App.kt"
    reader = java / "Reader.kt"
    app_before = digest(app)
    reader_before = digest(reader)
    book_hashes = {f.name: digest(f) for f in assets.iterdir() if f.is_file()}
    if NAV not in app.read_text("utf-8"):
        raise RuntimeError("v40 expected existing five-tab navigation")

    gradle = dest / "app/build.gradle"
    config = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 41", "versionCode 42"),
        ("versionName '0.39.1'", "versionName '0.40.0'"),
        ("applicationIdSuffix '.preview39'", "applicationIdSuffix '.preview40'"),
    ):
        config = replace_one(config, old, new, "isolated v40 preview package")
    gradle.write_text(config, "utf-8")

    make_fine_engraving(drawable)

    h = (kit / "scripts/ReferenceHomeV40.kt").read_text("utf-8")
    for name in ("contents", "collections", "glossary"):
        h = replace_one(h, f"R.drawable.iman_v32_{name}",
                        f"R.drawable.iman_v35_{name}", "preserve approved matte artwork")
    # Exactly four library choices; existing Notes remain in More/reader.
    library = h.split('item(key = "library-four")', 1)[1].split('item(key = "reading-stats")', 1)[0]
    if library.count('EditorialBookSection(') != 4:
        raise RuntimeError("v40 must have exactly four library tiles")
    if ('EditorialBookSection("Хадисы", "Источники"' not in library or
            "navigate(Route.Hadiths)" not in library or
            'EditorialBookSection("Заметки"' in library):
        raise RuntimeError("v40 did not replace the fourth library tile")
    (java / "ModernEditorialHome.kt").write_text(h, "utf-8")

    quote_file = java / "ImanQuoteCarousel.kt"
    original = quote_file.read_text("utf-8")
    marker = "@Composable\ninternal fun ImanFeaturedQuoteCarousel("
    if original.count(marker) != 1 or original.count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v40 quote inventory/anchors changed")
    q = (kit / "scripts/ReferenceQuoteV40.kt").read_text("utf-8")
    if ('R.drawable.iman_v40_engraving' not in q or
            'fontFamily = ImanCaveatFont' not in q or
            "fontFamily = if (length" in q or
            "TextOverflow.Ellipsis" in q):
        raise RuntimeError("v40 lost unbroken calligraphy or transparent art")
    quote_file.write_text(original[:original.index(marker)] + q, "utf-8")

    preload = java / "MedicineHomeArtwork.kt"
    current = preload.read_text("utf-8")
    current = replace_one(current,
        "        R.drawable.iman_v39_relief,",
        "        R.drawable.iman_v39_relief,\n"
        "        R.drawable.iman_v40_engraving,",
        "preload engraving off UI thread")
    preload.write_text(current, "utf-8")

    # Safe route presence: Hadiths are already backed by the original
    # reader/source catalogue, Notes still exist in More. Never rewrite App.
    more = (java / "ImanV38More.kt").read_text("utf-8")
    if "Route.Hadiths" not in more or "Route.Notes" not in more:
        raise RuntimeError("existing Hadiths or Notes menu route missing")
    if digest(app) != app_before or NAV not in app.read_text("utf-8") or digest(reader) != reader_before:
        raise RuntimeError("v40 changed reader or bottom tabs")
    for name, sha in book_hashes.items():
        if digest(assets / name) != sha:
            raise RuntimeError("v40 changed book/notes/quiz asset: " + name)
    if quote_file.read_text("utf-8").count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v40 lost any of the 79 citations")
    import json
    book = json.loads((assets / "book.json").read_text("utf-8"))
    if len(book["chapters"]) != 131:
        raise RuntimeError("v40 book chapter count changed")
    print("PASS v40: 4th Hadith tile, bigger same calligraphy, fine-line engraving, 131 chapters, 79 quotes, notes/reader/nav preserved")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args()
    build_v40(Path(__file__).resolve().parents[1], args.dest)
