"""v0.45.4 regression: no rectangular clipped shadow in reminder artwork."""
from pathlib import Path
import unittest
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


class ClippedShadowRegressionV454(unittest.TestCase):
    def make_art(self):
        art = Image.new("RGBA", (120, 111), (0, 0, 0, 0))
        draw = ImageDraw.Draw(art)
        draw.ellipse((18, 58, 102, 107), fill=(169, 127, 88, 255))
        draw.polygon([(65, 64), (95, 5), (99, 11), (73, 72)], fill=(191, 153, 113, 255))
        return art

    def test_contact_shadow_never_touches_image_edges(self):
        from scripts.iman_v454_bounded_shadow import add_contact_shadow
        art = self.make_art()
        after = add_contact_shadow(art)
        self.assertEqual(after.size, (120, 124))
        old = np.asarray(art.getchannel("A"))
        alpha = np.asarray(after.getchannel("A"))
        self.assertEqual(int(alpha[-1].max()), 0, "v0.45.3 created a hard horizontal shadow edge")
        self.assertLessEqual(int(alpha[:, 0].max()), int(old[:, 0].max()) + 1,
                             "v0.45.3 created a hard vertical shadow edge")
        self.assertLessEqual(int(alpha[:, -1].max()), int(old[:, -1].max()) + 1)
        self.assertEqual(after.getpixel((0, 123))[3], 0)
        self.assertEqual(after.getpixel((119, 123))[3], 0)
        self.assertGreater(int(alpha[110, 60]), 0, "shadow disappeared altogether")

    def test_original_opaque_artwork_is_identical(self):
        from scripts.iman_v454_bounded_shadow import add_contact_shadow
        art = self.make_art()
        output = add_contact_shadow(art)
        src = np.asarray(art)
        result = np.asarray(output)[:art.height, :art.width]
        opaque = src[..., 3] == 255
        self.assertTrue(np.array_equal(src[opaque], result[opaque]),
                        "Do not recolor or redraw the approved scroll and feather")

    def test_small_illustrations_and_text_wrap_are_unchanged(self):
        previous = (ROOT / "scripts/ReferenceQuoteV453.kt").read_text("utf-8")
        self.assertIn(".width(if (compactScreen) 80.dp else 99.dp)", previous)
        self.assertIn(".height(if (compactScreen) 86.dp else 103.dp)", previous)
        self.assertIn("Modifier.weight(1f)", previous)
        self.assertIn("ImanQuoteAnimatedText(current, ink, compactScreen)", previous)
        self.assertNotIn("TextOverflow.Ellipsis", previous)
        self.assertNotIn("maxLines =", previous)

    def test_version_and_book_protection(self):
        build = (ROOT / "scripts/build_iman_v454.py").read_text("utf-8")
        for token in ("build_v453(kit, dest)", "build_matte_artwork(",
                      "versionName '0.45.4'", "versionCode 54", "preview454",
                      "131", "79", "book_hashes", "protected", "NAV",
                      "assert_shadow_boundaries"):
            self.assertIn(token, build)


if __name__ == "__main__":
    unittest.main()
