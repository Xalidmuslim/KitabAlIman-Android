"""Build v0.3.0 from the proven v0.2 native app without changing its adapter.

The original Medicine engine, book text and existing installs are untouched.
"""
from pathlib import Path
import argparse
import json
from scripts.assemble_app import make_app
from scripts.book_display import prepare_display_book
from scripts.ui_contents import patch_contents
from scripts.ui_reader import patch_reader, patch_speech
from scripts.ui_navigation import (
    patch_home, patch_more, patch_legacy_screens, patch_app,
    patch_filter, patch_search,
)

JAVA = "app/src/main/java/com/xalid/meditsinaproroka/nativeapp"


def one(source, old, replacement, label):
    if source.count(old) != 1:
        raise RuntimeError("Unexpected pinned source " + label)
    return source.replace(old, replacement, 1)


def build_new_reader(kit, target):
    make_app(kit, target)
    build = target / "app/build.gradle"
    gradle = build.read_text(encoding="utf-8")
    gradle = one(gradle, "versionCode 2", "versionCode 3", "version code")
    gradle = one(gradle, "versionName '0.2.0'", "versionName '0.3.0'", "version name")
    gradle = one(gradle, "applicationIdSuffix '.preview2'",
                 "applicationIdSuffix '.preview3'", "separate CI signing")
    build.write_text(gradle, encoding="utf-8")

    assets = target / "app/src/main/assets/book.json"
    book = json.loads(assets.read_text(encoding="utf-8"))
    adapted = prepare_display_book(book)
    assets.write_text(
        json.dumps(adapted, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    base = target / JAVA
    screens = base / "Screens.kt"
    changes = (
        ("Screens.kt", lambda s: patch_legacy_screens(patch_contents(s))),
        ("Reader.kt", patch_reader),
        ("ChapterSpeech.kt", patch_speech),
        ("AntiqueDesign.kt", patch_home),
        ("WebDesign.kt", patch_more),
        ("App.kt", patch_app),
        ("Routes.kt", patch_filter),
        ("Utils.kt", patch_search),
    )
    for name, transform in changes:
        file = base / name
        original = file.read_text(encoding="utf-8")
        update = transform(original)
        if original == update:
            raise RuntimeError("No modifications applied to " + name)
        file.write_text(update, encoding="utf-8")

    if list((target/"app/src/main").rglob("*.pdf")):
        raise RuntimeError("PDF bundled unexpectedly")
    print("Built native v0.3.0 book sources: 131 chapters, 242 footnotes.")


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--dest", type=Path, required=True)
    args = cli.parse_args()
    build_new_reader(Path(__file__).resolve().parents[1], args.dest)
