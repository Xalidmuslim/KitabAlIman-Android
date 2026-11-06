"""All-chapters regression: no punctuation orphaned after Quran references."""
import json,unittest
from pathlib import Path
from scripts.assemble_app import russian_quran_only
from scripts.book_display import prepare_display_book
from scripts.reader_study_v6 import prepare_study_data
from scripts.build_iman_v7 import verse_slices,patch_reader

class PunctuationTests(unittest.TestCase):
    def test_examples(self):
        for s,expected in [
            ('Аллах сказал: «Аят» [40:10]. Это объяснение.','Это объяснение.'),
            ('Аллах сказал: «Аят» [48:18], слова Всевышнего.','слова Всевышнего.'),
            ('Аллах сказал: «Аят» [7:196]. Всевышний сказал:','Всевышний сказал:')]:
            chunks=verse_slices(s)
            self.assertEqual(s,''.join(s[a:b] for a,b,_ in chunks))
            self.assertEqual(expected,s[chunks[-1][0]:chunks[-1][1]])
            self.assertTrue(s[chunks[-2][0]:chunks[-2][1]].rstrip().endswith(('.',',')))
    def test_whole_book(self):
        root=Path(__file__).resolve().parents[1]
        data=json.loads((root/'assets/book.json').read_text(encoding='utf-8'))
        book,quiz,_=prepare_study_data(prepare_display_book(russian_quran_only(data)))
        self.assertEqual(131,len(book['chapters']))
        self.assertEqual(524,sum(map(len,quiz['chapters'].values())))
        self.assertEqual(242,sum(b['type']=='footnote' for c in book['chapters'] for b in c['blocks']))
        count=0;with_punctuation=0
        for chapter in book['chapters']:
            for block in chapter['blocks']:
                if block['type']=='footnote':continue
                s=block['text']; parts=verse_slices(s)
                self.assertEqual(s,''.join(s[a:b] for a,b,_ in parts))
                for a,b,verse in parts:
                    if not verse:continue
                    count+=1
                    self.assertFalse(b<len(s) and s[b] in '.,;:!?')
                    if s[a:b].rstrip().endswith(('.',',',';',':','!','?')):with_punctuation+=1
        self.assertEqual(857,count)
        self.assertGreaterEqual(with_punctuation,790)
    def test_non_quran_text_unaffected(self):
        s='Обычное предложение. Раздел текста без цитат.'
        self.assertEqual([(0,len(s),False)],verse_slices(s))
        with self.assertRaises(RuntimeError):patch_reader('unrelated source')
