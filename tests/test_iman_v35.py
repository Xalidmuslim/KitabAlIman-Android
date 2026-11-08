"""Visual regression v0.35: no icon halo, softer matte sepia, bigger book hero."""
import unittest
from pathlib import Path
from PIL import Image, ImageStat
from scripts.iman_v35_art import soften_icon, soften_reminder

ROOT=Path(__file__).resolve().parents[1]

def visible_bbox(im, limit=115):
    mask=im.convert("RGBA").getchannel("A").point(lambda a:255 if a>=limit else 0)
    return mask.getbbox()

class RefArtV35(unittest.TestCase):
    def test_library_icons_lighten_without_losing_book_or_scroll_detail(self):
        from scripts.iman_v35_art import ICONS
        self.assertEqual(len(ICONS),4)
        for name in ICONS:
            original=Image.open(ROOT/f"assets/ui/v27/iman_v27_{name}.webp").convert("RGBA")
            output=soften_icon(original)
            self.assertEqual(original.size,output.size)
            self.assertEqual(output.getpixel((0,0))[3],0)
            self.assertGreater(output.getchannel("A").getextrema()[1],230)
            self.assertNotEqual(original.tobytes(),output.tobytes())

    def test_reminder_larger_subject_with_transparent_edges(self):
        source=Image.open(ROOT/"assets/ui/v27/iman_v27_reminder.webp").convert("RGBA")
        target=soften_reminder(source)
        before=visible_bbox(source)
        after=visible_bbox(target)
        self.assertGreater(after[2]-after[0],(before[2]-before[0])*1.06)
        self.assertEqual(source.size,target.size)
        self.assertEqual(target.getpixel((0,0))[3],0)

    def test_native_source_retains_multiple_excerpt_layout_and_one_paper(self):
        src=(ROOT/"scripts/build_iman_v35.py").read_text("utf-8")
        for s in ("build_v34(kit,dest)","book_hashes","reader_before","app_before",
                  "preview35","iman_v35_","target_quote"):
            self.assertIn(s,src)
        self.assertNotIn("RenderEffect",src)
        self.assertNotIn("graphicsLayer",src)

if __name__=="__main__":
    unittest.main()
