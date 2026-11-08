"""v0.25 seamless single-canvas visual regression tests.

These tests protect the real routes and reader; intentionally fail until
Home/Quote/Shell v25 and 6 independent image assets are installed.
"""
from pathlib import Path
from PIL import Image
import hashlib
import unittest
from scripts.build_iman_v25 import patch_shell, install_v25_reminder, NAV, QUOTE_MARKER

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets/ui/v25"

class SeamlessPageV25Tests(unittest.TestCase):
    def test_distinct_true_generated_images_not_atlas_crops(self):
        files = [
            "unified_home.webp", "reminder.webp",
            "library_contents.webp", "library_collections.webp",
            "library_glossary.webp", "library_bookmarks.webp",
        ]
        digests = set()
        for filename in files:
            path = ASSETS / filename
            self.assertTrue(path.is_file(), filename)
            self.assertGreater(path.stat().st_size, 3000, filename)
            with Image.open(path) as im:
                self.assertGreaterEqual(im.width, 300 if filename == "unified_home.webp" else 250)
                if filename != "unified_home.webp":
                    self.assertEqual(im.mode, "RGBA", filename)
                    low, high = im.getchannel("A").getextrema()
                    self.assertLess(low, 30)
                    self.assertGreater(high, 225)
            digests.add(hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(len(digests), len(files))

    def test_single_fullscreen_canvas_in_app_shell(self):
        shell = (ROOT / "scripts/SeamlessShellPatchV25.kt").read_text("utf-8")
        self.assertIn("R.drawable.iman_v25_unified_home", shell)
        self.assertIn("Modifier.matchParentSize()", shell)
        self.assertIn("ContentScale.FillBounds", shell)
        self.assertIn("current == Route.Home", shell)
        self.assertIn("seamlessHome = seamlessHome", shell)
        self.assertIn("Color.Transparent", shell)

    def test_home_does_not_repaint_over_root_background(self):
        home = (ROOT / "scripts/SeamlessHomeV25.kt").read_text("utf-8")
        self.assertNotIn('readerPaperOverlay("light")', home)
        self.assertNotIn("R.drawable.reader_parchment_source", home)
        self.assertNotIn("Color(0xFFFCF8F3)", home.split("ModernEditorialHomeScreen(", 1)[-1])
        self.assertIn("Column(modifier.fillMaxSize())", home)
        self.assertIn('item(key = "library-four")', home)
        for icon in ("contents", "collections", "glossary", "bookmarks"):
            self.assertIn("R.drawable.iman_v25_" + icon, home)
        for route in (
            "Route.Book", "Route.Collections", "Route.Glossary", "Route.Bookmarks",
            "Route.Progress", "Route.Reader(it.id, resume = last != null)",
            "Route.CollectionDetail(entry.id)",
        ):
            self.assertIn(route, home)

    def test_reminder_art_does_not_overlap_text_and_retains_deep_link(self):
        quote = (ROOT / "scripts/SeamlessQuoteV25.kt").read_text("utf-8")
        self.assertIn("R.drawable.iman_v25_reminder", quote)
        self.assertIn("Row(", quote)
        self.assertIn("Modifier.weight(0.61f)", quote)
        self.assertIn("Modifier.weight(0.39f)", quote)
        self.assertIn("Crossfade(", quote)
        self.assertIn("tween(180)", quote)
        self.assertIn('Text("Другая ↻"', quote)
        self.assertIn("Route.Reader(q.chapterId, q.blockId)", quote)
        self.assertIn("maxLines = 5", quote)
        self.assertNotIn("R.drawable.iman_v24_reminder", quote)

    def test_shell_patch_fails_closed_for_unknown_native_app(self):
        with self.assertRaises(RuntimeError):
            patch_shell("unrecognized")

if __name__=="__main__":
    unittest.main()
