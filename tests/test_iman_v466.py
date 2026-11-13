"""Regression tests for one matte palette across Home icon, reminder and launcher."""
import hashlib
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from scripts.build_iman_v466 import (
    LIBRARY, adjust_color, contact_shadow, feather_edges, prepare_style,
    reference_brown
)


def fake_art(size, color, boundary=(.20, .16, .80, .85)):
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    x, y = size
    ImageDraw.Draw(im).rounded_rectangle(
        (round(x * boundary[0]), round(y * boundary[1]),
         round(x * boundary[2]), round(y * boundary[3])),
        radius=10, fill=color,
    )
    return im


class UnifiedMattePaletteV466(unittest.TestCase):
    def test_sepia_tone_moves_towards_library_reference(self):
        original = fake_art((128, 100), (221, 175, 112, 255))
        target = np.array([157, 124, 91], dtype=np.float32)
        result = adjust_color(original, target, .83)
        def mean_opaque(im):
            rgba = np.asarray(im, dtype=np.uint8)
            return np.median(rgba[:, :, :3][rgba[:, :, 3] > 100], axis=0)
        self.assertLess(
            np.linalg.norm(mean_opaque(result) - target),
            np.linalg.norm(mean_opaque(original) - target),
        )

    def test_reminder_edges_feather_not_rectangular(self):
        raw = Image.new("RGBA", (256, 225), (207, 157, 97, 250))
        feathered = feather_edges(raw)
        alpha = np.asarray(feathered.getchannel("A"))
        self.assertEqual(int(alpha[0, :].max()), 0)
        self.assertEqual(int(alpha[:, 0].max()), 0)
        self.assertEqual(int(alpha[-1, :].max()), 0)
        self.assertGreater(int(alpha[112, 128]), 240)
        depth = contact_shadow(feathered, .12, 5, 3)
        self.assertEqual(depth.size, raw.size)

    def test_generated_all_three_art_resources_preserve_library(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "app/src/main/res"
            draw = root / "drawable-nodpi"
            draw.mkdir(parents=True)
            (root / "mipmap-anydpi").mkdir()
            for name in LIBRARY:
                fake_art((100, 96), (158, 123, 89, 255)).save(draw / name, "WEBP", lossless=True)
            fake_art((320, 320), (164, 137, 105, 255)).save(
                draw / "iman_v463_header.webp", "WEBP", lossless=True
            )
            fake_art((320, 320), (204, 181, 149, 190)).save(
                draw / "iman_v464_home_soft.webp", "WEBP", lossless=True
            )
            # Expose the old harsh colored rectangle to the new edge treatment.
            Image.new("RGBA", (256, 225), (216, 175, 114, 255)).save(
                draw / "iman_v465_scroll.webp", "WEBP", lossless=True
            )
            fake_art((512, 512), (173, 143, 114, 255)).save(
                draw / "iman_v39_launcher_foreground.webp", "WEBP", lossless=True
            )
            Image.new("RGB", (200, 200), (240, 229, 209)).save(
                draw / "iman_v38_flat_paper.webp", "WEBP"
            )
            before = {name: hashlib.sha256((draw / name).read_bytes()).hexdigest()
                      for name in LIBRARY}
            self.assertTrue(reference_brown(draw)[0] > reference_brown(draw)[1])
            prepare_style(Path(d))
            after = {name: hashlib.sha256((draw / name).read_bytes()).hexdigest()
                     for name in LIBRARY}
            self.assertEqual(before, after)
            with Image.open(draw / "iman_v464_home_soft.webp") as home:
                self.assertEqual(home.size, (320, 320))
                self.assertEqual(home.mode, "RGBA")
                self.assertGreater(home.getchannel("A").getextrema()[1], 170)
            with Image.open(draw / "iman_v465_scroll.webp") as rem:
                a = np.asarray(rem.getchannel("A"))
                self.assertEqual(int(a[0, :].max()), 0)
                self.assertGreater(int(a[112, 128]), 100)
            with Image.open(draw / "iman_v39_launcher_foreground.webp") as icon:
                self.assertEqual(icon.size, (512, 512))
                self.assertEqual(icon.mode, "RGBA")
            with Image.open(root / "mipmap-anydpi/iman_v39_launcher.webp") as icon:
                self.assertEqual(icon.size, (512, 512))
                self.assertEqual(icon.mode, "RGB")

    def test_version_keeps_v465_book_and_navigation_untouched(self):
        src = (Path(__file__).resolve().parents[1] / "scripts/build_iman_v466.py").read_text("utf-8")
        for line in (
            "build_v465(kit, dest)",
            "versionCode 66", "versionName '0.46.6'",
            "app/src/main/assets", "ImanQuoteCarousel.kt", "Reader.kt",
            "iman_v35_contents.webp", "iman_v465_scroll.webp",
            "iman_v39_launcher_foreground.webp",
        ):
            self.assertIn(line, src)


if __name__ == "__main__":
    unittest.main()
