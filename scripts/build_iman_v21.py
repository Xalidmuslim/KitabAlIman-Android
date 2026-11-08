"""Build v0.21: low-chrome editorial homepage and frameless five-tab shell.

Builds from the verified v0.20 code. Leaves book, quiz, excerpts, reader,
study flows and stored preferences untouched. v0.21 has an independent preview
package so existing installs and their on-device user data are not replaced.
"""
from pathlib import Path
import argparse
import hashlib
import json

from scripts.build_iman_v20 import build_v20, patch_quote, replace_one, APP, NAV

def patch_bottom_nav(source: str) -> str:
    if source.count(NAV) != 1:
        raise RuntimeError("Expected native bottom nav anchor missing or duplicated")
    index = source.index(NAV)
    prefix, nav = source[:index], source[index:]
    old_actions = [line.strip() for line in nav.splitlines()
                   if line.strip().startswith('NavItem("')]
    nav = replace_one(nav,
        "val panelShape = RoundedCornerShape(16.dp)",
        "val panelShape = RoundedCornerShape(0.dp)",
        "bottom nav square safe-area background")
    nav = replace_one(nav,
        ".padding(start = 13.dp, end = 13.dp, top = 4.dp, bottom = 4.dp)",
        ".padding(start = 0.dp, end = 0.dp, top = 3.dp, bottom = 1.dp)",
        "bottom nav edge-to-edge spacing")
    nav = replace_one(nav,
        """                    .background(if (dark) MaterialTheme.colorScheme.surface else Color(0xFFF2E8D9))
                    .border(
                        width = 0.9.dp,
                        color = if (dark) MaterialTheme.colorScheme.outline else Color(0xFFCDBBA2),
                        shape = panelShape,
                    ),""",
        """                    .background(if (dark) MaterialTheme.colorScheme.surface else Color(0xFFF7F3EC)),""",
        "bottom nav contour")
    nav = replace_one(nav,
        """                if (!dark) {
                    Image(
                        painter = MedicineHomeArtwork.painter(R.drawable.antique_card_paper),
                        contentDescription = null,
                        modifier = Modifier.matchParentSize(),
                        contentScale = ContentScale.Crop,
                        alpha = 0.40f,
                    )
                }
                Row(""",
        """                Row(""",
        "bottom nav decorative artwork")
    new_actions = [line.strip() for line in nav.splitlines()
                   if line.strip().startswith('NavItem("')]
    if old_actions != new_actions or len(new_actions) not in (0, 5):
        raise RuntimeError("Five native navigation actions were changed")
    if ".border(" in nav or "R.drawable.antique_card_paper" in nav:
        raise RuntimeError("Bottom navigation frame or old paper artwork survived")
    return prefix + nav

def build_v21(kit: Path, dest: Path) -> None:
    build_v20(kit, dest)
    gradle = dest / "app/build.gradle"
    g = gradle.read_text("utf-8")
    for a, b in (
        ("versionCode 20", "versionCode 21"),
        ("versionName '0.20.0'", "versionName '0.21.0'"),
        ("applicationIdSuffix '.preview20'", "applicationIdSuffix '.preview21'"),
    ):
        g = replace_one(g, a, b, "v21 version")
    gradle.write_text(g, "utf-8")

    main = dest / APP
    res = dest / "app/src/main/res"
    old = {p.name: p.read_bytes() for p in main.glob("*.kt")
           if p.name not in ("ModernEditorialHome.kt", "ImanQuoteCarousel.kt", "App.kt")}
    nav_icons = {p.relative_to(res).as_posix(): p.read_bytes()
                 for p in res.rglob("*") if p.is_file() and
                 (p.name.startswith("nav_") or p.name.startswith("ic_nav_"))}
    assets = dest / "app/src/main/assets"
    book_hashes = {name: hashlib.sha256((assets / name).read_bytes()).hexdigest()
                   for name in ("book.json", "quiz.json", "featured_quotes.json")}

    home = (kit / "scripts/BorderlessHomeV21.kt").read_text("utf-8")
    quote = (kit / "scripts/BorderlessQuoteV21.kt").read_text("utf-8")
    for name, content in (("home", home), ("quote", quote)):
        if "border = null" not in content or "shadowElevation = 0.dp" not in content:
            raise RuntimeError("Borderless " + name + " did not remove frames")
        if "BorderStroke(" in content:
            raise RuntimeError("Old surface outline in " + name)
    for anchor in ("ModernEditorialHomeScreen(", "EditorialResumeCard(",
                   "EditorialBookSection(", "ImanFeaturedQuoteCarousel(navigate)",
                   "Route.Book", "Route.Glossary", "Route.Collections",
                   "Route.Bookmarks", "Route.Progress",
                   "Route.Reader(it.id, resume = last != null)",
                   "Route.CollectionDetail(entry.id)",
                   "R.drawable.iman_v17_contents",
                   "R.drawable.iman_v17_collections",
                   "R.drawable.iman_v17_glossary",
                   "R.drawable.iman_v17_bookmarks"):
        if anchor not in home:
            raise RuntimeError("v21 homepage feature removed: " + anchor)
    if "StandaloneBottomNav(" in home or "WebView(" in home:
        raise RuntimeError("Unexpected v21 navigation rewrite")
    (main / "ModernEditorialHome.kt").write_text(home, "utf-8")

    quotes_path = main / "ImanQuoteCarousel.kt"
    quotes_path.write_text(patch_quote(quotes_path.read_text("utf-8"), quote), "utf-8")
    nav_path = main / "App.kt"
    nav_before = nav_path.read_text("utf-8")
    nav_after = patch_bottom_nav(nav_before)
    if nav_after[:nav_after.index(NAV)] != nav_before[:nav_before.index(NAV)]:
        raise RuntimeError("Unrelated app state/router changed")
    nav_path.write_text(nav_after, "utf-8")

    for filename, content in old.items():
        if (main / filename).read_bytes() != content:
            raise RuntimeError("Reader, preferences or another screen changed: " + filename)
    for relative, content in nav_icons.items():
        if (res / relative).read_bytes() != content:
            raise RuntimeError("Original navigation icon modified: " + relative)
    for name, digest in book_hashes.items():
        if hashlib.sha256((assets / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError("Protected book data, quizzes or source quotes changed: " + name)
    excerpts = json.loads((assets / "featured_quotes.json").read_text("utf-8"))
    if len(excerpts) != 79 or len({q["text"] for q in excerpts}) != 79:
        raise RuntimeError("Source reminders missing or repeated")
    if list((dest / "app/src/main").rglob("*.pdf")):
        raise RuntimeError("Source PDF accidentally bundled")
    print("v0.21: no home/nav outlines, five routes intact, 131 book chapters safe")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dest", required=True, type=Path)
    args = p.parse_args()
    build_v21(Path(__file__).resolve().parents[1], args.dest)
