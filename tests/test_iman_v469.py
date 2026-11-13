"""Checks that latest user-approved Kitab-al-Iman icon blends into real parchment."""
import base64
import hashlib
import io
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from scripts.build_iman_v469 import (
    ICON_V469, SHA256_ICON, render_matching_icon, parchment_color, sample_icon
)

ROOT = Path(__file__).resolve().parents[1]


class LatestIconPaperMatch469(unittest.TestCase):
    def test_exact_user_approved_icon_source_and_ink(self):
        payload = base64.b64decode((ROOT / ICON_V469).read_text("ascii").strip(), validate=True)
        self.assertEqual(hashlib.sha256(payload).hexdigest(), SHA256_ICON)
        with Image.open(io.BytesIO(payload)) as im:
            self.assertEqual(im.format, "WEBP")
            self.assertEqual(im.size, (256, 256))

    def test_parchment_uses_real_page_paper_not_old_flat_color(self):
        with tempfile.TemporaryDirectory() as d:
            res = Path(d)
            (res / "drawable-nodpi").mkdir()
            paper = Image.new("RGB", (320, 320), (247, 239, 221))
            paper.save(res / "drawable-nodpi/iman_v38_flat_paper.webp", lossless=True)
            color = parchment_color(res)
            self.assertTrue(all(abs(c-t)<=2 for c,t in zip(color, (247,239,221))))

    def test_header_edges_transparent_and_launcher_safe(self):
        rgb = Image.new("RGB", (256,256), (237, 216, 186))
        header, adaptive, legacy = render_matching_icon(rgb, (247,239,221))
        self.assertEqual(header.size, (320,320))
        self.assertEqual(header.getchannel("A").getpixel((0,0)),0)
        self.assertEqual(header.getchannel("A").getpixel((319,319)),0)
        self.assertGreater(header.getchannel("A").getpixel((160,160)),240)
        self.assertEqual(adaptive.size, (512,512))
        bounds=adaptive.getchannel("A").getbbox()
        self.assertTrue(all(78<=n<=435 for n in bounds),bounds)
        self.assertEqual(legacy.size, (512,512))
        self.assertEqual(legacy.mode, "RGB")
        self.assertTrue(all(abs(x-y)<=3 for x,y in zip(legacy.getpixel((0,0)), (247,239,221))))

    def test_book_code_and_reminder_still_unchanged(self):
        script=(ROOT/"scripts/build_iman_v469.py").read_text("utf-8")
        for needle in ("build_v468(kit, dest)","featured_quotes.json","book.json",
                       "quiz.json","ImanQuoteCarousel.kt","iman_v465_scroll.webp",
                       "versionCode 69", "versionName '0.46.9'",
                       "preview469","iman_v39_icon_colors.xml"):
            self.assertIn(needle,script)


if __name__=="__main__":
    unittest.main()
