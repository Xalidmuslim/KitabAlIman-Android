"""v0.16: 79 exact-source reminders and compact native cards and TTS controls.

The existing book, paragraph anchors, bottom navigation, icons, TTS engine,
reader data, history, bookmarks and memory tasks remain unchanged.
"""
import argparse
import json
from pathlib import Path
import re
from scripts.build_iman_v15 import build_v15
from scripts.build_iman_v14 import patch_player

JAVA = Path("app/src/main/java/com/xalid/meditsinaproroka/nativeapp")
NAV = "@Composable\nprivate fun StandaloneBottomNav("
SPLIT = re.compile(r"(?<=[.!?])\s+(?=[А-ЯЁ«])")

def once(source, old, new, label):
    if source.count(old) != 1:
        raise RuntimeError(f"{label}: expected one anchor, got {source.count(old)}")
    return source.replace(old, new, 1)

def segment(source, before, after, replacement, label):
    if source.count(before) != 1 or source.count(after) != 1:
        raise RuntimeError(f"{label}: changed boundaries")
    start,end = source.index(before),source.index(after)
    if start >= end: raise RuntimeError(f"{label}: invalid boundaries")
    return source[:start] + replacement + source[end:]

def load_curated_quotes(book, key_text, previous_source):
    keys=[line.partition("|")[::2] for line in key_text.splitlines()
          if line.strip() and not line.lstrip().startswith("#")]
    if len(keys) != 79 or any(not block or not prefix for block,prefix in keys):
        raise RuntimeError("79 curated block/phrase anchors are required")
    originals=re.findall(
        r'FeaturedExcerpt\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)"\)',
        previous_source,flags=re.MULTILINE)
    if len(originals)!=7: raise RuntimeError("Original seven excerpts must be preserved")
    by_id={b["id"]:(ch["id"],b) for ch in book["chapters"] for b in ch["blocks"]}
    records=[]
    for i,(block_id,prefix) in enumerate(keys):
        if block_id not in by_id: raise RuntimeError("Missing original block: "+block_id)
        chapter_id,block=by_id[block_id]
        if block["type"] not in ("text", "scholar"): raise RuntimeError("Unexpected footnote/verse source")
        if i<7:
            cid,bid,text=originals[i]
            if cid!=chapter_id or bid!=block_id or not text.startswith(prefix):
                raise RuntimeError("Original excerpt no longer matches")
        else:
            candidates=[text for text in SPLIT.split(" ".join(block["text"].split()))
                        if text.startswith(prefix) and text in block["text"]]
            if len(candidates)!=1:
                raise RuntimeError(f"Ambiguous excerpt {block_id} / {prefix}: {len(candidates)}")
            text=candidates[0]
        if text not in block["text"]:raise RuntimeError("Unverifiable excerpt")
        record=(chapter_id,block_id,text,block.get("sourcePage"))
        if any(item[:3]==record[:3] for item in records):
            raise RuntimeError("Duplicate quotation")
        records.append(record)
    if len(set(c for c,_,_,_ in records))<50:
        raise RuntimeError("Not enough chapter diversity")
    return records

def kotlin_literal(value):
    return json.dumps(value,ensure_ascii=False).replace("$",r"\$")

def build_quote_source(source,records):
    lines=["private val imanExcerpts = listOf("]
    for chapter,block,excerpt,page in records:
        lines.append(f"    FeaturedExcerpt({kotlin_literal(chapter)}, {kotlin_literal(block)},")
        lines.append(f"        {kotlin_literal(excerpt)}),")
    lines.append(")\n")
    result=segment(source,"private val imanExcerpts = listOf(",
        "\n@Composable\ninternal fun ImanFeaturedQuoteCarousel",
        "\n".join(lines),"curated quote source")
    if result.count('FeaturedExcerpt("iman-chapter-')!=len(records):
        raise RuntimeError("Kotlin quote inventory mismatch")
    return result

HOME_LINK='''@Composable
private fun IbnHomeLink(
    label: String, count: String, icon: Int, modifier: Modifier, onClick: () -> Unit,
) {
    val dark = sepiaDark()
    val ink = if (dark) MaterialTheme.colorScheme.onSurface else SepiaInk
    val muted = if (dark) MaterialTheme.colorScheme.onSurfaceVariant else SepiaMuted
    SepiaPanel(modifier.heightIn(min = 81.dp), onClick) {
        Box(Modifier.fillMaxWidth().heightIn(min = 81.dp)) {
            if (!dark) {
                Image(MedicineHomeArtwork.painter(icon), contentDescription = null,
                    modifier = Modifier.align(Alignment.BottomEnd)
                        .size(width = 76.dp, height = 65.dp),
                    contentScale = ContentScale.Fit)
            }
            Column(Modifier.align(Alignment.CenterStart).fillMaxWidth(0.66f)
                .padding(start = 9.dp, top = 7.dp, bottom = 7.dp)) {
                Text(label, fontFamily = WebLiterataFont,
                    fontSize = 13.5.sp, lineHeight = 17.sp,
                    fontWeight = FontWeight.Bold, color = ink,
                    maxLines = 2, overflow = TextOverflow.Ellipsis)
                Spacer(Modifier.height(3.dp))
                Text(count, fontFamily = WebSansFont, fontSize = 10.sp,
                    lineHeight = 12.sp, color = muted, maxLines = 1)
            }
            Icon(Icons.Default.ChevronRight, null,
                Modifier.align(Alignment.TopEnd).padding(top = 6.dp, end = 3.dp).size(13.dp),
                tint = muted)
        }
    }
}

'''
COLLECTION_LINK='''@Composable
private fun IbnCollectionLink(collection: BookCollection, modifier: Modifier, onClick: () -> Unit) {
    SepiaPanel(modifier.heightIn(min = 86.dp), onClick) {
        Column(Modifier.fillMaxWidth().padding(horizontal = 10.dp, vertical = 10.dp)) {
            Text(collection.title, fontFamily = WebLiterataFont, fontSize = 14.5.sp,
                fontWeight = FontWeight.SemiBold, maxLines = 2,
                overflow = TextOverflow.Ellipsis, lineHeight = 18.sp)
            Spacer(Modifier.height(5.dp))
            Text(collection.chapterIds.size.toString() + " глав", fontFamily = WebSansFont,
                fontSize = 10.5.sp, maxLines = 1,
                color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

'''

def patch_home_style(source):
    source=segment(source,"@Composable\nprivate fun IbnHomeLink(",
        "@Composable\nprivate fun IbnCollectionLink(",HOME_LINK,"small section cards")
    return segment(source,"@Composable\nprivate fun IbnCollectionLink(",
        "@Composable\ninternal fun IbnStyleContentsScreen(",
        COLLECTION_LINK,"compact theme collections")

def build_v16(kit,dest):
    build_v15(kit,dest)
    gradle=dest/"app/build.gradle"
    g=gradle.read_text(encoding="utf-8")
    for old,new in (("versionCode 15","versionCode 16"),
                    ("versionName '0.15.0'","versionName '0.16.0'"),
                    ("applicationIdSuffix '.preview15'","applicationIdSuffix '.preview16'")):
        g=once(g,old,new,"version")
    gradle.write_text(g,encoding="utf-8")
    root=dest/JAVA
    app=(root/"App.kt").read_text(encoding="utf-8")
    nav=app.split(NAV,1)[1]
    res=dest/"app/src/main/res"
    icons={str(p.relative_to(res)):p.read_bytes() for p in res.rglob("*")
           if p.is_file() and (p.name.startswith("nav_") or p.name.startswith("ic_nav_"))}
    book=json.loads((dest/"app/src/main/assets/book.json").read_text(encoding="utf-8"))
    file=root/"ImanQuoteCarousel.kt"
    original=file.read_text(encoding="utf-8")
    records=load_curated_quotes(book,
        (kit/"scripts/v16_curated_keys.txt").read_text(encoding="utf-8"),original)
    file.write_text(build_quote_source(original,records),encoding="utf-8")
    (dest/"app/src/main/assets/featured_quotes.json").write_text(
        json.dumps([dict(chapterId=c,blockId=b,text=t,sourcePage=p)
                    for c,b,t,p in records],ensure_ascii=False,indent=1),encoding="utf-8")
    style=root/"IbnQayyimStyle.kt"
    style.write_text(patch_home_style(style.read_text(encoding="utf-8")),encoding="utf-8")
    player=(kit/"scripts/v16_reader_player.kt").read_text(encoding="utf-8")
    for key in ("active.play(chapter)","controller?.pause()","controller?.stop()",
                "controller?.cycleRate()","RUVOICE_ENGINE_PACKAGE"):
        if key not in player:raise RuntimeError("Missing TTS control: "+key)
    reader=root/"Reader.kt"
    reader.write_text(patch_player(reader.read_text(encoding="utf-8"),player),encoding="utf-8")
    if (root/"App.kt").read_text(encoding="utf-8").split(NAV,1)[1]!=nav:
        raise RuntimeError("Original five-tab bottom navigation changed")
    if any((res/rel).read_bytes()!=old for rel,old in icons.items()):
        raise RuntimeError("Bottom icons changed")
    if list((dest/"app/src/main").rglob("*.pdf")):
        raise RuntimeError("Unexpected PDF")
    print(f"PASS v0.16: {len(records)} exact excerpts from {len(set(x[0] for x in records))} chapters, compact 3D cards and one-row audio panel")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dest",type=Path,required=True)
    a=p.parse_args()
    build_v16(Path(__file__).resolve().parents[1],a.dest)
