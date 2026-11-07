import unittest
from pathlib import Path
from scripts.build_iman_v13 import patch_app, patch_style, NAV

class V13VisualParity(unittest.TestCase):
    def test_more_route_not_bottom_nav(self):
        s = 'Route.More -> WebMoreScreen(screenModifier, ::navigate)\n'+NAV+'\nNavItem("Главная", R.drawable.nav_home)\n'
        r=patch_app(s)
        self.assertIn('Route.More -> ImanV38MoreScreen(',r)
        self.assertEqual(s.split(NAV)[1],r.split(NAV)[1])
    def test_invalid_anchors_fail(self):
        with self.assertRaises(RuntimeError):patch_app("old file")
        with self.assertRaises((RuntimeError,ValueError)):patch_style("old file")
    def test_compact_sepia_more_has_no_green_icons(self):
        s=(Path(__file__).resolve().parents[1]/"scripts/iman_v38_more.kt").read_text("utf-8")
        self.assertIn("ЛИЧНАЯ БИБЛИОТЕКА",s)
        self.assertIn("Прогресс чтения",s)
        self.assertIn("39.dp",s)
        self.assertNotIn("StandaloneBottomNav",s)
        self.assertNotIn("MedicalServices",s)

if __name__=="__main__":unittest.main()
