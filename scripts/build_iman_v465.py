"""v0.46.5: replace only the reminder illustration with approved manuscript art.

v0.46.4 is preserved as the parent. Book, quizzes, typography, navigation,
reading progress, launcher assets and all other images stay untouched.
"""
import argparse
import base64
import hashlib
import io
from pathlib import Path

from PIL import Image
from scripts.build_iman_v464 import build_v464
from scripts.build_iman_v20 import APP, replace_one

SOURCE = "assets/ui/v465/iman_v465_scroll.webp.b64"
DIGEST = "642c5612caf458929d2eff5660da849f82269376f24306b684464dd8a8b84e7c"
DRAWABLE = "iman_v465_scroll"


def build_v465(kit: Path, dest: Path) -> None:
    build_v464(kit, dest)
    image_data = base64.b64decode((kit / SOURCE).read_text("ascii").strip(), validate=True)
    if hashlib.sha256(image_data).hexdigest() != DIGEST:
        raise RuntimeError("Approved manuscript art is missing or altered")
    with Image.open(io.BytesIO(image_data)) as picture:
        if picture.size != (256, 225) or picture.mode != "RGBA":
            raise RuntimeError("Reminder artwork must be 256x225 RGBA WebP")
        if picture.getchannel("A").getextrema()[0] != 0:
            raise RuntimeError("Reminder artwork has no transparent edges")
    target = dest / "app/src/main/res/drawable-nodpi" / (DRAWABLE + ".webp")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(image_data)
    quote_path = dest / APP / "ImanQuoteCarousel.kt"
    quote = quote_path.read_text("utf-8")
    quote = replace_one(
        quote,
        "R.drawable.iman_v464_reminder_feathered",
        "R.drawable." + DRAWABLE,
        "replace only the approved reminder picture",
    )
    if "navigate(Route.Reader(q.chapterId, q.blockId))" not in quote:
        raise RuntimeError("Existing exact-fragment reminder link disappeared")
    quote_path.write_text(quote, "utf-8")
    gradle = dest / "app/build.gradle"
    source = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 64", "versionCode 65"),
        ("versionName '0.46.4'", "versionName '0.46.5'"),
        ("applicationIdSuffix '.preview464'", "applicationIdSuffix '.preview465'"),
    ):
        source = replace_one(source, old, new, "v0.46.5 version")
    gradle.write_text(source, "utf-8")
    print("PASS: v0.46.5 approved manuscript asset applied; existing functionality retained")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", required=True, type=Path)
    args = parser.parse_args()
    build_v465(Path(__file__).resolve().parents[1], args.dest)
