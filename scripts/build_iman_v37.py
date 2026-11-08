"""v0.37: minimal device-feedback layout patch layered on the verified v0.36 app.

Changes only Compose home/quote/statistics sources and preview version. Data, navigation,
reader, app shell and established asset pipelines remain exactly as in v0.36.
"""
from pathlib import Path
import argparse
import hashlib

from scripts.build_iman_v20 import APP, NAV, replace_one
from scripts.build_iman_v36 import build_v36, QUOTE_MARKER


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_v37(kit: Path, dest: Path) -> None:
    build_v36(kit, dest)
    java = dest / APP
    app = java / "App.kt"
    reader = java / "Reader.kt"
    app_before = sha(app)
    reader_before = sha(reader)
    assets = dest / "app/src/main/assets"
    book_hashes = {
        p.name: sha(p) for p in assets.iterdir() if p.is_file()
    }
    nav_before = NAV in app.read_text("utf-8")

    gradle = dest / "app/build.gradle"
    text = gradle.read_text("utf-8")
    for before, after in (
        ("versionCode 36", "versionCode 38"),
        ("versionName '0.36.0'", "versionName '0.37.1'"),
        ("applicationIdSuffix '.preview36'", "applicationIdSuffix '.preview37'"),
    ):
        text = replace_one(text, before, after, "v37 isolated test package")
    gradle.write_text(text, "utf-8")

    home = (kit / "scripts/ReferenceHomeV37.kt").read_text("utf-8")
    # Match the approved v0.35 matte icons reused by the verified v0.36 build.
    for name in ("contents", "collections", "glossary", "bookmarks"):
        home = replace_one(home, f"R.drawable.iman_v32_{name}",
                           f"R.drawable.iman_v35_{name}",
                           "retain approved library illustrations")
    quote = (kit / "scripts/ReferenceQuoteV37.kt").read_text("utf-8")
    stats = (kit / "scripts/ReadingStatisticsV37.kt").read_text("utf-8")
    if "ImanReadingStatistics(book, store)" not in home or "maxLines = 5" in quote:
        raise RuntimeError("v37 home/quote regression contract failed")
    if "heightIn(min = 92.dp)" not in quote or "heightIn(min = 18.dp)" not in stats:
        raise RuntimeError("v37 viewport/statistics regression contract failed")
    if "height(42.dp).clipToBounds()" not in stats:
        raise RuntimeError("v37 chart not expanded")
    (java / "ModernEditorialHome.kt").write_text(home, "utf-8")
    (java / "ReadingStatisticsV36.kt").write_text(stats, "utf-8")

    qfile = java / "ImanQuoteCarousel.kt"
    old = qfile.read_text("utf-8")
    if old.count(QUOTE_MARKER) != 1 or old.count('FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v37 would lose source-verified reminders")
    qfile.write_text(old[:old.index(QUOTE_MARKER)] + quote, "utf-8")

    if sha(app) != app_before or sha(reader) != reader_before:
        raise RuntimeError("v37 would modify reading or navigation code")
    if (NAV in app.read_text("utf-8")) != nav_before or not nav_before:
        raise RuntimeError("v37 changed five-tab navigation")
    for name, before in book_hashes.items():
        if sha(assets / name) != before:
            raise RuntimeError("v37 would change source book or user-study assets: " + name)
    if (java / "ImanQuoteCarousel.kt").read_text("utf-8").count(
            'FeaturedExcerpt("iman-chapter-') != 79:
        raise RuntimeError("v37 lost reminders")
    print("PASS v37: complete quotes, full chapter titles, improved readability; book and navigation unchanged")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args()
    build_v37(Path(__file__).resolve().parents[1], args.dest)
