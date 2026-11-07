"""Regression tests: new images integrated, no stretching, unchanged quote behavior."""
import unittest
from pathlib import Path
from scripts.build_iman_v17 import ART, patch_quote, patch_home, install_artwork

ROOT=Path(__file__).resolve().parents[1]

class LightSepiaTests(unittest.TestCase):
    def test_five_approved_artworks_present(self):
        self.assertEqual(len(ART),5)
        names=set(ART)
        self.assertEqual(names,{
            "iman_v17_quote.webp","iman_v17_contents.webp","iman_v17_collections.webp",
            "iman_v17_glossary.webp","iman_v17_bookmarks.webp"})
        for name in names:
            self.assertTrue((ROOT/"assets/ui/v17"/name).is_file(),name)

    def test_quote_does_not_stretch_when_card_height_changes(self):
        old='''            if (!dark) Image(
                painter = MedicineHomeArtwork.painter(R.drawable.iman_quote_v15),
                contentDescription = null, modifier = Modifier.matchParentSize(),
                contentScale = ContentScale.FillBounds)'''
        sample='''private val imanExcerpts = listOf(
        Text("Другая ↻")
        Route.Reader(q.chapterId, q.blockId)
        Modifier.fillMaxWidth(0.70f)
        Color(0xFFF6E3C9)
'''+old
        new=patch_quote(sample)
        self.assertIn("ContentScale.Fit",new)
        self.assertIn("Alignment.BottomEnd",new)
        self.assertNotIn("FillBounds",new)
        self.assertIn('Text("Другая ↻")',new)

    def test_quote_source_anchors_required(self):
        with self.assertRaises(RuntimeError):
            patch_quote("outdated reminder widget")

    def test_section_card_aspect_and_size_preserved(self):
        sample='''R.drawable.iman_section_contents, Modifier.weight(1f))
R.drawable.iman_section_collections, Modifier.weight(1f))
R.drawable.iman_section_glossary, Modifier.weight(1f))
R.drawable.iman_section_bookmarks, Modifier.weight(1f))
width = 76.dp, height = 65.dp
ContentScale.Fit'''
        new=patch_home(sample)
        self.assertIn("R.drawable.iman_v17_bookmarks",new)
        self.assertIn("R.drawable.iman_v17_contents",new)
        self.assertIn("width = 76.dp, height = 65.dp",new)
        self.assertNotIn("R.drawable.iman_section_contents",new)

if __name__=="__main__":
    unittest.main()
