"""Isolated regression checks for the approved manuscript reminder art."""
import base64
import hashlib
import io
import unittest
from pathlib import Path
from PIL import Image

from scripts.build_iman_v465 import SOURCE, DIGEST, DRAWABLE

ROOT = Path(__file__).resolve().parents[1]


class ManuscriptReminderV465Test(unittest.TestCase):
    def test_approved_webp_is_exact_and_has_transparency(self):
        data = base64.b64decode((ROOT / SOURCE).read_text("ascii").strip(), validate=True)
        self.assertEqual(hashlib.sha256(data).hexdigest(), DIGEST)
        with Image.open(io.BytesIO(data)) as im:
            self.assertEqual(im.size, (256, 225))
            self.assertEqual(im.mode, "RGBA")
            self.assertEqual(im.getchannel("A").getextrema()[0], 0)

    def test_only_quote_art_is_replaced(self):
        script = (ROOT / "scripts/build_iman_v465.py").read_text("utf-8")
        self.assertIn("build_v464(kit, dest)", script)
        self.assertIn("R.drawable.iman_v464_reminder_feathered", script)
        self.assertIn("R.drawable." + DRAWABLE, script)
        self.assertIn("navigate(Route.Reader(q.chapterId, q.blockId))", script)
        self.assertIn("versionName '0.46.5'", script)


if __name__ == "__main__":
    unittest.main()
