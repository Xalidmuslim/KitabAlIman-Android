"""The chapter quiz CTA must look tappable without cards, fills or borders."""
import unittest
from pathlib import Path
from scripts.iman_v458_quiz_cta import patch_quiz_cta

ROOT = Path(__file__).resolve().parents[1]

class QuizCTA(unittest.TestCase):
    def test_renders_semantic_text_button_with_icon_arrow_no_frame(self):
        source = """package sample.book
import androidx.compose.material3.TextButton
fun quiz() {
    TextButton(onClick = { openQuiz() }, modifier = Modifier.fillMaxWidth()) {
        Text("Проверить прочитанное")
    }
}"""
        out = patch_quiz_cta(source)
        self.assertIn("TextButton(onClick = { openQuiz() }", out)
        self.assertIn("Icons.Default.CheckCircle", out)
        self.assertIn("Icons.Default.ChevronRight", out)
        self.assertIn('Text("Проверить прочитанное"', out)
        self.assertIn("FontWeight.SemiBold", out)
        self.assertIn("MaterialTheme.colorScheme.primary", out)
        self.assertIn("Modifier.size(19.dp)", out)
        self.assertNotIn("OutlinedButton(", out)
        self.assertNotIn("BorderStroke(", out)
        self.assertNotIn("containerColor =", out)
        self.assertEqual(out.count("openQuiz()"), 1)

    def test_does_not_misapply_to_non_quiz_routes(self):
        before = 'TextButton(onClick = { goBack() }) { Text("Назад") }'
        self.assertRaises(RuntimeError, patch_quiz_cta, before)

    def test_refuses_multiple_equal_labels(self):
        source = 'fun x() { Text("Проверить прочитанное"); Text("Проверить прочитанное") }'
        self.assertRaises(RuntimeError, patch_quiz_cta, source)

    def test_build_invariants(self):
        s=(ROOT/"scripts/build_iman_v458.py").read_text("utf-8")
        for value in ("build_v457", "versionCode 58", "0.45.8", "preview458",
                      "131", "79", "book.json", "quiz.json", "featured_quotes.json",
                      "ImanQuoteCarousel.kt", "App.kt"):
            self.assertIn(value, s)
        w=(ROOT/".github/workflows/build-iman-v458.yml").read_text("utf-8")
        self.assertIn("scripts.build_iman_v458 --dest AndroidApp",w)
        self.assertIn("test_iman_v458.py",w)
        self.assertIn("Publish installable APK",w)

if __name__=="__main__":
    unittest.main()
