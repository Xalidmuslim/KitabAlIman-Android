"""Approved native home-layout v0.10 regression tests."""
import unittest
from scripts.build_iman_v10 import patch_home

class HomeV10Tests(unittest.TestCase):
    def test_integrated_paper_cards_bronze_cta_native_author(self):
        template='''@Composable
private fun PaperCard() {}
@Composable
private fun AntiqueHomeHeader() {
val bannerHeight = maxWidth / 3f
val scale = ContentScale.FillBounds
                Text(
                    book.title,
                    modifier = Modifier.align(Alignment.CenterStart)
                        .fillMaxWidth(0.51f)
                        .padding(start = 22.dp, top = 25.dp),
                    fontFamily = WebLiterataFont,
                    fontSize = 23.sp,
                    lineHeight = 27.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF49321F),
                )
}
@Composable
private fun ReadingCard() { Color(0xFF315A46) }
@Composable
private fun AntiqueQuickCard() {}
@OptIn(ExperimentalLayoutApi::class)
fun Home() {
AntiqueIcon(R.drawable.antique_search_detail, Modifier.size(width = 58.dp, height = 42.dp))
if (first != null) WebCollectionCard(first, Modifier.weight(1f)) { navigate(Route.CollectionDetail(first.id)) }
if (second != null) WebCollectionCard(second, Modifier.weight(1f)) { navigate(Route.CollectionDetail(second.id)) }
}'''
        result=patch_home(template)
        for token in ('Шейхуль-Ислам Ибн Таймийя','Modifier.align(Alignment.TopStart)',
            'Color(0xFFF9DFBC)','Color(0xFF8E6832)',
            'ImanHomeCollectionCard(first','ImanHomeCollectionCard(second',
            'ContentScale.FillBounds','val bannerHeight = maxWidth / 3f',
            'Modifier.clickable(role = Role.Button, onClick = onClick)'):
            self.assertIn(token,result)
        self.assertNotIn('Color(0xFF315A46)',result)
        self.assertIn('navigate(Route.CollectionDetail(first.id))',result)
    def test_pinned_source_fail_closed(self):
        with self.assertRaises(RuntimeError): patch_home('unrelated UI')

if __name__ == '__main__':
    unittest.main()
