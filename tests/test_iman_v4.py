"""Book-wide structural and quote-display regression checks (Android v0.4)."""
import json
import unittest
from pathlib import Path

from scripts.assemble_app import russian_quran_only
from scripts.book_display import prepare_display_book
from scripts.build_iman_v4 import cited_verses, normalize_heading

ROOT = Path(__file__).resolve().parents[1]
BASE = json.loads((ROOT / "assets/book.json").read_text(encoding="utf-8"))


class V4BookWideRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous = prepare_display_book(russian_quran_only(BASE))
        cls.chapters = cls.previous["chapters"]
        cls.blocks = [block for c in cls.chapters for block in c["blocks"]]

    def test_original_text_anchor_ids_and_footnote_count_unchanged(self):
        self.assertEqual(131, len(self.chapters))
        self.assertEqual(1795, len(self.blocks))
        self.assertEqual(1795, len({b["id"] for b in self.blocks}))
        self.assertEqual(242, sum(b["type"] == "footnote" for b in self.blocks))
        self.assertEqual(0, sum(b["type"] == "quran" for b in self.blocks))
        self.assertTrue(all(b["text"] and b["anchor"] for b in self.blocks))
        self.assertFalse(any("Страница оригинала" in c["section"] for c in self.chapters))

    def test_130_repeated_chapter_titles_including_chapter_42(self):
        matching = [
            c["order"] for c in self.chapters
            if normalize_heading(c["title"]) == normalize_heading(c["blocks"][0]["text"])
        ]
        self.assertEqual(130, len(matching))
        self.assertIn(42, matching)
        self.assertNotIn(1, matching) # Contains original editor footnote marker.

    def test_857_scripture_quote_ranges_preserve_every_character(self):
        count = 0
        touched = set()
        for chapter in self.chapters:
            for block in chapter["blocks"]:
                if block["type"] == "footnote":
                    continue
                segments = cited_verses(block["text"])
                joined = "".join(block["text"][a:b] for a,b,_ in segments)
                self.assertEqual(block["text"], joined)
                for start, end, is_verse in segments:
                    self.assertTrue(0 <= start < end <= len(block["text"]))
                    if is_verse:
                        count += 1
                        touched.add(block["id"])
                        self.assertIn("»", block["text"][start:end])
        self.assertEqual(857, count)
        self.assertEqual(334, len(touched))

    def test_reader_example_9_31_is_separated_from_hadith_commentary(self):
        block = next(
            b for b in self.chapters[41]["blocks"]
            if "Они признали господами помимо Аллаха" in b["text"] and "[9:31]" in b["text"]
        )
        ranges = cited_verses(block["text"])
        self.assertTrue(any(kind and "[9:31]" in block["text"][start:end]
                            for start,end,kind in ranges))
        self.assertTrue(any(not kind for _,_,kind in ranges))

    def test_uncited_or_incomplete_quotes_stay_prose(self):
        text = "Автор сказал: «Это цитата без указания аята»."
        self.assertEqual([(0,len(text),False)], cited_verses(text))
        for text in ("Нет кавычек [2:42].", "Обрыв » [2:42]"):
            self.assertFalse(any(x[2] for x in cited_verses(text)))


if __name__ == "__main__":
    unittest.main()
