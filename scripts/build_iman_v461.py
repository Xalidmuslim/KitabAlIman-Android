"""v0.46.1 — unified brand artwork for native Home, More and Android launcher.

Preserve 131 book/quiz chapters, 79 quotes, all routes, user state, v460
launcher XML and every approved UI optimization. Only change two header
images and the three resource bitmaps dedicated to this icon.
"""
from pathlib import Path
import argparse
import hashlib
import json
from PIL import Image

from scripts.build_iman_v460 import build_v460
from scripts.build_iman_v20 import APP, NAV, replace_one

ICON_SHA = "68a4e51a72d51daf06fca7beec07ac20ea97a141050a3cd998436f0f70a00965"
ICON_PATH = Path("assets/ui/v461/iman_v461_brand_icon.webp")
TARGETS = {
    "drawable-nodpi/iman_v39_launcher_foreground.webp",
    "mipmap-anydpi/iman_v39_launcher.webp",
    "drawable-nodpi/iman_v461_brand_icon.webp",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def patch_inapp_brand(java: Path):
    home = java/"ModernEditorialHome.kt"
    more = java/"ImanV38More.kt"

    text = home.read_text("utf-8")
    old = "R.drawable.iman_v39_header"
    if text.count(old) != 1:
        raise RuntimeError("Home header resource count changed")
    updated = text.replace(old, "R.drawable.iman_v461_brand_icon")
    # No background or clip added: the source has antialiased transparent edges.
    home.write_text(updated, "utf-8")

    text = more.read_text("utf-8")
    if text.count('Text("Ещё",') != 1:
        raise RuntimeError("More-page title row changed")
    if "import androidx.compose.foundation.Image" not in text:
        text = text.replace("import androidx.compose.foundation.clickable",
                            "import androidx.compose.foundation.Image\nimport androidx.compose.foundation.clickable", 1)
    if "import androidx.compose.ui.layout.ContentScale" not in text:
        text = text.replace("import androidx.compose.ui.Modifier",
                            "import androidx.compose.ui.Modifier\nimport androidx.compose.ui.layout.ContentScale", 1)
    art = """Image(
                painter = MedicineHomeArtwork.painter(R.drawable.iman_v461_brand_icon),
                contentDescription = null,
                modifier = Modifier.size(38.dp),
                contentScale = ContentScale.Fit,
            )
            Spacer(Modifier.width(9.dp))
            """
    text = text.replace('Text("Ещё",', art + 'Text("Ещё",', 1)
    more.write_text(text, "utf-8")


def generate_launcher(kit: Path, res: Path):
    source = kit/ICON_PATH
    if digest(source) != ICON_SHA:
        raise RuntimeError("Uploaded icon digest does not match the approved asset")
    with Image.open(source) as image:
        if image.size != (160,160) or image.mode != "RGBA":
            raise RuntimeError("Icon lost its transparency or square proportions")
        original = image.copy()
    drawable = res/"drawable-nodpi"
    mipmap = res/"mipmap-anydpi"
    drawable.mkdir(parents=True, exist_ok=True)
    mipmap.mkdir(parents=True, exist_ok=True)
    new_art = drawable/"iman_v461_brand_icon.webp"
    new_art.write_bytes(source.read_bytes())

    # Safe optical margin for Android's circular/squircle adaptive masks;
    # transparent empty space, not a second beige/grey rectangular plate.
    foreground = Image.new("RGBA", (512,512), (0,0,0,0))
    fitted = original.resize((344,344), Image.Resampling.LANCZOS)
    foreground.alpha_composite(fitted, (84,84))
    foreground.save(drawable/"iman_v39_launcher_foreground.webp",
                    "WEBP", lossless=True, method=6, exact=True)
    legacy = original.resize((480,480),Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA",(512,512),(0,0,0,0))
    canvas.alpha_composite(legacy,(16,16))
    canvas.save(mipmap/"iman_v39_launcher.webp",
                "WEBP",lossless=True,method=6,exact=True)


def build_v461(kit: Path, dest: Path):
    build_v460(kit, dest)
    java=dest/APP
    assets=dest/"app/src/main/assets"
    res=dest/"app/src/main/res"
    manifest=dest/"app/src/main/AndroidManifest.xml"
    gradle=dest/"app/build.gradle"
    before_nav=(java/"App.kt").read_text("utf-8")
    before_manifest=manifest.read_bytes()
    protected_java={p.name:digest(p) for p in java.glob("*.kt") if p.name not in (
        "ModernEditorialHome.kt","ImanV38More.kt")}
    assets_before={p.name:digest(p) for p in assets.iterdir() if p.is_file()}
    res_before={str(p.relative_to(res)):digest(p) for p in res.rglob("*") if p.is_file()}

    config=gradle.read_text("utf-8")
    for old,new in (
        ("versionCode 60","versionCode 61"),
        ("versionName '0.46.0'","versionName '0.46.1'"),
        ("applicationIdSuffix '.preview460'","applicationIdSuffix '.preview461'"),
    ):
        config=replace_one(config,old,new,"v461 parallel-safe preview")
    gradle.write_text(config,"utf-8")

    patch_inapp_brand(java)
    generate_launcher(kit,res)

    for name,checksum in protected_java.items():
        if digest(java/name)!=checksum:
            raise RuntimeError("Unrelated Kotlin changed: "+name)
    for name,checksum in assets_before.items():
        if digest(assets/name)!=checksum:
            raise RuntimeError("Book or quiz data changed: "+name)
    for name,checksum in res_before.items():
        if name not in TARGETS and digest(res/name)!=checksum:
            raise RuntimeError("Unrelated resource changed: "+name)
    if (java/"App.kt").read_text("utf-8")!=before_nav or NAV not in before_nav:
        raise RuntimeError("Five-tab navigation/user state changed")
    if manifest.read_bytes()!=before_manifest:
        raise RuntimeError("Android manifest changed")
    book=json.loads((assets/"book.json").read_text("utf-8"))
    quiz=json.loads((assets/"quiz.json").read_text("utf-8"))
    quotes=json.loads((assets/"featured_quotes.json").read_text("utf-8"))
    if len(book["chapters"])!=131 or len(quiz["chapters"])!=131 or len(quotes)!=79:
        raise RuntimeError("Protected content counts changed")
    for name in ("ModernEditorialHome.kt","ImanV38More.kt"):
        if (java/name).read_text("utf-8").count("R.drawable.iman_v461_brand_icon")!=1:
            raise RuntimeError("Brand icon not integrated into "+name)
    print("PASS v461: transparent icon in Home, More, launcher; 131 chapters/79 quotes intact")


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--dest",required=True,type=Path)
    args=ap.parse_args()
    build_v461(Path(__file__).resolve().parents[1],args.dest)
