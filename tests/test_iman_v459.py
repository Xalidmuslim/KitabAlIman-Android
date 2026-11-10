"""v0.45.9 – seamless approved manuscript artwork integration regressions."""
import base64
import hashlib
import io
import unittest
from pathlib import Path
from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
APPROVED_HASH = "f9c796e981e63a5f47891c1e2cadcead8f44f98cb6c436689af464f8ac465233"


class SeamlessManuscriptV459(unittest.TestCase):
    def test_exact_approved_transparent_asset(self):
        blob = (ROOT/"assets/ui/v459/iman_v459_integrated_manuscript.webp").read_bytes()
        self.assertEqual(hashlib.sha256(blob).hexdigest(), APPROVED_HASH)
        with Image.open(io.BytesIO(blob)) as image:
            self.assertEqual(image.mode, "RGBA")
            self.assertEqual(image.size, (180, 122))
            alpha = np.asarray(image.getchannel("A"))
            self.assertGreater(int(alpha.max()), 230)
            self.assertEqual(int(alpha[-1].max()), 0)
            self.assertLessEqual(int(alpha[0].max()), 2)
            self.assertEqual(int(alpha[:, -1].max()), 0)
            self.assertEqual(int(alpha[:, 0].max()), 0)
            self.assertGreater(np.count_nonzero(alpha > 90), 3000)

    def test_one_seamless_artwork_instead_of_old_generated_layers(self):
        quote = (ROOT/"scripts/ReferenceQuoteV459.kt").read_text("utf-8")
        original = (ROOT/"scripts/ReferenceQuoteV456.kt").read_text("utf-8")
        self.assertIn("R.drawable.iman_v459_integrated_manuscript", quote)
        self.assertNotIn("R.drawable.iman_v455_ground_rug", quote)
        self.assertNotIn("R.drawable.iman_v43_approved_scroll", quote)
        self.assertIn("ContentScale.Fit", quote)
        self.assertIn(".width(if (compactScreen) 80.dp else 99.dp)", quote)
        self.assertIn("ImanQuoteAnimatedText(current, ink, compactScreen)", quote)
        self.assertIn("Modifier.weight(1f)", quote)
        self.assertNotIn("TextOverflow.Ellipsis", quote)
        self.assertNotIn("maxLines =", quote)
        start = "                    // Background relief is transparent"
        end = "                }\n                HorizontalDivider("
        self.assertEqual(original.split(start)[0], quote.split("                    // Approved integrated")[0])
        self.assertEqual(original.split(end)[1], quote.split(end)[1])

    def test_minimal_builder_preserves_book_and_quiz_sources(self):
        builder = (ROOT/"scripts/build_iman_v459.py").read_text("utf-8")
        for requirement in (
            "build_v458(kit, dest)",
            "versionCode 59",
            "versionName '0.45.9'",
            ".preview459",
            "APPROVED_HASH", "131", "79",
            "assets_before", "protected", "NAV",
            "iman_v459_integrated_manuscript.webp",
        ):
            self.assertIn(requirement, builder)

    def test_ci_checks_foreground_app_not_android_launcher(self):
        yaml = (ROOT/".github/workflows/build-iman-v459.yml").read_text("utf-8")
        self.assertIn("com.xalid.kitabaliman.preview459", yaml)
        self.assertNotIn("adb shell am start -W -n com.xalid.kitabaliman.preview456", yaml)
        self.assertIn("mCurrentFocus", yaml)
        self.assertIn('adb shell am start -W -n "$PKG/com.xalid.meditsinaproroka.nativeapp.MainActivity"', yaml)
        self.assertIn("test_iman_v459.py", yaml)


if __name__ == "__main__":
    unittest.main()
