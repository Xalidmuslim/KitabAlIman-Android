"""v0.26 regressions: single textured page and precomposited matte illustrations."""
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageStat, ImageChops

from scripts.iman_v26_finish import finish_paper, finish_illustration, generate_assets

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/"assets/ui/v25"

class MattePageV26Tests(unittest.TestCase):
    def test_paper_has_real_grain_not_flat_color_and_keeps_navigation_wave(self):
        base=Image.open(ART/"unified_home.webp").convert("RGB")
        done=finish_paper(base)
        self.assertEqual(base.size,done.size)
        # Inspect empty center area of the source texture; avoid text/layout.
        crop=lambda im: im.crop((im.width//4,im.height//3,3*im.width//4,im.height//2)).convert("L")
        self.assertGreater(ImageStat.Stat(crop(done)).stddev[0],
                           ImageStat.Stat(crop(base)).stddev[0] + 2.0)
        # The image is still ivory, not a hard overlay or a gray canvas.
        rgb=ImageStat.Stat(done).mean
        self.assertGreater(rgb[0],rgb[1])
        self.assertGreater(rgb[1],rgb[2])
        self.assertGreater(rgb[2],165)
        # The original continuous curved foot of the parchment is preserved.
        self.assertLess(abs(ImageStat.Stat(done).mean[0]-ImageStat.Stat(base).mean[0]),9)
        self.assertEqual(done.tobytes(),finish_paper(base).tobytes())

    def test_each_image_keeps_sharp_core_but_gains_soft_contact_shadow(self):
        for key in ("reminder","library_contents","library_collections",
                    "library_glossary","library_bookmarks"):
            src=Image.open(ART/(key+".webp")).convert("RGBA")
            dst=finish_illustration(src)
            self.assertEqual(src.size,dst.size,key)
            self.assertEqual(dst.getpixel((0,0))[3],0,key)
            self.assertGreater(dst.getchannel("A").getextrema()[1],220,key)
            self.assertNotEqual(src.tobytes(),dst.tobytes(),key)

    def test_generate_six_separate_native_resources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            generate_assets(ART,root)
            targets=list(root.glob("iman_v26_*.webp"))
            self.assertEqual(len(targets),6)
            for target in targets:
                self.assertGreater(target.stat().st_size,2000)
                with Image.open(target) as im:
                    im.load()
                    if "unified_home" not in target.name:
                        self.assertEqual(im.mode,"RGBA")
                    else:
                        self.assertEqual(im.mode,"RGB")

    def test_build_preserves_one_root_background_and_reader_storage(self):
        script=(ROOT/"scripts/build_iman_v26.py").read_text("utf-8")
        self.assertIn("build_v25(kit,dest)",script)
        self.assertIn("reader_before",script)
        self.assertIn("app_before",script)
        self.assertIn("protected_assets",script)
        self.assertIn("R.drawable.iman_v26_unified_home",script)
        self.assertIn('f"R.drawable.iman_v26_{name}"',script)
        self.assertIn('applicationIdSuffix \'.preview26\'',script)
        self.assertNotIn("RenderEffect",script)
        self.assertNotIn("BlurEffect",script)

if __name__=="__main__":
    unittest.main()
