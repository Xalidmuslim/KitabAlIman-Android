"""v0.45.5: approved parchment ground relief; no image tiles or text overlap."""
from pathlib import Path
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


class ApprovedGroundReliefV455(unittest.TestCase):
    def test_ornament_dissolves_before_all_canvas_edges(self):
        from scripts.iman_v455_ground import make_ground, verify_ground
        rug = make_ground()
        self.assertTrue(verify_ground(rug))
        self.assertEqual(rug.size, (684, 496))
        alpha = np.asarray(rug.getchannel("A"))
        self.assertEqual(int(alpha[0].max()), 0)
        self.assertEqual(int(alpha[-1].max()), 0)
        self.assertEqual(int(alpha[:, 0].max()), 0)
        self.assertEqual(int(alpha[:, -1].max()), 0)
        self.assertGreater(int(alpha[360:475,40:180].max()), 8)

    def test_original_scroll_remains_separate_and_20_percent_reduced(self):
        q=(ROOT/"scripts/ReferenceQuoteV455.kt").read_text("utf-8")
        older=(ROOT/"scripts/ReferenceQuoteV453.kt").read_text("utf-8")
        for token in ("Modifier.weight(1f)", "ImanQuoteAnimatedText(current, ink, compactScreen)",
                      'preferences.edit().putInt("last_shown", current).apply()',
                      "navigate(Route.Reader(q.chapterId, q.blockId))"):
            self.assertIn(token,q)
            self.assertIn(token,older)
        for token in ("R.drawable.iman_v43_approved_scroll",
                      "R.drawable.iman_v455_ground_rug",
                      ".width(if (compactScreen) 80.dp else 99.dp)",
                      ".height(if (compactScreen) 86.dp else 103.dp)",
                      ".requiredWidth(if (compactScreen) 119.dp else 147.dp)",
                      "ContentScale.Fit", "ContentScale.FillBounds"):
            self.assertIn(token,q)
        self.assertIn("androidx.compose.foundation.layout.Box(",q)
        self.assertNotIn("TextOverflow.Ellipsis",q)
        self.assertNotIn("maxLines =",q)

    def test_no_other_composable_changes(self):
        new=(ROOT/"scripts/ReferenceQuoteV455.kt").read_text("utf-8")
        old=(ROOT/"scripts/ReferenceQuoteV453.kt").read_text("utf-8")
        start="                    Image(\n                        painter = MedicineHomeArtwork.painter(R.drawable.iman_v43_approved_scroll),"
        end="                }\n                HorizontalDivider("
        self.assertEqual(new.split(start)[0],old.split(start)[0])
        self.assertEqual(new.split(end)[1],old.split(end)[1])
        self.assertIn(end,new)

    def test_builder_guards_book_and_user_state(self):
        src=(ROOT/"scripts/build_iman_v455.py").read_text("utf-8")
        for token in ("build_v454(kit, dest)","versionName '0.45.5'",
                      "versionCode 55", "preview455", "book_hashes",
                      "original_scroll_hash", "131","79","NAV","protected",
                      "make_ground", "verify_ground"):
            self.assertIn(token,src)


if __name__=="__main__":
    unittest.main()
