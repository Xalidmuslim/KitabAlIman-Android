"""v0.46.0: the explicitly approved parchment/scroll image must be the Android icon."""
import hashlib
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "assets/ui/v460/iman_approved_source.webp"
DIGEST = "9390a83b5bc6948c3480501b7281e2a0f47d7d1011bb9a797857ed925bf14ae6"


class ApprovedLauncherIconV460(unittest.TestCase):
    def test_approved_scroll_icon_is_exact_and_decodable(self):
        self.assertTrue(ART.is_file(), "Approved image is not committed")
        self.assertEqual(hashlib.sha256(ART.read_bytes()).hexdigest(), DIGEST)
        with Image.open(ART) as img:
            self.assertEqual(img.size, (256, 256))
            self.assertEqual(img.format, "WEBP")
            self.assertEqual(img.mode, "RGB")

    def test_launcher_code_preserves_original_art_and_framing(self):
        from scripts.build_iman_v460 import icon_resources
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            res = Path(tmp)/"app/src/main/res"
            (res/"drawable-nodpi").mkdir(parents=True)
            (res/"mipmap-anydpi").mkdir(parents=True)
            icon_resources(ROOT, res)
            fg = res/"drawable-nodpi/iman_v39_launcher_foreground.webp"
            legacy = res/"mipmap-anydpi/iman_v39_launcher.webp"
            self.assertGreater(fg.stat().st_size, 1000)
            self.assertGreater(legacy.stat().st_size, 1000)
            with Image.open(fg) as a, Image.open(legacy) as b:
                self.assertEqual(a.size, (512,512))
                self.assertEqual(b.size, (512,512))
                self.assertEqual(a.mode, "RGBA")
                self.assertEqual(b.mode, "RGB")
                self.assertGreaterEqual(a.getpixel((256,256))[3], 254)

    def test_version_keeps_book_and_manifest_route_safety(self):
        builder = (ROOT/"scripts/build_iman_v460.py").read_text("utf-8")
        for marker in ("build_v459", "versionCode 60", "0.46.0",
                       "preview460", "book.json", "quiz.json", "featured_quotes.json",
                       "131", "79", "App.kt", "AndroidManifest.xml",
                       "iman_v39_launcher_foreground.webp", "iman_v39_launcher.webp"):
            self.assertIn(marker,builder)
        flow = (ROOT/".github/workflows/build-iman-v460.yml").read_text("utf-8")
        self.assertIn("scripts.build_iman_v460 --dest AndroidApp", flow)
        self.assertIn("test_iman_v460.py",flow)
        self.assertIn("Verify APK signature and embedded text", flow)
        self.assertIn("Render Home on Android emulator",flow)


if __name__ == "__main__":
    unittest.main()
