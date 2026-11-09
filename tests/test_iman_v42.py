"""V42 contract: a dedicated manuscript and reed pen replaces all old reminder art."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class ManuscriptQalamV42(unittest.TestCase):
    def test_new_art_replaces_relief_everywhere_in_featured_reminder(self):
        quote=(ROOT/"scripts/ReferenceQuoteV42.kt").read_text("utf-8")
        self.assertIn("R.drawable.iman_v42_manuscript_qalam",quote)
        self.assertNotIn("R.drawable.iman_v41_engraving",quote)
        self.assertNotIn("showIllustration",quote)
        self.assertIn("ImanQuoteAnimatedText(current, ink)",quote)
        self.assertIn("fontFamily = ImanCaveatFont",quote)
        self.assertIn("Route.Reader(q.chapterId, q.blockId)",quote)

    def test_right_aligned_asset_preserves_text(self):
        quote=(ROOT/"scripts/ReferenceQuoteV42.kt").read_text("utf-8")
        self.assertIn(".align(Alignment.BottomEnd)",quote)
        self.assertIn(".offset(x = 18.dp",quote)
        self.assertIn("q.text.length > 125",quote)
        self.assertIn("ContentScale.Fit",quote)
        self.assertNotIn("TextOverflow.Ellipsis",quote)

    def test_webp_has_transparency_and_manuscript_art(self):
        art=ROOT/"assets/ui/v42/iman_v42_manuscript_qalam.webp"
        self.assertTrue(art.is_file() and art.stat().st_size > 1000)
        from PIL import Image
        with Image.open(art) as image:
            self.assertEqual(image.mode,"RGBA")
            self.assertGreater(image.getchannel("A").getextrema()[1],90)
            self.assertLess(image.getchannel("A").getbbox()[0], image.size[0] - 80)
            self.assertEqual(image.getpixel((0,0))[3],0)

    def test_build_preserves_reader_statistics_and_notes(self):
        b=(ROOT/"scripts/build_iman_v42.py").read_text("utf-8")
        for token in ("build_v41(kit, dest)", "preview42", "book_hashes",
                      "reader_before", "NAV", "79", "131", "Route.Notes",
                      "Route.Hadiths", "ReadingStatisticsV36.kt"):
            self.assertIn(token,b)
        h=(ROOT/"scripts/ReferenceHomeV41.kt").read_text("utf-8")
        self.assertIn('EditorialBookSection("Хадисы", "Источники",',h)

if __name__=="__main__":
    unittest.main()
