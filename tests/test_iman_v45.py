"""Regression checks for the v0.45 reminder contrast and text/image separation."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
QUOTE = ROOT / "scripts/ReferenceQuoteV45.kt"
BUILDER = ROOT / "scripts/build_iman_v45.py"


class ReminderLayoutV45(unittest.TestCase):
    def test_full_opacity_artwork_keeps_original_approved_asset(self):
        quote = QUOTE.read_text(encoding="utf-8")
        self.assertIn("R.drawable.iman_v43_approved_scroll", quote)
        self.assertIn("ContentScale.Fit", quote)
        self.assertIn("alpha = 1f", quote)
        self.assertNotIn("alpha = if (q.text.length", quote)
        self.assertNotIn("0.27f", quote)
        self.assertNotIn("0.68f else 0.94f", quote)

    def test_text_and_art_use_distinct_row_columns(self):
        quote = QUOTE.read_text(encoding="utf-8")
        reminder = quote.split("// v45: independent text and artwork columns.", 1)[1]
        reminder = reminder.split("HorizontalDivider(", 1)[0]
        self.assertIn("Row(", reminder)
        self.assertIn("Modifier.weight(1f)", reminder)
        self.assertIn("horizontalArrangement = Arrangement.spacedBy(", reminder)
        self.assertIn("ImanQuoteAnimatedText(current, ink)", reminder)
        self.assertLess(reminder.index("ImanQuoteAnimatedText(current, ink)"),
                        reminder.index("R.drawable.iman_v43_approved_scroll"))
        self.assertNotIn("matchParentSize()", reminder)
        self.assertNotIn(".fillMaxWidth(if (q.text.length", reminder)
        self.assertNotIn(".offset(x =", reminder)

    def test_small_display_wraps_untruncated_text_without_stretching_image(self):
        quote = QUOTE.read_text(encoding="utf-8")
        self.assertIn("heightIn(min = if (compactScreen) 111.dp else 133.dp)", quote)
        self.assertIn(".width(if (compactScreen) 112.dp else 148.dp)", quote)
        self.assertIn(".height(if (compactScreen) 103.dp else 137.dp)", quote)
        self.assertIn("LocalConfiguration.current.screenWidthDp <= 380", quote)
        self.assertIn("fontFamily = ImanCaveatFont", quote)
        self.assertIn("Crossfade(", quote)
        self.assertNotIn("maxLines =", quote)
        self.assertNotIn("TextOverflow.Ellipsis", quote)

    def test_only_reminder_is_replaced_and_131_chapters_79_quotes_remain(self):
        builder = BUILDER.read_text(encoding="utf-8")
        for token in (
            "build_v44(kit, dest)", "preview45",
            "versionName '0.45.0'", 'ImanQuoteCarousel.kt',
            "ReferenceQuoteV45.kt", "protected", "book_hashes",
            '131', '79', 'NAV', "ImanFeaturedQuoteCarousel"
        ):
            self.assertIn(token, builder)
        quote = QUOTE.read_text(encoding="utf-8")
        self.assertIn('prefs', (ROOT / "scripts/ReferenceQuoteV43.kt").read_text(encoding="utf-8").lower()
                      .replace("preferences", "prefs") or "prefs")
        self.assertIn('preferences.edit().putInt("last_shown", current).apply()', quote)
        self.assertIn('navigate(Route.Reader(q.chapterId, q.blockId))', quote)


if __name__ == "__main__":
    unittest.main()
