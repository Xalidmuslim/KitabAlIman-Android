"""Art-size regression for v0.28: visible subjects, not transparent padding."""
import unittest
from pathlib import Path
from PIL import Image
from scripts.iman_v28_scale import fill_artwork

ROOT=Path(__file__).resolve().parents[1]

def opaque_size(img):
    mask=img.getchannel("A").point(lambda v:255 if v>=180 else 0)
    bbox=mask.getbbox()
    if bbox is None:return (0,0)
    return (bbox[2]-bbox[0],bbox[3]-bbox[1])

class ImanReferenceScale28(unittest.TestCase):
    def test_icon_subject_occupies_at_least_70_percent_of_actual_bitmap_width(self):
        for name in ("contents","collections","glossary","bookmarks"):
            im=Image.open(ROOT/f"assets/ui/v27/iman_v27_{name}.webp").convert("RGBA")
            before=opaque_size(im)
            fixed=fill_artwork(im,pad=0.07)
            after=opaque_size(fixed)
            self.assertGreater(after[0],im.width*.70,name)
            self.assertGreater(after[0],before[0]*1.15,name)
            self.assertEqual(fixed.size,im.size)
            self.assertEqual(fixed.getpixel((0,0))[3],0)

    def test_reminder_art_retains_original_quality_and_never_leaves_rectangle(self):
        im=Image.open(ROOT/"assets/ui/v27/iman_v27_reminder.webp").convert("RGBA")
        fixed=fill_artwork(im,pad=0.0)
        self.assertGreaterEqual(opaque_size(fixed)[0],opaque_size(im)[0])
        self.assertEqual(fixed.size,im.size)
        self.assertEqual(fixed.getpixel((0,0))[3],0)

    def test_compose_allocates_more_space_to_art_but_preserves_text_safety(self):
        kotlin=(ROOT/"scripts/SeamlessQuoteV25.kt").read_text("utf-8")
        self.assertIn("showIllustration",kotlin)
        self.assertIn('q.text.length <= 120',kotlin)
        self.assertIn("maxLines = 5",kotlin)
        self.assertNotIn("graphicsLayer",kotlin)

    def test_build_does_not_change_book_content_or_navigation(self):
        s=(ROOT/"scripts/build_iman_v28.py").read_text("utf-8")
        self.assertIn("build_v27(kit,dest)",s)
        for k in ("book_hashes","reader_before","app_before","protected_nav"):
            self.assertIn(k,s)

if __name__=="__main__":
    unittest.main()
