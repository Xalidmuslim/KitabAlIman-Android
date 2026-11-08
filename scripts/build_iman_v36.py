"""v0.36: reference-aligned native Home with real statistics and scripted Caveat text.

Derived from v0.35; never alters saved user state, book payloads or five-tab
navigation. Separately versioned preview package avoids clobbering older APKs.
"""
from pathlib import Path
from io import BytesIO
import argparse
import hashlib
import urllib.request
from PIL import Image, ImageEnhance, ImageFilter
from fontTools.ttLib import TTFont

from scripts.build_iman_v35 import build_v35
from scripts.build_iman_v20 import APP, NAV, replace_one

QUOTE_MARKER = "@Composable\ninternal fun ImanFeaturedQuoteCarousel("
CURE_REPO = "https://raw.githubusercontent.com/Xalidmuslim/IbnQayyim-Disease-And-Cure/main/app/src/main/assets/"

def _download(path):
    req = urllib.request.Request(CURE_REPO + path, headers={"User-Agent": "iman-native-visual-build"})
    with urllib.request.urlopen(req, timeout=40) as response:
        return response.read()

def _install_caveat(dest):
    """Use the exact OFL handwriting typeface from Disease and Cure."""
    data = _download("font-writing.woff2")
    font = TTFont(BytesIO(data))
    if font.flavor != "woff2":
        raise RuntimeError("Font source is not WOFF2")
    font.flavor = None
    folder = dest/"app/src/main/res/font"
    folder.mkdir(parents=True, exist_ok=True)
    font.save(folder/"iman_caveat.ttf")
    license = _download("font-license.txt")
    if b"OPEN FONT LICENSE" not in license:
        raise RuntimeError("Font copyright notice absent")
    (dest/"app/src/main/assets/iman_caveat_OFL.txt").write_bytes(license)
    java = dest/APP
    (java/"ImanCaveatFont.kt").write_text("""package com.xalid.meditsinaproroka.nativeapp
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
internal val ImanCaveatFont = FontFamily(Font(R.font.iman_caveat))
""", "utf-8")

def _soft_integrated_art(drawable):
    """Premultiplied softly feathered transparent art: wallpaper remains underneath."""
    source = drawable/"iman_v35_reminder.webp"
    with Image.open(source) as im:
        obj = im.convert("RGBA")
    rgb = ImageEnhance.Color(obj.convert("RGB")).enhance(.88)
    rgb = ImageEnhance.Contrast(rgb).enhance(.955)
    rgb = ImageEnhance.Brightness(rgb).enhance(1.045)
    alpha = obj.getchannel("A").filter(ImageFilter.GaussianBlur(1.6))
    # Diffuse leftover halo, retain opaque highlights of the actual book/quill.
    alpha = alpha.point(lambda p: round(p * (.77 if p < 180 else .92)))
    rgb.putalpha(alpha)
    out = drawable/"iman_v36_reminder.webp"
    rgb.save(out,"WEBP",quality=96,method=6)
    if out.stat().st_size < 2500: raise RuntimeError("v36 art unexpectedly empty")

def build_v36(kit: Path, dest: Path):
    build_v35(kit,dest)
    gradle=dest/"app/build.gradle"
    g=gradle.read_text("utf-8")
    for before,after in (
        ("versionCode 35","versionCode 36"),
        ("versionName '0.35.0'","versionName '0.36.0'"),
        ("applicationIdSuffix '.preview35'","applicationIdSuffix '.preview36'"),
    ):
        g=replace_one(g,before,after,"v36 app version")
    gradle.write_text(g,"utf-8")

    java=dest/APP
    app=java/"App.kt"
    reader=java/"Reader.kt"
    app_before=app.read_bytes()
    reader_before=reader.read_bytes()
    preserved={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
               for p in java.glob("*.kt")
               if p.name not in ("ModernEditorialHome.kt","ImanQuoteCarousel.kt",
                                 "MedicineHomeArtwork.kt")}
    assets=dest/"app/src/main/assets"
    book_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in assets.iterdir() if p.is_file()}
    wallpaper=dest/"app/src/main/res/drawable-nodpi/iman_v29_unified_home.webp"
    wallpaper_hash=hashlib.sha256(wallpaper.read_bytes()).hexdigest()

    home=(kit/"scripts/ReferenceHomeV36.kt").read_text("utf-8")
    for name in ("contents","collections","glossary","bookmarks"):
        home=replace_one(home,f"R.drawable.iman_v32_{name}",
                         f"R.drawable.iman_v35_{name}","v36 reuse matte library art")
    if (home.count(".statusBarsPadding()")!=1 or
        "ImanReadingStatistics(book, store)" not in home or
        "Темы для изучения" in home):
        raise RuntimeError("v36 home reference layout invariant failed")
    (java/"ModernEditorialHome.kt").write_text(home,"utf-8")
    (java/"ReadingStatisticsV36.kt").write_text(
        (kit/"scripts/ReadingStatisticsV36.kt").read_text("utf-8"),"utf-8")

    old=(java/"ImanQuoteCarousel.kt").read_text("utf-8")
    if old.count(QUOTE_MARKER)!=1 or old.count('FeaturedExcerpt("iman-chapter-')!=79:
        raise RuntimeError("v36 cannot protect 79 source-verified excerpts")
    new=(kit/"scripts/ReferenceQuoteV36.kt").read_text("utf-8")
    if (new.count("Route.Reader(q.chapterId, q.blockId)")!=1 or
        "ImanCaveatFont" not in new or "Crossfade(" not in new):
        raise RuntimeError("v36 featured reminder lost interaction or font")
    (java/"ImanQuoteCarousel.kt").write_text(old[:old.index(QUOTE_MARKER)]+new,"utf-8")

    drawable=dest/"app/src/main/res/drawable-nodpi"
    _soft_integrated_art(drawable)
    preload=java/"MedicineHomeArtwork.kt"
    preload.write_text(replace_one(preload.read_text("utf-8"),
        "        R.drawable.iman_v35_reminder,",
        "        R.drawable.iman_v35_reminder,\n        R.drawable.iman_v36_reminder,",
        "v36 background preloader"),"utf-8")
    _install_caveat(dest)
    if reader.read_bytes()!=reader_before or app.read_bytes()!=app_before:
        raise RuntimeError("v36 reader or native bottom navigation modified")
    for name,digest in preserved.items():
        if hashlib.sha256((java/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError("v36 unrelated native Kotlin changed: "+name)
    for name,digest in book_hashes.items():
        if hashlib.sha256((assets/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError("v36 translated book or quiz changed: "+name)
    if hashlib.sha256(wallpaper.read_bytes()).hexdigest()!=wallpaper_hash:
        raise RuntimeError("v36 lost continuous parchment wallpaper")
    if NAV not in app.read_text("utf-8"):
        raise RuntimeError("v36 nav actions changed")
    print("PASS v36: native parchment, actual ledger/quiz statistics, protected reading data and navigation")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--dest",type=Path,required=True)
    args=parser.parse_args()
    build_v36(Path(__file__).resolve().parents[1],args.dest)
