"""v0.46.7: move the manuscript illustration right and feather its paper haze.

The v0.46.6 library-matched warm matte colors, manuscript, fonts, library
assets, user state and original book are retained. Only translucent pixels
inside the reminder image, its horizontal modifier and preview version change.
"""
import argparse
import hashlib
from pathlib import Path

import numpy as np
from PIL import Image

from scripts.build_iman_v466 import build_v466, PAPER
from scripts.build_iman_v20 import APP, replace_one


def _smoothstep(values: np.ndarray) -> np.ndarray:
    t = np.clip(values, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def soften_reminder_background(picture: Image.Image) -> Image.Image:
    """Lighten diffuse parchment haze; keep scroll, ink and quill high-contrast.

    Mask both edges of the image so a +6dp rightward shift remains *inside*
    the Home screen and cannot crop any strongly opaque object pixels.
    """
    raw = np.asarray(picture.convert("RGBA"), dtype=np.float32).copy()
    height, width = raw.shape[:2]
    if (width, height) != (256, 225):
        raise RuntimeError("Unexpected approved manuscript aspect or size")

    rgb = raw[:, :, :3]
    lum = rgb @ np.array([.2126, .7152, .0722], dtype=np.float32)
    # Bright diffuse paper, window lighting and background glow should blend
    # with native parchment; deep-brown manuscript contours retain their relief.
    paper_haze = _smoothstep((lum - 143.0) / 97.0)
    rgb[:] = np.clip(rgb + (
        np.asarray(PAPER, dtype=np.float32)[None, None, :] - rgb
    ) * (.065 * paper_haze[..., None]), 0, 255)

    alpha = raw[:, :, 3] * (.96 - .36 * paper_haze)
    x = np.arange(width, dtype=np.float32)
    y = np.arange(height, dtype=np.float32)
    # 35px right feathering supplies room for the intended 6dp Compose offset.
    left = _smoothstep(x / 47.0)
    right = _smoothstep((width - 1 - x) / 35.0)
    top = _smoothstep(y / 19.0)
    bottom = _smoothstep((height - 1 - y) / 20.0)
    alpha *= (left * right)[None, :] * (top * bottom)[:, None]
    alpha[:, 0] = 0
    alpha[:, -1] = 0
    alpha[0, :] = 0
    alpha[-1, :] = 0
    raw[:, :, 3] = np.clip(alpha, 0, 255)

    return Image.fromarray(np.rint(raw).astype(np.uint8), "RGBA")


def patch_position(source: str) -> str:
    # Preserve width, height, alignment, quote typography and exact chapter links.
    old = ".offset(y = (0).dp)"
    new = ".offset(x = 6.dp, y = (0).dp)"
    return replace_one(source, old, new, "right-aligned manuscript within feathered margin")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_v467(kit: Path, dest: Path) -> None:
    build_v466(kit, dest)
    res = dest / "app/src/main/res"
    image_path = res / "drawable-nodpi/iman_v465_scroll.webp"
    source_path = dest / APP / "ImanQuoteCarousel.kt"
    assets = dest / "app/src/main/assets"
    java = dest / APP

    immutable_paths = (
        assets / "book.json", assets / "quiz.json",
        assets / "featured_quotes.json",
        java / "App.kt", java / "Reader.kt", java / "ModernEditorialHome.kt",
        java / "ImanV38More.kt",
        res / "drawable-nodpi/iman_v35_contents.webp",
        res / "drawable-nodpi/iman_v35_collections.webp",
        res / "drawable-nodpi/iman_v35_glossary.webp",
        res / "drawable-nodpi/iman_v38_notes.webp",
        res / "drawable-nodpi/iman_v39_launcher_foreground.webp",
        res / "mipmap-anydpi/iman_v39_launcher.webp",
    )
    before = {str(p): sha(p) for p in immutable_paths}

    with Image.open(image_path) as opened:
        updated = soften_reminder_background(opened.copy())
    a = np.asarray(updated.getchannel("A"))
    if a.max() < 200 or a[0].max() != 0 or a[:, -1].max() != 0:
        raise RuntimeError("Manuscript lost relief or may clip near right edge")
    updated.save(image_path, "WEBP", lossless=True, method=6, exact=True)

    quote = source_path.read_text("utf-8")
    quote = patch_position(quote)
    if "R.drawable.iman_v465_scroll" not in quote:
        raise RuntimeError("Approved illustration missing from quote carousel")
    if "navigate(Route.Reader(q.chapterId, q.blockId))" not in quote:
        raise RuntimeError("Exact-fragment reading navigation changed")
    if ".requiredWidth(" in quote:
        raise RuntimeError("Legacy oversized/cropped illustration was reintroduced")
    source_path.write_text(quote, "utf-8")

    for name, expected in before.items():
        if sha(Path(name)) != expected:
            raise RuntimeError("Unrelated content, library artwork or icon changed: " + name)

    gradle = dest / "app/build.gradle"
    code = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 66", "versionCode 67"),
        ("versionName '0.46.6'", "versionName '0.46.7'"),
        ("applicationIdSuffix '.preview466'", "applicationIdSuffix '.preview467'"),
    ):
        code = replace_one(code, old, new, "isolated reminder alignment patch")
    gradle.write_text(code, "utf-8")
    print("PASS v467: manuscript right-shifted within transparent safe area; unchanged book, icons and navigation")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", required=True, type=Path)
    args = parser.parse_args()
    build_v467(Path(__file__).resolve().parents[1], args.dest)
