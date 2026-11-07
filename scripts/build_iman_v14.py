"""Kitab al-Iman v0.14: rotating sourced quotes and integrated 3D book visuals.

Reader data, original footnotes, bookmarks, navigation and memory exercises remain unchanged.
"""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import lzma
import re

from scripts.build_iman_v13 import build_v13

JAVA = Path("app/src/main/java/com/xalid/meditsinaproroka/nativeapp")
NAV = "@Composable\nprivate fun StandaloneBottomNav("
ASSET_DIGEST = "b7b494119aa4ce84b0697a3a8fd49da066ad1e6142f581b0cef2d55fe111f1fb"

def one(source, old, new, label):
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 pinned anchor, got {count}")
    return source.replace(old,new,1)

def segment(source, first, last, new, label):
    if source.count(first) != 1 or source.count(last) != 1:
        raise RuntimeError(f"{label}: missing or duplicate boundaries")
    start, end = source.index(first), source.index(last)
    if start >= end:
        raise RuntimeError(f"{label}: reversed boundaries")
    return source[:start] + new + source[end:]

HOME_CARD = '''@Composable
private fun IbnHomeLink(
    label: String, count: String, icon: Int, modifier: Modifier, onClick: () -> Unit,
) {
    val dark = sepiaDark()
    val ink = if (dark) MaterialTheme.colorScheme.onSurface else SepiaInk
    val muted = if (dark) MaterialTheme.colorScheme.onSurfaceVariant else SepiaMuted
    SepiaPanel(modifier.heightIn(min = 96.dp), onClick) {
        Box(Modifier.fillMaxWidth().heightIn(min = 96.dp)) {
            if (!dark) {
                // Original generated WebP alpha: independent 3D object, no image background.
                Image(MedicineHomeArtwork.painter(icon), contentDescription = null,
                    modifier = Modifier.align(Alignment.BottomEnd)
                        .size(width = 100.dp, height = 85.dp),
                    contentScale = ContentScale.Fit)
            }
            Column(Modifier.align(Alignment.CenterStart).fillMaxWidth(0.73f)
                .padding(start = 11.dp, top = 9.dp, bottom = 9.dp)) {
                Text(label, fontFamily = WebLiterataFont, fontSize = 14.5.sp,
                    lineHeight = 19.sp, fontWeight = FontWeight.Bold, color = ink)
                Spacer(Modifier.height(3.dp))
                Text(count, fontFamily = WebSansFont, fontSize = 10.5.sp,
                    lineHeight = 13.sp, color = muted)
            }
            Icon(Icons.Default.ChevronRight, null,
                Modifier.align(Alignment.TopEnd).padding(top = 6.dp, end = 3.dp).size(14.dp),
                tint = muted)
        }
    }
}

'''

def patch_style(source):
    source = segment(source, '            item(key = "quote") {',
        '            item(key = "reading-progress") {',
        '            item(key = "quote") {\n                ImanFeaturedQuoteCarousel(navigate)\n            }\n',
        "replace fixed quote with verified rotating component")
    for old,new in (
        ("R.drawable.antique_books_detail, Modifier.weight(1f))",
         "R.drawable.iman_section_contents, Modifier.weight(1f))"),
        ("R.drawable.antique_scroll_detail, Modifier.weight(1f))",
         "R.drawable.iman_section_collections, Modifier.weight(1f))"),
        ("R.drawable.iman_glossary_detail, Modifier.weight(1f))",
         "R.drawable.iman_section_glossary, Modifier.weight(1f))"),
        ("R.drawable.antique_bookmark_detail, Modifier.weight(1f))",
         "R.drawable.iman_section_bookmarks, Modifier.weight(1f))"),
    ):
        source = one(source,old,new,"distinct generated icon")
    source = segment(source, "@Composable\nprivate fun IbnHomeLink(",
        "@Composable\nprivate fun IbnCollectionLink(", HOME_CARD,
        "compact transparent 3D object cards")
    return source

def patch_player(source, new_function):
    edited = segment(source, "@Composable\nprivate fun ReaderChapterSpeechBar(",
        "@OptIn(ExperimentalMaterial3Api::class)\n@Composable\nprivate fun ReaderBlock(",
        new_function, "chapter TTS controls")
    if "Бесплатный нейроголос RuVoice (установка)" in edited:
        raise RuntimeError("Installation advertisement survived")
    return edited

def patch_progress(source, new_function):
    return segment(source,"@Composable\ninternal fun V38ReaderStatus(",
        "private data class V38ReviewQuestion(",new_function,
        "compact progress on original parchment")

def validate_quotes(book, kotlin):
    chapters = {c["id"]: c for c in book["chapters"]}
    records = re.findall(
        r'FeaturedExcerpt\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)"\)',
        kotlin, flags=re.MULTILINE)
    if len(records) != 7:
        raise RuntimeError("Expected exactly seven curated quotations")
    for chapter_id, block_id, excerpt in records:
        chapter = chapters.get(chapter_id)
        if chapter is None:
            raise RuntimeError("Incorrect quote chapter "+chapter_id)
        block = next((b for b in chapter["blocks"] if b["id"] == block_id),None)
        if block is None or excerpt not in block["text"]:
            raise RuntimeError("Quotation missing or modified: "+chapter_id+"/"+block_id)

def install_images(kit, root):
    from PIL import Image
    encoded = "".join((kit/"scripts/v14_art_pack.b64").read_text("ascii").splitlines())
    raw = lzma.decompress(base64.b64decode(encoded,validate=True))
    if hashlib.sha256(raw).hexdigest() != ASSET_DIGEST:
        raise RuntimeError("Generated artwork checksum differs")
    mapping = json.loads(raw.decode("utf-8"))
    expected = {"iman_quote_background.webp","iman_section_contents.webp",
        "iman_section_collections.webp","iman_section_glossary.webp",
        "iman_section_bookmarks.webp"}
    if set(mapping) != expected:
        raise RuntimeError("Generated art inventory mismatch")
    target = root/"app/src/main/res/drawable-nodpi"
    target.mkdir(parents=True,exist_ok=True)
    for name, encoded_file in mapping.items():
        data = base64.b64decode(encoded_file,validate=True)
        file = target/name
        file.write_bytes(data)
        with Image.open(file) as art:
            if art.format != "WEBP":
                raise RuntimeError("Expected WebP artwork")
            if name.startswith("iman_section_"):
                if art.size != (320,280) or art.mode != "RGBA" or art.getchannel("A").getextrema() != (0,255):
                    raise RuntimeError("3D icon must have real transparency: "+name)
            elif art.size != (1280,520):
                raise RuntimeError("Quotation background has incorrect ratio")

def build_v14(kit, destination):
    build_v13(kit,destination)
    gradle = destination/"app/build.gradle"
    g=gradle.read_text("utf-8")
    for old,new in (
        ("versionCode 13","versionCode 14"),
        ("versionName '0.13.0'","versionName '0.14.0'"),
        ("applicationIdSuffix '.preview13'","applicationIdSuffix '.preview14'"),
    ):
        g=one(g,old,new,"version")
    gradle.write_text(g,"utf-8")
    src=destination/JAVA
    app=src/"App.kt"
    original=app.read_bytes()
    if NAV not in original.decode("utf-8"):
        raise RuntimeError("Bottom navigation anchor unavailable")
    bottom=original.decode("utf-8").split(NAV,1)[1]
    resources=destination/"app/src/main/res"
    icons={str(p.relative_to(resources)):p.read_bytes()
        for p in resources.rglob("*")
        if p.is_file() and (p.name.startswith("nav_") or p.name.startswith("ic_nav_"))}
    preserved={p.name:p.read_bytes() for p in src.glob("*.kt")
        if p.name not in ("IbnQayyimStyle.kt","Reader.kt","IbnV38StudyEngine.kt","MedicineHomeArtwork.kt")}
    quote=(kit/"scripts/ImanQuoteCarousel.kt").read_text("utf-8")
    validate_quotes(json.loads((destination/"app/src/main/assets/book.json").read_text("utf-8")),quote)
    (src/"ImanQuoteCarousel.kt").write_text(quote,"utf-8")
    style=src/"IbnQayyimStyle.kt"
    style.write_text(patch_style(style.read_text("utf-8")),"utf-8")
    speech=(kit/"scripts/v14_reader_player.kt").read_text("utf-8")
    reader=src/"Reader.kt"
    reader.write_text(patch_player(reader.read_text("utf-8"),speech),"utf-8")
    progress=(kit/"scripts/v14_reader_progress.kt").read_text("utf-8")
    engine=src/"IbnV38StudyEngine.kt"
    engine.write_text(patch_progress(engine.read_text("utf-8"),progress),"utf-8")
    preload=src/"MedicineHomeArtwork.kt"
    s=preload.read_text("utf-8")
    s=one(s,"        R.drawable.iman_glossary_detail,",
        """        R.drawable.iman_glossary_detail,
        R.drawable.iman_quote_background,
        R.drawable.iman_section_contents,
        R.drawable.iman_section_collections,
        R.drawable.iman_section_glossary,
        R.drawable.iman_section_bookmarks,""",
        "off-thread preload for generated images")
    preload.write_text(s,"utf-8")
    install_images(kit,destination)
    if app.read_text("utf-8").split(NAV,1)[1] != bottom:
        raise RuntimeError("Bottom navigation changed")
    for name,data in preserved.items():
        if (src/name).read_bytes()!=data:
            raise RuntimeError("Unrelated Kotlin code changed: "+name)
    for name,data in icons.items():
        if (resources/name).read_bytes()!=data:
            raise RuntimeError("Bottom navigation icon changed: "+name)
    if list((destination/"app/src/main").rglob("*.pdf")):
        raise RuntimeError("PDF may not be bundled")
    print("PASS v0.14: source-matched rotating quotations, unique alpha icons, book-style audio and paper-matched progress")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dest",type=Path,required=True)
    x=p.parse_args()
    build_v14(Path(__file__).resolve().parents[1],x.dest)
