"""v0.22 exact reader-paper reuse and compact illustration regression checks."""
import unittest
from pathlib import Path

from scripts.build_iman_v22 import install_paper_quote, QUOTE_MARKER

ROOT = Path(__file__).resolve().parents[1]


class ReaderPaperV22Tests(unittest.TestCase):
    def test_home_uses_exact_light_reader_paper_not_synthetic_gradient(self):
        home = (ROOT / "scripts/ReadingPaperHomeV22.kt").read_text(encoding="utf-8")
        self.assertIn("R.drawable.reader_parchment_source", home)
        self.assertIn('readerPaperOverlay("light")', home)
        self.assertIn("ContentScale.FillBounds", home)
        self.assertIn("Modifier.matchParentSize()", home)
        self.assertNotIn("Brush.horizontalGradient", home)

    def test_reminder_has_antique_paper_and_no_right_hand_book_illustration(self):
        quote = (ROOT / "scripts/ReadingPaperQuoteV22.kt").read_text(encoding="utf-8")
        self.assertIn("R.drawable.reader_parchment_source", quote)
        self.assertIn("ContentScale.Crop", quote)
        self.assertNotIn("R.drawable.iman_v17_quote", quote)
        self.assertNotIn('readerPaperOverlay("light")', quote)
        self.assertIn("Crossfade(", quote)
        self.assertIn("tween(180)", quote)
        self.assertIn('Text("Другая ↻"', quote)
        self.assertIn("Route.Reader(q.chapterId, q.blockId)", quote)

    def test_library_has_small_soft_original_icons_and_all_routes(self):
        home = (ROOT / "scripts/ReadingPaperHomeV22.kt").read_text(encoding="utf-8")
        self.assertIn("width = 58.dp, height = 60.dp", home)
        self.assertIn("0.74f", home)
        for item in ("R.drawable.iman_v17_contents", "R.drawable.iman_v17_collections",
                     "R.drawable.iman_v17_glossary", "R.drawable.iman_v17_bookmarks",
                     "Route.Book", "Route.Collections", "Route.Glossary",
                     "Route.Bookmarks", "Route.Progress",
                     "Route.Reader(it.id, resume = last != null)"):
            self.assertIn(item, home)
        self.assertIn("heightIn(min = 78.dp)", home)

    def test_quote_replacement_preserves_79_source_entries_and_deep_link(self):
        original = (
            'FeaturedExcerpt("iman-chapter-007", "b1", "Original source"),\n' * 79
        )
        new_component = (ROOT / "scripts/ReadingPaperQuoteV22.kt").read_text("utf-8")
        result = install_paper_quote(original + QUOTE_MARKER + "old_body", new_component)
        self.assertEqual(result.count('FeaturedExcerpt("iman-chapter-'), 79)
        self.assertIn("Route.Reader(q.chapterId, q.blockId)", result)
        self.assertNotIn("old_body", result)

    def test_quote_replacement_fails_closed_if_inventory_mismatches(self):
        component = (ROOT / "scripts/ReadingPaperQuoteV22.kt").read_text("utf-8")
        with self.assertRaises(RuntimeError):
            install_paper_quote("unrecognized", component)
        with self.assertRaises(RuntimeError):
            install_paper_quote(
                'FeaturedExcerpt("iman-chapter-007", "b1", "excerpt"),\n' * 78
                + QUOTE_MARKER + "old_body", component
            )


if __name__ == "__main__":
    unittest.main()
