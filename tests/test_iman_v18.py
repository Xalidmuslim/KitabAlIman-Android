import unittest
from pathlib import Path
from scripts.build_iman_v18 import patch_style,patch_quote,START,END
ROOT=Path(__file__).resolve().parents[1]

class ModernEditorialTests(unittest.TestCase):
    def test_only_home_replaced_without_impacting_toc(self):
        original="PRE\n"+START+" \nBIG OLD HOME\n}\n"+END+"TOC\n"
        result=patch_style(original)
        self.assertNotIn("BIG OLD HOME",result)
        self.assertIn("ModernEditorialHomeScreen",result)
        self.assertEqual(original.split(END,1)[1],result.split(END,1)[1])

    def test_fail_closed_on_unknown_source(self):
        with self.assertRaises(RuntimeError):patch_style("new file")
        with self.assertRaises(RuntimeError):patch_quote("new file")

    def test_home_preserves_routes_and_eliminates_duplicate_blocks(self):
        code=(ROOT/"scripts/ModernEditorialHome.kt").read_text("utf-8")
        for anchor in ("ImanFeaturedQuoteCarousel(navigate)","EditorialReadingCard",
                       "Route.Reader(it.id,resume=last!=null)","Route.Progress",
                       "Route.Book","Route.Glossary","Route.Bookmarks",
                       "Route.CollectionDetail(collection.id)"):
            self.assertIn(anchor,code)
        self.assertNotIn('Text("Читать и размышлять."',code)
        self.assertNotIn("SepiaMiniStat(",code)
        self.assertNotIn("StandaloneBottomNav(",code)
        self.assertNotIn("WebView(",code)

    def test_card_heights_and_accessibility(self):
        code=(ROOT/"scripts/ModernEditorialHome.kt").read_text("utf-8")
        self.assertIn("heightIn(min=90.dp)",code)
        self.assertIn("heightIn(min=44.dp)",code)
        self.assertIn("drawStopIndicator={}",code)
if __name__=="__main__":unittest.main()
