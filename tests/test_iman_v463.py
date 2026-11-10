"""v0.46.3 regression: no home square, Android icon mask safe, readable full reminder."""
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


class SeamlessIconAndReminderV463(unittest.TestCase):
    def test_previous_clipped_illustration_is_reproduced(self):
        """Regression proof: 170dp image overflows 99dp slot in v459."""
        prior = (ROOT/"scripts/ReferenceQuoteV459.kt").read_text("utf-8")
        self.assertIn(".width(if (compactScreen) 80.dp else 99.dp)", prior)
        self.assertIn(".requiredWidth(if (compactScreen) 132.dp else 170.dp)", prior)

    def test_new_quote_is_measured_and_not_cropped(self):
        from scripts.build_iman_v463 import patch_quote
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/"ImanQuoteCarousel.kt"
            old = (ROOT/"scripts/ReferenceQuoteV459.kt").read_text("utf-8")
            p.write_text(old, "utf-8")
            patch_quote(p)
            code = p.read_text("utf-8")
            self.assertNotIn(".requiredWidth(", code)
            self.assertIn(".width(if (compactScreen) 112.dp else 128.dp)", code)
            self.assertIn(".fillMaxSize()", code)
            self.assertIn("ContentScale.Fit", code)
            self.assertIn("R.drawable.iman_v463_reminder_depth", code)
            for unchanged in ("imanExcerpts.size", "ImanQuoteAnimatedText(current, ink, compactScreen)",
                              "navigate(Route.Reader(q.chapterId, q.blockId))", "Другая ↻",
                              "fontFamily = ImanCaveatFont", "quote-rotation"):
                self.assertIn(unchanged, code)

    def test_home_icon_has_true_alpha_and_launcher_stays_in_mask(self):
        from scripts.build_iman_v463 import prepare_artwork
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            prepare_artwork(ROOT, output)
            drawable=output/"drawable-nodpi"
            with Image.open(drawable/"iman_v463_header.webp") as header:
                self.assertEqual(header.size,(320,320))
                self.assertEqual(header.mode,"RGBA")
                a=np.asarray(header.getchannel("A"))
                self.assertEqual(int(a[0,0]),0)
                self.assertEqual(int(a[0,-1]),0)
                self.assertEqual(int(a[-1,0]),0)
                self.assertEqual(int(a[-1,-1]),0)
                self.assertGreater(int((a>200).sum()),7000)
                self.assertLess(float((a>10).mean()),.75)
            with Image.open(drawable/"iman_v39_launcher_foreground.webp") as icon:
                self.assertEqual(icon.size,(512,512))
                a=np.asarray(icon.getchannel("A"))
                self.assertEqual(int(a[0,0]),0)
                y,x=np.ogrid[:512,:512]
                outside=(x-256)**2+(y-256)**2>185**2
                self.assertLess(int(np.count_nonzero(a[outside]>30)),100)
            with Image.open(output/"mipmap-anydpi/iman_v39_launcher.webp") as legacy:
                self.assertEqual(legacy.size,(512,512))
                self.assertEqual(legacy.mode,"RGB")

    def test_reminder_has_deeper_pigment_without_opaque_rectangle(self):
        from scripts.build_iman_v463 import enhance_reminder
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)
            src=ROOT/"assets/ui/v459/iman_v459_integrated_manuscript.webp"
            dst=out/"output.webp"
            enhance_reminder(src,dst)
            with Image.open(src) as old, Image.open(dst) as new:
                self.assertEqual(old.size,new.size)
                self.assertEqual(new.mode,"RGBA")
                self.assertEqual(new.getpixel((0,0))[3],0)
                self.assertEqual(new.getpixel((179,121))[3],0)
                oa=np.asarray(old.getchannel("A"),dtype=np.float32)
                na=np.asarray(new.getchannel("A"),dtype=np.float32)
                old_rgb=np.asarray(old.convert("RGB"),dtype=np.float32)
                new_rgb=np.asarray(new.convert("RGB"),dtype=np.float32)
                visible=oa>180
                self.assertGreater(int(np.count_nonzero(visible)),250)
                self.assertLess(float(new_rgb[visible].mean()),
                                float(old_rgb[visible].mean())-8.0)
                self.assertGreaterEqual(float(na[visible].mean()),
                                        float(oa[visible].mean())-1.0)

    def test_only_brand_and_quote_ui_change(self):
        src=(ROOT/"scripts/build_iman_v463.py").read_text("utf-8")
        for item in ("build_v462(kit, dest)", "versionCode 63",
                     "versionName '0.46.3'", "preview463",
                     "AndroidManifest.xml", "App.kt",
                     "131", "79", "ImanV38More.kt"):
            self.assertIn(item,src)
        self.assertIn("R.drawable.iman_v462_brand_icon", 
                      (ROOT/"scripts/build_iman_v462.py").read_text("utf-8"))


if __name__=="__main__":
    unittest.main()
