"""v0.19 regression checks: actual source-driven layout and safety guards."""
import unittest
from pathlib import Path
from scripts.build_iman_v19 import install_quote

ROOT = Path(__file__).resolve().parents[1]

class PremiumEditorialV19Tests(unittest.TestCase):
    def test_reminder_keeps_all_79_original_sources(self):
        header = "package x\nimport androidx.compose.foundation.clickable\n"
        header += "import androidx.compose.ui.graphics.Color\n"
        header += "private val imanExcerpts = listOf(\n"
        for i in range(79):
            header += 'FeaturedExcerpt("iman-chapter-%03d", "b%03d", "q"),\n' % (i,i)
        header += ")\n"
        old = header + "@Composable\ninternal fun ImanFeaturedQuoteCarousel(" + "previous implementation"
        implementation = (ROOT/"scripts/PremiumEditorialQuote.kt").read_text("utf-8")
        updated = install_quote(old, implementation)
        self.assertEqual(updated.count('FeaturedExcerpt("iman-chapter-'), 79)
        self.assertIn("Route.Reader(q.chapterId, q.blockId)", updated)
        self.assertIn("Text(\"Другая ↻\"", updated)
        self.assertIn("Brush.horizontalGradient", updated)

    def test_bad_or_missing_quote_inventory_rejected(self):
        implementation = (ROOT/"scripts/PremiumEditorialQuote.kt").read_text("utf-8")
        with self.assertRaises(RuntimeError):
            install_quote("unrelated source", implementation)

    def test_redesign_is_not_the_previous_empty_tile_layout(self):
        text = (ROOT/"scripts/PremiumEditorialHome.kt").read_text("utf-8")
        self.assertIn("heightIn(min = 76.dp)", text)
        self.assertIn("EditorialBookSection(", text)
        self.assertIn("EditorialResumeCard(", text)
        self.assertIn("ImanFeaturedQuoteCarousel(navigate)", text)
        self.assertIn("R.drawable.iman_v17_glossary", text)
        self.assertIn("Route.Bookmarks", text)
        self.assertIn("Route.CollectionDetail(entry.id)", text)
        self.assertNotIn('Text("Читать и размышлять."', text)
        self.assertNotIn("StandaloneBottomNav", text)
        self.assertNotIn("WebView(", text)
        self.assertNotIn("SepiaMiniStat(", text)

    def test_reminder_adapts_to_long_quotes_and_screen_width(self):
        code = (ROOT/"scripts/PremiumEditorialQuote.kt").read_text("utf-8")
        self.assertIn("maxLines = 4", code)
        self.assertIn("TextOverflow.Ellipsis", code)
        self.assertIn("ContentScale.Fit", code)
        self.assertIn("heightIn(min = 110.dp)", code)
        self.assertNotIn("ContentScale.FillBounds", code)
        self.assertIn("heightIn(min = 40.dp)", code)

if __name__ == "__main__":
    unittest.main()
