"""Visual regression contracts for compact, fully readable reminder v0.45.1."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class ReminderCompactV451(unittest.TestCase):
    def test_small_display_uses_readable_adaptive_sizes(self):
        quote=(ROOT/"scripts/ReferenceQuoteV451.kt").read_text("utf-8")
        self.assertIn(".width(if (compactScreen) 100.dp else 124.dp)",quote)
        self.assertIn(".height(if (compactScreen) 98.dp else 118.dp)",quote)
        self.assertIn("Modifier.weight(1f).padding(top = 2.dp, bottom = 2.dp)",quote)
        self.assertIn("ImanQuoteAnimatedText(current, ink, compactScreen)",quote)
        self.assertIn("compactScreen && length > 160 -> 15.0.sp",quote)
        self.assertIn("compactScreen && length > 120 -> 16.5.sp",quote)
        self.assertIn("length > 150 -> 17.5.sp",quote)
        self.assertIn("compactScreen && length > 160 -> 18.sp",quote)
        self.assertIn("compactScreen && length > 120 -> 19.5.sp",quote)
        self.assertIn("length > 150 -> 21.sp",quote)

    def test_contrast_and_text_exclusion_still_work(self):
        quote=(ROOT/"scripts/ReferenceQuoteV451.kt").read_text("utf-8")
        self.assertIn("alpha = 1f",quote)
        self.assertIn("ContentScale.Fit",quote)
        self.assertIn("Row(",quote)
        self.assertIn("Modifier.weight(1f)",quote)
        self.assertIn("R.drawable.iman_v43_approved_scroll",quote)
        self.assertNotIn("alpha = if (q.text.length",quote)
        self.assertNotIn(".fillMaxWidth(if (q.text.length",quote)
        self.assertNotIn("TextOverflow.Ellipsis",quote)
        self.assertNotIn("maxLines =",quote)
        self.assertIn('preferences.edit().putInt("last_shown", current).apply()',quote)

    def test_builder_preserves_existing_project_and_data(self):
        builder=(ROOT/"scripts/build_iman_v451.py").read_text("utf-8")
        for value in ("build_v45(kit, dest)", "versionName '0.45.1'",
                      "versionCode 51", "preview451", "ReferenceQuoteV451.kt",
                      "book_hashes", "131", "79", "NAV", "protected"):
            self.assertIn(value,builder)


if __name__=="__main__":
    unittest.main()
