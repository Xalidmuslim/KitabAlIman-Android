"""TDD regression for left-aligned compact contents and smaller centered reader heading."""
import unittest
from scripts.build_iman_v5 import patch_contents_v5, patch_reader_v5


class ChapterCardLayoutTests(unittest.TestCase):
    def test_compact_toc_left_aligned_with_number_badge(self):
        source = '''@Composable
private fun ChapterRow(chapter: Chapter, onClick: () -> Unit, trailing: String? = null, centeredTitle: Boolean = false) {
    Card(
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick)) { Text(chapter.title) }
}
@Composable
private fun MetricCard(title: String, value: String, modifier: Modifier = Modifier, onClick: () -> Unit) { }
@Composable
fun BookScreen() {
    LazyColumn(verticalArrangement = Arrangement.spacedBy(3.dp)) { }
}
@Composable
fun TopicsScreen() { }
'''
        result = patch_contents_v5(source)
        start = result.index('if (centeredTitle) {')
        end = result.index('return', start)
        toc = result[start:end]
        self.assertIn('fontSize = 15.sp', toc)
        self.assertIn('TextAlign.Start', toc)
        self.assertIn('chapter.order.toString().padStart(2', toc)
        self.assertIn('Modifier.size(38.dp)', toc)
        self.assertNotIn('TextAlign.Center', toc)
        self.assertIn('Arrangement.spacedBy(6.dp)', result)
        self.assertIn('modifier = Modifier.fillMaxWidth().clickable(onClick = onClick))', result)

    def test_reader_heading_centered_and_smaller(self):
        source = '''                Text(
                    chapter.title.removeSurrounding("[", "]"),
                    fontFamily = WebLiterataFont,
                    fontSize = (if (chapter.title.length > 60) 23 else 27).sp,
                    lineHeight = (if (chapter.title.length > 60) 28 else 32).sp,
                    fontWeight = FontWeight.SemiBold,
                )'''
        changed = patch_reader_v5(source)
        self.assertIn('Modifier.fillMaxWidth()', changed)
        self.assertIn('TextAlign.Center', changed)
        self.assertIn('21 else 24', changed)
        self.assertIn('26 else 29', changed)
        self.assertIn('FontWeight.Bold', changed)

    def test_unknown_source_does_not_silently_change(self):
        with self.assertRaises((RuntimeError, ValueError)):
            patch_contents_v5('unknown')
        with self.assertRaises((RuntimeError, ValueError)):
            patch_reader_v5('unknown')

if __name__ == '__main__':
    unittest.main()
