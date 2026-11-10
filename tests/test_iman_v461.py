"""v0.46.1 – exact user-supplied contour icon on Home, More and launcher."""
import hashlib
import tempfile
import unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"assets/ui/v461/iman_v461_brand_icon.webp"
HASH="68a4e51a72d51daf06fca7beec07ac20ea97a141050a3cd998436f0f70a00965"

class ContourBrandIconV461(unittest.TestCase):
    def test_asset_has_no_square_backdrop(self):
        self.assertTrue(SOURCE.is_file())
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(),HASH)
        with Image.open(SOURCE) as art:
            self.assertEqual(art.size,(160,160))
            self.assertEqual(art.mode,"RGBA")
            a=np.asarray(art.getchannel("A"))
            self.assertEqual(int(a[0,0]),0)
            self.assertEqual(int(a[0,-1]),0)
            self.assertEqual(int(a[-1,0]),0)
            self.assertEqual(int(a[-1,-1]),0)
            self.assertGreater(int(a[80,80]),250)
            self.assertLess(float(np.mean(a[:12,:12])),15)

    def test_patch_only_home_header_and_more_header(self):
        from scripts.build_iman_v461 import patch_inapp_brand
        with tempfile.TemporaryDirectory() as tmp:
            java=Path(tmp)
            home=(ROOT/"scripts/ReferenceHomeV39.kt").read_text("utf-8")
            more=(ROOT/"scripts/ImanUnifiedMoreV44.kt").read_text("utf-8")
            (java/"ModernEditorialHome.kt").write_text(home,"utf-8")
            (java/"ImanV38More.kt").write_text(more,"utf-8")
            patch_inapp_brand(java)
            newer_home=(java/"ModernEditorialHome.kt").read_text("utf-8")
            newer_more=(java/"ImanV38More.kt").read_text("utf-8")
            self.assertEqual(newer_home.count("R.drawable.iman_v461_brand_icon"),1)
            self.assertNotIn("R.drawable.iman_v39_header",newer_home)
            self.assertEqual(newer_more.count("R.drawable.iman_v461_brand_icon"),1)
            self.assertIn('Text("Ещё"',newer_more)
            for route in ("Route.Book","Route.About","Route.Settings","Route.Hadiths","Route.Notes"):
                self.assertIn(route,newer_more)
            self.assertIn("ContentScale.Fit",newer_home)
            self.assertIn("ContentScale.Fit",newer_more)
            self.assertNotIn("RoundedCornerShape(",newer_more)

    def test_icon_launcher_framing_and_safe_area(self):
        from scripts.build_iman_v461 import generate_launcher
        with tempfile.TemporaryDirectory() as tmp:
            res=Path(tmp)
            generate_launcher(ROOT,res)
            fg=res/"drawable-nodpi/iman_v39_launcher_foreground.webp"
            legacy=res/"mipmap-anydpi/iman_v39_launcher.webp"
            with Image.open(fg) as a,Image.open(legacy) as b:
                self.assertEqual(a.size,(512,512))
                self.assertEqual(b.size,(512,512))
                self.assertEqual(a.mode,"RGBA")
                self.assertEqual(b.mode,"RGBA")
                self.assertEqual(a.getpixel((0,0))[3],0)
                self.assertEqual(b.getpixel((0,0))[3],0)
                self.assertGreater(a.getpixel((160,160))[3],250)
                self.assertGreater(b.getpixel((160,160))[3],250)

    def test_build_maintains_quiz_nav_and_reader(self):
        code=(ROOT/"scripts/build_iman_v461.py").read_text("utf-8")
        for item in ("build_v460(kit, dest)","versionCode 61",
                     "versionName '0.46.1'","preview461","131","79",
                     "assets_before","before_nav","protected_java","AndroidManifest.xml"):
            self.assertIn(item,code)

if __name__=="__main__":unittest.main()
