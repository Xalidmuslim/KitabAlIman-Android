"""v0.45.3: contact shadow matches the library without touching reminder layout."""
from pathlib import Path
import unittest
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]


class V453ShadowTests(unittest.TestCase):
    def test_new_contact_shadow_is_below_scroll_and_keeps_opaque_pixels(self):
        from scripts.iman_v453_contact_shadow import add_contact_shadow
        original=Image.new("RGBA",(256,256),(0,0,0,0))
        d=ImageDraw.Draw(original)
        d.ellipse((45,136,212,219),fill=(181,149,107,255))
        d.polygon([(152,145),(179,22),(185,31),(172,157)],fill=(183,154,120,255))
        result=add_contact_shadow(original)
        self.assertEqual(result.size,(256,287))
        self.assertEqual(result.getpixel((80,165)),original.getpixel((80,165)))
        self.assertGreater(result.getpixel((127,229))[3],original.getpixel((127,229))[3])
        self.assertEqual(result.getpixel((0,0))[3],0)
        self.assertEqual(result.getpixel((0,286))[3],0)
        self.assertEqual(result.getpixel((255,286))[3],0)

    def test_shadow_does_not_add_rectangular_background(self):
        from scripts.iman_v453_contact_shadow import add_contact_shadow
        original=Image.new("RGBA",(320,320),(0,0,0,0))
        ImageDraw.Draw(original).ellipse((72,125,240,245),fill=(160,120,80,255))
        result=add_contact_shadow(original)
        self.assertEqual(result.size,(320,358))
        for point in ((0,0),(319,0),(0,357),(319,357),(18,180),(290,180)):
            self.assertEqual(result.getpixel(point)[3],0,point)
        self.assertGreater(result.getpixel((160,255))[3],0)

    def test_only_drawable_and_version_change(self):
        source=(ROOT/"scripts/build_iman_v453.py").read_text("utf-8")
        for anchor in ("build_v452(kit, dest)", "preview453", "versionName '0.45.3'",
                       "versionCode 53", "add_contact_shadow", "book_hashes",
                       "protected", "NAV", "131", "79"):
            self.assertIn(anchor,source)
        shadow=(ROOT/"scripts/iman_v453_contact_shadow.py").read_text("utf-8")
        self.assertIn("GaussianBlur",shadow)
        self.assertIn("Image.new",shadow)
        self.assertIn("Image.alpha_composite",shadow)
        self.assertIn("RGBA",shadow)

    def test_existing_20_percent_size_and_text_wrap_are_unchanged(self):
        quote=(ROOT/"scripts/ReferenceQuoteV452.kt").read_text("utf-8")
        self.assertIn(".width(if (compactScreen) 80.dp else 99.dp)",quote)
        self.assertIn(".height(if (compactScreen) 78.dp else 94.dp)",quote)
        updated=(ROOT/"scripts/ReferenceQuoteV453.kt").read_text("utf-8")
        self.assertIn(".height(if (compactScreen) 86.dp else 103.dp)",updated)
        self.assertIn(".width(if (compactScreen) 80.dp else 99.dp)",updated)
        self.assertIn("Modifier.weight(1f)",quote)
        self.assertIn("ImanQuoteAnimatedText(current, ink, compactScreen)",quote)
        self.assertNotIn("TextOverflow.Ellipsis",quote)
        self.assertNotIn("maxLines =",quote)


if __name__=="__main__":
    unittest.main()
