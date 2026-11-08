"""v0.29 specification: reference-calibrated parchment, enlarged illustration,
two visible home topic previews and preserved source/book/navigation logic.
"""
import unittest
from pathlib import Path
from PIL import Image, ImageFilter, ImageStat
import numpy as np

ROOT=Path(__file__).resolve().parents[1]

class PixelReferenceV29(unittest.TestCase):
    def test_paper_is_real_embossed_pulp_not_smooth_or_pixel_noise(self):
        file=ROOT/"assets/ui/v29/iman_v29_unified_home.webp"
        self.assertTrue(file.is_file())
        with Image.open(file) as img:
            paper=img.convert("RGB")
            self.assertEqual(paper.size,(648,1152))
            c=paper.crop((150,750,485,830))
            signal=np.asarray(c,dtype=np.float32)-np.asarray(
                c.filter(ImageFilter.GaussianBlur(9)),dtype=np.float32)
            deviations=signal.std(axis=(0,1))
            self.assertGreater(float(deviations.min()),3.1)
            self.assertLess(float(deviations.max()),7.0)
            means=np.asarray(c).mean(axis=(0,1))
            self.assertTrue(235 < means[0] < 250)
            self.assertTrue(228 < means[1] < 245)
            self.assertTrue(209 < means[2] < 231)
            # Bottom wave must remain part of the same bitmap.
            self.assertGreater(np.asarray(paper.crop((0,1020,648,1080))).std(),3)

    def test_reminder_has_visual_space_but_text_must_not_be_overlapped(self):
        src=(ROOT/"scripts/ReferenceQuoteV29.kt").read_text("utf-8")
        self.assertIn("Modifier.weight(0.54f)",src)
        self.assertIn("Modifier.weight(0.46f)",src)
        self.assertIn("height(174.dp)",src)
        self.assertIn("q.text.length <= 120",src)
        self.assertIn("Crossfade(",src)
        self.assertIn("Route.Reader(q.chapterId, q.blockId)",src)
        self.assertIn("maxLines = 5",src)
        self.assertNotIn("R.drawable.iman_v17_quote",src)

    def test_reading_progress_and_library_compact_typography_remain_interactive(self):
        src=(ROOT/"scripts/ReferenceHomeV29.kt").read_text("utf-8")
        self.assertIn("book.collections.take(2)",src)
        self.assertIn("R.drawable.iman_v28_contents",src)
        self.assertIn("R.drawable.iman_v28_bookmarks",src)
        for route in ("Route.Book","Route.Collections","Route.Glossary","Route.Bookmarks",
                      "Route.Progress","Route.Reader(it.id, resume = last != null)",
                      "Route.CollectionDetail(entry.id)"):
            self.assertIn(route,src)
        self.assertIn("LinearProgressIndicator(",src)
        self.assertIn("color = Color.Transparent",src)

    def test_native_builder_does_not_edit_reader_or_user_state(self):
        src=(ROOT/"scripts/build_iman_v29.py").read_text("utf-8")
        for word in ("build_v28(kit,dest)","app_before","reader_before",
                     "book_hashes","protected_nav","NAV"):
            self.assertIn(word,src)
        self.assertIn("R.drawable.iman_v29_unified_home",src)
        self.assertIn("applicationIdSuffix '.preview29'",src)

if __name__=="__main__":
    unittest.main()
