"""v0.8 — approved illustrated hero and app launcher identity."""
from pathlib import Path
from io import BytesIO
from urllib.request import Request, urlopen
import argparse
import hashlib
import shutil
from scripts.build_iman_v7 import build_v7

ASSETS = (
    ("iman_home_banner.webp", "antique_hero_refined.webp",
     "https://gcdn.picsart.com/picsart-mcp/6e6b1e65-8b64-4b04-b090-9d640de69780.png",
     "f917d41e80f3e6e71fc6d13ac12ab42ed6179a05821cbceea154f2168c89fc6d", (1280, 427)),
    ("iman_launcher_icon.webp", "medicine_launcher_book.webp",
     "https://gcdn.picsart.com/picsart-mcp/5fba7d78-11e1-4250-bf27-22aa3e4cd970.png",
     "1cf2e4bb68cb1a5b95f4e6a6cc7ae2a775db16a244d6b9c9dd180710c9f10c00", (512, 512)),
)

def one(source, old, new):
    if source.count(old) != 1:
        raise RuntimeError("Pinned layout changed: " + old[:60])
    return source.replace(old, new, 1)

def patch_home(source):
    start = "@Composable\nprivate fun AntiqueHomeHeader(book: BookData, onSettings: () -> Unit) {"
    end = "@Composable\nprivate fun ReadingCard("
    if source.count(start) != 1 or source.count(end) != 1:
        raise RuntimeError("Original home component missing")
    a, b = source.index(start), source.index(end)
    original = source[a:b]
    if "antique_hero_refined" not in original or "medicine_launcher_book" not in original:
        raise RuntimeError("Unexpected home header")
    source = one(source, "import androidx.compose.material.icons.filled.ChevronRight",
                 "import androidx.compose.material.icons.filled.ChevronRight\nimport androidx.compose.material.icons.filled.Settings")
    modern = """@Composable
private fun AntiqueHomeHeader(book: BookData, onSettings: () -> Unit) {
    val dark = MaterialTheme.colorScheme.background.red < 0.25f
    if (dark) {
        Row(
            Modifier.fillMaxWidth().statusBarsPadding()
                .padding(horizontal = 15.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                Text(book.title, fontFamily = WebLiterataFont,
                    fontWeight = FontWeight.Bold, fontSize = 20.sp)
                Text(book.author, fontFamily = WebSansFont,
                    color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 11.sp)
            }
            IconButton(onClick = onSettings) {
                Icon(Icons.Default.Settings, contentDescription = "Настройки чтения")
            }
        }
    } else {
        BoxWithConstraints(Modifier.fillMaxWidth()) {
            // Exactly 3:1; preserve the whole art rather than arbitrary cropping.
            val bannerHeight = maxWidth / 3f
            Box(Modifier.fillMaxWidth().height(bannerHeight)) {
                Image(
                    MedicineHomeArtwork.painter(R.drawable.antique_hero_refined),
                    contentDescription = book.title + " — " + book.author,
                    modifier = Modifier.matchParentSize(),
                    contentScale = ContentScale.FillBounds,
                )
                Box(
                    Modifier.fillMaxWidth().height(25.dp)
                        .align(Alignment.TopCenter)
                        .background(Color(0xFFF5E9DA).copy(alpha = 0.42f)),
                )
                IconButton(
                    onClick = onSettings,
                    modifier = Modifier.align(Alignment.TopEnd).statusBarsPadding()
                        .padding(top = 3.dp, end = 10.dp).size(38.dp)
                        .clip(CircleShape)
                        .background(Color(0xFFF8EBDD).copy(alpha = 0.88f)),
                ) {
                    Icon(Icons.Default.Settings, contentDescription = "Настройки чтения",
                        modifier = Modifier.size(20.dp), tint = AntiqueInk)
                }
            }
        }
    }
}

"""
    return source.replace(original, modern, 1)

def image_for(kit, image_name, url, expected_sha, size):
    from PIL import Image
    folder = kit / "assets/ui"
    folder.mkdir(parents=True, exist_ok=True)
    saved = folder / image_name
    if saved.is_file():
        with Image.open(saved) as image:
            if image.format != "WEBP" or image.size != size:
                raise RuntimeError("Invalid vendored WebP: " + image_name)
        return saved
    with urlopen(Request(url, headers={"User-Agent": "KitabAlIman-Android/0.8"}), timeout=45) as response:
        raw = response.read(6_000_000)
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise RuntimeError("Approved artwork checksum mismatch: " + image_name)
    with Image.open(BytesIO(raw)) as source:
        if source.format != "PNG":
            raise RuntimeError("Approved artwork is not a PNG")
        source.convert("RGB").resize(size, Image.Resampling.LANCZOS).save(
            saved, "WEBP", quality=80, method=6)
    return saved

def build_v8(kit, destination):
    build_v7(kit, destination)
    gradle = destination / "app/build.gradle"
    s = gradle.read_text(encoding="utf-8")
    for old, new in (("versionCode 7", "versionCode 8"),
                     ("versionName '0.7.0'", "versionName '0.8.0'"),
                     ("applicationIdSuffix '.preview7'", "applicationIdSuffix '.preview8'")):
        s = one(s, old, new)
    gradle.write_text(s, encoding="utf-8")
    home = destination / "app/src/main/java/com/xalid/meditsinaproroka/nativeapp/AntiqueDesign.kt"
    home.write_text(patch_home(home.read_text(encoding="utf-8")), encoding="utf-8")
    res = destination / "app/src/main/res/drawable-nodpi"
    for name, original, url, sha, size in ASSETS:
        art = image_for(kit, name, url, sha, size)
        shutil.copy2(art, res / original)
    if list((destination/"app/src/main").rglob("*.pdf")):
        raise RuntimeError("PDF found in app")
    print("Applied v0.8 approved 3:1 hero and launcher icon")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dest", type=Path, required=True)
    args = p.parse_args()
    build_v8(Path(__file__).resolve().parents[1], args.dest)
