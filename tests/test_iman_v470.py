"""Regression: icon is a borderless parchment cutout on Home and in launcher."""
import base64
import hashlib
import io
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image
from scripts.build_iman_v470 import (
    SOURCE, DIGEST, read_approved, render_icons, compose_size_patch,
    native_paper_texture,
)

ROOT = Path(__file__).resolve().parents[1]


class BorderlessIconV470Tests(unittest.TestCase):
    def test_approved_foreground_exact_and_no_square_background(self):
        raw = base64.b64decode((ROOT / SOURCE).read_text("ascii").strip(), validate=True)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), DIGEST)
        art = read_approved(ROOT)
        self.assertEqual(art.size, (256, 256))
        self.assertEqual(art.mode, "RGBA")
        alpha = np.asarray(art.getchannel("A"))
        self.assertEqual(int(alpha[0].max()), 0)
        self.assertEqual(int(alpha[-1].max()), 0)
        self.assertEqual(int(alpha[:, 0].max()), 0)
        self.assertEqual(int(alpha[:, -1].max()), 0)
        self.assertGreater(int(alpha.max()), 225)

    def test_header_larger_without_touching_title_or_actions(self):
        source = '''Image(painter = painterResource(R.drawable.iman_v464_home_soft),
            contentDescription = null, modifier = Modifier.size(46.dp),
            contentScale = ContentScale.Fit)
        Spacer(Modifier.width(8.dp))
        Text("Книга Имана")'''
        updated = compose_size_patch(source)
        self.assertIn("Modifier.size(50.dp)", updated)
        self.assertIn('Spacer(Modifier.width(8.dp))', updated)
        self.assertIn('Text("Книга Имана")', updated)
        with self.assertRaises(RuntimeError):
            compose_size_patch(updated)

    def test_adaptive_legacy_and_header_share_original_3d_art(self):
        art = read_approved(ROOT)
        with tempfile.TemporaryDirectory() as d:
            paper = Path(d) / "native.webp"
            Image.new("RGB", (200, 250), (246, 236, 217)).save(paper, "WEBP", lossless=True)
            background, color = native_paper_texture(paper)
            self.assertEqual(background.size, (512, 512))
            header, adaptive, legacy = render_icons(art, background)
            self.assertEqual(header.size, (320, 320))
            self.assertEqual(header.mode, "RGBA")
            self.assertEqual(header.getchannel("A").getpixel((0, 0)), 0)
            self.assertEqual(adaptive.size, (512, 512))
            self.assertEqual(adaptive.mode, "RGBA")
            bbox = adaptive.getchannel("A").getbbox()
            self.assertTrue(all(78 <= x <= 435 for x in bbox), bbox)
            self.assertEqual(legacy.mode, "RGB")
            self.assertEqual(legacy.size, (512, 512))
            self.assertEqual(tuple(int(c) for c in color), (246,236,217))
            self.assertEqual(legacy.getpixel((0,0)), background.getpixel((0,0)))

    def test_preserves_book_and_quote_content_in_build(self):
        src = (ROOT / "scripts/build_iman_v470.py").read_text("utf-8")
        for token in ("build_v469(kit, dest)", "versionCode 70",
                      "versionName '0.46.10'", "preview470",
                      "book.json", "quiz.json", "featured_quotes.json",
                      "ImanQuoteCarousel.kt", "iman_v465_scroll.webp",
                      "iman_v470_launcher_background.webp",
                      "iman_v39_launcher_foreground.webp"):
            self.assertIn(token, src)


if __name__ == "__main__":
    unittest.main()
