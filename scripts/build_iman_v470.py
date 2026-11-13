"""v0.46.10: precise 50dp borderless Home icon and native-paper Android launcher.

Base is the approved v0.46.9. The foreground is an image-backed cutout from
the user-approved scroll, quill and inkpot illustration, not redrawn text.
Only the Home icon modifier and its three launcher/header resources change.
"""
import argparse
import base64
import hashlib
import io
from pathlib import Path

import numpy as np
from PIL import Image

from scripts.build_iman_v469 import build_v469
from scripts.build_iman_v20 import APP, replace_one

SOURCE = "assets/ui/v470/approved_borderless_scroll.webp.b64"
DIGEST = "6599477404d4a9a6547fd54af5d3163db4b46876af1fd2e0e1972f07eb6d447f"


def read_approved(kit: Path) -> Image.Image:
    raw = base64.b64decode((kit / SOURCE).read_text("ascii").strip(), validate=True)
    if hashlib.sha256(raw).hexdigest() != DIGEST:
        raise RuntimeError("User-approved icon image changed or missing")
    with Image.open(io.BytesIO(raw)) as opened:
        if opened.format != "WEBP" or opened.size != (256, 256):
            raise RuntimeError("Expected approved 256x256 WebP cutout")
        result = opened.convert("RGBA")
    alpha = np.asarray(result.getchannel("A"))
    if not (alpha[0].max() == alpha[-1].max() == alpha[:, 0].max()
            == alpha[:, -1].max() == 0):
        raise RuntimeError("Approved cutout has nontransparent edges")
    return result


def native_paper_texture(path: Path) -> tuple[Image.Image, tuple[int,int,int]]:
    """Use the actual app paper bitmap as the phone icon's backdrop."""
    with Image.open(path) as opened:
        paper = opened.convert("RGB")
    a = np.asarray(paper)
    color = tuple(int(round(v)) for v in np.median(a.reshape(-1, 3), axis=0))
    w, h = paper.size
    side = min(w, h)
    left, top = (w - side) // 2, (h - side) // 2
    square = paper.crop((left, top, left + side, top + side))
    square = square.resize((512, 512), Image.Resampling.LANCZOS)
    # Reduce harsh paper grain on very small icons but preserve actual page tint.
    uniform = Image.new("RGB", (512, 512), color)
    return Image.blend(uniform, square, .65), color


def render_icons(art: Image.Image, paper: Image.Image):
    """One foreground drawing for both surfaces; no rounded frame or plate."""
    if art.size != (256, 256) or art.mode != "RGBA":
        raise RuntimeError("Unexpected icon cutout")
    if paper.size != (512, 512) or paper.mode != "RGB":
        raise RuntimeError("Unexpected paper")
    home = art.resize((320, 320), Image.Resampling.LANCZOS)
    adaptive = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    adaptive.alpha_composite(
        art.resize((330, 330), Image.Resampling.LANCZOS), (91, 91)
    )
    legacy = paper.convert("RGBA")
    legacy.alpha_composite(
        art.resize((460, 460), Image.Resampling.LANCZOS), (26, 26)
    )
    bbox = adaptive.getchannel("A").getbbox()
    if bbox is None or any(v < 78 or v > 435 for v in bbox):
        raise RuntimeError("Launcher adaptive-icon foreground exceeds safe bounds")
    return home, adaptive, legacy.convert("RGB")


def compose_size_patch(code: str) -> str:
    # Change only Home image size, without touching search/toggle or font sizes.
    old = "contentDescription = null, modifier = Modifier.size(46.dp),"
    new = "contentDescription = null, modifier = Modifier.size(50.dp),"
    return replace_one(code, old, new, "header icon from 46dp to 50dp")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _save(image: Image.Image, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest, "WEBP", quality=89, method=6, exact=True)


def build_v470(kit: Path, dest: Path) -> None:
    build_v469(kit, dest)
    res = dest / "app/src/main/res"
    drawable = res / "drawable-nodpi"
    src = dest / APP
    assets = dest / "app/src/main/assets"

    untouched = [
        assets / "book.json", assets / "quiz.json",
        assets / "featured_quotes.json", src / "App.kt",
        src / "Reader.kt", src / "ImanQuoteCarousel.kt",
        src / "ImanV38More.kt", drawable / "iman_v465_scroll.webp",
        drawable / "iman_v35_contents.webp",
        drawable / "iman_v35_collections.webp",
        drawable / "iman_v35_glossary.webp",
        drawable / "iman_v38_notes.webp",
        res / "app_icon_ignore_missing",
    ]
    untouched = [p for p in untouched if p.is_file()]
    before = {str(path): _sha(path) for path in untouched}

    paper_path = drawable / "iman_v38_flat_paper.webp"
    if not paper_path.is_file():
        raise RuntimeError("Native Home paper missing")
    paper, color = native_paper_texture(paper_path)
    header, adaptive, legacy = render_icons(read_approved(kit), paper)
    _save(header, drawable / "iman_v464_home_soft.webp")
    _save(adaptive, drawable / "iman_v39_launcher_foreground.webp")
    _save(legacy, res / "mipmap-anydpi/iman_v39_launcher.webp")
    _save(paper, drawable / "iman_v470_launcher_background.webp")

    xml_path = res / "mipmap-anydpi-v26/iman_v39_launcher.xml"
    xml = xml_path.read_text("utf-8")
    xml = replace_one(xml, "@color/iman_v39_icon_background",
                      "@drawable/iman_v470_launcher_background",
                      "adaptive icon uses the page's paper texture")
    xml_path.write_text(xml, "utf-8")

    home = src / "ModernEditorialHome.kt"
    prev = home.read_text("utf-8")
    updated = compose_size_patch(prev)
    if "R.drawable.iman_v464_home_soft" not in updated:
        raise RuntimeError("Home icon image disconnected")
    if "Spacer(Modifier.width(8.dp))" not in updated:
        raise RuntimeError("Header content spacing changed unexpectedly")
    home.write_text(updated, "utf-8")

    for name, old in before.items():
        if _sha(Path(name)) != old:
            raise RuntimeError("Unrelated text, book, navigation or library icon changed: " + name)
    quote = (src / "ImanQuoteCarousel.kt").read_text("utf-8")
    if "navigate(Route.Reader(q.chapterId, q.blockId))" not in quote:
        raise RuntimeError("Reminder chapter navigation changed")
    if "R.drawable.iman_v465_scroll" not in quote:
        raise RuntimeError("Approved quote illustration changed")

    gradle = dest / "app/build.gradle"
    code = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 69", "versionCode 70"),
        ("versionName '0.46.9'", "versionName '0.46.10'"),
        ("applicationIdSuffix '.preview469'", "applicationIdSuffix '.preview470'"),
    ):
        code = replace_one(code, old, new, "version after isolated icon repair")
    gradle.write_text(code, "utf-8")
    print(f"PASS 0.46.10: borderless 50dp Home and launcher, matched native paper {color}, book/routes preserved")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dest", required=True, type=Path)
    args = p.parse_args()
    build_v470(Path(__file__).resolve().parents[1], args.dest)
