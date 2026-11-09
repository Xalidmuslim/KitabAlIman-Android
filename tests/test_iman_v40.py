"""v0.40 regression: four library items, safe Hadith route, legible quote & line-only relief."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class V40HomeContracts(unittest.TestCase):
    def test_hadiths_is_the_fourth_not_fifth_library_item(self):
        src=(ROOT/"scripts/ReferenceHomeV40.kt").read_text("utf-8")
        row=src.split('item(key = "library-four")',1)[1].split('item(key = "reading-stats")',1)[0]
        self.assertEqual(row.count('EditorialBookSection('),4)
        self.assertIn('EditorialBookSection("Хадисы", "Источники",',row)
        self.assertIn('R.drawable.iman_v35_bookmarks',row)
        self.assertIn('navigate(Route.Hadiths)',row)
        self.assertNotIn('EditorialBookSection("Заметки"',row)
        self.assertNotIn('EditorialBookSection("Закладки"',row)
        for label in ('Оглавление','Подборки','Понятия'):
            self.assertIn('EditorialBookSection("'+label+'"',row)

    def test_same_handwritten_font_and_larger_type_at_all_lengths(self):
        q=(ROOT/"scripts/ReferenceQuoteV40.kt").read_text("utf-8")
        self.assertIn('fontFamily = ImanCaveatFont',q)
        self.assertNotIn('fontFamily = if (length',q)
        self.assertNotIn('maxLines = 5',q)
        self.assertNotIn('TextOverflow.Ellipsis',q)
        for value in ('22.5.sp','20.5.sp','19.sp','17.5.sp'):
            self.assertIn(value,q)
        self.assertIn('Route.Reader(q.chapterId, q.blockId)',q)
        self.assertIn('Crossfade(',q)

    def test_haze_is_removed_with_sparse_engraving_alpha(self):
        q=(ROOT/"scripts/ReferenceQuoteV40.kt").read_text("utf-8")
        b=(ROOT/"scripts/build_iman_v40.py").read_text("utf-8")
        self.assertIn('R.drawable.iman_v40_engraving',q)
        self.assertIn('ImageFilter.FIND_EDGES',b)
        self.assertIn('coverage',b)
        self.assertIn('<= 0.34',b)
        self.assertIn('iman_v40_engraving.webp',b)
        self.assertNotIn('R.drawable.iman_v39_relief',q)
        self.assertIn('if (isDark)',q)
        self.assertIn('ImanQuoteAnimatedText(current, ink)',q)

    def test_preserves_book_routes_and_notes_data(self):
        b=(ROOT/"scripts/build_iman_v40.py").read_text("utf-8")
        for invariant in ('build_v39(kit, dest)','book_hashes','reader_before',
                          'NAV','79','131','preview40','Route.Hadiths','Route.Notes'):
            self.assertIn(invariant,b)
        self.assertIn('versionName',b)
        home=(ROOT/"scripts/ReferenceHomeV40.kt").read_text("utf-8")
        self.assertIn('ImanReadingStatistics(book, store)',home)

if __name__=="__main__":
    unittest.main()
