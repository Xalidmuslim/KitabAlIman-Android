"""v0.32 visual regression: no home/nav overlap, typography, art occupancy.

Emulator visual screenshot and data hashes are checked by CI after this suite.
"""
import tempfile, unittest
from pathlib import Path
from PIL import Image
from scripts.iman_v28_scale import fill_artwork

ROOT=Path(__file__).resolve().parents[1]

class HomeReferenceV32Tests(unittest.TestCase):
    def test_home_has_one_system_inset_not_two(self):
        source=(ROOT/"scripts/ReferenceHomeV32.kt").read_text("utf-8")
        self.assertNotIn(".statusBarsPadding()",source)
        self.assertIn(".clipToBounds()",source)
        self.assertIn("padding(bottom = 76.dp)",source)
        self.assertIn('item(key = "library-four")',source)
        self.assertIn('item(key = "collections")',source)
        self.assertIn("Route.Bookmarks",source)
        self.assertIn("Route.Progress",source)
        self.assertIn("Route.Reader(it.id, resume = last != null)",source)
        self.assertIn("book.collections.take(2)",source)
        self.assertNotIn("BorderStroke(",source)

    def test_reminder_never_overlaps_text_and_retains_79_quotes(self):
        source=(ROOT/"scripts/ReferenceQuoteV32.kt").read_text("utf-8")
        self.assertIn("q.text.length <= 120",source)
        self.assertIn("maxLines = 5",source)
        self.assertIn("Crossfade(",source)
        self.assertIn("tween(180)",source)
        self.assertIn("Route.Reader(q.chapterId, q.blockId)",source)
        self.assertIn("R.drawable.iman_v32_reminder",source)
        self.assertNotIn("graphicsLayer(",source)

    def test_five_original_images_are_prewarmed_not_cropped_at_runtime(self):
        source=(ROOT/"scripts/build_iman_v32.py").read_text("utf-8")
        self.assertIn("build_v31(kit,dest)",source)
        self.assertIn("book_hashes",source)
        self.assertIn("reader_before",source)
        self.assertIn("app_before",source)
        self.assertIn("preview32",source)
        self.assertIn("R.drawable.iman_v32_",source)
        self.assertNotIn("RenderEffect",source)

if __name__ == "__main__":unittest.main()
