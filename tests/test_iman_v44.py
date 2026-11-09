"""v0.44.0 design regression contracts. Run before and after a native build."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class UnifiedPaperContracts(unittest.TestCase):
    def test_scope_excludes_approved_home(self):
        paper=(ROOT/"scripts/ImanUnifiedPaperV44.kt").read_text("utf-8")
        transform=(ROOT/"scripts/iman_v44_transform.py").read_text("utf-8")
        self.assertIn("if (isHome)",paper)
        self.assertIn("content()\n        return",paper)
        self.assertIn("R.drawable.iman_v38_flat_paper", (ROOT/"scripts/build_iman_v38.py").read_text("utf-8"))
        self.assertIn("ImanUnifiedRouteTheme(isHome = route == Route.Home)",transform)

    def test_inventory_includes_all_primary_native_screens(self):
        transformer=(ROOT/"scripts/iman_v44_transform.py").read_text("utf-8")
        for name in ("App.kt", "Screens.kt", "Reader.kt", "WebDesign.kt",
                     "IbnQayyimStyle.kt","IbnV38StudyEngine.kt","FaithStudy.kt"):
            self.assertIn('"'+name+'"',transformer)
        more=(ROOT/"scripts/ImanUnifiedMoreV44.kt").read_text("utf-8")
        self.assertIn("ImanV38MoreScreen",more)
        self.assertNotIn("Surface(",more)
        self.assertNotIn("Card(",more)
        for name in ("Route.Book","Route.Progress","Route.Collections",
                     "Route.Glossary","Route.Hadiths","Route.Notes",
                     "Route.History","Route.Settings","Route.About","Route.Source"):
            self.assertIn(name,more)

    def test_preserve_reader_and_user_assets(self):
        builder=(ROOT/"scripts/build_iman_v44.py").read_text("utf-8")
        for token in ("build_v43(kit, dest)","book_hashes",
                      "quiz.json","131","79","Route.Notes","Route.Hadiths",
                      "preview44","NAV","Reader.kt",
                      "ModernEditorialHome.kt","ImanQuoteCarousel.kt"):
            self.assertIn(token,builder)
        t=(ROOT/"scripts/iman_v44_transform.py").read_text("utf-8")
        self.assertIn("(if (chapter.title.length > 60) 18 else 20).sp",t)
        self.assertIn('WebHeader("Настройки чтения"',t)
        self.assertIn('"Screens.kt"', (ROOT/"scripts/iman_v44_transform.py").read_text("utf-8"))
        self.assertIn("Content", (ROOT/"scripts/ReferenceHomeV41.kt").read_text("utf-8"))

if __name__=="__main__":
    unittest.main()
