"""v0.25: one native Compose background for the complete Home + bottom navigation.

Parent is the verified v0.24 Android build. All decorative images are
individually generated, stored separately as WebP; NO screenshot is used.
Chapter content, glossary, footnotes, quizzes, reader, settings, saved data,
five native navigation actions and preloading remain protected by invariants.
"""
from pathlib import Path
from PIL import Image
import argparse
import hashlib
import json
import shutil

from scripts.build_iman_v24 import build_v24
from scripts.build_iman_v23 import install_variant4_quote, ICON_NAMES
from scripts.build_iman_v20 import APP, NAV, replace_one

ARTWORK_NAMES = ("unified_home", "reminder", *ICON_NAMES)


def patch_shell(source: str, background_fragment: str | None = None) -> str:
    """Decorate root once; do not add a second background to the bottom nav."""
    if source.count(NAV) != 1:
        raise RuntimeError("v25: original standalone five-tab nav entry is missing")
    anchor = "        Box(Modifier.fillMaxSize().padding(insets)) {\n            AnimatedContent("
    if source.count(anchor) != 1:
        raise RuntimeError("v25: expected native Scaffold root not found")
    if background_fragment is None:
        raise RuntimeError("v25: no full-screen source fragment supplied")
    if ("R.drawable.iman_v25_unified_home" not in background_fragment or
        "Modifier.matchParentSize()" not in background_fragment or
        "ContentScale.FillBounds" not in background_fragment or
        "val seamlessHome = current == Route.Home" not in background_fragment):
        raise RuntimeError("v25: incorrect root wallpaper fragment")
    source = replace_one(
        source, anchor,
        "        Box(Modifier.fillMaxSize().padding(insets)) {\n"
        + background_fragment
        + "            AnimatedContent(",
        "v25 one fullscreen paper background before AnimatedContent",
    )
    call = """                modifier = Modifier.align(Alignment.BottomCenter),
            )"""
    source = replace_one(
        source, call,
        """                seamlessHome = seamlessHome,
                modifier = Modifier.align(Alignment.BottomCenter),
            )""",
        "v25 transparent home nav call",
    )
    pos = source.index(NAV)
    before, nav = source[:pos], source[pos:]
    items = [line.strip() for line in nav.splitlines() if line.strip().startswith('NavItem("')]
    if len(items) != 5:
        raise RuntimeError("v25: expected exactly 5 original nav actions")
    nav = replace_one(
        nav,
        "    modifier: Modifier = Modifier,\n) {\n    data class NavItem(",
        "    modifier: Modifier = Modifier,\n    seamlessHome: Boolean = false,\n) {\n    data class NavItem(",
        "v25 nav seam control signature",
    )
    nav = replace_one(
        nav,
        ".background(if (dark) MaterialTheme.colorScheme.surface else Color(0xFFFCF8F3))",
        ".background(if (seamlessHome) Color.Transparent else if (dark) MaterialTheme.colorScheme.surface else Color(0xFFFCF8F3))",
        "v25 transparent navigation surface",
    )
    if [line.strip() for line in nav.splitlines()
        if line.strip().startswith('NavItem("')] != items:
        raise RuntimeError("v25: action or icon was changed in bottom navigation")
    if ".border(" in nav or "antique_card_paper" in nav or "RoundedCornerShape(16.dp)" in nav:
        raise RuntimeError("v25: old bottom nav frame returned")
    return before + nav


def build_v25(kit: Path, dest: Path) -> None:
    build_v24(kit, dest)
    gradle = dest / "app/build.gradle"
    source = gradle.read_text("utf-8")
    for old,new in (
        ("versionCode 24", "versionCode 25"),
        ("versionName '0.24.0'", "versionName '0.25.0'"),
        ("applicationIdSuffix '.preview24'", "applicationIdSuffix '.preview25'"),
    ):
        source = replace_one(source, old, new, "v25 version and isolated package")
    gradle.write_text(source, "utf-8")

    java = dest / APP
    assets = dest / "app/src/main/assets"
    res = dest / "app/src/main/res"
    drawable = res / "drawable-nodpi"

    original_java = {p.name:p.read_bytes() for p in java.glob("*.kt")
         if p.name not in ("ModernEditorialHome.kt","ImanQuoteCarousel.kt",
                            "App.kt","MedicineHomeArtwork.kt")}
    original_reader = (java/"Reader.kt").read_bytes()
    nav_icon_hashes = {
       p.relative_to(res).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
       for p in res.rglob("*") if p.is_file() and
          (p.name.startswith("nav_") or p.name.startswith("ic_nav_"))
    }
    protected_assets = {
       name: hashlib.sha256((assets/name).read_bytes()).hexdigest()
       for name in ("book.json","quiz.json","featured_quotes.json")
    }
    reading_paper = drawable / "reader_parchment_source.png"
    reading_paper_hash = hashlib.sha256(reading_paper.read_bytes()).hexdigest()

    home = (kit/"scripts/SeamlessHomeV25.kt").read_text("utf-8")
    quote = (kit/"scripts/SeamlessQuoteV25.kt").read_text("utf-8")
    patch_fragment = (kit/"scripts/SeamlessShellPatchV25.kt").read_text("utf-8")
    for token in (
        "ModernEditorialHomeScreen(","EditorialBookSection(",
        "EditorialResumeCard(","LinearProgressIndicator(",
        "ImanFeaturedQuoteCarousel(navigate)",
        'item(key = "library-four")',
        "Route.Book","Route.Collections","Route.Glossary",
        "Route.Bookmarks","Route.Progress",
        "Route.Reader(it.id, resume = last != null)",
        "Route.CollectionDetail(entry.id)",
    ):
        if token not in home:
            raise RuntimeError("v25: home feature lost: " + token)
    for token in (
        "R.drawable.iman_v25_reminder",
        "Modifier.weight(0.61f)", "Modifier.weight(0.39f)",
        "showIllustration", "Crossfade(", "tween(180)",
        'Text("Другая ↻"', "Route.Reader(q.chapterId, q.blockId)",
        "maxLines = 5",
    ):
        if token not in quote:
            raise RuntimeError("v25: quote function lost: " + token)
    for name in ICON_NAMES:
        if f"R.drawable.iman_v25_{name}" not in home:
            raise RuntimeError("v25: new icon not used: " + name)
        if f"R.drawable.iman_v17_{name}" not in home:
            raise RuntimeError("v25: existing dark-mode icon lost: " + name)
    if ('readerPaperOverlay(' in home or 'reader_parchment_source' in home or
        'R.drawable.iman_v24_' in home or 'R.drawable.iman_v24_' in quote):
        raise RuntimeError("v25: old nested backgrounds or placeholder graphics present")
    if "BorderStroke(" in home or "StandaloneBottomNav(" in home:
        raise RuntimeError("v25: framed or duplicated native shell detected")

    (java/"ModernEditorialHome.kt").write_text(home,"utf-8")
    oldQuote = java/"ImanQuoteCarousel.kt"
    oldQuote.write_text(install_variant4_quote(oldQuote.read_text("utf-8"),quote),"utf-8")
    app = java/"App.kt"
    app.write_text(patch_shell(app.read_text("utf-8"),patch_fragment),"utf-8")

    source_dir=kit/"assets/ui/v25"
    for name in ARTWORK_NAMES:
        src = source_dir / f"{name if name in ('unified_home','reminder') else 'library_'+name}.webp"
        dst = drawable / f"iman_v25_{name}.webp"
        if not src.is_file() or src.stat().st_size < 3000:
            raise RuntimeError("v25: generated independent art missing: "+str(src))
        with Image.open(src) as im:
            im.load()
            if im.width < 250 or im.height < 180:
                raise RuntimeError("v25: insufficient image resolution "+str(src))
            if name != "unified_home":
                if im.mode != "RGBA" or im.getchannel("A").getextrema()[0] >= 30:
                    raise RuntimeError("v25: illustration lacks clean transparency "+str(src))
        shutil.copyfile(src,dst)

    preload=java/"MedicineHomeArtwork.kt"
    before=preload.read_text("utf-8")
    added=",\n".join("        R.drawable.iman_v25_"+k for k in ARTWORK_NAMES)
    preload.write_text(replace_one(
        before,
        "        R.drawable.iman_v24_reminder,",
        "        R.drawable.iman_v24_reminder,\n"+added+",",
        "preload six v25 images off main thread",
    ),"utf-8")
    for name in ARTWORK_NAMES:
        if f"R.drawable.iman_v25_{name}" not in preload.read_text("utf-8"):
            raise RuntimeError("v25: missing preload for "+name)
    for name,data in original_java.items():
        if (java/name).read_bytes() != data:
            raise RuntimeError("v25: non-UI Kotlin code changed "+name)
    if (java/"Reader.kt").read_bytes() != original_reader:
        raise RuntimeError("v25: existing native reader changed")
    for path,digest in nav_icon_hashes.items():
        if hashlib.sha256((res/path).read_bytes()).hexdigest()!=digest:
            raise RuntimeError("v25: existing native tab icon changed "+path)
    for name,digest in protected_assets.items():
        if hashlib.sha256((assets/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError("v25: book content/quizzes/quotes changed "+name)
    if hashlib.sha256(reading_paper.read_bytes()).hexdigest()!=reading_paper_hash:
        raise RuntimeError("v25: actual reader paper theme was modified")
    excerpts=json.loads((assets/"featured_quotes.json").read_text("utf-8"))
    if len(excerpts)!=79 or len({x["text"] for x in excerpts})!=79:
        raise RuntimeError("v25: original 79 sourced reminders changed")
    if list((dest/"app/src/main").rglob("*.pdf")):
        raise RuntimeError("v25: source PDF unexpectedly bundled")
    print("PASS v0.25: one full-screen paper behind Home+nav; six original graphics; source book and five routes unchanged")


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--dest",type=Path,required=True)
    args=parser.parse_args()
    build_v25(Path(__file__).resolve().parents[1],args.dest)
