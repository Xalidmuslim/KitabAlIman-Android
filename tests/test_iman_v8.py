import unittest
from scripts.build_iman_v8 import patch_home, ASSETS

class ArtworkRegression(unittest.TestCase):
    def test_banner_no_unintended_cropping_or_duplicate_native_title(self):
        old = """import androidx.compose.material.icons.filled.ChevronRight
@Composable
private fun AntiqueHomeHeader(book: BookData, onSettings: () -> Unit) {
    Image(MedicineHomeArtwork.painter(R.drawable.antique_hero_refined), null)
    Image(MedicineHomeArtwork.painter(R.drawable.medicine_launcher_book), null)
}
@Composable
private fun ReadingCard(title: String) { }
"""
        new = patch_home(old)
        light = new.split("} else {",1)[1]
        self.assertIn("val bannerHeight = maxWidth / 3f", light)
        self.assertIn("ContentScale.FillBounds", light)
        self.assertNotIn("Text(book.title", light)
        self.assertIn("Icons.Default.Settings", light)
        self.assertIn("contentDescription = book.title", light)
    def test_valid_sizes_and_resources(self):
        self.assertEqual((1280,427), ASSETS[0][-1])
        self.assertEqual((512,512), ASSETS[1][-1])
        self.assertEqual("antique_hero_refined.webp", ASSETS[0][1])
        self.assertEqual("medicine_launcher_book.webp", ASSETS[1][1])
    def test_changed_native_component_must_fail(self):
        with self.assertRaises(RuntimeError):
            patch_home("unrelated")
