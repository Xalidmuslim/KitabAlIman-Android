"""Regression of v32 actual emulator failure: topic row drawn under navbar.

v33 requires compact visual-height controls, preserved click handlers,
a clipped Home viewport, an unchanged reader and 5 native nav actions.
"""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]

class NavFidelityV33(unittest.TestCase):
    def test_quote_chrome_does_not_allocate_material_default_48dp_twice(self):
        q=(ROOT/"scripts/ReferenceQuoteV33.kt").read_text("utf-8")
        self.assertGreaterEqual(q.count("modifier = Modifier.height(36.dp)"),2)
        self.assertNotIn("heightIn(min = 24.dp)",q)
        for s in ("Crossfade(","tween(180)",'Text("Другая ↻"',
                  "Route.Reader(q.chapterId, q.blockId)",
                  "q.text.length <= 120","maxLines = 5"):
            self.assertIn(s,q)

    def test_resume_and_all_topics_have_constrained_height(self):
        home=(ROOT/"scripts/ReferenceHomeV33.kt").read_text("utf-8")
        self.assertIn("Modifier.height(36.dp)",home)
        self.assertIn(".clipToBounds()",home)
        self.assertNotIn(".statusBarsPadding()",home)
        self.assertIn("book.collections.take(2)",home)
        for route in ("Route.Book","Route.Collections","Route.Glossary",
                      "Route.Bookmarks","Route.Progress"):
            self.assertIn(route,home)

    def test_build_only_changes_ui_and_version(self):
        src=(ROOT/"scripts/build_iman_v33.py").read_text("utf-8")
        self.assertIn("build_v32(kit,dest)",src)
        for key in ("book_hashes","app_before","reader_before","nav_sha"):
            self.assertIn(key,src)
        self.assertIn("preview33",src)

if __name__=="__main__":unittest.main()
