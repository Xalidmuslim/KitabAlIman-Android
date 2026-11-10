"""v0.46.2 — user-supplied parchment image on Home and Android launcher.

Uses the latest native v0.46.1 chain, without affecting existing content,
settings icon, More row icons, reading routes, progress, user storage or quiz.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

from scripts.build_iman_v20 import APP, NAV, replace_one
from scripts.build_iman_v461 import build_v461, digest

SOURCE = Path("assets/ui/v462/iman_v462_reference.webp")
SOURCE_SHA = "af9ca88d701739f010f7a997550c7c9a41827b7334272b16a6ca311df8f2ac5f"

# Exactly the inserted v461 header decoration, not the regular settings gear
# and not the existing glyphs or navigation chevrons in the More list.
ADDED_MORE_ICON = """Image(
                painter = MedicineHomeArtwork.painter(R.drawable.iman_v461_brand_icon),
                contentDescription = null,
                modifier = Modifier.size(38.dp),
                contentScale = ContentScale.Fit,
            )
            Spacer(Modifier.width(9.dp))
            """


def remove_extra_more_brand_and_update_home(java: Path):
    home = java / "ModernEditorialHome.kt"
    more = java / "ImanV38More.kt"

    original_home = home.read_text("utf-8")
    if original_home.count("R.drawable.iman_v461_brand_icon") != 1:
        raise RuntimeError("Home branding contract changed")
    home.write_text(
        original_home.replace("R.drawable.iman_v461_brand_icon",
                              "R.drawable.iman_v462_brand_icon", 1),
        "utf-8",
    )

    text = more.read_text("utf-8")
    if text.count(ADDED_MORE_ICON) != 1:
        raise RuntimeError("Expected v461 More brand image not found exactly once")
    if text.count("R.drawable.iman_v461_brand_icon") != 1:
        raise RuntimeError("Unexpected other v461 brand use in More")
    result = text.replace(ADDED_MORE_ICON, "", 1)
    # v461 inserted these imports only for the added header image.
    for unwanted in ("import androidx.compose.foundation.Image\n",
                     "import androidx.compose.ui.layout.ContentScale\n"):
        if result.count(unwanted) != 1:
            raise RuntimeError("More imports changed; abort to protect menu")
        result = result.replace(unwanted, "", 1)
    more.write_text(result, "utf-8")


def install_user_brand(kit: Path, res: Path):
    source = kit / SOURCE
    if digest(source) != SOURCE_SHA:
        raise RuntimeError("The user-approved icon is missing or was modified")
    with Image.open(source) as src:
        if src.size != (192, 192) or src.mode != "RGB" or src.format != "WEBP":
            raise RuntimeError("Unexpected approved icon dimensions/format")
        art = src.copy()
    drawable = res / "drawable-nodpi"
    mipmap = res / "mipmap-anydpi"
    drawable.mkdir(parents=True, exist_ok=True)
    mipmap.mkdir(parents=True, exist_ok=True)
    (drawable / "iman_v462_brand_icon.webp").write_bytes(source.read_bytes())
    # Original user artwork fills the mask; its own textured parchment
    # already has sufficient visual margin around the scroll and feather.
    rendered = art.resize((512, 512), Image.Resampling.LANCZOS)
    rendered.save(drawable / "iman_v39_launcher_foreground.webp",
                  "WEBP", lossless=True, method=6)
    rendered.save(mipmap / "iman_v39_launcher.webp",
                  "WEBP", lossless=True, method=6)


def build_v462(kit: Path, dest: Path):
    build_v461(kit, dest)
    java = dest / APP
    res = dest / "app/src/main/res"
    assets = dest / "app/src/main/assets"
    manifest = dest / "app/src/main/AndroidManifest.xml"
    gradle = dest / "app/build.gradle"

    nav_before = (java / "App.kt").read_bytes()
    manifest_before = manifest.read_bytes()
    content_before = {p.name: digest(p) for p in assets.iterdir() if p.is_file()}
    java_before = {p.name: digest(p) for p in java.glob("*.kt")
                   if p.name not in ("ModernEditorialHome.kt", "ImanV38More.kt")}
    more_source = (kit / "scripts/ImanUnifiedMoreV44.kt").read_text("utf-8")

    configuration = gradle.read_text("utf-8")
    for old, new in (
        ("versionCode 61", "versionCode 62"),
        ("versionName '0.46.1'", "versionName '0.46.2'"),
        ("applicationIdSuffix '.preview461'", "applicationIdSuffix '.preview462'"),
    ):
        configuration = replace_one(configuration, old, new, "v462 isolated icon fix")
    gradle.write_text(configuration, "utf-8")

    remove_extra_more_brand_and_update_home(java)
    install_user_brand(kit, res)

    if (java / "ImanV38More.kt").read_text("utf-8") != more_source:
        raise RuntimeError("More menu changed beyond removal of the new brand icon")
    if (java / "App.kt").read_bytes() != nav_before or NAV not in nav_before.decode():
        raise RuntimeError("Five-tab navigator changed")
    if manifest.read_bytes() != manifest_before:
        raise RuntimeError("Android manifest changed")
    for name, checksum in content_before.items():
        if digest(assets/name) != checksum:
            raise RuntimeError("Protected book/quiz/user asset changed: " + name)
    for name, checksum in java_before.items():
        if digest(java/name) != checksum:
            raise RuntimeError("Unrelated Kotlin changed: " + name)

    book = json.loads((assets/"book.json").read_text("utf-8"))
    quiz = json.loads((assets/"quiz.json").read_text("utf-8"))
    quotes = json.loads((assets/"featured_quotes.json").read_text("utf-8"))
    if len(book["chapters"]) != 131 or len(quiz["chapters"]) != 131 or len(quotes) != 79:
        raise RuntimeError("Protected 131 chapters or 79 quotes changed")
    home = (java/"ModernEditorialHome.kt").read_text("utf-8")
    more = (java/"ImanV38More.kt").read_text("utf-8")
    if home.count("R.drawable.iman_v462_brand_icon") != 1:
        raise RuntimeError("New image missing on Home")
    if "R.drawable.iman_v462_brand_icon" in more:
        raise RuntimeError("Extra branding icon present in More")
    print("PASS v462: user image on Home/launcher; original icon-rich More restored; 131 chapters, 79 quotes preserved")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True, type=Path)
    args = ap.parse_args()
    build_v462(Path(__file__).resolve().parents[1], args.dest)
