"""v0.46.0: apply only the user-approved light parchment Android launcher icon.

Builds on the latest v0.45.9 native app. Launcher XML and AndroidManifest are
unchanged; only their existing foreground and legacy bitmap resources change.
No book data, quiz, user storage, reader or navigation source is changed.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

from scripts.build_iman_v459 import build_v459
from scripts.build_iman_v20 import APP, NAV, replace_one

ICON_SHA = "9390a83b5bc6948c3480501b7281e2a0f47d7d1011bb9a797857ed925bf14ae6"
ICON_PATH = Path("assets/ui/v460/iman_approved_source.webp")
ICON_TARGETS = {
    "drawable-nodpi/iman_v39_launcher_foreground.webp",
    "mipmap-anydpi/iman_v39_launcher.webp",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def icon_resources(kit: Path, res: Path) -> None:
    source = kit / ICON_PATH
    if digest(source) != ICON_SHA:
        raise RuntimeError("Selected/approved icon bytes changed")
    with Image.open(source) as opened:
        if opened.format != "WEBP" or opened.size != (256, 256) or opened.mode != "RGB":
            raise RuntimeError("Approved square icon format invalid")
        art = opened.copy()

    # Android adaptive masks (circle, squircle, rounded square) crop the edge.
    # Keep the approved artwork intact with a slight optical safety inset.
    canvas = Image.new("RGBA", (512, 512), (232, 210, 187, 255))
    subject = art.resize((472, 472), Image.Resampling.LANCZOS).convert("RGBA")
    canvas.alpha_composite(subject, (20, 20))
    foreground = res / "drawable-nodpi/iman_v39_launcher_foreground.webp"
    foreground.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(foreground, "WEBP", lossless=True, method=6, exact=True)

    # Existing pre-Android-8 bitmap resource keeps the same supplied design.
    legacy = res / "mipmap-anydpi/iman_v39_launcher.webp"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    art.resize((512, 512), Image.Resampling.LANCZOS).save(
        legacy, "WEBP", quality=96, method=6
    )
    for target in (foreground, legacy):
        with Image.open(target) as image:
            if image.size != (512, 512) or image.getbbox() is None:
                raise RuntimeError("Android launcher asset empty or resized")


def build_v460(kit: Path, dest: Path) -> None:
    build_v459(kit, dest)
    java = dest / APP
    assets = dest / "app/src/main/assets"
    res = dest / "app/src/main/res"
    manifest = dest / "app/src/main/AndroidManifest.xml"
    gradle = dest / "app/build.gradle"

    before_nav = (java / "App.kt").read_text("utf-8")
    before_manifest = manifest.read_bytes()
    before_java = {p.name: digest(p) for p in java.glob("*.kt")}
    before_assets = {p.name: digest(p) for p in assets.iterdir() if p.is_file()}
    before_res = {
        str(p.relative_to(res)): digest(p)
        for p in res.rglob("*") if p.is_file()
    }
    for attr in ('android:icon="@mipmap/iman_v39_launcher"',
                 'android:roundIcon="@mipmap/iman_v39_launcher"'):
        if attr not in before_manifest.decode("utf-8"):
            raise RuntimeError("Unexpected Android icon resource wiring")
    if NAV not in before_nav:
        raise RuntimeError("Native five-tab navigator missing")

    version = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 59", "versionCode 60"),
        ("versionName '0.45.9'", "versionName '0.46.0'"),
        ("applicationIdSuffix '.preview459'", "applicationIdSuffix '.preview460'"),
    ):
        version = replace_one(version, old, new, "v460 isolated icon preview")
    gradle.write_text(version, "utf-8")

    icon_resources(kit, res)

    for file, sha in before_java.items():
        if digest(java / file) != sha:
            raise RuntimeError("Unexpected modification to Kotlin: " + file)
    for file, sha in before_assets.items():
        if digest(assets / file) != sha:
            raise RuntimeError("Unexpected modification to book/quiz data: " + file)
    for file, sha in before_res.items():
        if file not in ICON_TARGETS and digest(res / file) != sha:
            raise RuntimeError("Unexpected change to existing artwork: " + file)
    if manifest.read_bytes() != before_manifest or (java / "App.kt").read_text("utf-8") != before_nav:
        raise RuntimeError("Android activity, manifest or navigator modified")

    book = json.loads((assets / "book.json").read_text("utf-8"))
    quiz = json.loads((assets / "quiz.json").read_text("utf-8"))
    quotes = json.loads((assets / "featured_quotes.json").read_text("utf-8"))
    if len(book["chapters"]) != 131 or len(quiz["chapters"]) != 131 or len(quotes) != 79:
        raise RuntimeError("Protected 131 chapters / 79 excerpts inventory changed")

    print("PASS v460: user-approved parchment icon installed in adaptive and legacy launcher",
          "resource; native reader, navigation, book and quiz content unchanged")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args()
    build_v460(Path(__file__).resolve().parents[1], args.dest)
