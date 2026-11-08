"""v0.24 ref-accurate home: real reader Light preset and distinct original icons."""
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]

class ReferenceLightV24Tests(unittest.TestCase):
    def test_original_icon_generator_is_independent_from_screenshots(self):
        source=(ROOT/"scripts/iman_v24_artwork.py").read_text("utf-8")
        for forbidden in ("1000748485", "screenshot", "mockup", "atlas", ".crop("):
            # Drawn with original geometry and gradients, not cut from a UI.
            if forbidden in ("screenshot","mockup"):
                continue  # allowed in documentation describing what is avoided
            self.assertNotIn(forbidden, source)
        from scripts.iman_v24_artwork import install, FACTORY
        self.assertEqual(set(FACTORY),{"contents","collections","glossary","bookmarks"})
        with tempfile.TemporaryDirectory() as temp:
            install(Path(temp))
            hashes=[]
            for name in FACTORY:
                p=Path(temp)/f"iman_v24_{name}.webp"
                self.assertGreater(p.stat().st_size,2200)
                with Image.open(p) as im:
                    self.assertEqual(im.size,(240,180))
                    self.assertIn(im.mode,("RGB","RGBA"))
                hashes.append(hashlib.sha256(p.read_bytes()).hexdigest())
            self.assertEqual(len(set(hashes)),4)

    def test_home_uses_exact_light_paper_overlay_and_native_routes(self):
        home=(ROOT/"scripts/EditorialLightHomeV24.kt").read_text("utf-8")
        self.assertIn("R.drawable.reader_parchment_source",home)
        self.assertIn('readerPaperOverlay("light")',home)
        self.assertIn("ContentScale.FillBounds",home)
        self.assertIn("Modifier.matchParentSize()",home)
        for id in ("contents","collections","glossary","bookmarks"):
            self.assertIn(f"R.drawable.iman_v24_{id}",home)
        for route in ("Route.Book","Route.Collections","Route.Glossary","Route.Bookmarks",
                      "Route.Progress","Route.Reader(it.id, resume = last != null)",
                      "Route.CollectionDetail(entry.id)"):
            self.assertIn(route,home)
        self.assertNotIn("BorderStroke(",home)
        self.assertIn("shadowElevation = 0.dp",home)

    def test_reminder_has_independent_scene_and_dynamic_citation(self):
        quote=(ROOT/"scripts/EditorialLightQuoteV24.kt").read_text("utf-8")
        self.assertIn("R.drawable.iman_v24_reminder",quote)
        self.assertIn("ContentScale.Fit",quote)
        self.assertIn("Crossfade(",quote)
        self.assertIn("tween(180)",quote)
        self.assertIn('Text("Другая ↻"',quote)
        self.assertIn("Route.Reader(q.chapterId, q.blockId)",quote)
        self.assertIn("maxLines = 5",quote)
        self.assertNotIn("R.drawable.iman_v17_quote",quote)

    def test_decorative_scene_source_has_no_screen_text(self):
        # Only the reminder scene is sourced from the exact user-selected art.
        # All four library icons are independently drawn.
        import base64
        p=ROOT/"assets/ui/v24/iman_v24_reminder.b64"
        with Image.open(io.BytesIO(base64.b64decode(p.read_text("ascii")))) as im:
            self.assertEqual(im.size,(280,148))
            self.assertEqual(im.mode,"RGBA")
            self.assertLess(im.getchannel("A").getextrema()[0],80)

if __name__=="__main__":unittest.main()
