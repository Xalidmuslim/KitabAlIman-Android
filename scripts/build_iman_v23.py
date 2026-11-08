"""v0.23 / reference #4: borderless editorial paper, generated matte icon quartet.

Parent: tested v0.22. Reader, all 131 chapters, 242 footnotes, 524 quizzes,
79 linked excerpts, navigation routes, app storage and TTS remain intact.
This build has its own preview23 application ID; it never replaces user data.
"""
from pathlib import Path
import argparse
import base64
import hashlib
import io
import json

from scripts.build_iman_v22 import build_v22
from scripts.build_iman_v20 import replace_one, APP, NAV, QUOTE as QUOTE_MARKER

ICON_NAMES = ("contents", "collections", "glossary", "bookmarks")
ATLAS_SHA256 = "496f4817ea569cb1739cc4950aa6aa6e851e8c30eaac439679657eb2123ad8cc"

def install_variant4_quote(source: str, implementation: str) -> str:
    if source.count(QUOTE_MARKER) != 1:
        raise RuntimeError("v23: quote component anchor unexpected")
    prefix = source[:source.index(QUOTE_MARKER)]
    if prefix.count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v23: 79 source-anchored quotes not preserved")
    for token in (
        "Crossfade(", "tween(180)", 'Text("Другая ↻"',
        "Route.Reader(q.chapterId, q.blockId)", "maxLines = 5",
        "border = null", "shadowElevation = 0.dp",
    ):
        if token not in implementation:
            raise RuntimeError("v23: reminder interaction missing " + token)
    if "reader_parchment_source" in implementation or "iman_v17_quote" in implementation:
        raise RuntimeError("v23: no textured or illustrated reminder card allowed")
    return prefix + implementation

def patch_nav_background(source: str) -> str:
    if source.count(NAV) != 1:
        raise RuntimeError("v23: native navigation anchor missing")
    pos = source.index(NAV)
    prefix, nav = source[:pos], source[pos:]
    tabs = [line.strip() for line in nav.splitlines()
            if line.strip().startswith('NavItem("')]
    nav = replace_one(
        nav, "Color(0xFFF7F3EC)", "Color(0xFFFCF8F3)", "v23 bottom nav matching paper")
    if len(tabs) != 5 or tabs != [
        line.strip() for line in nav.splitlines()
        if line.strip().startswith('NavItem("')
    ]:
        raise RuntimeError("v23: five tab icons/actions changed")
    if ".border(" in nav or "antique_card_paper" in nav:
        raise RuntimeError("v23: floating framed nav was reintroduced")
    return prefix + nav

def install_icon_quartet(kit: Path, target_res: Path):
    from PIL import Image
    encoded = (kit / "assets/ui/v23/iman_v23_library_atlas.b64").read_text("ascii").strip()
    raw = base64.b64decode(encoded, validate=True)
    if hashlib.sha256(raw).hexdigest() != ATLAS_SHA256:
        raise RuntimeError("v23: original matte illustration atlas checksum differs")
    image = Image.open(io.BytesIO(raw))
    image.load()
    if image.format != "JPEG" or image.size != (320, 80):
        raise RuntimeError("v23: unexpected icon atlas format/size")
    folder = target_res / "drawable-nodpi"
    for i, name in enumerate(ICON_NAMES):
        cut = image.crop((i * 80, 0, (i + 1) * 80, 80)).convert("RGB")
        dst = folder / f"iman_v23_{name}.webp"
        cut.save(dst, "WEBP", quality=93, method=6)
        if dst.stat().st_size < 350:
            raise RuntimeError("v23: empty generated illustration " + name)
    return raw

def build_v23(kit: Path, dest: Path):
    build_v22(kit, dest)
    gradle = dest / "app/build.gradle"
    g = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 22", "versionCode 23"),
        ("versionName '0.22.0'", "versionName '0.23.0'"),
        ("applicationIdSuffix '.preview22'", "applicationIdSuffix '.preview23'"),
    ):
        g = replace_one(g, old, new, "v23 version")
    gradle.write_text(g, "utf-8")

    java = dest / APP
    res = dest / "app/src/main/res"
    assets = dest / "app/src/main/assets"
    protected_java = {
        p.name: p.read_bytes() for p in java.glob("*.kt")
        if p.name not in ("ModernEditorialHome.kt", "ImanQuoteCarousel.kt", "App.kt", "MedicineHomeArtwork.kt")
    }
    before_nav = (java / "App.kt").read_text("utf-8")
    book_hashes = {
        name: hashlib.sha256((assets / name).read_bytes()).hexdigest()
        for name in ("book.json", "quiz.json", "featured_quotes.json")
    }
    icon_hashes = {
        p.relative_to(res).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in res.rglob("*") if p.is_file() and
        (p.name.startswith("nav_") or p.name.startswith("ic_nav_"))
    }
    paper = res / "drawable-nodpi/reader_parchment_source.png"
    before_paper = hashlib.sha256(paper.read_bytes()).hexdigest()

    home = (kit / "scripts/EditorialVariant4HomeV23.kt").read_text("utf-8")
    quote = (kit / "scripts/EditorialVariant4QuoteV23.kt").read_text("utf-8")
    required_routes = (
        "Route.Book", "Route.Collections", "Route.Glossary",
        "Route.Bookmarks", "Route.Progress",
        "Route.Reader(it.id, resume = last != null)",
        "Route.CollectionDetail(entry.id)",
    )
    for anchor in (
        "ModernEditorialHomeScreen(", "ImanFeaturedQuoteCarousel(navigate)",
        "EditorialBookSection(", "EditorialResumeCard(",
        "EditorialOrnamentDivider(", "Color(0xFFFCF8F3)",
        *required_routes,
    ):
        if anchor not in home:
            raise RuntimeError("v23: home feature missing " + anchor)
    for name in ICON_NAMES:
        if f"R.drawable.iman_v23_{name}" not in home:
            raise RuntimeError("v23: generated illustration not linked " + name)
        if f"R.drawable.iman_v17_{name}" not in home:
            raise RuntimeError("v23: dark theme fallback lost " + name)
    if "reader_parchment_source" in home or "readerPaperOverlay(" in home:
        raise RuntimeError("v23: old full-page cracked parchment still present")
    if "BorderStroke(" in home or "StandaloneBottomNav(" in home:
        raise RuntimeError("v23: a framed card or duplicate nav was introduced")
    (java / "ModernEditorialHome.kt").write_text(home, "utf-8")
    qpath = java / "ImanQuoteCarousel.kt"
    qpath.write_text(install_variant4_quote(qpath.read_text("utf-8"), quote), "utf-8")
    after_nav = patch_nav_background(before_nav)
    if before_nav[:before_nav.index(NAV)] != after_nav[:after_nav.index(NAV)]:
        raise RuntimeError("v23: non-nav app code changed")
    (java / "App.kt").write_text(after_nav, "utf-8")
    install_icon_quartet(kit, res)

    # Decode v23 book images via the established asynchronous preloader,
    # keeping thumbnail raster decoding off the Compose UI thread.
    preload_path = java / "MedicineHomeArtwork.kt"
    preload_before = preload_path.read_text("utf-8")
    preload_after = replace_one(
        preload_before,
        "        R.drawable.iman_v17_bookmarks,",
        """        R.drawable.iman_v17_bookmarks,
        R.drawable.iman_v23_contents,
        R.drawable.iman_v23_collections,
        R.drawable.iman_v23_glossary,
        R.drawable.iman_v23_bookmarks,""",
        "v23 new artwork preload",
    )
    preload_path.write_text(preload_after, "utf-8")

    for name in ICON_NAMES:
        if f"R.drawable.iman_v23_{name}" not in preload_path.read_text("utf-8"):
            raise RuntimeError("v23: generated icon is not preloaded: " + name)
    for name, content in protected_java.items():
        if (java / name).read_bytes() != content:
            raise RuntimeError("v23: book reader, preferences or unrelated screen edited")
    for name, digest in book_hashes.items():
        if hashlib.sha256((assets / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError("v23: book / tests / quotes data changed")
    for name, digest in icon_hashes.items():
        if hashlib.sha256((res / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError("v23: existing nav icon overwritten")
    if hashlib.sha256(paper.read_bytes()).hexdigest() != before_paper:
        raise RuntimeError("v23: reading paper inadvertently edited")
    excerpts = json.loads((assets / "featured_quotes.json").read_text("utf-8"))
    if len(excerpts) != 79 or len({e["text"] for e in excerpts}) != 79:
        raise RuntimeError("v23: reminders inventory changed")
    if list((dest / "app/src/main").rglob("*.pdf")):
        raise RuntimeError("v23: PDF unexpectedly included")
    print("PASS v0.23: reference 4 seamless page, 4 original matte illustrations, native data/routes unchanged")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args()
    build_v23(Path(__file__).resolve().parents[1], args.dest)
