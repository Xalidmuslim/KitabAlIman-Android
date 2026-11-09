"""Regression contracts for the user-approved compact scroll and quill (v0.43)."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ApprovedV43Artwork(unittest.TestCase):
    def test_real_asset_not_a_generated_screen_mockup(self):
        from PIL import Image
        art = ROOT / "assets/ui/v43/iman_v43_approved_scroll_inkwell_quill.webp"
        self.assertTrue(art.exists(), "Approved transparent source image must be committed")
        self.assertGreater(art.stat().st_size, 3000)
        with Image.open(art) as image:
            self.assertEqual(image.mode, "RGBA")
            width, height = image.size
            self.assertGreater(height / width, 0.83)
            self.assertLess(height / width, 1.12)
            self.assertEqual(image.getpixel((0, 0))[3], 0)
            self.assertGreater(image.getchannel("A").getextrema()[1], 220)

    def test_ratio_does_not_stretch_and_illustration_is_right_aligned(self):
        source = (ROOT / "scripts/ReferenceQuoteV43.kt").read_text("utf-8")
        self.assertIn("R.drawable.iman_v43_approved_scroll", source)
        self.assertNotIn("R.drawable.iman_v42_manuscript_qalam", source)
        self.assertIn(".align(Alignment.BottomEnd)", source)
        self.assertIn("ContentScale.Fit", source)
        self.assertIn(".width(148.dp).height(137.dp)", source)
        self.assertIn(".offset(x = 9.dp", source)
        self.assertIn("ImanQuoteAnimatedText(current, ink)", source)
        self.assertIn("fontFamily = ImanCaveatFont", source)
        self.assertNotIn("TextOverflow.Ellipsis", source)

    def test_build_keeps_all_existing_book_state_and_stats(self):
        b = (ROOT / "scripts/build_iman_v43.py").read_text("utf-8")
        for key in (
            "build_v42(kit, dest)", "preview43",
            "assets/ui/v43/iman_v43_approved_scroll_inkwell_quill.webp",
            "book_hashes", "reader_before", "NAV", "Route.Notes",
            "Route.Hadiths", "ReadingStatisticsV36.kt", "79", "131",
        ):
            self.assertIn(key, b)
        self.assertIn("R.drawable.iman_v43_approved_scroll", b)
        self.assertIn("imam"[:0] + "ImanFeaturedQuoteCarousel", b)

if __name__ == "__main__":
    unittest.main()
