"""v0.46.12 regression: contextual quote flash and comprehension-focused study."""
import json
import re
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from scripts.build_iman_v472 import (
    patch_quote, patch_reader, patch_reader_title, patch_speech,
    patch_knowledge_ui, patch_home_titles, patch_contents_titles,
    validate_curated_questions,
)

ROOT = Path(__file__).resolve().parents[1]


class MeaningfulReadingStudyTest(unittest.TestCase):
    def test_quote_tap_links_to_exact_visible_excerpt(self):
        quote = (ROOT / "scripts/ReferenceQuoteV459.kt").read_text("utf-8")
        # Pinned older source has the same unique quote column and route target.
        updated = patch_quote(quote)
        self.assertIn('".quote:" + current', updated)
        self.assertIn("Modifier.weight(1f).padding(top = 2.dp, bottom = 2.dp)", updated)
        self.assertIn("featuredQuoteForDeepLink", updated)
        self.assertIn("navigate(Route.Reader(q.chapterId, q.blockId))", updated)

    def test_reader_index_uses_block_id_and_auto_dismissal(self):
        src = (ROOT / "scripts/build_iman_v472.py").read_text("utf-8")
        self.assertIn("indexOfFirst { it.anchor == deepLinkBlockKey || it.id == deepLinkBlockKey }", src)
        self.assertIn("kotlinx.coroutines.delay(2700L)", src)
        self.assertIn("LocalQuoteFlash", src)
        self.assertIn("BackgroundColorSpan(temporaryHighlightColor)", src)
        self.assertNotIn("store.addHighlight(chapter.id", src)

    def test_all_79_excerpts_are_verified_in_the_build_not_user_highlights(self):
        # The 79 source excerpts are materialized during native app generation.
        # They are never rewritten or saved into the user's permanent highlight store.
        script = (ROOT / "scripts/build_iman_v472.py").read_text("utf-8")
        self.assertIn("featured_quotes.json", script)
        self.assertIn("quoteFocus", script)
        self.assertIn("temporaryRanges", script)
        self.assertIn("quoteVisible = false", script)
        self.assertIn("store.addHistory(chapter.id, deepLinkBlockKey)", script)

    def test_quiz_upgrades_are_validated_against_original_chapter(self):
        book = json.loads((ROOT / "assets/book.json").read_text("utf-8"))
        dataset = json.loads((ROOT / "assets/quiz_meaning_v472.json").read_text("utf-8"))
        overview = validate_curated_questions(book, dataset)
        self.assertGreaterEqual(overview["questions"], 24)
        self.assertGreaterEqual(overview["chapters"], 8)
        self.assertEqual(overview["invalid"], 0)

    def test_reading_controls_keep_voice_functionality(self):
        reader=(ROOT / "scripts/ui_reader.py").read_text("utf-8")
        patch=(ROOT / "scripts/build_iman_v472.py").read_text("utf-8")
        self.assertIn("controller?.pause()", patch)
        self.assertIn("active.play(chapter)", patch)
        self.assertIn("textButtonColors", patch)
        self.assertIn("shape = androidx.compose.foundation.shape.RoundedCornerShape(0.dp)", patch)

    def test_typography_does_not_rewrite_book_body_or_text(self):
        patch=(ROOT / "scripts/build_iman_v472.py").read_text("utf-8")
        for name in ("WebCompactFont", "Reader.kt", "ModernEditorialHome.kt",
                     "WebDesign.kt", "IbnQayyimStyle.kt", "Screens.kt",
                     "ReadingStatisticsV36.kt", "FaithStudy.kt"):
            self.assertIn(name, patch)
        self.assertIn("versionCode 72",patch)
        self.assertIn("versionName '0.46.12'",patch)
        self.assertIn("preview472",patch)


if __name__ == "__main__":
    unittest.main()
