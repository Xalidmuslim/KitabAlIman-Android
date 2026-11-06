"""Expand and verify the v0.6 source bundle after checkout."""
from pathlib import Path
import base64
import hashlib
import json
import lzma

root = Path(__file__).resolve().parents[1]
pieces = [root / "scripts" / "v6_bundle" / f"part{i}.txt" for i in range(4)]
encoded = "".join(p.read_text(encoding="ascii").strip() for p in pieces)
assert len(encoded) == 12800, "v0.6 payload transport size mismatch"
raw = lzma.decompress(base64.b64decode(encoded, validate=True))
expected = "b6033a05062a071755a2265994492cfc63abc8b1cded55147f410c9f09986c12"
assert hashlib.sha256(raw).hexdigest() == expected, "v0.6 payload checksum mismatch"
files = json.loads(raw.decode("utf-8"))
assert set(files) == {"scripts/reader_study_v6.py","scripts/build_iman_v6.py","scripts/faith_study_ui_v6.kt","tests/test_iman_v6.py"}
for rel, content in files.items():
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
print("Verified and extracted", len(files), "native book study modules")
