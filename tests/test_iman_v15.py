"""Regression tests for exact approved background and working quote rotation."""
import hashlib
import unittest
from pathlib import Path
from PIL import Image
from scripts.build_iman_v15 import validate_card_source, ART_SHA256, ART_SIZE

ROOT=Path(__file__).resolve().parents[1]

class V15QuoteBackgroundTests(unittest.TestCase):
    def test_approved_webp_dimensions_and_checksum(self):
        image = ROOT/"assets/ui/iman_quote_v15.webp"
        self.assertTrue(image.is_file())
        self.assertEqual(hashlib.sha256(image.read_bytes()).hexdigest(),ART_SHA256)
        with Image.open(image) as opened:
            self.assertEqual(opened.format,"WEBP")
            self.assertEqual(opened.size,ART_SIZE)

    def test_source_card_has_new_background_and_preserves_actions(self):
        source = (ROOT/"scripts/ImanQuoteCarousel.kt").read_text("utf-8")
        validate_card_source(source)
        self.assertNotIn("R.drawable.iman_quote_background",source)
        self.assertIn('prefs.edit().putInt("last_shown", current).apply()',source)
        self.assertIn('Route.Reader(q.chapterId, q.blockId)',source)

    def test_fail_closed_on_wrong_quote_switch_layout(self):
        source = (ROOT/"scripts/ImanQuoteCarousel.kt").read_text("utf-8")
        with self.assertRaises(RuntimeError):
            validate_card_source(source.replace('R.drawable.iman_quote_v15','R.drawable.other'))
        with self.assertRaises(RuntimeError):
            validate_card_source(source.replace('Text("Другая ↻"','Text("Другая ↻"')*2)

if __name__=="__main__":
    unittest.main()
