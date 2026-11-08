"""v0.38: incremental home dashboard refinement layered on preserved native v0.37."""
from pathlib import Path
import argparse

from scripts.build_iman_v20 import APP, NAV, replace_one
from scripts.build_iman_v36 import QUOTE_MARKER
from scripts.build_iman_v37 import build_v37, sha


def build_v38(kit: Path, dest: Path) -> None:
    build_v37(kit, dest)
    java = dest / APP
    app = java / "App.kt"
    reader = java / "Reader.kt"
    app_before, reader_before = sha(app), sha(reader)
    assets = dest / "app/src/main/assets"
    book_hashes = {p.name: sha(p) for p in assets.iterdir() if p.is_file()}
    if NAV not in app.read_text("utf-8"):
        raise RuntimeError("v38 must retain native five-tab navigation")

    gradle = dest / "app/build.gradle"
    config = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 38", "versionCode 39"),
        ("versionName '0.37.1'", "versionName '0.38.0'"),
        ("applicationIdSuffix '.preview37'", "applicationIdSuffix '.preview38'"),
    ):
        config = replace_one(config, old, new, "v38 isolated preview version")
    gradle.write_text(config, "utf-8")

    home = (kit / "scripts/ReferenceHomeV38.kt").read_text("utf-8")
    for name in ("contents", "collections", "glossary"):
        home = replace_one(
            home, f"R.drawable.iman_v32_{name}", f"R.drawable.iman_v35_{name}",
            "retain approved matte book illustrations"
        )
    stats = (kit / "scripts/ReadingStatisticsV38.kt").read_text("utf-8")
    quote = (kit / "scripts/ReferenceQuoteV38.kt").read_text("utf-8")
    if home.count('EditorialBookSection("') != 3 or 'item(key = "library-three")' not in home:
        raise RuntimeError("v38 requires three library shortcuts")
    if "ImanReadingStatistics(book, store)" not in home or "navigate(Route.Progress)" not in home:
        raise RuntimeError("v38 lost reading progress")
    if "drawRoundRect(" not in stats or "ledger.daysAgo(" not in stats:
        raise RuntimeError("v38 requires real-data daily bar chart")
    if "store.quizBestPercent" not in stats or "Усвоение" in stats:
        raise RuntimeError("v38 requires accurately labelled quiz results")
    if "Route.Reader(q.chapterId, q.blockId)" not in quote or "maxLines = 5" in quote:
        raise RuntimeError("v38 quote must be source-linked and untruncated")

    (java / "ModernEditorialHome.kt").write_text(home, "utf-8")
    (java / "ReadingStatisticsV36.kt").write_text(stats, "utf-8")
    qfile = java / "ImanQuoteCarousel.kt"
    old = qfile.read_text("utf-8")
    if old.count(QUOTE_MARKER) != 1 or old.count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v38 would lose source-verified reminders")
    qfile.write_text(old[:old.index(QUOTE_MARKER)] + quote, "utf-8")

    if sha(app) != app_before or sha(reader) != reader_before:
        raise RuntimeError("v38 changed reader or app routing")
    if NAV not in app.read_text("utf-8"):
        raise RuntimeError("v38 changed five-tab navigation")
    for name, before in book_hashes.items():
        if sha(assets / name) != before:
            raise RuntimeError("v38 changed book or user study assets: " + name)
    if qfile.read_text("utf-8").count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v38 lost reminders")
    print("PASS v38: three library shortcuts, real charts and honest quiz labels; data and navigation unchanged")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args()
    build_v38(Path(__file__).resolve().parents[1], args.dest)
