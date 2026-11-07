"""v0.16 source excerpts, compact cards, single-row TTS and nav regression."""
import unittest
from pathlib import Path
from scripts.build_iman_v16 import (
    HOME_LINK,COLLECTION_LINK,load_curated_quotes,
    build_quote_source,patch_home_style,kotlin_literal
)
ROOT=Path(__file__).resolve().parents[1]
class V16Tests(unittest.TestCase):
    def test_curated_excerpt_inventory(self):
        rows=(ROOT/"scripts/v16_curated_keys.txt").read_text("utf-8").splitlines()
        self.assertEqual(len(rows),79)
        self.assertEqual(len(set(rows)),79)
        self.assertTrue(all("|" in x for x in rows))
    def test_cards_are_smaller_and_icon_background_transparent(self):
        self.assertIn("heightIn(min = 81.dp)",HOME_LINK)
        self.assertIn("width = 76.dp, height = 65.dp",HOME_LINK)
        self.assertIn("ContentScale.Fit",HOME_LINK)
        self.assertIn("heightIn(min = 86.dp)",COLLECTION_LINK)
        self.assertIn("collection.chapterIds.size.toString()",COLLECTION_LINK)
    def test_audio_controls_one_row_and_no_install_banner(self):
        player=(ROOT/"scripts/v16_reader_player.kt").read_text("utf-8")
        for action in ("active.play(chapter)","controller?.pause()","controller?.stop()",
                       "controller?.cycleRate()","RUVOICE_ENGINE_PACKAGE","BorderStroke(0.8.dp"):
            self.assertIn(action,player)
        self.assertNotIn("Бесплатный нейроголос",player)
        self.assertNotIn('Text("ОЗВУЧИВАНИЕ ГЛАВЫ"',player)
    def test_data_regression_checks(self):
        self.assertIn(r"\$",kotlin_literal("balance $x"))
        with self.assertRaises(RuntimeError):build_quote_source("invalid",[])
        with self.assertRaises(RuntimeError):patch_home_style("invalid")
        with self.assertRaises(RuntimeError):
            load_curated_quotes({"chapters":[]},
                (ROOT/"scripts/v16_curated_keys.txt").read_text("utf-8"),
                (ROOT/"scripts/ImanQuoteCarousel.kt").read_text("utf-8"))
if __name__=="__main__":unittest.main()
