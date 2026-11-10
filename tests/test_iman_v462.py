"""v0.46.2: the user's exact scroll artwork on Home and Android launcher.
Only the newly inserted brand image is removed from More. All original
settings, row glyphs, arrows and routes must remain present.
"""
import hashlib
import tempfile
import unittest
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/ui/v462/iman_v462_reference.webp"
SHA = "af9ca88d701739f010f7a997550c7c9a41827b7334272b16a6ca311df8f2ac5f"


class ApprovedBrandV462(unittest.TestCase):
    def test_exact_user_image_present(self):
        self.assertTrue(SOURCE.exists())
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(), SHA)
        with Image.open(SOURCE) as im:
            self.assertEqual(im.size, (192, 192))
            self.assertEqual(im.mode, "RGB")

    def test_only_new_more_header_icon_removed(self):
        from scripts.build_iman_v461 import patch_inapp_brand
        from scripts.build_iman_v462 import remove_extra_more_brand_and_update_home
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original_home = (ROOT / "scripts/ReferenceHomeV39.kt").read_text("utf-8")
            original_more = (ROOT / "scripts/ImanUnifiedMoreV44.kt").read_text("utf-8")
            (root / "ModernEditorialHome.kt").write_text(original_home, "utf-8")
            (root / "ImanV38More.kt").write_text(original_more, "utf-8")
            patch_inapp_brand(root)
            remove_extra_more_brand_and_update_home(root)
            home = (root / "ModernEditorialHome.kt").read_text("utf-8")
            more = (root / "ImanV38More.kt").read_text("utf-8")
            self.assertEqual(home.count("R.drawable.iman_v462_brand_icon"), 1)
            self.assertNotIn("R.drawable.iman_v461_brand_icon", home)
            self.assertNotIn("R.drawable.iman_v461_brand_icon", more)
            # Exact original More content: same settings button, menu icons,
            # text, arrows, routes, item spacing and typography.
            self.assertEqual(more, original_more)
            for expected in ('Icon(Icons.Default.Settings,',
                             'Text(entry.icon,',
                             'Icon(Icons.Default.ChevronRight,',
                             'navigate(entry.route)',
                             'navigate(Route.Settings)',
                             'Text("Ещё"'):
                self.assertIn(expected, more)

    def test_launcher_image_matches_reference_and_keeps_square_mask_safe(self):
        from scripts.build_iman_v462 import install_user_brand
        with tempfile.TemporaryDirectory() as temp:
            res = Path(temp)
            install_user_brand(ROOT, res)
            home = res / "drawable-nodpi/iman_v462_brand_icon.webp"
            foreground = res / "drawable-nodpi/iman_v39_launcher_foreground.webp"
            legacy = res / "mipmap-anydpi/iman_v39_launcher.webp"
            self.assertEqual(home.read_bytes(), SOURCE.read_bytes())
            for target in (foreground, legacy):
                with Image.open(target) as im:
                    self.assertEqual(im.size, (512,512))
                    self.assertIsNotNone(im.getbbox())
                    self.assertEqual(im.getpixel((256,256))[:3],
                                     Image.open(SOURCE).resize((512,512),
                                     Image.Resampling.LANCZOS).getpixel((256,256))[:3],
                                     msg=str(target))

    def test_v461_base_and_user_data_guardrails(self):
        source = (ROOT / "scripts/build_iman_v462.py").read_text("utf-8")
        for needle in ("build_v461(kit, dest)", "preview462",
                       "versionCode 62", "0.46.2",
                       "131", "79", "App.kt", "AndroidManifest.xml"):
            self.assertIn(needle, source)


if __name__ == "__main__":
    unittest.main()
