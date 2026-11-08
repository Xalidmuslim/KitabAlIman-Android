"""v0.27: require the six new independent image assets and one root wallpaper."""
from pathlib import Path
from PIL import Image, ImageStat
import hashlib
import unittest
from scripts.build_iman_v27 import ARTWORK_NAMES, install_v27_art

ROOT=Path(__file__).resolve().parents[1]

class RefTextureV27Tests(unittest.TestCase):
    def test_six_independently_generated_images_are_persisted(self):
        folder=ROOT/"assets/ui/v27"
        for name in ARTWORK_NAMES:
            path=folder/f"iman_v27_{name}.webp"
            self.assertTrue(path.is_file(),name)
            self.assertGreater(path.stat().st_size,3300,name)
            with Image.open(path) as im:
                im.load()
                if name=="unified_home":
                    self.assertEqual(im.size,(648,1152))
                    self.assertEqual(im.mode,"RGB")
                    self.assertGreater(ImageStat.Stat(im.convert("L")).stddev[0],2.0)
                else:
                    self.assertEqual(im.mode,"RGBA")
                    self.assertEqual(im.getpixel((0,0))[3],0)
                    self.assertGreater(im.getchannel("A").getextrema()[1],150)
        self.assertEqual(len(list(folder.glob("iman_v27_*.webp"))),6)

    def test_build_reuses_single_seamless_root_and_protects_book_data(self):
        s=(ROOT/"scripts/build_iman_v27.py").read_text("utf-8")
        self.assertIn("build_v26(kit,dest)",s)
        self.assertIn("app_before",s)
        self.assertIn("reader_before",s)
        self.assertIn("book_hashes",s)
        self.assertIn("R.drawable.iman_v27_unified_home",s)
        self.assertIn('applicationIdSuffix \'.preview27\'',s)
        self.assertNotIn("RenderEffect",s)
        self.assertNotIn("Brush.verticalGradient",s)

    def test_preload_separately_generated_resources(self):
        s=(ROOT/"scripts/build_iman_v27.py").read_text("utf-8")
        for name in ARTWORK_NAMES:
            self.assertIn("R.drawable.iman_v27_",s)
            self.assertIn("iman_v27_",s)

if __name__=="__main__":
    unittest.main()
