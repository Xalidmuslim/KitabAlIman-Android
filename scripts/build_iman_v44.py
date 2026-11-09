"""Assemble verified v43.1 then style EVERY native subpage with the Home's paper.

No changes to Home composables, book/quiz assets, navigation logic, reader text
content, bookmarks, notes or stored user preferences. Test as preview44.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

from scripts.build_iman_v43 import build_v43
from scripts.build_iman_v20 import APP, NAV, replace_one
from scripts.iman_v44_transform import patch_all

PROTECTED = (
    "ModernEditorialHome.kt",
    "ImanQuoteCarousel.kt",
    "MedicineHomeArtwork.kt",
    "AntiqueDesign.kt",
    "Theme.kt",
    "Routes.kt",
)

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def build_v44(kit: Path, dest: Path) -> None:
    build_v43(kit, dest)
    java=dest/APP
    assets=dest/"app/src/main/assets"
    app=java/"App.kt"
    reader=java/"Reader.kt"
    original_app=app.read_text("utf-8")
    original_reader=reader.read_text("utf-8")
    nav=original_app[original_app.index(NAV):]
    book_hashes={f.name:sha(f) for f in assets.iterdir() if f.is_file()}
    protected={name:sha(java/name) for name in PROTECTED}

    gradle=dest/"app/build.gradle"
    config=gradle.read_text("utf-8")
    for old,new in (
        ("versionCode 46","versionCode 47"),
        ("versionName '0.43.1'","versionName '0.44.0'"),
        ("applicationIdSuffix '.preview43'","applicationIdSuffix '.preview44'"),
    ):
        config=replace_one(config,old,new,"v44 isolated installation")
    gradle.write_text(config,"utf-8")

    patched=patch_all(java)
    shutil.copyfile(kit/"scripts/ImanUnifiedPaperV44.kt",java/"ImanUnifiedPaper.kt")
    shutil.copyfile(kit/"scripts/ImanUnifiedMoreV44.kt",java/"ImanV38More.kt")

    updated_app=app.read_text("utf-8")
    updated_reader=reader.read_text("utf-8")
    if NAV not in updated_app or updated_app[updated_app.index(NAV):] != nav:
        raise RuntimeError("v44 altered the protected five-tab navigation implementation")
    if updated_app.count("ImanUnifiedRouteTheme(isHome = route == Route.Home)") != 1:
        raise RuntimeError("v44 did not scope the unified palette to subpages")
    if updated_app.count("R.drawable.iman_v38_flat_paper") != 1:
        raise RuntimeError("v44 missing original approved background wallpaper")
    if updated_app.count("Route.Home -> WebHomeScreen(") != 1:
        raise RuntimeError("v44 changed the Home route")
    if updated_reader.count("ReaderScreen(") != original_reader.count("ReaderScreen("):
        raise RuntimeError("v44 reader function signature lost")
    if "reader_parchment_source" in updated_reader:
        raise RuntimeError("v44 left the independent reader wallpaper")
    if "(if (chapter.title.length > 60) 18 else 20).sp" not in updated_reader:
        raise RuntimeError("v44 did not reduce internal reading headings")
    if "V38ReadingSession(chapter = chapter, scrollState = scrollState)" not in updated_reader:
        raise RuntimeError("v44 lost reading session recording")
    if "FaithChapterQuiz(chapter = chapter, store = store)" not in updated_reader:
        raise RuntimeError("v44 lost chapter quizzes")
    more=(java/"ImanV38More.kt").read_text("utf-8")
    for route in ("Route.Notes","Route.Hadiths","Route.Book","Route.Settings","Route.History"):
        if route not in more:raise RuntimeError("v44 More route missing: "+route)
    for name,oldsha in protected.items():
        if sha(java/name)!=oldsha:
            raise RuntimeError("v44 altered approved Home or stable route model: "+name)
    for name,oldsha in book_hashes.items():
        if sha(assets/name)!=oldsha:
            raise RuntimeError("v44 altered source data: "+name)
    book=json.loads((assets/"book.json").read_text("utf-8"))
    quiz=json.loads((assets/"quiz.json").read_text("utf-8"))
    if len(book["chapters"])!=131 or len(quiz["chapters"])!=131:
        raise RuntimeError("v44 missing original 131 chapters or quizzes")
    if (java/"ImanQuoteCarousel.kt").read_text("utf-8").count('FeaturedExcerpt("iman-chapter-')!=79:
        raise RuntimeError("v44 changed 79 source-based reminders")
    print("PASS v44: same Home hash, full parchment on all routes, 7 screens flattened",
          len(patched),"131 chapters, 79 reminders and quizzes unchanged")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--dest",type=Path,required=True)
    args=parser.parse_args()
    build_v44(Path(__file__).resolve().parents[1],args.dest)
