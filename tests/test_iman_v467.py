"""v0.46.7: clipped-right reminder regression and seamless parchment material."""

import unittest
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

from scripts.build_iman_v467 import soften_reminder_background, patch_position

ROOT = Path(__file__).resolve().parents[1]


class ReminderRightSoftV467(unittest.TestCase):
    def test_light_paper_haze_fades_but_manuscript_stays_legible(self):
        # Intentionally opaque paper rectangle reproduces the user-visible bug.
        image = Image.new("RGBA", (256, 225), (220, 195, 155, 242))
        ImageDraw.Draw(image).rectangle((94, 100, 214, 184), fill=(126, 85, 49, 250))
        softened = soften_reminder_background(image)
        alpha = np.asarray(softened.getchannel("A"))
        self.assertEqual(softened.size, image.size)
        self.assertEqual(int(alpha[0].max()), 0)
        self.assertEqual(int(alpha[-1].max()), 0)
        self.assertEqual(int(alpha[:, 0].max()), 0)
        self.assertEqual(int(alpha[:, -1].max()), 0)
        self.assertLess(int(alpha[110, 56]), 190)   # atmospheric background
        self.assertGreater(int(alpha[145, 150]), 220)  # three-dimensional scroll
        self.assertLess(int(alpha[145, -12]), 90)   # 6dp-safe transparent margin

    def test_compose_position_shifts_only_visual_to_right(self):
        # Reproduce the current v466 modifier without touching quote navigation.
        src = """androidx.compose.foundation.layout.Box(
                modifier = Modifier
                    .width(if (compactScreen) 112.dp else 128.dp)
                    .height(if (compactScreen) 100.dp else 110.dp)
                    .offset(y = (0).dp),
                contentAlignment = Alignment.TopEnd,
            ) { Image(painter = painterResource(R.drawable.iman_v465_scroll)) }
            navigate(Route.Reader(q.chapterId, q.blockId))"""
        updated = patch_position(src)
        self.assertIn(".offset(x = 6.dp, y = (0).dp)", updated)
        self.assertNotIn(".offset(y = (0).dp)", updated)
        self.assertIn("navigate(Route.Reader(q.chapterId, q.blockId))", updated)
        self.assertIn(".width(if (compactScreen) 112.dp else 128.dp)", updated)

    def test_build_from_v466_preserves_all_book_content(self):
        script = (ROOT / "scripts/build_iman_v467.py").read_text("utf-8")
        for needle in (
            "build_v466(kit, dest)", "versionName '0.46.7'",
            "versionCode 67", "preview467", "featured_quotes.json",
            "book.json", "quiz.json", "iman_v465_scroll.webp",
            "patch_position(", "soften_reminder_background(",
        ):
            self.assertIn(needle, script)


if __name__ == "__main__":
    unittest.main()
