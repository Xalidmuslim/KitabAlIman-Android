"""Native v0.14 regression coverage; book data and bottom navigation are protected."""
import unittest
from pathlib import Path
import base64,hashlib,lzma,re
from scripts.build_iman_v14 import (
    ASSET_DIGEST, HOME_CARD, patch_player, patch_progress, patch_style,
    validate_quotes, install_images
)
ROOT=Path(__file__).resolve().parents[1]

class V14Tests(unittest.TestCase):
    def test_generated_art_pack_integrity_and_independent_transparency(self):
        raw=lzma.decompress(base64.b64decode(
            ''.join((ROOT/'scripts/v14_art_pack.b64').read_text('ascii').splitlines()),
            validate=True))
        self.assertEqual(hashlib.sha256(raw).hexdigest(),ASSET_DIGEST)
        self.assertIn('iman_section_bookmarks.webp',raw.decode('utf-8'))
        self.assertIn('iman_quote_background.webp',raw.decode('utf-8'))

    def test_rotating_quote_is_stable_across_recompositions(self):
        text=(ROOT/'scripts/ImanQuoteCarousel.kt').read_text('utf-8')
        self.assertIn('remember(prefs)',text)
        self.assertIn('mutableIntStateOf(initial)',text)
        self.assertIn('last_shown',text)
        self.assertIn('Route.Reader(q.chapterId, q.blockId)',text)
        self.assertEqual(text.count('FeaturedExcerpt("iman-chapter-'),7)

    def test_audio_preserves_pause_speed_stop_and_avoids_install_banner(self):
        new=(ROOT/'scripts/v14_reader_player.kt').read_text('utf-8')
        for term in ['active.play(chapter)','controller?.pause()',
                     'controller?.cycleRate()','controller?.stop()',
                     'ОЗВУЧИВАНИЕ ГЛАВЫ']:
            self.assertIn(term,new)
        self.assertNotIn('Бесплатный нейроголос',new)
        self.assertNotIn('Uri.parse(',new)
        test='@Composable\nprivate fun ReaderChapterSpeechBar(\nlegacy promo\n}\n\n'+\
             '@OptIn(ExperimentalMaterial3Api::class)\n@Composable\nprivate fun ReaderBlock('
        replaced=patch_player(test,new)
        self.assertIn('ОЗВУЧИВАНИЕ ГЛАВЫ',replaced)

    def test_reader_progress_matches_page_background(self):
        progress=(ROOT/'scripts/v14_reader_progress.kt').read_text('utf-8')
        self.assertIn('height(2.dp)',progress)
        self.assertIn('vertical = 4.dp',progress)
        self.assertIn('V38ReadingLedger(context)',progress)
        self.assertNotIn('Surface(',progress)
        self.assertNotIn('wordsLeft',progress)

    def test_3d_card_art_is_not_boxed_or_cropped(self):
        self.assertIn('ContentScale.Fit',HOME_CARD)
        self.assertNotIn('ContentScale.Crop',HOME_CARD)
        self.assertNotIn('background(',HOME_CARD)
        self.assertIn('heightIn(min = 96.dp)',HOME_CARD)

    def test_pinned_sources_fail_closed(self):
        with self.assertRaises(RuntimeError):
            patch_style('unknown code')
        with self.assertRaises(RuntimeError):
            patch_progress('unknown code','some progress')

if __name__=='__main__':
    unittest.main()
