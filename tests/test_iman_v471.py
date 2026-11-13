"""Regression: existing icon matches existing library colors without redrawing."""
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from scripts.build_iman_v470 import read_approved, render_icons
from scripts.build_iman_v471 import LIBRARY, QUANTILES, library_palette, harmonize_icon, _masks

ROOT = Path(__file__).resolve().parents[1]


def reference(color, shadow):
    im = Image.new("RGBA", (240, 180), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((22, 131, 224, 172), fill=(*shadow, 113))
    for i in range(4):
        tone = tuple(min(254, max(0, channel + (i - 2) * 11)) for channel in color)
        d.rounded_rectangle((24+i*8, 18+i*4, 200-i*3, 128+i*6), radius=8, fill=(*tone, 255))
    return im


class ExistingLibraryPaletteV471(unittest.TestCase):
    def test_existing_art_is_retinted_not_regenerated(self):
        art = read_approved(ROOT)
        old_bbox = art.getchannel("A").getbbox()
        references = [
            reference((166, 126, 89), (241, 225, 197)),
            reference((177, 137, 98), (239, 223, 196)),
            reference((171, 132, 95), (242, 227, 201)),
            reference((160, 124, 88), (244, 227, 197)),
        ]
        target, shadow_rgb, alpha = library_palette(references)
        self.assertEqual(target.shape, (len(QUANTILES), 3))
        self.assertGreater(float(alpha), 20)
        result, audit = harmonize_icon(art, references)
        self.assertEqual(result.size, art.size)
        self.assertEqual(result.getchannel("A").getbbox(), old_bbox)
        self.assertEqual(result.getchannel("A").getpixel((0,0)), 0)
        self.assertEqual(result.getchannel("A").getpixel((255,255)), 0)
        self.assertLess(audit["mean_rgb_error_after"], audit["mean_rgb_error_before"] * .82)

    def test_real_user_source_has_material_and_bottom_shadow(self):
        art = read_approved(ROOT)
        _, subject, shadow = _masks(art)
        self.assertGreater(int(subject.sum()), 500)
        self.assertGreater(int(shadow.sum()), 100)

    def test_launcher_still_respects_adaptive_mask_after_recolor(self):
        art = read_approved(ROOT)
        refs = [reference((164+i*5, 123+i*4, 86+i*3), (241,224,196)) for i in range(4)]
        matched, _ = harmonize_icon(art, refs)
        paper = Image.new("RGB", (512,512), (246,237,219))
        header, adaptive, legacy = render_icons(matched, paper)
        self.assertEqual(header.size, (320, 320))
        self.assertEqual(header.mode, "RGBA")
        self.assertEqual(adaptive.size, (512, 512))
        self.assertEqual(legacy.size, (512, 512))
        self.assertTrue(all(78 <= x <= 435 for x in adaptive.getchannel("A").getbbox()))

    def test_build_changes_only_existing_generated_icon_resources(self):
        source = (ROOT / "scripts/build_iman_v471.py").read_text("utf-8")
        for text in (
            "build_v470(kit, dest)", "read_approved(kit)", "LIBRARY",
            "iman_v35_contents.webp", "iman_v35_collections.webp",
            "iman_v35_glossary.webp", "iman_v38_notes.webp",
            "iman_v464_home_soft.webp", "iman_v39_launcher_foreground.webp",
            "iman_v39_launcher.webp", "iman_v465_scroll.webp",
            "book.json", "quiz.json", "featured_quotes.json",
            "versionCode 71", "versionName '0.46.11'", "preview471",
            "Modifier.size(50.dp)", "navigate(Route.Reader(q.chapterId, q.blockId))",
        ):
            self.assertIn(text, source)


if __name__ == "__main__":
    unittest.main()
