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
target = root / "scripts/build_iman_v4.py"
target.write_text(s, encoding="utf-8")
print("Unpacked verified v0.4 reader adapter:", target, len(s), "characters")
