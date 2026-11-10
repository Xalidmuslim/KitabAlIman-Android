"""Regression contracts: frameless native reading UI and warm, legible parchment."""
import unittest
from pathlib import Path
from scripts.iman_v457_ui import remove_medical_notice, flatten_controls, warm_purple_literals

ROOT = Path(__file__).resolve().parents[1]

class BorderlessUIV457(unittest.TestCase):
    def test_about_discards_only_unrelated_medical_notice(self):
        source = '''Column {
            Text("Здесь сохранён полный текст издания с исходным порядком глав и дополнительной тематической навигацией.")
            Card(colors = CardDefaults.cardColors()) {
                Column {
                    Text("Важное примечание")
                    Text("Это историко-религиозный текст, а не современное медицинское руководство.")
                }
            }
            Text("Источники хадисов показываются только там, где они указаны в тексте книги. Степень достоверности здесь автоматически не присваивается.")
        }'''
        actual = remove_medical_notice(source)
        self.assertNotIn("Важное примечание", actual)
        self.assertNotIn("медицинское руководство", actual)
        self.assertIn("Здесь сохранён полный текст", actual)
        self.assertIn("Источники хадисов показываются", actual)
        self.assertEqual(actual.count("{"), actual.count("}"))

    def test_buttons_keep_click_handlers_but_lose_frame(self):
        source = '''OutlinedButton(onClick = { previous() }) { Text("Предыдущая") }
Button(onClick = { next() }) { Text("Следующая") }
FilledTonalButton(onClick = { speak() }) { Text("Слушать") }
SuggestionChip(onClick = { open() }, label = { Text("Вера") })'''
        out = flatten_controls(source)
        self.assertEqual(out.count("TextButton("), 3)
        self.assertNotIn("OutlinedButton(", out)
        self.assertNotIn("FilledTonalButton(", out)
        self.assertIn("SuggestionChip(", out)
        self.assertIn("border = null", out)
        for call in ("previous()", "next()", "speak()", "open()"):
            self.assertIn(call, out)

    def test_purple_literals_get_warm_color_but_neutral_text_unchanged(self):
        src = 'Color(0xFFE8DDF5) Color(0xFF8A6AB3) Color(0xFF352D27)'
        out = warm_purple_literals(src)
        self.assertNotIn('0xFFE8DDF5', out)
        self.assertNotIn('0xFF8A6AB3', out)
        self.assertIn('0xFF352D27', out)

    def test_new_version_integrity_and_no_faux_apk_release(self):
        builder=(ROOT/'scripts/build_iman_v457.py').read_text('utf-8')
        for name in ("build_v456", "versionCode 57", "0.45.7",
                     "preview457", "book.json", "quiz.json", "featured_quotes.json",
                     "131", "79", "NAV"):
            self.assertIn(name,builder)
        theme=(ROOT/'scripts/ImanUnifiedPaperV457.kt').read_text('utf-8')
        for key in ("secondaryContainer =", "tertiaryContainer =",
                    "onSurfaceVariant =", "outlineVariant ="):
            self.assertIn(key,theme)
        flow=(ROOT/'.github/workflows/build-iman-v457.yml').read_text('utf-8')
        self.assertIn('scripts.build_iman_v457 --dest AndroidApp',flow)
        self.assertIn('Publish installable APK',flow)
        self.assertIn('if: false  # Keep APK unpublished',flow)

if __name__ == '__main__':
    unittest.main()
