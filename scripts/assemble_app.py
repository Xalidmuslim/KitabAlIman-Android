"""Construct an independent Kitab al-Iman Android app from the pinned native engine.

The original Medicine source and golden baseline are never modified.
Text-only assets; no PDF is ever included in the APK.
"""
from pathlib import Path
import argparse
import shutil
import subprocess
import json

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



def russian_quran_only(source):
    """Keep existing Russian translations and stable anchor IDs, remove only 3 Arabic verse blocks."""
    import copy
    import re
    book = copy.deepcopy(source)
    expected = {"3:102", "4:1", "33:70–71"}
    found = set()
    for chapter in book["chapters"]:
        original = chapter["blocks"]
        result = []
        for i, block in enumerate(original):
            if block["type"] != "quran":
                result.append(block)
                continue
            ref = block.get("quranReference")
            if ref not in expected or ref in found:
                raise RuntimeError(f"Unexpected or duplicate Quran block: {ref}")
            if block.get("footnoteRefs"):
                raise RuntimeError(f"Cannot drop a Quran block with linked footnotes: {block['id']}")
            if i + 1 >= len(original):
                raise RuntimeError(f"Missing Russian verse after {ref}")
            russian = original[i+1]
            if russian["type"] != "text" or f"[{ref}]" not in russian["text"]:
                raise RuntimeError(f"Original Russian translation/reference not found after {ref}")
            if len(re.findall(r"[А-Яа-яЁё]", russian["text"])) < 20:
                raise RuntimeError(f"Russian verse text is unexpectedly short: {ref}")
            if russian.get("sourcePage") != block.get("sourcePage"):
                raise RuntimeError(f"Verse source-page mismatch: {ref}")
            found.add(ref)
        chapter["blocks"] = result
    if found != expected:
        raise RuntimeError(f"Expected exactly 3 Arabic Quran insertions, got {found}")
    book["stats"]["blocks"] = sum(len(c["blocks"]) for c in book["chapters"])
    return book


def customize_toc_screen(content):
    """Center and enlarge titles in BookScreen, not on bookmark/search/history screens."""
    replacements = [
        (
            "import androidx.compose.ui.text.style.TextOverflow",
            "import androidx.compose.ui.text.style.TextAlign\nimport androidx.compose.ui.text.style.TextOverflow",
        ),
        (
            "private fun ChapterRow(chapter: Chapter, onClick: () -> Unit, trailing: String? = null) {",
            "private fun ChapterRow(chapter: Chapter, onClick: () -> Unit, trailing: String? = null, centeredTitle: Boolean = false) {",
        ),
        (
            "Text(chapter.title, fontFamily = WebLiterataFont, fontWeight = FontWeight.Bold, fontSize = 16.sp, lineHeight = 20.sp)",
            """Text(
                    chapter.title,
                    modifier = if (centeredTitle) Modifier.fillMaxWidth() else Modifier,
                    fontFamily = WebLiterataFont,
                    fontWeight = FontWeight.Bold,
                    fontSize = if (centeredTitle) 18.sp else 16.sp,
                    lineHeight = if (centeredTitle) 23.sp else 20.sp,
                    textAlign = if (centeredTitle) TextAlign.Center else TextAlign.Start,
                )""",
        ),
        (
            """                        sectionTitle,
                        modifier = Modifier.fillMaxWidth()
                            .padding(start = 4.dp, top = 14.dp, bottom = 3.dp),
                        color = MaterialTheme.colorScheme.primary,
                        fontFamily = WebModernFont,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.SemiBold,""",
            """                        sectionTitle,
                        modifier = Modifier.fillMaxWidth()
                            .padding(top = 14.dp, bottom = 3.dp),
                        color = MaterialTheme.colorScheme.primary,
                        fontFamily = WebModernFont,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                        textAlign = TextAlign.Center,""",
        ),
        (
            "ChapterRow(chapter, { open(chapter.id) })",
            "ChapterRow(chapter, { open(chapter.id) }, centeredTitle = true)",
        ),
    ]
    for old, new in replacements:
        if content.count(old) != 1:
            raise RuntimeError(f"TOC layout changed in pinned source: {old[:90]!r}")
        content = content.replace(old, new, 1)
    return content


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
        ("versionName '1.0.0-modulecopy-preview'", "versionName '0.2.0'"),
        ("versionCode 1", "versionCode 2"),
        ("applicationIdSuffix '.ruvoicefix'", "applicationIdSuffix '.preview2'"),
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

    toc_path = src/"Screens.kt"
    toc_path.write_text(customize_toc_screen(toc_path.read_text(encoding="utf-8")), encoding="utf-8")
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
    original_book = json.loads((kit/"assets/book.json").read_text(encoding="utf-8"))
    prepared_book = russian_quran_only(original_book)
    (assets/"book.json").write_text(json.dumps(prepared_book, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
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
