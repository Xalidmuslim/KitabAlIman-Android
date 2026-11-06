"""Construct an independent Kitab al-Iman Android app from the pinned native engine.

The original Medicine source and golden baseline are never modified.
Text-only assets; no PDF is ever included in the APK.
"""
from pathlib import Path
import argparse
import shutil
import subprocess

REPO = "https://github.com/Xalidmuslim/Prophetic-Medicine-Native.git"
PIN = "e004dbc101345a171d9711316b3fda73ee146c61"
JAVA_SRC = "app/src/main/java/com/xalid/meditsinaproroka/nativeapp"


def replace_in(path, changes):
    original = path.read_text(encoding="utf-8")
    updated = original
    for old, new in changes:
        if old not in updated:
            raise RuntimeError(f"Missing expected source text in {path}: {old!r}")
        updated = updated.replace(old, new)
    if updated != original:
        path.write_text(updated, encoding="utf-8")


def make_app(kit, dest):
    if dest.exists():
        raise RuntimeError("Refusing to overwrite an existing destination")
    subprocess.run(["git", "clone", "--single-branch", "--branch",
                    "codex/medicine-ruvoice-natural-20261024",
                    REPO, str(dest)], check=True)
    subprocess.run(["git", "-C", str(dest), "checkout", "--detach", PIN], check=True)
    actual = subprocess.check_output(
        ["git", "-C", str(dest), "rev-parse", "HEAD"], text=True).strip()
    if actual != PIN:
        raise RuntimeError("The native source revision changed unexpectedly")
    replace_in(dest/"app/build.gradle", [
        ("applicationId 'com.xalid.meditsinaproroka.nativeapp.modulecopy'",
         "applicationId 'com.xalid.kitabaliman'"),
        ("versionName '1.0.0-modulecopy-preview'", "versionName '0.1.0'"),
        ("applicationIdSuffix '.ruvoicefix'", "applicationIdSuffix '.preview'"),
        ("applicationIdSuffix '.firstframe'", "applicationIdSuffix '.test'"),
    ])
    src = dest/JAVA_SRC

    # Keep Compose navigation, gestures, optimized lazy Reader, saved
    # bookmarks, notes, highlights, settings, and RuVoice integration.
    for filename in ["Reader.kt", "Screens.kt", "WebDesign.kt", "AntiqueDesign.kt"]:
        file = src/filename
        content = file.read_text(encoding="utf-8")
        for old, new in [
            ("Медицина Пророка ﷺ", "Книга Имана"),
            ("Медицина Пророка", "Книга Имана"),
            ("Средства", "Указатель понятий"),
            ("средства", "понятия"),
            ("Как лечили / что применялось", "Вопросы веры"),
            ("Как лечили", "Вопросы веры"),
            ("Состояние → средства → полный текст", "Тема → раздел → текст"),
            ("Состояние → понятия → полный текст", "Тема → раздел → текст"),
            ("Метки медицины эпохи", "Редакционные метки"),
            ("Подборки по смыслу и состояниям", "Тематические подборки"),
            ("Это историко-религиозный текст, а не современное медицинское руководство. Описанные методы не заменяют диагностику и лечение врача; отдельные исторические средства могут быть устаревшими или небезопасными.",
             "Это текст русского перевода издания 2022 года. Перевод и сноски требуют сверки с оригиналом; права на распространение принадлежат правообладателю."),
            ("Историко-религиозный справочник, а не персональная медицинская инструкция.",
             "Указатель тематических вопросов по тексту книги."),
            ("Руководство Пророка ﷺ в лечении", "Иман, Ислам и Ихсан"),
        ]:
            content = content.replace(old, new)
        file.write_text(content, encoding="utf-8")

    replace_in(src/"AntiqueDesign.kt", [
        ("Посланник Аллаха ﷺ сказал:", "Из начала книги:"),
        ("«Аллах не ниспослал ни одной болезни, не ниспослав вместе с ней исцеления»",
         "«Знай, что понятия «Иман» и «Ислам» объединяют в себе всю религию»"),
        ("Источник: Сахих аль-Бухари, хадис № 5678.",
         "Источник: «Книга Имана», стр. 11."),
        ("R.drawable.antique_mortar_detail", "R.drawable.antique_open_book_detail"),
        ("R.drawable.antique_remedies_detail", "R.drawable.antique_scroll_detail"),
    ])
    reader = src/"Reader.kt"
    content = reader.read_text(encoding="utf-8")
    anchor = '    if (block.type == "hadith") {'
    if anchor not in content:
        raise RuntimeError("ReaderBlock structure changed; abort")
    footnote = """    if (block.type == "footnote") {
        Surface(
            modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
            color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.35f),
            shape = androidx.compose.foundation.shape.RoundedCornerShape(10.dp),
            border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline.copy(alpha = 0.4f)),
        ) {
            Column(Modifier.padding(horizontal = 12.dp, vertical = 9.dp)) {
                Text("СНОСКА", fontFamily = WebSansFont, fontSize = 10.sp,
                     color = MaterialTheme.colorScheme.onSurfaceVariant)
                Spacer(Modifier.height(3.dp))
                SelectableNativeText(chapter, block, store)
            }
        }
        return
    }

"""
    reader.write_text(content.replace(anchor, footnote + anchor, 1), encoding="utf-8")
    speech = src/"ChapterSpeech.kt"
    replace_in(speech, [
        ("val parts = sequenceOf(title) + blocks.asSequence().map { it.text }",
         'val parts = sequenceOf(title) + blocks.asSequence().filter { it.type != "quran" }.map { it.text }'),
    ])
    for path in [dest/"app/src/main/res/values/strings.xml",
                 dest/"app/src/debug/res/values/strings.xml",
                 dest/"app/src/release/res/values/strings.xml"]:
        import re
        value = path.read_text(encoding="utf-8")
        value = re.sub(r'<string name="app_name">[^<]+</string>',
                       '<string name="app_name">Книга Имана — Ибн Таймия</string>', value)
        path.write_text(value, encoding="utf-8")
    assets = dest/"app/src/main/assets"
    shutil.copy2(kit/"assets/book.json", assets/"book.json")
    if any(p.suffix.lower()==".pdf" for p in (dest/"app/src/main").rglob("*")):
        raise RuntimeError("A PDF would be bundled; refusing build")
    # Retain version-pinned original source in a standalone ephemeral build.
    # Remove only inherited workflows from the ephemeral clone.
    workflows = dest/".github/workflows"
    if workflows.exists():
        for p in workflows.glob("*.yml"):
            p.unlink()
    print("Prepared independent Kitab al-Iman native source", flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--dest",type=Path,required=True)
    args=parser.parse_args()
    make_app(Path(__file__).resolve().parents[1], args.dest)
