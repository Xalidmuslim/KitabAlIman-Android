"""Test-driven constraints for v0.20 user-reported visual regression."""
import unittest
from pathlib import Path
from scripts.build_iman_v20 import patch_quote,QUOTE
ROOT=Path(__file__).resolve().parents[1]

class BookDashboardV20Tests(unittest.TestCase):
    def test_quote_inventory_and_deep_link_preserved(self):
        original='FeaturedExcerpt("iman-chapter-000", "b0", "example"),\n'*79
        before='package foo\n'+original+QUOTE+"old code"
        implementation=(ROOT/"scripts/ArtDirectedQuoteV20.kt").read_text("utf-8")
        changed=patch_quote(before,implementation)
        self.assertEqual(changed.count('FeaturedExcerpt("iman-chapter-'),79)
        self.assertIn("Route.Reader(q.chapterId, q.blockId)",changed)
        self.assertIn("Crossfade(",changed)
        self.assertIn('Text("Другая ↻"',changed)
        self.assertNotIn("old code",changed)

    def test_fail_closed_for_unrecognized_quote_source(self):
        with self.assertRaises(RuntimeError):
            patch_quote("unknown version", "new component")

    def test_compact_sections_with_matched_illustrations(self):
        text=(ROOT/"scripts/ArtDirectedHomeV20.kt").read_text("utf-8")
        for item in ("Route.Book","Route.Collections","Route.Glossary",
                     "Route.Bookmarks","Route.Progress",
                     "R.drawable.iman_v17_contents",
                     "R.drawable.iman_v17_collections",
                     "R.drawable.iman_v17_glossary",
                     "R.drawable.iman_v17_bookmarks"):
            self.assertIn(item,text)
        self.assertIn("Brush.horizontalGradient",text)
        self.assertIn("heightIn(min = 88.dp)",text)
        self.assertIn("width = 70.dp, height = 74.dp",text)
        self.assertNotIn("StandaloneBottomNav(",text)
        self.assertNotIn("WebView(",text)

    def test_reminder_avoids_overlap_and_still_opens_quote(self):
        text=(ROOT/"scripts/ArtDirectedQuoteV20.kt").read_text("utf-8")
        self.assertIn("Crossfade(",text)
        self.assertIn("heightIn(min = 118.dp)",text)
        self.assertIn("maxLines = 5",text)
        self.assertIn("ContentScale.Fit",text)
        self.assertIn("Route.Reader(q.chapterId, q.blockId)",text)
        self.assertNotIn("ContentScale.FillBounds",text)

if __name__=="__main__":
    unittest.main()
