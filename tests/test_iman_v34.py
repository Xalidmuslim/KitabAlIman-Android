"""Reference v34: no more tiny illustrations, no navbar overlap regression."""
from pathlib import Path
import unittest
from scripts.iman_v28_scale import fill_artwork

ROOT=Path(__file__).resolve().parents[1]

class ReferenceFidelityV34(unittest.TestCase):
    def test_home_has_realistic_icons_not_oversized_blank_frames(self):
        home=(ROOT/"scripts/ReferenceHomeV34.kt").read_text("utf-8")
        self.assertIn("R.drawable.iman_v34_contents",home)
        self.assertIn("R.drawable.iman_v34_collections",home)
        self.assertIn("R.drawable.iman_v34_glossary",home)
        self.assertIn("R.drawable.iman_v34_bookmarks",home)
        self.assertIn("height(78.dp)",home)
        self.assertIn("book.collections.take(2)",home)
        self.assertIn("modifier.fillMaxSize().padding(bottom = 76.dp).clipToBounds()",home)
        self.assertNotIn(".statusBarsPadding()",home)
        self.assertNotIn("BorderStroke(",home)

    def test_hero_has_reference_scale_without_covering_full_text(self):
        quote=(ROOT/"scripts/ReferenceQuoteV34.kt").read_text("utf-8")
        self.assertIn("R.drawable.iman_v34_reminder",quote)
        self.assertIn("width(290.dp).height(183.dp)",quote)
        self.assertIn("Modifier.fillMaxWidth(0.62f)",quote)
        self.assertIn("q.text.length <= 120",quote)
        self.assertIn("maxLines = 5",quote)
        self.assertIn("Crossfade(",quote)
        self.assertIn("Route.Reader(q.chapterId, q.blockId)",quote)

    def test_new_build_preserves_original_reader_navigation_and_content(self):
        src=(ROOT/"scripts/build_iman_v34.py").read_text("utf-8")
        for term in (
            "build_v33(kit,dest)","app_before","reader_before","book_hashes",
            "nav_sha","R.drawable.iman_v29_unified_home","iman_v34_reminder",
            "applicationIdSuffix '.preview34'",
        ):
            self.assertIn(term,src)

if __name__=="__main__":
    unittest.main()
