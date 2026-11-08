"""v36 reference and data integrity regression checks."""
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
class StatisticsReferenceV36(unittest.TestCase):
    def test_dashboard_is_a_native_data_driven_composable(self):
        home=(ROOT/"scripts/ReferenceHomeV36.kt").read_text("utf-8")
        stats=(ROOT/"scripts/ReadingStatisticsV36.kt").read_text("utf-8")
        self.assertIn("ImanReadingStatistics(book, store",home)
        self.assertNotIn('Text("Темы для изучения"',home)
        self.assertNotIn('book.collections.take(2)',home)
        for token in ("V38ReadingLedger(context)","ledger.daysAgo(","chapterReadFraction(","store.quizBestPercent","book.collections", "Canvas(", "Route.Progress"):
            self.assertIn(token, stats)
        self.assertNotIn("68%", stats)
        self.assertNotIn("72%", stats)
        self.assertNotIn("88%", stats)
    def test_art_is_embedded_and_quote_uses_real_handwriting_font(self):
        quote=(ROOT/"scripts/ReferenceQuoteV36.kt").read_text("utf-8")
        for token in ("iman_v36_reminder","ImanCaveatFont","Route.Reader(q.chapterId, q.blockId)","Crossfade("):
            self.assertIn(token,quote)
        self.assertIn(".offset(x = 9.dp", quote)
    def test_build_protects_book_and_navigation(self):
        src=(ROOT/"scripts/build_iman_v36.py").read_text("utf-8")
        for token in ("build_v35(kit,dest)","preview36","book_hashes","app_before","reader_before","ReadingStatisticsV36.kt","ReferenceQuoteV36.kt","ReferenceHomeV36.kt"):
            self.assertIn(token,src)
        self.assertNotIn("RenderEffect",src)
if __name__=="__main__": unittest.main()
