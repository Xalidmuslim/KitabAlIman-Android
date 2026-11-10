"""Change the exact native chapter quiz label into a recognizable flat CTA.

The clickable TextButton and its onClick/enable modifiers are not replaced.
Only the decorative child text is converted into a horizontally centered
icon + semibold label + disclosure arrow using existing Material3 colors.
"""
import re
from pathlib import Path
from scripts.iman_v44_transform import matching

LABEL = "Проверить прочитанное"
LITERAL = re.compile(r'(?<![\w.])Text\s*\(\s*"Проверить прочитанное"')

REQUIRED_IMPORTS = (
    "androidx.compose.foundation.layout.Arrangement",
    "androidx.compose.foundation.layout.Row",
    "androidx.compose.foundation.layout.Spacer",
    "androidx.compose.foundation.layout.width",
    "androidx.compose.material.icons.Icons",
    "androidx.compose.material.icons.filled.CheckCircle",
    "androidx.compose.material.icons.filled.ChevronRight",
    "androidx.compose.material3.Icon",
    "androidx.compose.material3.MaterialTheme",
    "androidx.compose.material3.Text",
    "androidx.compose.ui.Alignment",
    "androidx.compose.ui.Modifier",
    "androidx.compose.ui.text.font.FontWeight",
    "androidx.compose.ui.unit.dp",
    "androidx.compose.ui.unit.sp",
)
REPLACEMENT = '''Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.Center,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(
            imageVector = Icons.Default.CheckCircle,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.primary,
            modifier = Modifier.size(19.dp),
        )
        Spacer(Modifier.width(10.dp))
        Text("Проверить прочитанное",
            fontWeight = FontWeight.SemiBold,
            fontSize = 16.sp,
            color = MaterialTheme.colorScheme.primary,
        )
        Spacer(Modifier.width(5.dp))
        Icon(
            imageVector = Icons.Default.ChevronRight,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.primary,
            modifier = Modifier.size(20.dp),
        )
    }'''


def patch_quiz_cta(source: str) -> str:
    matches = list(LITERAL.finditer(source))
    if len(matches) != 1:
        raise RuntimeError(f"Cannot uniquely locate quiz CTA; found {len(matches)}")
    m = matches[0]
    p = source.index("(", m.start())
    end = matching(source, p)
    result = source[:m.start()] + REPLACEMENT + source[end + 1:]
    # Add only imports not already present, to whichever Kotlin module owns the CTA.
    inject = "\n".join("import " + name for name in REQUIRED_IMPORTS
                       if ("import " + name + "\n") not in result)
    if inject:
        package = re.search(r"^package [^\n]+\n", result, re.MULTILINE)
        if not package:
            raise RuntimeError("Kotlin file has no declared package")
        result = result[:package.end()] + "\n" + inject + "\n" + result[package.end():]
    return result


def patch_generated(java: Path) -> str:
    files = (java/"FaithStudy.kt", java/"Reader.kt")
    sources = {file: file.read_text("utf-8") for file in files}
    candidates = [file for file, source in sources.items() if LITERAL.search(source)]
    if len(candidates) != 1:
        raise RuntimeError("Chapter quiz CTA source ambiguous: " + ", ".join(str(p) for p in candidates))
    target = candidates[0]
    fixed = patch_quiz_cta(sources[target])
    if fixed.count("Icons.Default.CheckCircle") != 1 or fixed.count("Icons.Default.ChevronRight") < 1:
        raise RuntimeError("Accessible quiz icon and arrow missing")
    target.write_text(fixed, "utf-8")
    return target.name
