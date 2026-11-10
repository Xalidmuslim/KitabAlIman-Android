"""v0.46.4: matte, softer Home branding and a seamless top-safe reminder.

Keep all 131 chapters, 79 excerpts, quiz answers, More icons, launcher asset,
settings, reading progress, app identity and native navigation untouched.
Only change the in-app Home header resource, the quote resource and the quote
container's minimum height/vertical offset.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance

from scripts.build_iman_v463 import build_v463
from scripts.build_iman_v461 import digest
from scripts.build_iman_v20 import APP, NAV, replace_one


def tone_header(source: Path, destination: Path) -> None:
    """Reduce the Home illustration's intensity to the library's matte sepia.

    Do not repaint the Arabic lettering: every pixel is derived from v463.
    The Android launcher uses its own untouched foreground/background.
    """
    with Image.open(source) as opened:
        if opened.size != (320, 320) or opened.mode != "RGBA":
            raise RuntimeError("Unexpected approved v463 header resource")
        original = opened.copy()

    softer = ImageEnhance.Color(original).enhance(.84)
    softer = ImageEnhance.Contrast(softer).enhance(.84)
    softer = ImageEnhance.Brightness(softer).enhance(1.10)
    softened_alpha = softer.getchannel("A").point(lambda value: round(value * .87))
    softer.putalpha(softened_alpha)

    destination.parent.mkdir(parents=True, exist_ok=True)
    softer.save(destination, "WEBP", lossless=True, method=6, exact=True)


def feather_reminder(source: Path, destination: Path) -> None:
    """Add a true transparent margin above the arch and feather the paper haze.

    v463's 180x122 illustration reaches the first image row. In a clipped
    Android drawing region its architectural arch visually loses its top.
    Expand vertically, keep original coordinates and soften only translucent
    edge fog. Do not change the scroll text, quill or inkpot geometry.
    """
    with Image.open(source) as opened:
        if opened.size != (180, 122) or opened.mode != "RGBA":
            raise RuntimeError("Unexpected v463 reminder artwork")
        original = opened.copy()

    rgba = np.asarray(original, dtype=np.float32)
    h, w = rgba.shape[:2]
    luminance = (rgba[:, :, 0] * .21 + rgba[:, :, 1] * .72
                 + rgba[:, :, 2] * .07)
    a = rgba[:, :, 3].copy()
    # Diffuse bright pixels are the source of the rectangular parchment haze.
    # Remove just some of their opacity; preserve darker contours and shadows.
    fog = np.clip((luminance - 166.0) / 85.0, 0.0, 1.0)
    a *= 1.0 - .34 * fog
    yy = np.arange(h, dtype=np.float32)[:, None]
    xx = np.arange(w, dtype=np.float32)[None, :]
    top = np.clip((yy + 2.0) / 13.0, 0, 1)
    bottom = np.clip((h + 1.0 - yy) / 17.0, 0, 1)
    left = np.clip((xx + 2.0) / 18.0, 0, 1)
    right = np.clip((w + 1.0 - xx) / 17.0, 0, 1)
    a *= top * bottom * left * right
    a[:, 0] = 0
    a[:, -1] = 0
    a[0, :] = 0
    a[-1, :] = 0
    updated = original.copy()
    updated.putalpha(Image.fromarray(np.uint8(np.clip(a, 0, 255)), "L"))
    # 17px of transparent headroom above the original arch, plus 17px below.
    # The image fits ContentScale.Fit's existing 128x110dp region.
    canvas = Image.new("RGBA", (180, 156), (0, 0, 0, 0))
    canvas.alpha_composite(updated, (0, 17))
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, "WEBP", lossless=True, method=6, exact=True)


def patch_home(path: Path) -> None:
    source = path.read_text("utf-8")
    old = "R.drawable.iman_v463_header"
    if source.count(old) != 1:
        raise RuntimeError("Home header resource changed since v463")
    path.write_text(source.replace(old, "R.drawable.iman_v464_home_soft", 1), "utf-8")


def patch_quote(path: Path) -> None:
    source = path.read_text("utf-8")
    for old, new in (
        ("R.drawable.iman_v463_reminder_depth",
         "R.drawable.iman_v464_reminder_feathered"),
        (".offset(y = (-3).dp)", ".offset(y = (0).dp)"),
        ("heightIn(min = if (compactScreen) 111.dp else 133.dp)",
         "heightIn(min = if (compactScreen) 108.dp else 117.dp)"),
    ):
        if source.count(old) != 1:
            raise RuntimeError("Quote responsive sizing contract changed: " + old)
        source = source.replace(old, new, 1)
    if ".requiredWidth(" in source:
        raise RuntimeError("Previous clipping regression detected")
    path.write_text(source, "utf-8")


def build_v464(kit: Path, dest: Path) -> None:
    build_v463(kit, dest)
    java = dest / APP
    res = dest / "app/src/main/res"
    drawable = res / "drawable-nodpi"
    assets = dest / "app/src/main/assets"
    gradle = dest / "app/build.gradle"
    manifest = dest / "app/src/main/AndroidManifest.xml"

    nav_before = (java / "App.kt").read_bytes()
    more_before = (java / "ImanV38More.kt").read_bytes()
    manifest_before = manifest.read_bytes()
    kotlin_before = {p.name:digest(p) for p in java.glob("*.kt")
                     if p.name not in ("ModernEditorialHome.kt", "ImanQuoteCarousel.kt")}
    protected_content = {p.name:digest(p) for p in assets.iterdir() if p.is_file()}
    protected_res = {str(p.relative_to(res)):digest(p)
                     for p in res.rglob("*") if p.is_file()}
    launcher_checksums = {resource:digest(res / resource)
                          for resource in ("drawable-nodpi/iman_v39_launcher_foreground.webp",
                                           "mipmap-anydpi/iman_v39_launcher.webp")}

    version = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 63", "versionCode 64"),
        ("versionName '0.46.3'", "versionName '0.46.4'"),
        ("applicationIdSuffix '.preview463'", "applicationIdSuffix '.preview464'"),
    ):
        version = replace_one(version, old, new, "v464 isolated visual repair")
    gradle.write_text(version, "utf-8")

    patch_home(java / "ModernEditorialHome.kt")
    patch_quote(java / "ImanQuoteCarousel.kt")
    tone_header(drawable / "iman_v463_header.webp",
                drawable / "iman_v464_home_soft.webp")
    feather_reminder(drawable / "iman_v463_reminder_depth.webp",
                     drawable / "iman_v464_reminder_feathered.webp")

    if (java / "App.kt").read_bytes() != nav_before or NAV not in nav_before.decode("utf-8"):
        raise RuntimeError("Navigation changed")
    if (java / "ImanV38More.kt").read_bytes() != more_before:
        raise RuntimeError("Settings gear or More menu changed")
    if manifest.read_bytes() != manifest_before:
        raise RuntimeError("Android manifest changed")
    for name, checksum in kotlin_before.items():
        if digest(java / name) != checksum:
            raise RuntimeError("Unrelated Kotlin changed: " + name)
    for name, checksum in protected_content.items():
        if digest(assets / name) != checksum:
            raise RuntimeError("Book/quiz/user data changed: " + name)
    for name, checksum in protected_res.items():
        if digest(res / name) != checksum:
            raise RuntimeError("Unrelated existing resource changed: " + name)
    for name, checksum in launcher_checksums.items():
        if digest(res / name) != checksum:
            raise RuntimeError("Android icon mask was modified: " + name)

    home = (java / "ModernEditorialHome.kt").read_text("utf-8")
    quote = (java / "ImanQuoteCarousel.kt").read_text("utf-8")
    if home.count("R.drawable.iman_v464_home_soft") != 1:
        raise RuntimeError("Soft header missing")
    if quote.count("R.drawable.iman_v464_reminder_feathered") != 1:
        raise RuntimeError("Feathered reminder missing")
    book = json.loads((assets / "book.json").read_text("utf-8"))
    quiz = json.loads((assets / "quiz.json").read_text("utf-8"))
    excerpts = json.loads((assets / "featured_quotes.json").read_text("utf-8"))
    if len(book["chapters"]) != 131 or len(quiz["chapters"]) != 131 or len(excerpts) != 79:
        raise RuntimeError("Protected content inventory changed")

    print("PASS v464: soft unframed Home art, feathered complete reminder, original launcher/More/data")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True, type=Path)
    args = ap.parse_args()
    build_v464(Path(__file__).resolve().parents[1], args.dest)
