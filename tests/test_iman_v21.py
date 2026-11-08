"""Regression checks for v0.21 borderless native editorial screen."""
import unittest
from pathlib import Path
from scripts.build_iman_v21 import patch_bottom_nav

ROOT = Path(__file__).resolve().parents[1]


class BorderlessEditorialV21Tests(unittest.TestCase):
    def test_home_does_not_draw_card_outlines_or_shadows(self):
        home = (ROOT / "scripts/BorderlessHomeV21.kt").read_text("utf-8")
        self.assertIn("ModernEditorialHomeScreen(", home)
        self.assertIn("EditorialResumeCard(", home)
        self.assertIn('item(key = "collections")', home)
        self.assertIn("Color.Transparent", home)
        self.assertIn("shadowElevation = 0.dp", home)
        self.assertIn("border = null", home)
        self.assertNotIn("BorderStroke(", home)
        for feature in ("Route.Book", "Route.Collections", "Route.Glossary",
                        "Route.Bookmarks", "Route.Progress",
                        "Route.Reader(it.id, resume = last != null)",
                        "Route.CollectionDetail(entry.id)"):
            self.assertIn(feature, home)

    def test_79_quotes_keep_animation_and_deep_links_without_border(self):
        quote = (ROOT / "scripts/BorderlessQuoteV21.kt").read_text("utf-8")
        self.assertIn("Crossfade(", quote)
        self.assertIn("tween(180)", quote)
        self.assertIn('Text("Другая ↻"', quote)
        self.assertIn("Route.Reader(q.chapterId, q.blockId)", quote)
        self.assertIn("maxLines = 5", quote)
        self.assertIn("ContentScale.Fit", quote)
        self.assertIn("border = null", quote)
        self.assertIn("shadowElevation = 0.dp", quote)
        self.assertNotIn("BorderStroke(", quote)

    def test_nav_patch_only_touches_shell_not_tab_actions(self):
        snippet = (
            '@Composable\nprivate fun StandaloneBottomNav(\n'
            '  current: Route,\n) {\n'
            '    val panelShape = RoundedCornerShape(16.dp)\n'
            '    Box(modifier.fillMaxWidth()) {\n'
            '        Box(\n'
            '            Modifier.fillMaxWidth().navigationBarsPadding()\n'
            '                .padding(start = 13.dp, end = 13.dp, top = 4.dp, bottom = 4.dp),\n'
            '        ) {\n'
            '            Box(\n'
            '                Modifier.fillMaxWidth()\n'
            '                    .clip(panelShape)\n'
            '                    .background(if (dark) MaterialTheme.colorScheme.surface else Color(0xFFF2E8D9))\n'
            '                    .border(\n'
            '                        width = 0.9.dp,\n'
            '                        color = if (dark) MaterialTheme.colorScheme.outline else Color(0xFFCDBBA2),\n'
            '                        shape = panelShape,\n'
            '                    ),\n'
            '            ) {\n'
            '                if (!dark) {\n'
            '                    Image(\n'
            '                        painter = MedicineHomeArtwork.painter(R.drawable.antique_card_paper),\n'
            '                        contentDescription = null,\n'
            '                        modifier = Modifier.matchParentSize(),\n'
            '                        contentScale = ContentScale.Crop,\n'
            '                        alpha = 0.40f,\n'
            '                    )\n'
            '                }\n'
            '                Row(\n'
            '                    items.forEach { item -> item.action() }\n'
            '                )\n'
            '            }\n'
            '        }\n'
            '    }\n'
            '}\n'
        )
        changed = patch_bottom_nav(snippet)
        self.assertIn('items.forEach { item -> item.action() }', changed)
        self.assertIn("RoundedCornerShape(0.dp)", changed)
        self.assertNotIn(".border(", changed)
        self.assertNotIn("antique_card_paper", changed)
        self.assertIn("Color(0xFFF7F3EC)", changed)

    def test_nav_patch_fails_on_unrecognized_source(self):
        with self.assertRaises(RuntimeError):
            patch_bottom_nav("@Composable\nprivate fun StandaloneBottomNav(\n unexpected")


if __name__ == "__main__":
    unittest.main()
