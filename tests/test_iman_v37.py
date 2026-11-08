"""Regression contracts from the Nov 8 real-device screenshot versus approved design."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class RealDeviceLayoutV37(unittest.TestCase):
    def test_quotes_show_complete_source_text_without_fixed_height_truncation(self):
        text = (ROOT / "scripts/ReferenceQuoteV37.kt").read_text("utf-8")
        self.assertIn('heightIn(min = 132.dp)', text)
        self.assertNotIn('.height(92.dp)', text)
        self.assertNotIn('maxLines = 5', text)
        self.assertNotIn('TextOverflow.Ellipsis', text)
        self.assertIn('Route.Reader(q.chapterId, q.blockId)', text)
        self.assertIn('ImanCaveatFont', text)
        self.assertIn('Crossfade(', text)
        self.assertIn('width(190.dp).height(132.dp)', text)
        self.assertNotIn('.offset(x = 24.dp', text)

    def test_full_chapter_titles_and_unframed_library(self):
        home = (ROOT / "scripts/ReferenceHomeV37.kt").read_text("utf-8")
        self.assertIn('height(64.dp)', home)
        self.assertIn('heightIn(min = 92.dp)', home)
        self.assertIn('ImanReadingStatistics(book, store)', home)
        self.assertIn('navigate(Route.Bookmarks)', home)
        self.assertIn('navigate(Route.Progress)', home)
        resume = home.split('private fun EditorialResumeCard(', 1)[1].split('@Composable', 1)[0]
        self.assertNotIn('maxLines = 2', resume)
        self.assertNotIn('TextOverflow.Ellipsis', resume)
        self.assertIn('border = null', home)
        self.assertIn('shadowElevation = 0.dp', home)

    def test_statistics_are_real_and_readable(self):
        stats = (ROOT / "scripts/ReadingStatisticsV37.kt").read_text("utf-8")
        self.assertIn('height(56.dp).clipToBounds()', stats)
        self.assertIn('heightIn(min = 24.dp)', stats)
        self.assertIn('width(32.dp)', stats)
        for token in ('ledger.daysAgo(', 'chapterReadFraction(', 'store.quizBestPercent', 'book.collections'):
            self.assertIn(token, stats)
        for forbidden in ('68%', '72%', '88%'):
            self.assertNotIn(forbidden, stats)

    def test_build_isolated_preview_and_content_preservation(self):
        builder = (ROOT / "scripts/build_iman_v37.py").read_text("utf-8")
        for token in ('build_v36(kit, dest)', 'preview37', 'book_hashes', 'app_before',
                      'reader_before', 'ReferenceQuoteV37.kt', 'ReadingStatisticsV37.kt',
                      'ReferenceHomeV37.kt'):
            self.assertIn(token, builder)

if __name__ == "__main__":
    unittest.main()
