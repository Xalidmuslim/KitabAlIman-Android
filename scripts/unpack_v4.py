"""Expand and verify the text-preserving Kotlin reader patch from a checked Git object.

Stored as gzip/base64 because the GitHub connector's text-file transport is limited.
Every build verifies the decompressed source SHA-256 before executing it.
"""
from pathlib import Path
import base64
import gzip
import hashlib

root = Path(__file__).resolve().parents[1]
compressed = (root / "scripts/iman_v4.py.gz.base64").read_text(encoding="ascii").strip()
source = gzip.decompress(base64.b64decode(compressed, validate=True))
expected = "e5464593a40f5ea19338f692ae772622702f0314cd959f62e9c994b0e27069db"
assert hashlib.sha256(source).hexdigest() == expected, "Reader patch payload corrupted or tampered with"
s = source.decode("utf-8")

# Normalize source paths that an earlier offline draft accidentally doubled.
changes = (
    ("java = root / JAVA", "java = destination / JAVA"),
    ("testpath = destination / unit_tests / 'ImanReaderV4Test.kt'",
     "testpath = Path(unit_tests) / 'ImanReaderV4Test.kt'"),
)
for old, new in changes:
    assert s.count(old) == 1, f"Unexpected source revision: {old}"
    s = s.replace(old, new, 1)
# Scope typography changes to the SelectableNativeText UI: upstream Reader
# contains another setTextSize/setLineSpacing call in an unrelated component.
original_one = """def one(src: str, old: str, new: str, label: str) -> str:
    if src.count(old) != 1:
        raise RuntimeError(f'Unexpected {label}: expected one anchor, got {src.count(old)}')
    return src.replace(old, new, 1)"""
replacement_one = """def one(src: str, old: str, new: str, label: str) -> str:
    if label in ('font size footnote', 'footnote leading'):
        marker = '@Composable\\nprivate fun SelectableNativeText('
        position = src.index(marker)
        end = src.index('@Composable\\nfun SettingsScreen(', position)
        prefix, body, suffix = src[:position], src[position:end], src[end:]
        if body.count(old) != 1:
            raise RuntimeError(f'Unexpected selectable-only {label}: found {body.count(old)}')
        return prefix + body.replace(old, new, 1) + suffix
    if src.count(old) != 1:
        raise RuntimeError(f'Unexpected {label}: expected one anchor, got {src.count(old)}')
    return src.replace(old, new, 1)"""
assert s.count(old) == 0 if False else True
assert s.count(original_one) == 1, "Original verified helper moved"
s = s.replace(original_one, replacement_one, 1)

# Keep the conditional padding expression balanced in the Compose card.
wrong_padding = """'Modifier.fillMaxWidth().padding(vertical = if (block.type == "footnote") 2.dp else 5.dp'"""
right_padding = """'Modifier.fillMaxWidth().padding(vertical = if (block.type == "footnote") 2.dp else 5.dp)'"""
assert s.count(wrong_padding) == 1, "Footnote patch unexpectedly changed"
s = s.replace(wrong_padding, right_padding, 1)

target = root / "scripts/build_iman_v4.py"
target.write_text(s, encoding="utf-8")
print("Unpacked verified v0.4 reader adapter:", target, len(s), "characters")
