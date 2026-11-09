"""v0.39 home identity and consistent reminder presentation regression tests."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ImanV39PresentationTests(unittest.TestCase):
    def test_all_79_reminders_use_the_same_handwritten_font(self):
        q = (ROOT/"scripts/ReferenceQuoteV39.kt").read_text("utf-8")
        self.assertIn("fontFamily = ImanCaveatFont", q)
        self.assertNotIn("fontFamily = if (length", q)
        self.assertNotIn("WebLiterataFont", q)
        self.assertIn("Crossfade(", q)
        self.assertIn("Route.Reader(q.chapterId, q.blockId)", q)

    def test_embossed_relief_is_unconditional_even_in_dark_mode(self):
        q = (ROOT/"scripts/ReferenceQuoteV39.kt").read_text("utf-8")
        self.assertIn("R.drawable.iman_v39_relief", q)
        self.assertNotIn("if (showIllustration)", q)
        self.assertNotIn("q.text.length <= 155", q)
        self.assertNotIn("!isDark && q.text.length", q)
        self.assertIn("ImanQuoteAnimatedText(current, ink)", q)
        self.assertIn("ColorFilter.tint", q)
        self.assertNotIn("TextOverflow.Ellipsis", q)

    def test_header_and_launcher_are_both_replaced(self):
        h = (ROOT/"scripts/ReferenceHomeV39.kt").read_text("utf-8")
        b = (ROOT/"scripts/build_iman_v39.py").read_text("utf-8")
        self.assertIn("R.drawable.iman_v39_header", h)
        self.assertNotIn("R.drawable.medicine_launcher_book", h)
        self.assertIn("iman_v35_bookmarks.webp", b)
        self.assertIn("android:icon", b)
        self.assertIn("android:roundIcon", b)
        self.assertIn("mipmap-anydpi-v26", b)
        self.assertIn("iman_v39_launcher", b)

    def test_build_keeps_book_and_navigation(self):
        b=(ROOT/"scripts/build_iman_v39.py").read_text("utf-8")
        for token in ("build_v38(kit, dest)", "book_hashes", "reader_before", "NAV", "79",
                      "preview39", "R.drawable.iman_v39_relief"):
            self.assertIn(token, b)
        home = (ROOT/"scripts/ReferenceHomeV39.kt").read_text("utf-8")
        self.assertIn('EditorialBookSection("Заметки"', home)
        self.assertNotIn('EditorialBookSection("Закладки"', home)

if __name__ == "__main__":
    unittest.main()
