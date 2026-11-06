"""Structural regression checks for the supplied book and Android adapter."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BOOK = json.loads((ROOT / "assets/book.json").read_text(encoding="utf-8"))


class BookStructureTests(unittest.TestCase):
    def test_complete_table_of_contents(self):
        chapters = BOOK["chapters"]
        self.assertEqual(131, len(chapters))
        self.assertEqual(len(chapters), len({c["id"] for c in chapters}))
        self.assertEqual(list(range(1, 132)), [c["order"] for c in chapters])

    def test_no_missing_or_duplicate_blocks(self):
        blocks = [b for c in BOOK["chapters"] for b in c["blocks"]]
        self.assertEqual(1798, len(blocks))
        self.assertEqual(len(blocks), len({b["id"] for b in blocks}))
        self.assertTrue(all(b["text"].strip() for b in blocks))
        self.assertEqual(242, sum(b["type"] == "footnote" for b in blocks))

    def test_references_and_indices_resolve(self):
        valid = {c["id"] for c in BOOK["chapters"]}
        for c in BOOK["chapters"]:
            if c.get("previousId"):
                self.assertIn(c["previousId"], valid)
            if c.get("nextId"):
                self.assertIn(c["nextId"], valid)
        for t in BOOK["topics"]:
            self.assertTrue(set(t["chapterIds"]).issubset(valid))
        for t in BOOK["remedies"]:
            self.assertTrue(set(t["chapterIds"]).issubset(valid))

    def test_text_only_assets(self):
        self.assertEqual([], list(ROOT.rglob("*.pdf")))
        self.assertEqual("Книга Имана", BOOK["title"])

    def test_engine_is_pinned_and_isolated(self):
        source = (ROOT/"scripts/assemble_app.py").read_text(encoding="utf-8")
        self.assertIn("e004dbc101345a171d9711316b3fda73ee146c61", source)
        self.assertIn("com.xalid.kitabaliman", source)
        self.assertIn('block.type == "footnote"', source)
        self.assertNotIn("PdfRenderer", source)


if __name__ == "__main__":
    unittest.main()
