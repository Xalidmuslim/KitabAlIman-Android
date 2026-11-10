"""v0.46.4: preserve old book art but eliminate clipped arch and dark header sticker."""
import hashlib
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

class SoftBookArtworkV464(unittest.TestCase):
    def test_previous_reminder_top_boundary_was_visible(self):
        """Reproduce the visual bug in v463 before testing the patch."""
        from scripts.build_iman_v463 import enhance_reminder
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"old.webp"
            enhance_reminder(ROOT/"assets/ui/v459/iman_v459_integrated_manuscript.webp",path)
            with Image.open(path) as picture:
                top_region=np.asarray(picture.getchannel("A"))[:10]
                self.assertGreater(int(top_region.max()),180)

    def test_reminder_top_and_edges_feather_without_cutting_scroll_or_quill(self):
        from scripts.build_iman_v463 import enhance_reminder
        from scripts.build_iman_v464 import feather_reminder
        with tempfile.TemporaryDirectory() as tmp:
            old=Path(tmp)/"old.webp"; dst=Path(tmp)/"new.webp"
            enhance_reminder(ROOT/"assets/ui/v459/iman_v459_integrated_manuscript.webp",old)
            feather_reminder(old,dst)
            with Image.open(old) as before, Image.open(dst) as after:
                self.assertEqual(after.size,(180,156))
                self.assertEqual(after.mode,"RGBA")
                a=np.asarray(after.getchannel("A"))
                self.assertEqual(int(a[:12].max()),0)
                self.assertEqual(int(a[0].max()),0)
                self.assertEqual(int(a[-1].max()),0)
                self.assertEqual(int(a[:,0].max()),0)
                self.assertGreater(int(a[40:140,35:165].max()),245)
                # The solid core stays present; only diffuse fog edges are softened.
                old_alpha=np.asarray(before.getchannel("A"))
                self.assertGreater(int(np.count_nonzero(a[17:139, :]>160)),
                                   int(np.count_nonzero(old_alpha>160)*.72))

    def test_header_matches_soft_library_palette_and_has_no_plate(self):
        from scripts.build_iman_v463 import prepare_artwork
        from scripts.build_iman_v464 import tone_header
        with tempfile.TemporaryDirectory() as tmp:
            res=Path(tmp)
            prepare_artwork(ROOT,res)
            before=res/"drawable-nodpi/iman_v463_header.webp"
            after=res/"drawable-nodpi/iman_v464_home_soft.webp"
            tone_header(before,after)
            with Image.open(before) as b, Image.open(after) as a:
                self.assertEqual(a.size,(320,320))
                self.assertEqual(a.mode,"RGBA")
                self.assertEqual(a.getpixel((0,0))[3],0)
                self.assertEqual(a.getpixel((319,319))[3],0)
                old=np.asarray(b.convert("RGBA"),dtype=np.float32)
                new=np.asarray(a.convert("RGBA"),dtype=np.float32)
                opaque=old[:,:,3]>230
                self.assertGreater(float(new[:,:,:3][opaque].mean()),
                                   float(old[:,:,:3][opaque].mean())+1.5)
                self.assertLess(float(new[:,:,3].mean()),float(old[:,:,3].mean())*.94)
                self.assertGreater(int(new[:,:,3].max()),185)

    def test_patch_modifies_only_home_brand_and_quote_layout(self):
        from scripts.build_iman_v464 import patch_home, patch_quote
        from scripts.build_iman_v463 import patch_quote as v463_patch_quote
        with tempfile.TemporaryDirectory() as tmp:
            h=Path(tmp)/"ModernEditorialHome.kt"
            q=Path(tmp)/"ImanQuoteCarousel.kt"
            h.write_text((ROOT/"scripts/ReferenceHomeV39.kt").read_text("utf-8").replace(
                "R.drawable.iman_v39_header","R.drawable.iman_v463_header"),"utf-8")
            q.write_text((ROOT/"scripts/ReferenceQuoteV459.kt").read_text("utf-8"),"utf-8")
            v463_patch_quote(q)
            patch_home(h)
            patch_quote(q)
            home=h.read_text("utf-8");quote=q.read_text("utf-8")
            self.assertEqual(home.count("R.drawable.iman_v464_home_soft"),1)
            self.assertIn("R.drawable.iman_v464_reminder_feathered",quote)
            self.assertNotIn("R.drawable.iman_v463_reminder_depth",quote)
            self.assertNotIn(".offset(y = (-3).dp)",quote)
            self.assertNotIn(".requiredWidth(",quote)
            self.assertIn("heightIn(min = if (compactScreen) 108.dp else 117.dp)",quote)
            self.assertIn("ImanQuoteAnimatedText(current, ink, compactScreen)",quote)
            self.assertIn("navigate(Route.Reader(q.chapterId, q.blockId))",quote)
            self.assertIn("Ибн Таймийя",home)

    def test_build_guardrails(self):
        script=(ROOT/"scripts/build_iman_v464.py").read_text("utf-8")
        for s in ("build_v463(kit, dest)","versionCode 64",
                  "versionName '0.46.4'", "preview464",
                  "AndroidManifest.xml","ImanV38More.kt","131","79",
                  "iman_v39_launcher_foreground.webp"):
            self.assertIn(s,script)

if __name__ == "__main__":unittest.main()
