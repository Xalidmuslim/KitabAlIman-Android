"""Contracts for the v0.38 editorial dashboard on top of verified v0.37."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class HomeRefinementV38(unittest.TestCase):
    def _read(self, name):
        return (ROOT / "scripts" / name).read_text("utf-8")

    def test_library_has_three_destinations_and_no_duplicate_bookmarks(self):
        home = self._read("ReferenceHomeV38.kt")
        self.assertIn('item(key = "library-three")', home)
        library = home.split('item(key = "library-three")', 1)[1].split('item(key = "reading-stats")', 1)[0]
        self.assertEqual(library.count('EditorialBookSection('), 3)
        self.assertNotIn('navigate(Route.Bookmarks)', library)
        for route in ('Route.Book', 'Route.Collections', 'Route.Glossary'):
            self.assertIn('navigate(' + route + ')', library)
        self.assertIn('ImanReadingStatistics(book, store)', home)
        self.assertIn('navigate(Route.Progress)', home)

    def test_statistics_show_real_minutes_and_label_test_results_truthfully(self):
        stats = self._read("ReadingStatisticsV38.kt")
        for source in ('ledger.daysAgo(', 'chapterReadFraction(', 'book.collections', 'store.quizBestPercent'):
            self.assertIn(source, stats)
        self.assertIn('drawRoundRect(', stats)
        self.assertIn('height(42.dp).clipToBounds()', stats)
        self.assertIn('heightIn(min = 18.dp)', stats)
        self.assertIn('Результаты тестов', stats)
        self.assertIn('глав с результатом ≥ 80%', stats)
        self.assertIn('Средний лучший:', stats)
        self.assertNotIn('Усвоение', stats)
        self.assertNotIn('mastery', stats)
        for placeholder in ('68%', '72%', '88%'):
            self.assertNotIn(placeholder, stats)

    def test_illustration_preserves_full_quote_and_source_navigation(self):
        quote = self._read("ReferenceQuoteV38.kt")
        self.assertIn('R.drawable.iman_v36_reminder', quote)
        self.assertIn('heightIn(min = 92.dp)', quote)
        self.assertIn('Route.Reader(q.chapterId, q.blockId)', quote)
        self.assertIn('ImanCaveatFont', quote)
        self.assertIn('Crossfade(', quote)
        self.assertNotIn('maxLines = 5', quote)
        self.assertNotIn('TextOverflow.Ellipsis', quote)

    def test_builder_is_safe_layer_on_v37(self):
        builder = self._read("build_iman_v38.py")
        for token in ('build_v37(kit, dest)', 'book_hashes', 'sha(app)', 'sha(reader)',
                      'ReferenceHomeV38.kt', 'ReadingStatisticsV38.kt',
                      'ReferenceQuoteV38.kt', 'preview38'):
            self.assertIn(token, builder)

if __name__ == "__main__":
    unittest.main()
