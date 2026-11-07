import unittest
from pathlib import Path
from scripts.build_iman_v11 import patch_home, patch_app, patch_reader, HOME_SIGNATURE, NAV_SIGNATURE

class IbnQayyimStylePortTests(unittest.TestCase):
    def test_home_delegates_to_native_compose_and_preserves_other_components(self):
        content = "KEEP OTHER COMPOSABLES\n" + HOME_SIGNATURE + "OLD HOME CODE\n}\n"
        changed = patch_home(content)
        self.assertIn('IbnStyleHomeScreen(book, store, modifier, navigate, onGlobalSearch, onToggleTheme)', changed)
        self.assertTrue(changed.startswith("KEEP OTHER COMPOSABLES"))
        self.assertNotIn("OLD HOME CODE", changed)

    def test_bottom_nav_source_is_byte_identical(self):
        old = '''                Route.Book -> BookScreen(
                    book, screenModifier, ::goBack,
                    focusChapterId = lastReaderChapterId,
                    focusRequest = contentsRequest,
                ) { navigate(Route.Reader(it)) }
''' + NAV_SIGNATURE + '''
    val items = listOf(
        NavItem("Оглавление", R.drawable.nav_topics, true, onTopics),
        NavItem("Главная", R.drawable.nav_home, true, onHome))
'''
        result = patch_app(old)
        self.assertIn('book, store, screenModifier, ::goBack', result)
        self.assertEqual(old.split(NAV_SIGNATURE)[1], result.split(NAV_SIGNATURE)[1])
        self.assertIn('R.drawable.nav_topics', result)

    def test_reader_stable_lazy_item_count(self):
        old = '''item(key = "chapter-header") {
                ReaderChapterSpeechBar(chapter = chapter)
            }
            items(count = groupStarts.size) {}
'''
        result = patch_reader(old)
        self.assertEqual(old.count('item(key = "chapter-header")'), result.count('item(key = "chapter-header")'))
        self.assertIn('ReaderChapterSpeechBar(', result)
        self.assertIn('Text("❦"', result)

    def test_pinned_anchors_fail_closed(self):
        for fn in (patch_home, patch_app, patch_reader):
            with self.assertRaises(RuntimeError): fn("arbitrary replaced source")

    def test_style_source_preserves_app_navigation_and_data(self):
        src = Path(__file__).resolve().parents[1] / 'scripts/ibn_qayyim_style.kt'
        text = src.read_text(encoding='utf-8')
        self.assertIn('rememberLazyListState()', text)
        self.assertIn('rememberSaveable', text)
        self.assertIn('store.progress[chapter.id]', text)
        self.assertIn('isChapterComplete(chapter, pos)', text)
        self.assertIn('Route.Progress', text)
        self.assertNotIn('StandaloneBottomNav', text)
        self.assertNotIn('fun ReaderScreen(', text)
        self.assertNotIn('WebView(', text)
        self.assertNotIn('class MainActivity', text)

if __name__=='__main__':
    unittest.main()
