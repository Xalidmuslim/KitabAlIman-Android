"""v0.46.11: retone the EXISTING borderless icon from four library icons.

Do not generate or redraw anything. Pixel transforms are calculated from
existing Android library drawables. Preserve exact Arabic lettering, shape,
50dp Home placement, approved quote art, navigation, and book content.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from scripts.build_iman_v470 import build_v470, read_approved, render_icons, _save
from scripts.build_iman_v20 import APP, replace_one

LIBRARY = (
    "iman_v35_contents.webp",
    "iman_v35_collections.webp",
    "iman_v35_glossary.webp",
    "iman_v38_notes.webp",
)
QUANTILES = (15, 40, 65, 85)


def _masks(image: Image.Image):
    pixels = np.asarray(image.convert("RGBA"), dtype=np.float32)
    rgb = pixels[:, :, :3]
    alpha = pixels[:, :, 3]
    lightness = rgb @ np.array([.213, .715, .072], dtype=np.float32)
    warm = (rgb[:, :, 0] - rgb[:, :, 1] > 9) & (rgb[:, :, 1] - rgb[:, :, 2] > 9)
    foreground = (alpha > 155) & (lightness > 47) & (lightness < 248) & warm
    h, _ = alpha.shape
    row = np.arange(h, dtype=np.float32)[:, None]
    shadow = (alpha > 10) & (alpha < 158) & (row > h * .67)
    return pixels, foreground, shadow


def library_palette(images: list[Image.Image]):
    quantiles, shadows, shadow_alphas = [], [], []
    for image in images:
        rgba, subject, shadow = _masks(image)
        if subject.sum() < 100:
            raise RuntimeError("One library asset has no valid foreground")
        quantiles.append(np.percentile(rgba[:, :, :3][subject], QUANTILES, axis=0))
        if shadow.sum() >= 100:
            shadows.append(np.median(rgba[:, :, :3][shadow], axis=0))
            shadow_alphas.append(np.median(rgba[:, :, 3][shadow]))
    if len(shadows) < 2:
        raise RuntimeError("Could not measure the real library drop shadows")
    # Equal weighting avoids the large book taking priority over other cards.
    target = np.median(np.stack(quantiles), axis=0)
    shadow_color = np.median(np.stack(shadows), axis=0)
    return target, shadow_color, float(np.median(shadow_alphas))


def harmonize_icon(source: Image.Image, references: list[Image.Image]):
    """Quantile-map sepia highlights and blend existing bottom-shadow pixels."""
    rgba, subject, shadow_pixels = _masks(source)
    if source.size != (256, 256) or source.mode != "RGBA" or subject.sum() < 100:
        raise RuntimeError("Existing v470 alpha-cutout is missing or altered")
    target, shadow_tone, shadow_alpha = library_palette(references)
    before = np.percentile(rgba[:, :, :3][subject], QUANTILES, axis=0)
    rgb = rgba[:, :, :3].copy()

    for channel in range(3):
        knots_src = [0.0, *before[:, channel], 255.0]
        knots_dst = [0.0, *target[:, channel], 255.0]
        for i in range(1, len(knots_src)):
            knots_src[i] = max(knots_src[i], knots_src[i - 1] + .01)
            knots_dst[i] = max(knots_dst[i], knots_dst[i - 1] + .01)
        corrected = np.interp(rgb[:, :, channel], knots_src, knots_dst)
        rgb[:, :, channel] = rgb[:, :, channel] * .1 + corrected * .9

    # Retone the *existing* shadow. No added plate, border, halo or drop-shadow.
    alpha = rgba[:, :, 3].copy()
    height, _ = alpha.shape
    rows = np.arange(height, dtype=np.float32)[:, None]
    bottom = np.clip((rows - height * .66) / (height * .25), 0, 1)
    bottom = bottom * bottom * (3 - 2 * bottom)
    fine = 1 - np.clip((alpha - 50) / 170.0, 0, 1)
    weight = .9 * bottom * fine
    rgb = rgb * (1 - weight[:, :, None]) + shadow_tone[None, None, :] * weight[:, :, None]
    current_shadow_alpha = float(np.median(alpha[shadow_pixels])) if shadow_pixels.sum() > 100 else shadow_alpha
    factor = float(np.clip(shadow_alpha / max(1, current_shadow_alpha), .8, 1.2))
    alpha = np.minimum(255, alpha * (1 + (factor - 1) * weight))

    result = Image.fromarray(np.uint8(np.rint(np.clip(np.dstack((rgb, alpha)), 0, 255))), "RGBA")
    new_pixels, new_subject, _ = _masks(result)
    after = np.percentile(new_pixels[:, :, :3][new_subject], QUANTILES, axis=0)
    metric = lambda x: float(np.mean(np.abs(x - target)))
    before_error, after_error = metric(before), metric(after)
    if after_error >= before_error * .82:
        raise RuntimeError(f"Library-color improvement below contract: {before_error} -> {after_error}")
    if result.getchannel("A").getbbox() != source.getchannel("A").getbbox():
        raise RuntimeError("The actual icon silhouette changed")
    return result, {
        "source_midtones": before.round(1).tolist(),
        "library_midtones": target.round(1).tolist(),
        "final_midtones": after.round(1).tolist(),
        "mean_rgb_error_before": round(before_error, 2),
        "mean_rgb_error_after": round(after_error, 2),
        "measured_library_shadow_rgb": shadow_tone.round(1).tolist(),
        "measured_library_shadow_alpha": round(shadow_alpha, 1),
    }


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_v471(kit: Path, dest: Path) -> None:
    build_v470(kit, dest)
    res = dest / "app/src/main/res"
    drawable = res / "drawable-nodpi"
    src = dest / APP
    assets = dest / "app/src/main/assets"
    protected = [
        assets / "book.json", assets / "quiz.json", assets / "featured_quotes.json",
        src / "App.kt", src / "Reader.kt", src / "ImanQuoteCarousel.kt",
        src / "ModernEditorialHome.kt", src / "ImanV38More.kt",
        drawable / "iman_v465_scroll.webp",
        *[drawable / name for name in LIBRARY],
        res / "mipmap-anydpi-v26/iman_v39_launcher.xml",
        drawable / "iman_v470_launcher_background.webp",
    ]
    before = {str(path): _hash(path) for path in protected}
    references = []
    for name in LIBRARY:
        with Image.open(drawable / name) as image:
            references.append(image.convert("RGBA").copy())
    matched, audit = harmonize_icon(read_approved(kit), references)

    with Image.open(drawable / "iman_v470_launcher_background.webp") as opened:
        paper = opened.convert("RGB").copy()
    header, adaptive, legacy = render_icons(matched, paper)
    _save(header, drawable / "iman_v464_home_soft.webp")
    _save(adaptive, drawable / "iman_v39_launcher_foreground.webp")
    _save(legacy, res / "mipmap-anydpi/iman_v39_launcher.webp")

    for name, digest in before.items():
        if _hash(Path(name)) != digest:
            raise RuntimeError("Book, route, layout, quote or library asset modified: " + name)
    home = (src / "ModernEditorialHome.kt").read_text("utf-8")
    quote = (src / "ImanQuoteCarousel.kt").read_text("utf-8")
    if "contentDescription = null, modifier = Modifier.size(50.dp)," not in home:
        raise RuntimeError("Approved 50dp Home header layout changed")
    if "navigate(Route.Reader(q.chapterId, q.blockId))" not in quote:
        raise RuntimeError("Exact chapter navigation missing")
    gradle = dest / "app/build.gradle"
    source = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 70", "versionCode 71"),
        ("versionName '0.46.10'", "versionName '0.46.11'"),
        ("applicationIdSuffix '.preview470'", "applicationIdSuffix '.preview471'"),
    ):
        source = replace_one(source, old, new, "isolated existing-icon material tint")
    gradle.write_text(source, "utf-8")

    report = dest / "app/build/qa/iman_v471_palette.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(audit, ensure_ascii=False, indent=2), "utf-8")
    print("PASS v471: same icon geometry; matched four library assets, colors and soft contact shadow")
    print(json.dumps(audit, ensure_ascii=False))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dest", type=Path, required=True)
    args = p.parse_args()
    build_v471(Path(__file__).resolve().parents[1], args.dest)
