"""v0.41 regression: legible sparse engraving, aligned 7-day minutes, balanced empty space."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class ImanV41Layout(unittest.TestCase):
    def test_week_days_minutes_and_bars_share_one_column(self):
        s=(ROOT/"scripts/ReadingStatisticsV41.kt").read_text("utf-8")
        self.assertIn('daily.forEachIndexed { index, value ->',s)
        self.assertIn('Column(Modifier.weight(1f)',s)
        self.assertIn('Text("$minutes"',s)
        self.assertIn('Text(dayNames[index]',s)
        self.assertIn('height(22.dp)',s)
        self.assertIn('HorizontalDivider(Modifier.fillMaxWidth().align(Alignment.BottomCenter)',s)
        self.assertNotIn('height(32.dp)',s)
        self.assertNotIn('i * size.width / 6f',s)
        self.assertNotIn('Arrangement.SpaceBetween',s)
        self.assertIn('ledger.daysAgo(it)',s)

    def test_flexible_spacing_keeps_small_screens_scrollable(self):
        s=(ROOT/"scripts/ReadingStatisticsV41.kt").read_text("utf-8")
        h=(ROOT/"scripts/ReferenceHomeV41.kt").read_text("utf-8")
        self.assertIn('screenHeightDp >= 820',s)
        self.assertIn('screenHeightDp >= 820',h)
        self.assertIn('LazyColumn(',h)
        self.assertIn('ImanReadingStatistics(book, store)',h)
        self.assertIn('Column(modifier.fillMaxSize().padding(bottom = 76.dp).clipToBounds())',h)

    def test_only_engraving_strokes_gain_strength_no_filled_fog(self):
        q=(ROOT/"scripts/ReferenceQuoteV41.kt").read_text("utf-8")
        b=(ROOT/"scripts/build_iman_v41.py").read_text("utf-8")
        self.assertIn('R.drawable.iman_v41_engraving',q)
        self.assertIn('fontFamily = ImanCaveatFont',q)
        self.assertNotIn('TextOverflow.Ellipsis',q)
        self.assertIn('1.23',b)
        self.assertIn('getchannel("A")',b)
        self.assertIn('coverage',b)
        self.assertIn('0.34',b)
        self.assertIn('iman_v41_engraving.webp',b)

    def test_preserved_book_navigation_notes_and_hadiths(self):
        h=(ROOT/"scripts/ReferenceHomeV41.kt").read_text("utf-8")
        library=h.split('item(key = "library-four")',1)[1].split('item(key = "reading-stats")',1)[0]
        self.assertEqual(library.count('EditorialBookSection('),4)
        self.assertIn('EditorialBookSection("Хадисы", "Источники",',library)
        self.assertIn('navigate(Route.Hadiths)',library)
        b=(ROOT/"scripts/build_iman_v41.py").read_text("utf-8")
        for name in ('build_v40(kit, dest)','book_hashes','NAV','reader_before','preview41',
                     'ImanV38More.kt','ReadingStatisticsV36.kt','79','131'):
            self.assertIn(name,b)

if __name__=="__main__":
    unittest.main()
