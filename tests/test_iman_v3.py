"""Regression tests for the new compact faith reader, preserving every source anchor."""
import json
from pathlib import Path
import unittest

from scripts.assemble_app import russian_quran_only
from scripts.book_display import classify_quote, prepare_display_book
from scripts.ui_navigation import patch_app, patch_filter, patch_search

ROOT = Path(__file__).resolve().parents[1]
SOURCE = json.loads((ROOT/"assets/book.json").read_text(encoding="utf-8"))


class FaithReaderRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = russian_quran_only(SOURCE)
        cls.after = prepare_display_book(cls.before)

    def test_131_chapters_and_all_source_ids_texts_in_original_order(self):
        before = [(c["id"], b["id"], b["anchor"], b["text"])
                  for c in self.before["chapters"] for b in c["blocks"]]
        after = [(c["id"], b["id"], b["anchor"], b["text"])
                 for c in self.after["chapters"] for b in c["blocks"]]
        self.assertEqual(before, after)
        self.assertEqual(1795, len(after))
        self.assertEqual(131, len(self.after["chapters"]))

    def test_footnote_references_and_source_page_data_remain(self):
        old = [b for c in self.before["chapters"] for b in c["blocks"]]
        new = [b for c in self.after["chapters"] for b in c["blocks"]]
        self.assertEqual([b.get("sourcePage") for b in old],
                         [b.get("sourcePage") for b in new])
        self.assertEqual([b.get("footnoteRefs") for b in old],
                         [b.get("footnoteRefs") for b in new])
        self.assertEqual([b for b in old if b["type"]=="footnote"],
                         [b for b in new if b["type"]=="footnote"])
        self.assertEqual(242, sum(b["type"]=="footnote" for b in new))

    def test_remove_edition_page_labels_but_keep_book_metadata(self):
        self.assertTrue(all(not c["section"] for c in self.after["chapters"]))
        self.assertFalse(any(b["type"]=="quran"
                             for c in self.after["chapters"] for b in c["blocks"]))
        verse = [b for c in self.after["chapters"] for b in c["blocks"] if b["type"]=="verse"]
        self.assertEqual(3, len(verse))
        self.assertEqual({"3:102","4:1","33:70–71"},
                         {b["quranReference"] for b in verse})

    def test_scholarly_commentary_is_not_misattributed_as_quran(self):
        text = "Всевышний Аллах сказал: «Текст аята» [3:102]. Далее автор пояснил значение слов."
        self.assertEqual("verse_context", classify_quote(text))
        self.assertIsNone(classify_quote(text * 40))
        self.assertEqual("hadith", classify_quote("Пророк, да благословит его Аллах и да приветствует, сказал: «Доброе слово»."))
        self.assertEqual("scholar", classify_quote("Муджахид сказал: «Пример толкования»."))
        self.assertIsNone(classify_quote("Автор рассматривает различные мнения учёных."))

    def test_bottom_label_and_search_are_religious(self):
        old = 'NavItem("Темы", R.drawable.nav_topics, current == Route.Topics || current == Route.Book, onTopics),'
        self.assertIn('"Оглавление"', patch_app(old))
        self.assertIn('REMEDIES("Понятия")', patch_filter('REMEDIES("Средства")'))
        s = patch_search('SearchFilter.AUTHOR -> block.type == "text" || block.type == "historical_note"')
        self.assertIn('verse_context', s)

    def test_pinned_app_drift_is_not_silently_ignored(self):
        with self.assertRaises(RuntimeError):
            patch_app("unknown layout")


if __name__ == "__main__":
    unittest.main()
