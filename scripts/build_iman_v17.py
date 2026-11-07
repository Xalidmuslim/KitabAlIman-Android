"""v0.17: install five approved light sepia illustrations without stretching.

Book text, bookmarks, progress, quizzes and inherited bottom navigation are unchanged.
"""
from pathlib import Path
import argparse
import hashlib
from PIL import Image
from scripts.build_iman_v16 import build_v16, once

JAVA = Path("app/src/main/java/com/xalid/meditsinaproroka/nativeapp")
NAV = "@Composable\nprivate fun StandaloneBottomNav("
ART = {
    "iman_v17_quote.webp": ("220cc6ab2840109ec962f9bea4df556f7d9bd4ef7f2b38b69d121b0d9581a659", (280, 248)),
    "iman_v17_contents.webp": ("c985fb21c5a8391fd9e7237e0707d02fac54f64c464d9c3b35aacdee356f3910", (184, 158)),
    "iman_v17_collections.webp": ("f6d23a509644b883d0a70e58d89bb75d622aa88c9be27da7ad98992ae0e469e5", (184, 158)),
    "iman_v17_glossary.webp": ("6dc7b9b39c0d89f6726e4985e2e06e8dfd351617ec74b34b4cff3bcf9f1c0a5f", (184, 158)),
    "iman_v17_bookmarks.webp": ("8511449cb436c11bd9e28c28cbc8ed263cedc75c3e8521404299761b975d2a90", (184, 158)),
}

def install_artwork(kit: Path, dest: Path):
    res = dest / "app/src/main/res/drawable-nodpi"
    res.mkdir(parents=True,exist_ok=True)
    for name, (digest, dims) in ART.items():
        source = kit / "assets/ui/v17" / name
        data = source.read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise RuntimeError("Modified source art: " + name)
        with Image.open(source) as im:
            if im.format != "WEBP" or im.size != dims or im.mode != "RGBA":
                raise RuntimeError("Incorrect resource format: " + name)
            alpha=im.getchannel("A")
            if alpha.getextrema()[0] != 0 or alpha.getextrema()[1] < 180:
                raise RuntimeError("Expected faded/transparent artwork: " + name)
            if alpha.getpixel((0,0)) != 0:
                raise RuntimeError("Image corner is not transparent: " + name)
        (res / name).write_bytes(data)

def patch_quote(source: str) -> str:
    source = once(source,
        """            if (!dark) Image(
                painter = MedicineHomeArtwork.painter(R.drawable.iman_quote_v15),
                contentDescription = null, modifier = Modifier.matchParentSize(),
                contentScale = ContentScale.FillBounds)""",
        """            if (!dark) Image(
                painter = MedicineHomeArtwork.painter(R.drawable.iman_v17_quote),
                contentDescription = null,
                modifier = Modifier.align(Alignment.BottomEnd)
                    .size(width = 174.dp, height = 200.dp),
                contentScale = ContentScale.Fit)""",
        "background must be fixed-size and preserve aspect ratio")
    source = once(source,
        "Color(0xFFF6E3C9)",
        "Color(0xFFF9ECD9)",
        "lighter approved reminder surface")
    for token in (
        'Text("Другая ↻"', "Route.Reader(q.chapterId, q.blockId)",
        "private val imanExcerpts = listOf(",
        "Modifier.fillMaxWidth(0.70f)",
    ):
        if token not in source:
            raise RuntimeError("Reminder behavior was altered: " + token)
    if "ContentScale.FillBounds" in source:
        raise RuntimeError("Reminder still stretches background")
    return source

def patch_home(source: str) -> str:
    swaps = (
        ("R.drawable.iman_section_contents, Modifier.weight(1f))",
         "R.drawable.iman_v17_contents, Modifier.weight(1f))"),
        ("R.drawable.iman_section_collections, Modifier.weight(1f))",
         "R.drawable.iman_v17_collections, Modifier.weight(1f))"),
        ("R.drawable.iman_section_glossary, Modifier.weight(1f))",
         "R.drawable.iman_v17_glossary, Modifier.weight(1f))"),
        ("R.drawable.iman_section_bookmarks, Modifier.weight(1f))",
         "R.drawable.iman_v17_bookmarks, Modifier.weight(1f))"),
    )
    for old,new in swaps:
        source = once(source,old,new,"section resource reference")
    if "width = 76.dp, height = 65.dp" not in source:
        raise RuntimeError("Approved compact card size was altered")
    if "ContentScale.Fit" not in source:
        raise RuntimeError("Section icon lost aspect-preserving scaling")
    return source

def build_v17(kit: Path, dest: Path):
    build_v16(kit,dest)
    gradle=dest/"app/build.gradle"
    g=gradle.read_text("utf-8")
    for old,new in (
        ("versionCode 16","versionCode 17"),
        ("versionName '0.16.0'","versionName '0.17.0'"),
        ("applicationIdSuffix '.preview16'","applicationIdSuffix '.preview17'"),
    ):
        g=once(g,old,new,"version change")
    gradle.write_text(g,"utf-8")

    root=dest/JAVA
    app=(root/"App.kt").read_bytes()
    if NAV not in app.decode("utf-8"):
        raise RuntimeError("Bottom navigation not found")
    res=dest/"app/src/main/res"
    nav={str(p.relative_to(res)): p.read_bytes()
         for p in res.rglob("*") if p.is_file() and
         (p.name.startswith("nav_") or p.name.startswith("ic_nav_"))}
    protected={p.name:p.read_bytes() for p in root.glob("*.kt") if p.name not in
               ("ImanQuoteCarousel.kt","IbnQayyimStyle.kt","MedicineHomeArtwork.kt")}
    quote=root/"ImanQuoteCarousel.kt"
    quote.write_text(patch_quote(quote.read_text("utf-8")),"utf-8")
    style=root/"IbnQayyimStyle.kt"
    style.write_text(patch_home(style.read_text("utf-8")),"utf-8")
    preload=root/"MedicineHomeArtwork.kt"
    source=preload.read_text("utf-8")
    source=once(source,"        R.drawable.iman_quote_v15,",
        """        R.drawable.iman_quote_v15,
        R.drawable.iman_v17_quote,
        R.drawable.iman_v17_contents,
        R.drawable.iman_v17_collections,
        R.drawable.iman_v17_glossary,
        R.drawable.iman_v17_bookmarks,""",
        "preload all new assets outside main thread")
    preload.write_text(source,"utf-8")
    install_artwork(kit,dest)
    if (root/"App.kt").read_bytes()!=app:
        raise RuntimeError("Navigation changed")
    for p,data in protected.items():
        if (root/p).read_bytes()!=data:
            raise RuntimeError("Unrelated Kotlin file changed: "+p)
    for p,data in nav.items():
        if (res/p).read_bytes()!=data:
            raise RuntimeError("Bottom navigation icon changed: "+p)
    if list((dest/"app/src/main").rglob("*.pdf")):
        raise RuntimeError("PDF embedded in application")
    print("v0.17: five approved light sepia resources, natural fade, non-stretched reminder; bottom navigation unchanged")

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--dest",type=Path,required=True)
    args=parser.parse_args()
    build_v17(Path(__file__).resolve().parents[1],args.dest)
