"""Native Compose port of the user's Ibn Kayyim v38 antique reading UI.

The approved reference is the local Quick/assets/index.html in
IbnKayim_v38_Quiz_Review_30.zip. Port layout and screen interaction,
never book text. Existing bottom navigation and drawables are immutable.
"""
from pathlib import Path
import argparse
from scripts.build_iman_v10 import build_v10

JAVA = Path("app/src/main/java/com/xalid/meditsinaproroka/nativeapp")
HOME_SIGNATURE = "@OptIn(ExperimentalLayoutApi::class)\n@Composable\ninternal fun AntiqueHomeScreen("
APP_START = """                Route.Book -> BookScreen(
                    book, screenModifier, ::goBack,"""
APP_END = """                Route.Book -> IbnStyleContentsScreen(
                    book, store, screenModifier, ::goBack,"""
NAV_SIGNATURE = "@Composable\nprivate fun StandaloneBottomNav("

def one(source, old, new, label):
    actual = source.count(old)
    if actual != 1:
        raise RuntimeError(f"Pinned native code changed ({label}): {actual} matches")
    return source.replace(old, new, 1)

def patch_home(source):
    if source.count(HOME_SIGNATURE) != 1:
        raise RuntimeError("Existing home entry point changed")
    # Existing home is the last composable in the pinned AntiqueDesign.kt.
    head = source[:source.index(HOME_SIGNATURE)]
    return head + """@OptIn(ExperimentalLayoutApi::class)
@Composable
internal fun AntiqueHomeScreen(
    book: BookData, store: AppStore, modifier: Modifier,
    navigate: (Route) -> Unit, onGlobalSearch: () -> Unit,
    onToggleTheme: () -> Unit,
) {
    IbnStyleHomeScreen(book, store, modifier, navigate, onGlobalSearch, onToggleTheme)
}
"""

def patch_app(source):
    if NAV_SIGNATURE not in source:
        raise RuntimeError('Protected bottom nav anchor is missing')
    marker = source.index(NAV_SIGNATURE)
    untouched_bottom = source[marker:]
    result = one(source, APP_START, APP_END, "contents route")
    if result[result.index(NAV_SIGNATURE):] != untouched_bottom:
        raise RuntimeError("Bottom navigation changed: abort")
    if result.count('NavItem("Оглавление"') != 1:
        raise RuntimeError("Expected navigation label is missing")
    return result

def patch_reader(source):
    # Maintain LazyColumn, selection, citations, chapter gestures, footnotes,
    # voice, study quizzes and store offsets. A quiet title ornament only.
    marker = 'item(key = "chapter-header") {'
    if source.count(marker) != 1:
        raise RuntimeError("Reader header anchor changed")
    # Cosmetic only. Do not add/delete a LazyColumn item: row indexes are
    # stable for bookmarks and saved positions.
    if source.count('                ReaderChapterSpeechBar(') != 1:
        raise RuntimeError("Reader speech bar moved")
    return one(source,
        '                ReaderChapterSpeechBar(',
        '''                Text("❦", modifier = Modifier.fillMaxWidth(),
                    textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                    color = Color(0xFF987C55), fontSize = 16.sp)
                Spacer(Modifier.height(7.dp))
                ReaderChapterSpeechBar(''',
        "reader ornament"
    )

def build_v11(kit, dest):
    build_v10(kit, dest)
    gradle = dest / 'app/build.gradle'
    data = gradle.read_text(encoding='utf-8')
    for old,new in [
        ('versionCode 10', 'versionCode 11'),
        ("versionName '0.10.0'", "versionName '0.11.0'"),
        ("applicationIdSuffix '.preview10'", "applicationIdSuffix '.preview11'"),
    ]:
        data = one(data, old, new, "version")
    gradle.write_text(data, encoding='utf-8')

    java = dest / JAVA
    protected_files = {
        x.relative_to(java).as_posix(): x.read_bytes()
        for x in java.glob('*.kt') if x.name not in ('AntiqueDesign.kt', 'App.kt', 'Reader.kt')
    }
    # Bottom-nav icons and their colors are owned by the original app.
    res = dest / 'app/src/main/res'
    nav_icons = {
        p.relative_to(res).as_posix(): p.read_bytes()
        for p in res.rglob('*') if p.is_file() and
        ('nav_' in p.name or 'ic_nav_' in p.name)
    }
    app = java / 'App.kt'
    home = java / 'AntiqueDesign.kt'
    reader = java / 'Reader.kt'
    app.write_text(patch_app(app.read_text(encoding='utf-8')), encoding='utf-8')
    home.write_text(patch_home(home.read_text(encoding='utf-8')), encoding='utf-8')
    reader.write_text(patch_reader(reader.read_text(encoding='utf-8')), encoding='utf-8')

    src = kit / 'scripts/ibn_qayyim_style.kt'
    styled = src.read_text(encoding='utf-8')
    for required in ('IbnStyleHomeScreen', 'IbnStyleContentsScreen',
                     'ПУТЬ К ПОНИМАНИЮ', 'Все разделы', 'В процессе',
                     'Завершённые', 'Статистика и проверка знаний'):
        if required not in styled:
            raise RuntimeError('Style port incomplete: ' + required)
    (java / 'IbnQayyimStyle.kt').write_text(styled, encoding='utf-8')

    for rel, content in protected_files.items():
        if (java / rel).read_bytes() != content:
            raise RuntimeError('Unrelated native screen changed: ' + rel)
    for rel, content in nav_icons.items():
        if (res / rel).read_bytes() != content:
            raise RuntimeError('Bottom nav icon was modified: ' + rel)
    if list((dest / 'app/src/main').rglob('*.pdf')):
        raise RuntimeError('PDF unexpectedly packaged')
    print("Native v0.11: Ibn Kayyim v38 Home+Contents design, unchanged bottom nav/icons, intact book.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dest', type=Path, required=True)
    args = parser.parse_args()
    build_v11(Path(__file__).resolve().parents[1], args.dest)
