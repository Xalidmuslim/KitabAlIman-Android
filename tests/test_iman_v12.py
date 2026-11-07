import unittest
from scripts.build_iman_v12 import one

class V38PortTests(unittest.TestCase):
    def test_protected_pinned_files_fail_closed(self):
        with self.assertRaises(RuntimeError): one('a','b','c','missing')
        with self.assertRaises(RuntimeError): one('bb','b','c','repeated')
    def test_v38_engine_covers_reading_and_review(self):
        from pathlib import Path
        import base64,lzma,hashlib
        payload=(Path(__file__).resolve().parents[1]/'scripts/v12_engine.b64').read_text(encoding='ascii').strip()
        kotlin=lzma.decompress(base64.b64decode(payload, validate=True))
        assert hashlib.sha256(kotlin).hexdigest()=='a3578b8c0ee786675a3ead7e15b576adaad046062086b260093123fb1080f759'
        s=kotlin.decode('utf-8')
        for name in ['V38ReadingSession', 'V38ReaderStatus', 'V38StatisticsScreen', 'v38WeightedFraction', 'v38ReviewOrder', 'v38Streak', 'reviewHistory', 'saveReview']:
            self.assertIn(name,s)
        self.assertNotIn('StandaloneBottomNav',s)
        self.assertNotIn('WebView(',s)

if __name__=='__main__':unittest.main()
