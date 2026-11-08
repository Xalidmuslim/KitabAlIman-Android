"""Regressions for v0.38: user screenshot feedback, visual assets, weekly minutes and nav."""
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

class IntegratedDashboardV38(unittest.TestCase):
    def test_home_has_notes_with_illustration_and_keeps_bookmarks_in_bottom_nav(self):
        source = (ROOT/"scripts/ReferenceHomeV38.kt").read_text("utf-8")
        self.assertIn('EditorialBookSection("Заметки"', source)
        self.assertIn('R.drawable.iman_v38_notes', source)
        self.assertIn('navigate(Route.Notes)', source)
        self.assertNotIn('EditorialBookSection("Закладки"', source)
        self.assertIn('navigate(Route.Book)', source)
        self.assertIn('navigate(Route.Collections)', source)
        self.assertIn('navigate(Route.Glossary)', source)
        self.assertIn('ImanReadingStatistics(book, store)', source)

    def test_reminder_art_is_subtle_and_drawn_to_edge_without_cutting_text(self):
        q = (ROOT/"scripts/ReferenceQuoteV38.kt").read_text("utf-8")
        self.assertIn('R.drawable.iman_v38_reminder', q)
        self.assertIn('.offset(x = 16.dp)', q)
        self.assertIn('ImanQuoteAnimatedText(current, ink)', q)
        self.assertNotIn('maxLines = 5', q)
        self.assertIn('Route.Reader(q.chapterId, q.blockId)', q)

    def test_chart_days_values_and_bars_share_exact_columns(self):
        src=(ROOT/"scripts/ReadingStatisticsV38.kt").read_text("utf-8")
        self.assertIn('Modifier.weight(1f)', src)
        self.assertIn('dayNames[index]', src)
        self.assertIn('"\${minutes} м"', src)
        self.assertIn('ledger.daysAgo(', src)
        self.assertNotIn('Arrangement.SpaceBetween', src)
        self.assertNotIn('i * size.width / 6f', src)
        self.assertIn('store.quizBestPercent', src)

    def test_wallpaper_wave_removed_without_touching_book(self):
        src=(ROOT/"scripts/build_iman_v38.py").read_text("utf-8")
        for t in ('build_v37(kit, dest)', 'iman_v38_flat_paper.webp',
                  'R.drawable.iman_v38_flat_paper', 'iman_v38_notes.webp',
                  'iman_v38_reminder.webp', 'book_hashes', 'reader_before', 'NAV'):
            self.assertIn(t, src)
        icon = ROOT/"assets/ui/v38/iman_v38_notes.webp"
        self.assertTrue(icon.is_file() and icon.stat().st_size > 1000)
if __name__=="__main__":
    unittest.main()
