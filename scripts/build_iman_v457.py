"""Build v0.45.7 from verified v0.45.6: borderless reading, warm clarity.

Never alter the source book/quiz/featured-quote JSON, the five-tab navigator
or the saved user state. Separate applicationIdSuffix keeps this a preview.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from PIL import Image, ImageEnhance

from scripts.build_iman_v456 import build_v456
from scripts.build_iman_v20 import APP, NAV, replace_one
from scripts.iman_v457_ui import patch_ui


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def crisp_asset(path: Path, contrast: float, sharpness: float, brightness: float = 1.0):
    with Image.open(path) as original:
        transparent = original.mode in ("RGBA", "LA") or "transparency" in original.info
        source = original.convert("RGBA") if transparent else original.convert("RGB")
    alpha = source.getchannel("A") if transparent else None
    rgb = source.convert("RGB")
    rgb = ImageEnhance.Contrast(rgb).enhance(contrast)
    rgb = ImageEnhance.Sharpness(rgb).enhance(sharpness)
    rgb = ImageEnhance.Brightness(rgb).enhance(brightness)
    if transparent:
        rgb = rgb.convert("RGBA")
        rgb.putalpha(alpha)
    rgb.save(path, "WEBP", lossless=True, method=6, exact=True)
    with Image.open(path) as result:
        if result.size != source.size:
            raise RuntimeError("v457 resized approved illustration")
        if alpha is not None and result.getchannel("A").tobytes() != alpha.tobytes():
            raise RuntimeError("v457 damaged feathered illustration transparency")


def build_v457(kit: Path, dest: Path) -> None:
    build_v456(kit, dest)
    java = dest / APP
    assets = dest / "app/src/main/assets"
    drawable = dest / "app/src/main/res/drawable-nodpi"
    gradle = dest / "app/build.gradle"
    nav_before = (java / "App.kt").read_text("utf-8")
    if NAV not in nav_before:
        raise RuntimeError("Missing verified five-tab native navigator")
    assets_before = {p.name: sha(p) for p in assets.iterdir() if p.is_file()}
    quotes_before = sha(java / "ImanQuoteCarousel.kt")

    config = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 56", "versionCode 57"),
        ("versionName '0.45.6'", "versionName '0.45.7'"),
        ("applicationIdSuffix '.preview456'", "applicationIdSuffix '.preview457'"),
    ):
        config = replace_one(config, old, new, "v457 preview-only metadata")
    gradle.write_text(config, "utf-8")

    touched = patch_ui(java)
    theme = kit / "scripts/ImanUnifiedPaperV457.kt"
    if not theme.is_file():
        raise RuntimeError("The verified v457 palette is missing")
    shutil.copyfile(theme, java / "ImanUnifiedPaper.kt")
    crisp_asset(drawable / "iman_v38_flat_paper.webp", 1.05, 1.04, 1.015)
    crisp_asset(drawable / "iman_v43_approved_scroll.webp", 1.09, 1.12)

    # Preserve source text, all 79 excerpt anchors, the native route model,
    # bookmarks and saved reading state in every generated preview.
    if (java / "App.kt").read_text("utf-8") != nav_before:
        raise RuntimeError("v457 modified the navigator or reading state routing")
    if sha(java / "ImanQuoteCarousel.kt") != quotes_before:
        raise RuntimeError("v457 modified approved 79-reminder carousel")
    for name, checksum in assets_before.items():
        if sha(assets / name) != checksum:
            raise RuntimeError("v457 modified source book or quizzes: " + name)
    book = json.loads((assets / "book.json").read_text("utf-8"))
    quizzes = json.loads((assets / "quiz.json").read_text("utf-8"))
    quotes = json.loads((assets / "featured_quotes.json").read_text("utf-8"))
    if len(book["chapters"]) != 131 or len(quizzes["chapters"]) != 131 or len(quotes) != 79:
        raise RuntimeError("v457 source inventory changed")
    about = (java / "Screens.kt").read_text("utf-8")
    reader = (java / "Reader.kt").read_text("utf-8")
    if "Важное примечание" in about or "медицинское руководство" in about:
        raise RuntimeError("Old medical notice remains visible")
    if "OutlinedButton(" in reader or "SuggestionChip(" not in reader:
        raise RuntimeError("Reader action rows did not become borderless")
    print("PASS v457:", len(touched),
          "native UI modules, frameless reading controls, crisp parchment,",
          "131 chapters, 79 excerpts and 5-tab navigator preserved")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", type=Path, required=True)
    args = ap.parse_args()
    build_v457(Path(__file__).resolve().parents[1], args.dest)
