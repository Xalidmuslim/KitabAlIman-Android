"""v0.46.6: unify Home illustration tones with the existing library assets.

All artwork is derived from original, already approved v0.46.5 resources.
Do not redraw Arabic lettering or replace book/quiz content, navigation, or fonts.
Only the generated image resources and preview version change.
"""
import argparse
import hashlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

from scripts.build_iman_v465 import build_v465
from scripts.build_iman_v20 import APP, replace_one

LIBRARY = (
    "iman_v35_contents.webp",
    "iman_v35_collections.webp",
    "iman_v35_glossary.webp",
    "iman_v38_notes.webp",
)
PAPER = (245, 235, 216)


def reference_brown(drawable: Path) -> np.ndarray:
    samples = []
    for name in LIBRARY:
        path = drawable / name
        with Image.open(path) as original:
            pixels = np.asarray(original.convert("RGBA"), dtype=np.uint8)
        rgb = pixels[:, :, :3].astype(np.float32)
        alpha = pixels[:, :, 3]
        lightness = rgb @ np.array([.2126, .7152, .0722], dtype=np.float32)
        selection = (alpha > 100) & (lightness > 55) & (lightness < 198)
        if selection.sum() < 70:
            raise RuntimeError("Library color reference missing: " + name)
        samples.append(np.median(rgb[selection], axis=0))
    reference = np.median(np.stack(samples), axis=0)
    if not (reference[0] > reference[1] > reference[2]):
        raise RuntimeError("Existing library is not warm-sepia as expected")
    return reference


def adjust_color(source: Image.Image, reference: np.ndarray, amount: float) -> Image.Image:
    """Match the *foreground* midtones, not the parchment or highlights."""
    im = source.convert("RGBA")
    arr = np.asarray(im, dtype=np.float32)
    rgb = arr[:, :, :3]
    a = arr[:, :, 3]
    lum = rgb @ np.array([.2126, .7152, .0722], dtype=np.float32)
    subject = (a > 100) & (lum > 55) & (lum < 211)
    if subject.sum() < 100:
        raise RuntimeError("Artwork has no opaque foreground to harmonize")
    median = np.median(rgb[subject], axis=0)
    delta = np.clip(reference - median, -42, 42) * amount
    # Preserve highlight detail; shadows move most strongly towards library brown.
    strength = np.clip((238.0 - lum) / 128.0, .18, 1.0)[:, :, None]
    adjusted = np.clip(rgb + delta[None, None, :] * strength, 0, 255)
    # Darken shading softly for a matte relief, without artificial edge outlines.
    adjusted = np.clip((adjusted - 155) * 1.075 + 155, 0, 255)
    out = np.dstack([adjusted.astype(np.uint8), a.astype(np.uint8)])
    result = Image.fromarray(out, "RGBA")
    return ImageEnhance.Color(result).enhance(.96)


def feather_edges(picture: Image.Image, side: int = 30, vertical: int = 17) -> Image.Image:
    rgba = np.asarray(picture.convert("RGBA"), dtype=np.uint8).copy()
    h, w = rgba.shape[:2]
    x = np.minimum(np.arange(w), np.arange(w)[::-1]).astype(np.float32)
    y = np.minimum(np.arange(h), np.arange(h)[::-1]).astype(np.float32)
    def ease(a):
        a = np.clip(a, 0, 1)
        return a * a * (3 - 2 * a)
    falloff = ease(x / side)[None, :] * ease(y / vertical)[:, None]
    rgba[:, :, 3] = np.uint8(np.clip(rgba[:, :, 3].astype(np.float32) * falloff, 0, 255))
    return Image.fromarray(rgba, "RGBA")


def contact_shadow(picture: Image.Image, opacity: float, spread: int, dy: int) -> Image.Image:
    """A subtle alpha-derived shadow, not a card, halo, or opaque rectangle."""
    rgba = picture.convert("RGBA")
    mask = rgba.getchannel("A").filter(ImageFilter.GaussianBlur(spread))
    mask = mask.point(lambda p: int(p * opacity))
    shifted = Image.new("L", rgba.size, 0)
    shifted.paste(mask, (0, dy))
    shadow = Image.new("RGBA", rgba.size, (72, 52, 35, 0))
    shadow.putalpha(shifted)
    return Image.alpha_composite(shadow, rgba)


def save_webp(picture: Image.Image, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    picture.save(path, "WEBP", lossless=True, method=6, exact=True)


def prepare_style(dest: Path) -> None:
    res = dest / "app/src/main/res"
    drawable = res / "drawable-nodpi"
    palette = reference_brown(drawable)

    # The v464 header was faded twice (contrast 0.84 and alpha 0.87).
    # Restore contours from the approved v463 cutout, without changing Arabic text.
    with Image.open(drawable / "iman_v463_header.webp") as source:
        home = adjust_color(source.copy(), palette, .56)
    home = contact_shadow(home, .14, 4, 3)
    save_webp(home, drawable / "iman_v464_home_soft.webp")

    # Keep the exact user-approved manuscript composition: fix the hard rectangular
    # raster boundary and excessive yellow tint. Never regenerate pseudo-Arabic.
    with Image.open(drawable / "iman_v465_scroll.webp") as source:
        reminder = adjust_color(source.copy(), palette, .83)
    reminder = feather_edges(reminder, side=30, vertical=17)
    reminder = contact_shadow(reminder, .11, 5, 2)
    save_webp(reminder, drawable / "iman_v465_scroll.webp")

    # Use the same rich matte foreground for both Home and the real launcher icon.
    foreground_path = drawable / "iman_v39_launcher_foreground.webp"
    with Image.open(foreground_path) as image:
        foreground = adjust_color(image.copy(), palette, .70)
    foreground = contact_shadow(foreground, .19, 5, 4)
    save_webp(foreground, foreground_path)

    # Recompose the non-adaptive legacy icon from identical foreground artwork
    # on native parchment; don't introduce the old high-contrast square sticker.
    canvas_size = (512, 512)
    paper = Image.new("RGB", canvas_size, PAPER)
    paper_path = drawable / "iman_v38_flat_paper.webp"
    if paper_path.is_file():
        with Image.open(paper_path) as texture:
            texture = texture.convert("RGB").resize(canvas_size, Image.Resampling.BILINEAR)
        paper = Image.blend(paper, texture, .22)
    bounds = foreground.getchannel("A").getbbox()
    if bounds is None:
        raise RuntimeError("Launcher foreground unexpectedly empty")
    subject = foreground.crop(bounds)
    ratio = min(386 / subject.width, 386 / subject.height)
    subject = subject.resize(
        (max(1, round(subject.width * ratio)), max(1, round(subject.height * ratio))),
        Image.Resampling.LANCZOS,
    )
    flattened = paper.convert("RGBA")
    flattened.alpha_composite(
        subject, ((512 - subject.width) // 2, (512 - subject.height) // 2)
    )
    flattened.convert("RGB").save(
        res / "mipmap-anydpi/iman_v39_launcher.webp",
        "WEBP", quality=95, method=6,
    )

    # No book, quiz, user state, text, typeface, route or library icon is edited.
    for name in LIBRARY:
        if not (drawable / name).is_file():
            raise RuntimeError("Approved library artwork vanished: " + name)


def build_v466(kit: Path, dest: Path) -> None:
    build_v465(kit, dest)
    java = dest / APP
    assets = dest / "app/src/main/assets"
    untouched = {
        name: hashlib.sha256((assets / name).read_bytes()).hexdigest()
        for name in ("book.json", "quiz.json", "featured_quotes.json")
    }
    code_before = {
        name: hashlib.sha256((java / name).read_bytes()).hexdigest()
        for name in ("App.kt", "ImanQuoteCarousel.kt", "ModernEditorialHome.kt",
                     "Reader.kt", "ImanV38More.kt")
    }
    prepare_style(dest)
    for name, expected in untouched.items():
        assert hashlib.sha256((assets / name).read_bytes()).hexdigest() == expected
    for name, expected in code_before.items():
        assert hashlib.sha256((java / name).read_bytes()).hexdigest() == expected

    gradle = dest / "app/build.gradle"
    code = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 65", "versionCode 66"),
        ("versionName '0.46.5'", "versionName '0.46.6'"),
        ("applicationIdSuffix '.preview465'", "applicationIdSuffix '.preview466'"),
    ):
        code = replace_one(code, old, new, "version patch after palette repair")
    gradle.write_text(code, "utf-8")
    print("PASS v466: library-matched parchment relief on reminder/Home/launcher; unchanged book/nav")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", required=True, type=Path)
    args = parser.parse_args()
    build_v466(Path(__file__).resolve().parents[1], args.dest)
