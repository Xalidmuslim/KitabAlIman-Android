"""Visual reference #4: frameless book editor UI, handcrafted gallery icons, preserved paths."""
import unittest
from pathlib import Path
from scripts.build_iman_v23 import install_variant4_quote, QUOTE_MARKER, patch_nav_background, NAV

ROOT = Path(__file__).resolve().parents[1]

class EditorialReferenceV23Tests(unittest.TestCase):
    def test_frame_free_background_and_section_navigation(self):
        home=(ROOT/"scripts/EditorialVariant4HomeV23.kt").read_text("utf-8")
        self.assertIn("Color(0xFFFCF8F3)",home)
        self.assertNotIn("R.drawable.reader_parchment_source",home)
        self.assertNotIn("readerPaperOverlay(",home)
        self.assertIn("EditorialOrnamentDivider(",home)
        self.assertIn("EditorialBookSection(",home)
        for name in ("contents","collections","glossary","bookmarks"):
            self.assertIn("R.drawable.iman_v23_"+name,home)
        for route in ("Route.Book","Route.Collections","Route.Glossary",
                      "Route.Bookmarks","Route.Progress",
                      "Route.Reader(it.id, resume = last != null)",
                      "Route.CollectionDetail(entry.id)"):
            self.assertIn(route,home)
        self.assertNotIn("BorderStroke(",home)
        self.assertIn("shadowElevation = 0.dp",home)

    def test_quote_uses_page_background_without_illustration_or_tinted_block(self):
        quote=(ROOT/"scripts/EditorialVariant4QuoteV23.kt").read_text("utf-8")
        self.assertNotIn("reader_parchment_source",quote)
        self.assertNotIn("iman_v17_quote",quote)
        self.assertIn("Crossfade(",quote)
        self.assertIn("tween(180)",quote)
        self.assertIn('Text("Другая ↻"',quote)
        self.assertIn("Route.Reader(q.chapterId, q.blockId)",quote)
        self.assertIn("maxLines = 5",quote)
        self.assertIn("border = null",quote)

    def test_quote_install_refuses_changed_inventory(self):
        new=(ROOT/"scripts/EditorialVariant4QuoteV23.kt").read_text("utf-8")
        with self.assertRaises(RuntimeError):
            install_variant4_quote("broken",new)
        base='FeaturedExcerpt("iman-chapter-007", "b1", "source"),\n'*79
        result=install_variant4_quote(base+QUOTE_MARKER+"old_body",new)
        self.assertEqual(result.count('FeaturedExcerpt("iman-chapter-'),79)
        self.assertNotIn("old_body",result)

    def test_nav_background_only_not_tab_actions(self):
        snippet = "prefix " + NAV + "\n" + "val panelShape = RoundedCornerShape(0.dp)\n" + \
                  "Color(0xFFF7F3EC)\n" + \
                  "".join('NavItem("'+label+'", icon, selected, action)\n' for label in \
                          ("Главная", "Оглавление", "Поиск", "Закладки", "Ещё"))
        converted=patch_nav_background(snippet)
        self.assertIn('NavItem("Главная", icon, selected, action)',converted)
        self.assertIn("Color(0xFFFCF8F3)",converted)

    def test_artwork_bundle_present_and_not_blank(self):
        atlas=ROOT/"assets/ui/v23/iman_v23_library_atlas.b64"
        self.assertTrue(atlas.exists())
        import base64,io
        from PIL import Image
        image=Image.open(io.BytesIO(base64.b64decode(atlas.read_text("ascii").strip(),validate=True)))
        self.assertEqual(image.size,(320,80))
        self.assertEqual(image.mode,"RGB")
        for x in range(0,320,80):
            icon=image.crop((x,0,x+80,80)).convert("L")
            self.assertLess(icon.getextrema()[0],180)  # visible brown book illustration
            self.assertGreater(icon.getextrema()[1],240)  # pale seamless canvas

if __name__ == "__main__":
    unittest.main()
