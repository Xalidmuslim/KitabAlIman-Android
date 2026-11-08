"""v34 actual-emulator regression: home icon must not overlap system clock."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class StatusBarV34Tests(unittest.TestCase):
    def test_header_reserves_android_statusbar_once(self):
        source=(ROOT/"scripts/ReferenceHomeV34.kt").read_text("utf-8")
        self.assertEqual(source.count(".statusBarsPadding()"),1)
        self.assertIn("Modifier.fillMaxWidth().statusBarsPadding()",source)
        self.assertIn("modifier.fillMaxSize().padding(bottom = 76.dp).clipToBounds()",source)
        self.assertIn("book.collections.take(2)",source)
        self.assertNotIn("BorderStroke(",source)

    def test_builder_keeps_book_navigation_and_only_changes_home(self):
        src=(ROOT/"scripts/build_iman_v34.py").read_text("utf-8")
        for term in ("build_v33(kit,dest)","app_before","reader_before",
                     "book_hashes","preview34"):
            self.assertIn(term,src)
        self.assertNotIn("RenderEffect",src)
if __name__=="__main__": unittest.main()
