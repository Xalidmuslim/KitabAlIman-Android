"""v0.45.8: minimal visual affordance for frame-free chapter quiz action."""
import argparse
import hashlib
import json
from pathlib import Path
from scripts.build_iman_v457 import build_v457
from scripts.build_iman_v20 import APP, NAV, replace_one
from scripts.iman_v458_quiz_cta import patch_generated

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def build_v458(kit: Path, dest: Path) -> None:
    build_v457(kit, dest)
    java = dest/APP
    assets = dest/"app/src/main/assets"
    gradle = dest/"app/build.gradle"
    before = {p.name: digest(p) for p in java.glob("*.kt")}
    book_files = {p.name: digest(p) for p in assets.iterdir() if p.is_file()}
    original_nav = (java/"App.kt").read_text("utf-8")
    original_quote = digest(java/"ImanQuoteCarousel.kt")
    original_gradle = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 57", "versionCode 58"),
        ("versionName '0.45.7'", "versionName '0.45.8'"),
        ("applicationIdSuffix '.preview457'", "applicationIdSuffix '.preview458'"),
    ):
        original_gradle = replace_one(original_gradle, old, new, "v458 isolated preview")
    gradle.write_text(original_gradle, "utf-8")
    changed = patch_generated(java)
    for name, hash_before in before.items():
        if name != changed and digest(java/name) != hash_before:
            raise RuntimeError("Unrelated Kotlin source changed: "+name)
    if NAV not in original_nav or (java/"App.kt").read_text("utf-8") != original_nav:
        raise RuntimeError("Native five-tab navigation changed")
    if digest(java/"ImanQuoteCarousel.kt") != original_quote:
        raise RuntimeError("Approved manuscript, quote and 79 reminder source changed")
    for name, old in book_files.items():
        if digest(assets/name) != old:
            raise RuntimeError("Book or saved knowledge corpus changed: " + name)
    book = json.loads((assets/"book.json").read_text("utf-8"))
    quizzes = json.loads((assets/"quiz.json").read_text("utf-8"))
    quotes = json.loads((assets/"featured_quotes.json").read_text("utf-8"))
    if len(book["chapters"]) != 131 or len(quizzes["chapters"]) != 131 or len(quotes) != 79:
        raise RuntimeError("v458 changed protected 131 chapters, quizzes or 79 quotes")
    new=(java/changed).read_text("utf-8")
    for token in ('Text("Проверить прочитанное"', "Icons.Default.CheckCircle",
                  "Icons.Default.ChevronRight", "FontWeight.SemiBold"):
        if token not in new:
            raise RuntimeError("Quiz CTA contract missing: " + token)
    print("PASS v458: visually discoverable flat quiz CTA in", changed,
          "and preserved book, quiz, reminders, five-tab nav")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args()
    build_v458(Path(__file__).resolve().parents[1],args.dest)
