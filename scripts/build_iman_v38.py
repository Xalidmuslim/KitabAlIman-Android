"""Native v0.38: icon for Notes, integrated reminder art, aligned reading minutes, flat paper.
Build on the verified v0.37.1 without touching book/quiz, reader or saved state.
"""
from pathlib import Path
import argparse
import hashlib
import shutil
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

from scripts.build_iman_v37 import build_v37
from scripts.build_iman_v20 import APP, NAV, replace_one


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_integrated_reminder(drawable: Path) -> None:
    source = drawable / "iman_v36_reminder.webp"
    with Image.open(source) as f:
        art = f.convert("RGBA")
    # The book and arch now behave like aged ink printed into the paper rather
    # than a framed picture. Preserve the original transparent silhouette.
    rgb = ImageEnhance.Color(art.convert("RGB")).enhance(0.63)
    rgb = ImageEnhance.Contrast(rgb).enhance(0.79)
    rgb = ImageEnhance.Brightness(rgb).enhance(1.12)
    w, h = art.size
    x = np.arange(w, dtype=np.float32)[None, :]
    y = np.arange(h, dtype=np.float32)[:, None]
    left = np.clip(x / max(1., w * .34), 0., 1.)
    right = np.clip((w - 1 - x) / max(1., w * .08), 0., 1.)
    bottom = np.clip((h - 1 - y) / max(1., h * .16), 0., 1.)
    original_alpha = np.asarray(art.getchannel("A"), dtype=np.float32)
    softened = np.uint8(np.clip(original_alpha * left * right * bottom * .65, 0, 255))
    rgb.putalpha(Image.fromarray(softened, "L").filter(ImageFilter.GaussianBlur(.65)))
    rgb.save(drawable / "iman_v38_reminder.webp", "WEBP", quality=88, method=6)


def smooth_lower_paper(drawable: Path) -> None:
    """Remove the wavy image seam behind the native five-tab navigation."""
    path = drawable / "iman_v29_unified_home.webp"
    with Image.open(path) as f:
        paper = f.convert("RGB")
    w, h = paper.size
    start = int(h * .77)
    # Texture comes exclusively from the existing blank parchment above the
    # bottom ornament, so this introduces no second card or external artwork.
    quiet = paper.crop((0, int(h * .55), w, int(h * .73)))
    continuation = quiet.resize((w, h - start), Image.Resampling.BICUBIC)
    continuation = continuation.filter(ImageFilter.GaussianBlur(.55))
    alpha = Image.new("L", (w, h - start))
    ar = np.zeros((h-start,w),dtype=np.uint8)
    for row in range(h-start):
        ar[row,:] = min(255, round(255 * row / max(1, int(h*.09))))
    alpha = Image.fromarray(ar, "L")
    result = paper.copy()
    result.paste(continuation, (0,start), alpha)
    result.save(drawable/"iman_v38_flat_paper.webp", "WEBP", quality=94, method=6)


def build_v38(kit: Path, dest: Path) -> None:
    build_v37(kit, dest)
    java = dest / APP
    assets = dest / "app/src/main/assets"
    drawable = dest / "app/src/main/res/drawable-nodpi"
    app = java / "App.kt"
    reader = java / "Reader.kt"
    app_before = app.read_text("utf-8")
    reader_before = digest(reader)
    book_hashes = {p.name:digest(p) for p in assets.iterdir() if p.is_file()}
    if NAV not in app_before:
        raise RuntimeError("five-tab navigation invariant absent")

    gradle = dest/"app/build.gradle"
    g = gradle.read_text("utf-8")
    for old,new in (
        ("versionCode 38","versionCode 39"),
        ("versionName '0.37.1'","versionName '0.38.0'"),
        ("applicationIdSuffix '.preview37'","applicationIdSuffix '.preview38'"),
    ):
        g = replace_one(g,old,new,"v38 isolated native preview")
    gradle.write_text(g,"utf-8")

    # Generated illustration is committed as a small independent transparent WebP.
    source_icon = kit/"assets/ui/v38/iman_v38_notes.webp"
    if not source_icon.is_file() or source_icon.stat().st_size < 1000:
        raise RuntimeError("v38 generated Notes illustration unavailable")
    shutil.copyfile(source_icon,drawable/"iman_v38_notes.webp")
    make_integrated_reminder(drawable)
    smooth_lower_paper(drawable)

    home = (kit/"scripts/ReferenceHomeV38.kt").read_text("utf-8")
    for name in ("contents","collections","glossary"):
        home = replace_one(home,f"R.drawable.iman_v32_{name}",
                           f"R.drawable.iman_v35_{name}", "keep approved matte book art")
    if "EditorialBookSection(\"Закладки\"" in home or "navigate(Route.Notes)" not in home:
        raise RuntimeError("v38 library must show Notes instead of removed Bookmarks tile")
    (java/"ModernEditorialHome.kt").write_text(home,"utf-8")

    qpath = java/"ImanQuoteCarousel.kt"
    q_before = qpath.read_text("utf-8")
    marker = "@Composable\\ninternal fun ImanFeaturedQuoteCarousel("
    if q_before.count(marker) != 1 or q_before.count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v38 source quote anchors changed")
    quote = (kit/"scripts/ReferenceQuoteV38.kt").read_text("utf-8")
    qpath.write_text(q_before[:q_before.index(marker)] + quote,"utf-8")
    (java/"ReadingStatisticsV36.kt").write_text(
        (kit/"scripts/ReadingStatisticsV38.kt").read_text("utf-8"),"utf-8")

    # Switch the shared paper rather than adding any new panel to bottom nav.
    changed_app = replace_one(app_before,
        "R.drawable.iman_v29_unified_home",
        "R.drawable.iman_v38_flat_paper",
        "remove baked-in bottom navigation wave")
    app.write_text(changed_app,"utf-8")
    preload = java/"MedicineHomeArtwork.kt"
    src = preload.read_text("utf-8")
    src = replace_one(src,"        R.drawable.iman_v36_reminder,",
        "        R.drawable.iman_v36_reminder,\\n"
        "        R.drawable.iman_v38_reminder,\\n"
        "        R.drawable.iman_v38_notes,\\n"
        "        R.drawable.iman_v38_flat_paper,",
        "preload artwork outside draw path")
    preload.write_text(src,"utf-8")

    # The only App.kt change is the paper resource; reader and tabs untouched.
    if changed_app.replace("R.drawable.iman_v38_flat_paper",
                           "R.drawable.iman_v29_unified_home") != app_before:
        raise RuntimeError("native bottom nav / app navigation unexpectedly modified")
    if digest(reader) != reader_before or NAV not in changed_app:
        raise RuntimeError("v38 changed the reader or existing five-tab routing")
    for name,sha in book_hashes.items():
        if digest(assets/name) != sha:
            raise RuntimeError("v38 changed a book, notes/quiz data, or saved anchor: "+name)
    for name in ("iman_v38_notes.webp","iman_v38_reminder.webp",
                 "iman_v38_flat_paper.webp"):
        if (drawable/name).stat().st_size < 1000:
            raise RuntimeError("missing rendered illustration or paper: "+name)
    if qpath.read_text("utf-8").count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v38 lost a sourced reminder")
    print("PASS v38: notes art, integrated book illustration, aligned minutes, flat shared paper; content and navigation intact")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args()
    build_v38(Path(__file__).resolve().parents[1], args.dest)
