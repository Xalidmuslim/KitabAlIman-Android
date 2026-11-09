"""Regression checks: v0.45.2 changes only reminder artwork and its size."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class MatteReminderV452(unittest.TestCase):
    def test_reminder_is_exactly_twenty_percent_smaller(self):
        quote = (ROOT / "scripts/ReferenceQuoteV452.kt").read_text(encoding="utf-8")
        self.assertIn(".width(if (compactScreen) 80.dp else 99.dp)", quote)
        self.assertIn(".height(if (compactScreen) 78.dp else 94.dp)", quote)
        self.assertIn("alpha = 1f", quote)
        self.assertIn("ContentScale.Fit", quote)

    def test_text_does_not_overlap_art_or_get_truncated(self):
        quote = (ROOT / "scripts/ReferenceQuoteV452.kt").read_text(encoding="utf-8")
        self.assertIn("Modifier.weight(1f)", quote)
        self.assertIn("horizontalArrangement = Arrangement.spacedBy(", quote)
        self.assertIn("ImanQuoteAnimatedText(current, ink, compactScreen)", quote)
        self.assertNotIn("TextOverflow.Ellipsis", quote)
        self.assertNotIn("maxLines =", quote)
        self.assertIn('preferences.edit().putInt("last_shown", current).apply()', quote)
        self.assertIn("navigate(Route.Reader(q.chapterId, q.blockId))", quote)

    def test_artwork_is_color_matched_with_existing_library_assets(self):
        style = (ROOT / "scripts/iman_v452_style.py").read_text(encoding="utf-8")
        for name in ("iman_v35_contents.webp", "iman_v35_collections.webp",
                     "iman_v35_glossary.webp", "iman_v35_bookmarks.webp"):
            self.assertIn(name, style)
        self.assertIn("original_alpha", style)
        self.assertIn("reference_chroma", style)
        self.assertIn("Image.Resampling", style) if "Image.Resampling" in style else self.assertIn("Image.open", style)

    def test_builder_keeps_131_chapters_and_all_79_reminders(self):
        builder = (ROOT / "scripts/build_iman_v452.py").read_text(encoding="utf-8")
        for token in ("build_v451(kit, dest)", "versionName '0.45.2'",
                      "preview452", "versionCode 52", "book_hashes",
                      "131", "79", "NAV", "protected", "build_matte_artwork"):
            self.assertIn(token, builder)
        source = (ROOT / "scripts/ReferenceQuoteV452.kt").read_text(encoding="utf-8")
        previous = (ROOT / "scripts/ReferenceQuoteV451.kt").read_text(encoding="utf-8")
        changed = previous.replace(
            ".width(if (compactScreen) 100.dp else 124.dp)",
            ".width(if (compactScreen) 80.dp else 99.dp)"
        ).replace(
            ".height(if (compactScreen) 98.dp else 118.dp)",
            ".height(if (compactScreen) 78.dp else 94.dp)"
        )
        self.assertEqual(source, changed, "v452 may only shrink the existing artwork, not re-layout")
        

if __name__ == "__main__":
    unittest.main()
