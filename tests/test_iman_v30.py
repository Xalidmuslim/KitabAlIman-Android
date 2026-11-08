"""v0.30 screenshot-driven correction after REAL emulator v29 comparison.

Reference aligned at 432x768 (allow Android status bar insets).
The proof of bug is excessive vertical quote height and narrow hero artwork.
"""
from pathlib import Path
import unittest
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]

class AlignmentV30Tests(unittest.TestCase):
    def test_quote_no_longer_allocates_174dp_for_width_limited_image(self):
        q=(ROOT/"scripts/ReferenceQuoteV30.kt").read_text("utf-8")
        self.assertIn("Box(",q)
        self.assertIn("height(120.dp)",q)
        self.assertIn("width(220.dp).height(142.dp)",q)
        self.assertIn("Alignment.BottomEnd",q)
        self.assertIn("fillMaxWidth(0.66f)",q)
        self.assertIn("q.text.length <= 120",q)
        for anchor in ("Crossfade(", "tween(180)", "maxLines = 5",
                       "Route.Reader(q.chapterId, q.blockId)", 'Text("Другая ↻"'):
            self.assertIn(anchor,q)
        self.assertNotIn("Modifier.weight(0.46f)",q)

    def test_main_page_removes_extra_vertical_spacing_and_keeps_routes(self):
        s=(ROOT/"scripts/ReferenceHomeV30.kt").read_text("utf-8")
        self.assertIn("bottom = 0.dp",s)
        self.assertIn("verticalArrangement = Arrangement.spacedBy(3.dp)",s)
        self.assertIn("heightIn(min = 28.dp)",s)
        self.assertIn("book.collections.take(2)",s)
        self.assertIn("LinearProgressIndicator(",s)
        for nav in ("Route.Book","Route.Collections","Route.Glossary",
                    "Route.Bookmarks","Route.Progress","Route.Reader(it.id, resume = last != null)",
                    "Route.CollectionDetail(entry.id)"):
            self.assertIn(nav,s)
        self.assertIn("color = Color.Transparent",s)

    def test_hero_reframing_preserves_alpha_not_rectangle(self):
        from scripts.iman_v28_scale import fill_artwork
        source=ROOT/"assets/ui/v27/iman_v27_reminder.webp"
        with Image.open(source) as im:
            original=im.convert("RGBA")
        converted=fill_artwork(original,pad=0.0)
        self.assertEqual(converted.size,original.size)
        self.assertEqual(converted.getpixel((0,0))[3],0)
        self.assertGreater(converted.getchannel("A").getbbox()[2],300)

    def test_native_builder_preserves_user_book_state_and_real_wallpaper(self):
        b=(ROOT/"scripts/build_iman_v30.py").read_text("utf-8")
        for s in ("build_v29(kit,dest)","book_hashes","reader_before",
                  "app_before","protected_nav","iman_v29_unified_home",
                  "applicationIdSuffix '.preview30'"):
            self.assertIn(s,b)
        self.assertNotIn("RenderEffect",b)

if __name__=="__main__": unittest.main()
