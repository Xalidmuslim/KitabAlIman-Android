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


class BookDisplayRegressionTests(unittest.TestCase):
    def test_russian_only_verses_keep_original_text_anchors(self):
        from scripts.assemble_app import russian_quran_only
        prepared = russian_quran_only(BOOK)
        original_blocks = {b["id"]: b for c in BOOK["chapters"] for b in c["blocks"]}
        output = [b for c in prepared["chapters"] for b in c["blocks"]]
        self.assertEqual(1795, len(output))
        self.assertEqual(0, sum(b["type"] == "quran" for b in output))
        self.assertEqual(242, sum(b["type"] == "footnote" for b in output))
        self.assertEqual(1795, prepared["stats"]["blocks"])
        for block in output:
            self.assertEqual(original_blocks[block["id"]], block)
        for ref in ("3:102", "4:1", "33:70–71"):
            self.assertTrue(any(f"[{ref}]" in b["text"] for b in output))
        self.assertEqual(1798, sum(len(c["blocks"]) for c in BOOK["chapters"]))

    def test_corrupted_verse_translation_is_rejected(self):
        from scripts.assemble_app import russian_quran_only
        import copy
        book = copy.deepcopy(BOOK)
        book["chapters"][0]["blocks"] = [
            block for block in book["chapters"][0]["blocks"]
            if block["id"] != "iman-chapter-001-b0006"
        ]
        with self.assertRaises(RuntimeError):
            russian_quran_only(book)

    def test_toc_style_does_not_touch_other_screens(self):
        from scripts.assemble_app import customize_toc_screen
        fragment = """import androidx.compose.ui.text.style.TextOverflow
private fun ChapterRow(chapter: Chapter, onClick: () -> Unit, trailing: String? = null) {
Text(chapter.title, fontFamily = WebLiterataFont, fontWeight = FontWeight.Bold, fontSize = 16.sp, lineHeight = 20.sp)
                        sectionTitle,
                        modifier = Modifier.fillMaxWidth()
                            .padding(start = 4.dp, top = 14.dp, bottom = 3.dp),
                        color = MaterialTheme.colorScheme.primary,
                        fontFamily = WebModernFont,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.SemiBold,
ChapterRow(chapter, { open(chapter.id) })
ChapterRow(ch, { onOpen(ch.id, bm.anchor) }, if (bm.anchor != null) "Фрагмент" else bm.folder)
"""
        patched = customize_toc_screen(fragment)
        self.assertIn("centeredTitle = true", patched)
        self.assertIn("fontSize = if (centeredTitle) 18.sp else 16.sp", patched)
        self.assertIn("textAlign = if (centeredTitle) TextAlign.Center else TextAlign.Start", patched)
        self.assertIn("textAlign = TextAlign.Center", patched)
        self.assertIn("ChapterRow(ch, { onOpen(ch.id, bm.anchor) }", patched)

    def test_upstream_toc_reformatting_fails_closed(self):
        from scripts.assemble_app import customize_toc_screen
        with self.assertRaises(RuntimeError):
            customize_toc_screen("new unrelated layout")


if __name__ == "__main__":
    unittest.main()
