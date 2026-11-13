"""v0.46.9 — latest approved icon, with paper matching the actual Home page.

Keep all native Compose screens, the 79 quotes, 131 chapters, original fonts,
reading state, and the v468 reminder manuscript. Change only the Home brand
picture, legacy/adaptive launcher icon and their shared parchment background.
"""
import argparse
import base64
import hashlib
import io
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from scripts.build_iman_v468 import build_v468
from scripts.build_iman_v20 import APP, replace_one

ICON_V469 = "assets/ui/v469/latest_iman_icon.webp.b64"
SHA256_ICON = "28a87ea17e13dfda27a4470e860f4478f900da5b1e5d86add19f2abfdcc45448"


def sample_icon(kit: Path) -> Image.Image:
    raw = base64.b64decode((kit / ICON_V469).read_text("ascii").strip(), validate=True)
    if hashlib.sha256(raw).hexdigest() != SHA256_ICON:
        raise RuntimeError("Latest user-approved icon bytes altered")
    with Image.open(io.BytesIO(raw)) as source:
        if source.format != "WEBP" or source.size != (192,192):
            raise RuntimeError("Approved icon format or dimensions changed")
        return source.convert("RGB").copy()


def parchment_color(res: Path) -> tuple[int, int, int]:
    """Sample Home paper texture; never use the old #F7EAD7 launcher color."""
    home = res / "drawable-nodpi/iman_v29_unified_home.webp"
    paper = res / "drawable-nodpi/iman_v38_flat_paper.webp"
    path = home if home.is_file() else paper
    if not path.is_file():
        raise RuntimeError("Approved parchment resource is missing")
    with Image.open(path) as image:
        rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    h,w=rgb.shape[:2]
    # Avoid corner texture shadows and highly illuminated strips.
    center=rgb[h//3:2*h//3,w//3:2*w//3]
    color=np.median(center.reshape(-1,3),axis=0)
    return tuple(int(round(x)) for x in color)


def _smoothstep(values):
    t=np.clip(values,0.0,1.0)
    return t*t*(3.0-2.0*t)


def render_matching_icon(original: Image.Image, paper: tuple[int, int, int]):
    if original.size == (192,192):
        original=original.resize((256,256),Image.Resampling.LANCZOS)
    elif original.size != (256,256):
        raise RuntimeError("Unexpected approved icon size")
    rgba=np.asarray(original.convert("RGB"),dtype=np.float32).copy()
    luminance=rgba @ np.array([.2126,.7152,.0722],dtype=np.float32)
    # Preserve engraved Arabic text, feather, folds and inkpot.
    # Only lift high-luminance paper to the sampled Home parchment tone.
    bright=_smoothstep((luminance-142.0)/100.0)[...,None] * .72
    page=np.asarray(paper,dtype=np.float32)[None,None,:]
    rgba=np.clip(rgba*(1.0-bright)+page*bright,0,255).astype(np.uint8)
    subject=Image.fromarray(rgba,"RGB").convert("RGBA")

    # Deliberately soft transparent perimeter: Home must not show a sharp square.
    alpha=Image.new("L",(256,256),0)
    ImageDraw.Draw(alpha).rounded_rectangle((17,16,239,240),radius=52,fill=255)
    alpha=alpha.filter(ImageFilter.GaussianBlur(2.3))
    subject.putalpha(alpha)
    header=subject.resize((320,320),Image.Resampling.LANCZOS)

    # Android adaptive icon foreground remains inside the center 66% safe circle.
    adaptive=Image.new("RGBA",(512,512),(0,0,0,0))
    adaptive.alpha_composite(subject.resize((318,318),Image.Resampling.LANCZOS),(97,97))

    # Same parchment as main Home page behind original subject on older launchers.
    legacy=Image.new("RGBA",(512,512),(*paper,255))
    legacy.alpha_composite(subject.resize((464,464),Image.Resampling.LANCZOS),(24,24))
    return header,adaptive,legacy.convert("RGB")


def _save(image: Image.Image, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path,"WEBP",quality=88,method=6,exact=True)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_v469(kit: Path, dest: Path) -> None:
    build_v468(kit, dest)
    res=dest/"app/src/main/res"
    drawable=res/"drawable-nodpi"
    java=dest/APP
    assets=dest/"app/src/main/assets"
    untouched=[
        assets/"book.json", assets/"quiz.json", assets/"featured_quotes.json",
        java/"App.kt",java/"Reader.kt",java/"ImanQuoteCarousel.kt",
        java/"ModernEditorialHome.kt",java/"ImanV38More.kt",
        drawable/"iman_v465_scroll.webp",
        drawable/"iman_v35_contents.webp",drawable/"iman_v35_collections.webp",
        drawable/"iman_v35_glossary.webp",drawable/"iman_v38_notes.webp",
    ]
    before={str(path):_digest(path) for path in untouched}
    paper=parchment_color(res)
    header,adaptive,legacy=render_matching_icon(sample_icon(kit),paper)
    _save(header,drawable/"iman_v464_home_soft.webp")
    _save(adaptive,drawable/"iman_v39_launcher_foreground.webp")
    _save(legacy,res/"mipmap-anydpi/iman_v39_launcher.webp")

    colors=res/"values/iman_v39_icon_colors.xml"
    if not colors.is_file():
        raise RuntimeError("Launcher adaptive icon background resource missing")
    new_color=f'#{paper[0]:02X}{paper[1]:02X}{paper[2]:02X}'
    color_xml=f'<resources><color name="iman_v39_icon_background">{new_color}</color></resources>'
    colors.write_text(color_xml,encoding="utf-8")

    home=(java/"ModernEditorialHome.kt").read_text("utf-8")
    quote=(java/"ImanQuoteCarousel.kt").read_text("utf-8")
    if "R.drawable.iman_v464_home_soft" not in home:
        raise RuntimeError("Home header picture disconnected")
    if "R.drawable.iman_v465_scroll" not in quote:
        raise RuntimeError("Original user-approved reminder art disconnected")
    if "navigate(Route.Reader(q.chapterId, q.blockId))" not in quote:
        raise RuntimeError("Book chapter fragment navigation disconnected")
    for name,old in before.items():
        if _digest(Path(name))!=old:
            raise RuntimeError("Unrelated asset or Kotlin source changed: "+name)

    gradle=dest/"app/build.gradle"
    source=gradle.read_text("utf-8")
    for old,new in (
        ("versionCode 68","versionCode 69"),
        ("versionName '0.46.8'","versionName '0.46.9'"),
        ("applicationIdSuffix '.preview468'","applicationIdSuffix '.preview469'"),
    ):
        source=replace_one(source,old,new,"native icon/page match version")
    gradle.write_text(source,encoding="utf-8")
    print(f"PASS v469: user-approved newest icon in Home and Android launcher; sampled parchment {new_color}; book unchanged")


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dest",type=Path,required=True)
    args=p.parse_args()
    build_v469(Path(__file__).resolve().parents[1],args.dest)
