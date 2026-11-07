import unittest
from pathlib import Path

class HomeArtRegression(unittest.TestCase):
    def test_light_header_has_native_title_and_no_opaque_top_bar(self):
        from scripts.build_iman_v9 import patch_header
        initial = '''@Composable
private fun AntiqueHomeHeader(book: BookData, onSettings: () -> Unit) {
    val dark = true
    if (dark) {
        Text(book.title, fontSize = 20.sp)
    } else {
        BoxWithConstraints(Modifier.fillMaxWidth()) {
            val bannerHeight = maxWidth / 3f
            Box(Modifier.fillMaxWidth().height(bannerHeight)) {
                Image(
                    MedicineHomeArtwork.painter(R.drawable.antique_hero_refined),
                    contentDescription = book.title + " — " + book.author,
                    modifier = Modifier.matchParentSize(),
                    contentScale = ContentScale.FillBounds,
                )
                Box(
                    Modifier.fillMaxWidth().height(25.dp)
                        .align(Alignment.TopCenter)
                        .background(Color(0xFFF5E9DA).copy(alpha = 0.42f)),
                )
                IconButton(onClick = onSettings) {}
            }
        }
    }
}
'''
        output = patch_header(initial)
        light = output.split('} else {',1)[-1]
        self.assertIn('Text(\n                    book.title,',light)
        self.assertIn('ContentScale.FillBounds',light)
        self.assertIn('.fillMaxWidth(0.51f)',light)
        self.assertNotIn('height(25.dp)',light)
        self.assertNotIn('contentDescription = book.title +',light)
        self.assertIn('fontSize = 23.sp',light)

    def test_quickcards_get_six_distinct_book_assets(self):
        from scripts.build_iman_v9 import patch_icons
        old='''AntiqueIcon(R.drawable.antique_open_book_detail, Modifier.size(width = 52.dp, height = 36.dp), scale = ContentScale.Fit)
AntiqueIcon(R.drawable.antique_search_detail, Modifier.size(39.dp))
AntiqueIcon(icon, Modifier.size(width = 70.dp, height = 48.dp))
AntiqueQuickCard(R.drawable.antique_scroll_detail, "Понятия", "15 позиций", Modifier.weight(1f)) {}
'''
        changed=patch_icons(old)
        self.assertIn('R.drawable.iman_glossary_detail',changed)
        self.assertIn('width = 84.dp, height = 56.dp',changed)
        self.assertIn('width = 58.dp, height = 42.dp',changed)
        self.assertIn('width = 68.dp, height = 46.dp',changed)
        self.assertNotIn('Modifier.size(39.dp)',changed)
        self.assertNotIn('antique_remedies_detail',changed)

    def test_preload_registers_glossary_icon(self):
        from scripts.build_iman_v9 import patch_preload
        original='''        R.drawable.antique_scroll_detail,
        R.drawable.antique_remedies_detail,
'''
        changed=patch_preload(original)
        self.assertIn('R.drawable.iman_glossary_detail',changed)
        self.assertEqual(1,changed.count('iman_glossary_detail'))

    def test_pinned_code_has_fail_closed_guards(self):
        from scripts.build_iman_v9 import patch_header, patch_icons, patch_preload
        for func in (patch_header,patch_icons,patch_preload):
            with self.assertRaises(RuntimeError):func('unrelated new API')

    def test_resized_images_integrity(self):
        from scripts.build_iman_v9 import RESOURCE_MAP
        from PIL import Image
        source=Path(__file__).resolve().parent.parent / 'assets' / 'ui' / 'v9'
        if not source.exists():
            source=Path(__file__).resolve().parent
        self.assertEqual(7,len(RESOURCE_MAP))
        resources=[r[0] for r in RESOURCE_MAP]
        self.assertEqual(7,len(set(resources)))
        for dest,filename,sha,size in RESOURCE_MAP:
            f=source/filename
            self.assertTrue(f.exists(),filename)
            import hashlib
            self.assertEqual(sha,hashlib.sha256(f.read_bytes()).hexdigest())
            with Image.open(f) as im:
                self.assertEqual('WEBP',im.format)
                self.assertEqual(size,im.size)
                if dest!='antique_hero_refined.webp':
                    self.assertIn('A',im.getbands())

if __name__=='__main__':unittest.main()
