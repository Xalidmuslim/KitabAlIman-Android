"""v0.45.6: visual-grounding regressions for reminder artwork."""
import unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]

class GroundedReliefV456(unittest.TestCase):
    def test_ornament_has_legible_left_detail_without_dark_patch(self):
        from scripts.iman_v456_ground import make_ground
        a=np.asarray(make_ground().convert("RGBA"))[...,3]
        self.assertEqual(a.shape,(496,842))
        for side in (a[0],a[-1],a[:,0],a[:,-1]):
            self.assertEqual(int(np.max(side)),0)
        left=a[325:470,20:270]
        middle=a[335:470,260:585]
        self.assertGreater(np.count_nonzero(left>75),2000)
        self.assertLess(float(middle.mean()),45.0)  # no dark brown translucent mat
        self.assertGreater(float(middle.std()),25.0) # discernible etched lines


    def test_ornament_is_not_speckled_at_actual_phone_size(self):
        from PIL import ImageFilter
        from scripts.iman_v456_ground import make_ground
        alpha=make_ground().convert("RGBA").resize(
            (174,103),Image.Resampling.LANCZOS).getchannel("A")
        blur=alpha.filter(ImageFilter.GaussianBlur(1.2))
        fine=np.asarray(alpha,dtype=float)[65:100,10:170]
        low=np.asarray(blur,dtype=float)[65:100,10:170]
        self.assertLess(float(np.abs(fine-low).mean()),7.4,
                        "too many tiny medallions render as speckled noise")
        self.assertGreater(float(np.percentile(fine,95)),75,
                           "ornament must remain visible at smartphone scale")

    def test_perspective_ornament_dissolves_without_internal_hard_border(self):
        from scripts.iman_v456_ground import make_ground
        alpha=np.asarray(make_ground().getchannel("A"),dtype=float)
        lower=np.abs(np.diff(alpha,axis=0))[340:475,110:730]
        self.assertLess(float(np.percentile(lower,95)),40.0,
                        "perspective ornament still has a visible straight lower boundary")

    def test_preserve_quote_wrap_and_approved_scroll(self):
        v455=(ROOT/"scripts/ReferenceQuoteV455.kt").read_text("utf-8")
        v456=(ROOT/"scripts/ReferenceQuoteV456.kt").read_text("utf-8")
        expected=v455.replace(
            ".requiredWidth(if (compactScreen) 119.dp else 147.dp)",
            ".requiredWidth(if (compactScreen) 133.dp else 174.dp)"
        )
        self.assertEqual(v456,expected,"only ornamental backdrop width is allowed to change")
        for token in ('R.drawable.iman_v43_approved_scroll',
                      'ImanQuoteAnimatedText(current, ink, compactScreen)',
                      'Modifier.weight(1f)',
                      '.width(if (compactScreen) 80.dp else 99.dp)',
                      '.height(if (compactScreen) 86.dp else 103.dp)'):
            self.assertIn(token,v456)
        self.assertNotIn('TextOverflow.Ellipsis',v456)

    def test_data_and_resource_protection(self):
        code=(ROOT/"scripts/build_iman_v456.py").read_text("utf-8")
        for token in ('build_v455(kit, dest)','versionName \'0.45.6\'',
                      "preview456","versionCode 56",
                      "131","79","book_hashes","protected","NAV",
                      "iman_v455_ground_rug.webp","original_scroll_hash"):
            self.assertIn(token,code)

if __name__=="__main__":unittest.main()
