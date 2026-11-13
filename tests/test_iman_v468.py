"""Regression tests for the exact two approved user images in the Android build."""
import base64
import hashlib
import io
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from scripts.build_iman_v468 import (
    QUOTE_SOURCE, ICON_SOURCE, QUOTE_SHA256, ICON_SHA256,
    render_manuscript, render_launcher_assets,
)

ROOT = Path(__file__).resolve().parents[1]


class ApprovedImagePairV468Test(unittest.TestCase):
    def test_approved_sources_are_embedded_not_recreated(self):
        for path, expected in ((QUOTE_SOURCE, QUOTE_SHA256), (ICON_SOURCE, ICON_SHA256)):
            payload = base64.b64decode((ROOT / path).read_text("ascii").strip(), validate=True)
            self.assertEqual(hashlib.sha256(payload).hexdigest(), expected)
            with Image.open(io.BytesIO(payload)) as im:
                self.assertEqual(im.format, "WEBP")

    def test_transparent_seamless_manuscript_preserves_3d_detail(self):
        source = base64.b64decode((ROOT / QUOTE_SOURCE).read_text("ascii"))
        with Image.open(io.BytesIO(source)) as src:
            result = render_manuscript(src)
        self.assertEqual(result.size, (256, 222))
        self.assertEqual(result.mode, "RGBA")
        a = np.asarray(result.getchannel("A"))
        self.assertEqual(int(a[0].max()), 0)
        self.assertEqual(int(a[-1].max()), 0)
        self.assertEqual(int(a[:, 0].max()), 0)
        self.assertEqual(int(a[:, -1].max()), 0)
        self.assertGreater(int(a.max()), 195)
        self.assertLess(int(a[105, 1]), 15)

    def test_adaptive_launcher_safe_zone_and_header_use_same_art(self):
        source = base64.b64decode((ROOT / ICON_SOURCE).read_text("ascii"))
        with Image.open(io.BytesIO(source)) as src:
            header, adaptive, legacy = render_launcher_assets(src)
        self.assertEqual(header.size, (320, 320))
        self.assertEqual(adaptive.size, (512, 512))
        self.assertEqual(legacy.size, (512, 512))
        self.assertEqual(header.mode, "RGBA")
        self.assertEqual(adaptive.getchannel("A").getextrema()[0], 0)
        self.assertEqual(legacy.mode, "RGB")
        bbox = adaptive.getchannel("A").getbbox()
        self.assertTrue(all(78 <= n <= 438 for n in bbox))
        self.assertGreater(header.getchannel("A").getextrema()[1], 200)

    def test_built_from_v467_without_touching_reading_or_routes(self):
        script = (ROOT / "scripts/build_iman_v468.py").read_text("utf-8")
        for marker in (
            "build_v467(kit, dest)", "versionCode 68", "versionName '0.46.8'",
            "preview468", "ImanQuoteCarousel.kt", "book.json", "quiz.json",
            "featured_quotes.json", "ImanV38More.kt", "iman_v39_launcher_foreground.webp",
            "iman_v464_home_soft.webp", "iman_v465_scroll.webp",
        ):
            self.assertIn(marker, script)


if __name__ == "__main__":
    unittest.main()
