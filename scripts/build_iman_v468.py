"""v0.46.8: install the two user-approved images into the native reader.

Use the uploaded scroll-and-quill scene in the reminder and the exact uploaded
Kitab-al-Iman rounded art in the Home header and Android launcher. Maintain
existing shapes, layout, fonts, navigation, content, progress and bookmarks.
"""
import argparse
import base64
import hashlib
import io
from pathlib import Path

import numpy as np
from PIL import Image

from scripts.build_iman_v467 import build_v467
from scripts.build_iman_v20 import APP, replace_one

QUOTE_SOURCE = "assets/ui/v468/approved_manuscript_scene.webp.b64"
ICON_SOURCE = "assets/ui/v468/approved_launcher_icon.webp.b64"
QUOTE_SHA256 = "895372371e55225671af9f5084f94fff4cf357b34b8cdd5d496e267f75acb587"
ICON_SHA256 = "6c71c0185c0acf333826bda243b8e9af3bdb337459c96a87d32b13bdafebab02"
PAPER_RGB = (246, 235, 217)


def _read_source(kit: Path, name: str, digest: str) -> Image.Image:
    source = base64.b64decode((kit / name).read_text("ascii").strip(), validate=True)
    if hashlib.sha256(source).hexdigest() != digest:
        raise RuntimeError("Approved user image missing or changed: " + name)
    with Image.open(io.BytesIO(source)) as opened:
        if opened.format != "WEBP":
            raise RuntimeError("Unexpected approved image format: " + name)
        return opened.copy()


def _smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def render_manuscript(original: Image.Image) -> Image.Image:
    # Cropped from the approved 1338x1176 image: retain only the right-hand scene.
    # Remove its rectangular paper background, without redrawing any detail.
    if original.size != (256, 222):
        raise RuntimeError("Unexpected approved scroll source geometry")
    rgb = np.asarray(original.convert("RGB"), dtype=np.float32)
    h, w = rgb.shape[:2]
    lum = rgb @ np.array([.2126, .7152, .0722], dtype=np.float32)
    alpha = np.clip((246.0 - lum) * 3.7, 0, 251)
    x = np.arange(w, dtype=np.float32)[None, :]
    y = np.arange(h, dtype=np.float32)[:, None]
    # Diffuse atmospheric background; keep opaque manuscript and dark 3D edges.
    alpha *= (
        _smoothstep(x / 29.0)
        * _smoothstep((w - 1 - x) / 24.0)
        * _smoothstep(y / 16.0)
        * _smoothstep((h - 1 - y) / 21.0)
    )
    alpha[0, :] = 0
    alpha[-1, :] = 0
    alpha[:, 0] = 0
    alpha[:, -1] = 0
    result = Image.fromarray(
        np.dstack((rgb.astype(np.uint8), alpha.astype(np.uint8))), "RGBA"
    )
    if result.getchannel("A").getextrema()[1] < 195:
        raise RuntimeError("Scroll and quill lose their visible 3D relief")
    return result


def render_launcher_assets(original: Image.Image):
    # Rounded parchment relief and exact كتاب الإيمان text from user-approved icon.
    if original.size != (240, 240):
        raise RuntimeError("Unexpected approved icon source geometry")
    header = original.convert("RGBA").resize((320, 320), Image.Resampling.LANCZOS)
    adaptive = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    # Entire icon stays inside Android adaptive mask's 66% central safety area.
    adaptive.alpha_composite(
        original.convert("RGBA").resize((318, 318), Image.Resampling.LANCZOS),
        (97, 97)
    )
    legacy = Image.new("RGBA", (512, 512), (*PAPER_RGB, 255))
    legacy.alpha_composite(
        original.convert("RGBA").resize((464, 464), Image.Resampling.LANCZOS),
        (24, 24)
    )
    return header, adaptive, legacy.convert("RGB")


def _save(image: Image.Image, destination: Path):
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, "WEBP", quality=80, method=6, exact=True)


def _sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_v468(kit: Path, dest: Path) -> None:
    build_v467(kit, dest)
    res = dest / "app/src/main/res"
    drawable = res / "drawable-nodpi"
    java = dest / APP
    assets = dest / "app/src/main/assets"
    protected = (
        assets / "book.json", assets / "quiz.json",
        assets / "featured_quotes.json",
        java / "App.kt", java / "Reader.kt", java / "ImanQuoteCarousel.kt",
        java / "ModernEditorialHome.kt", java / "ImanV38More.kt",
        drawable / "iman_v35_contents.webp",
        drawable / "iman_v35_collections.webp",
        drawable / "iman_v35_glossary.webp",
        drawable / "iman_v38_notes.webp",
    )
    before = {str(p): _sha(p) for p in protected}

    manuscript = render_manuscript(_read_source(kit, QUOTE_SOURCE, QUOTE_SHA256))
    icon = _read_source(kit, ICON_SOURCE, ICON_SHA256)
    header, adaptive, legacy = render_launcher_assets(icon)
    _save(manuscript, drawable / "iman_v465_scroll.webp")
    _save(header, drawable / "iman_v464_home_soft.webp")
    _save(adaptive, drawable / "iman_v39_launcher_foreground.webp")
    _save(legacy, res / "mipmap-anydpi/iman_v39_launcher.webp")

    # Keep the approved +6dp right alignment and the exact quote-to-fragment link.
    quote = (java / "ImanQuoteCarousel.kt").read_text("utf-8")
    home = (java / "ModernEditorialHome.kt").read_text("utf-8")
    if ".offset(x = 6.dp, y = (0).dp)" not in quote:
        raise RuntimeError("Reminder right-side offset removed")
    if "navigate(Route.Reader(q.chapterId, q.blockId))" not in quote:
        raise RuntimeError("Chapter-fragment navigation changed")
    if "R.drawable.iman_v465_scroll" not in quote:
        raise RuntimeError("Approved reminder drawable missing")
    if "R.drawable.iman_v464_home_soft" not in home:
        raise RuntimeError("Approved Home header drawable missing")
    for path, expected in before.items():
        if _sha(Path(path)) != expected:
            raise RuntimeError("Unrelated book, navigation or library artwork modified: " + path)

    gradle = dest / "app/build.gradle"
    source = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 67", "versionCode 68"),
        ("versionName '0.46.7'", "versionName '0.46.8'"),
        ("applicationIdSuffix '.preview467'", "applicationIdSuffix '.preview468'"),
    ):
        source = replace_one(source, old, new, "paired approved image rollout")
    gradle.write_text(source, "utf-8")
    print("PASS v468: two approved visuals installed, clean edges, safe adaptive icon, all book and navigation preserved")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args()
    build_v468(Path(__file__).resolve().parents[1], args.dest)
