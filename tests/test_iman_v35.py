"""v35: hero artwork is reference-scale, all content and bottom navigation preserved."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class ReferenceHeroV35(unittest.TestCase):
    def test_hero_does_not_cover_text_and_shares_one_paper(self):
        s=(ROOT/"scripts/ReferenceQuoteV35.kt").read_text("utf-8")
        self.assertIn("width(380.dp).height(240.dp)",s)
        self.assertIn("offset(x = 100.dp, y = 24.dp)",s)
        for required in ("Modifier.fillMaxWidth(0.62f)","q.text.length <= 120",
                         "maxLines = 5","Crossfade(","tween(180)",
                         "Route.Reader(q.chapterId, q.blockId)",
                         "R.drawable.iman_v34_reminder"):
            self.assertIn(required,s)
        self.assertNotIn("BorderStroke(",s)

    def test_build_fails_closed_on_book_and_user_data(self):
        s=(ROOT/"scripts/build_iman_v35.py").read_text("utf-8")
        for token in ("build_v34(kit,dest)","reader_before","app_before",
                      "book_hashes","nav_sha","R.drawable.iman_v29_unified_home",
                      "applicationIdSuffix '.preview35'"):
            self.assertIn(token,s)

if __name__=="__main__":
    unittest.main()
