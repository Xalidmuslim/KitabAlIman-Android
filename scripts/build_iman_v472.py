"""v0.46.12: exact temporary quote highlight, quiet listening control, compact headings and meaning-focused study.

All 131 chapters and 79 quotations remain verbatim. The old reader selection,
notes, text anchors, progress, chapter navigation, launch graphics and rendering
performance are preserved. Only scoped Kotlin UI edits and reviewed quiz records.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

from scripts.build_iman_v471 import build_v471
from scripts.build_iman_v20 import APP, replace_one


def one(s: str, old: str, new: str, name: str) -> str:
    return replace_one(s, old, new, name)


def patch_quote(source: str) -> str:
    helper = r'''/** Lookup only original user-visible excerpts. Encoded route contains no user data. */
internal fun featuredQuoteForDeepLink(chapterId: String, encodedAnchor: String?): Pair<String, String>? {
    val encoded = encodedAnchor ?: return null
    val position = encoded.substringAfter(".quote:", "").toIntOrNull() ?: return null
    val quote = imanExcerpts.getOrNull(position) ?: return null
    if (quote.chapterId != chapterId || encoded.substringBefore(".quote:") != quote.blockId) return null
    return quote.blockId to quote.text
}

'''
    source = one(
        source, '@Composable\ninternal fun ImanFeaturedQuoteCarousel(',
        helper + '@Composable\ninternal fun ImanFeaturedQuoteCarousel(',
        "quote deep-link lookup",
    )
    source = one(
        source, 'Modifier.weight(1f).padding(top = 2.dp, bottom = 2.dp)',
        '''Modifier.weight(1f).padding(top = 2.dp, bottom = 2.dp)
                            .clickable(
                                onClickLabel = "Открыть и временно выделить напоминание в книге"
                            ) {
                                navigate(Route.Reader(q.chapterId, q.blockId + ".quote:" + current))
                            }''',
        "make handwriting text open the exact featured excerpt",
    )
    if "navigate(Route.Reader(q.chapterId, q.blockId))" not in source:
        raise RuntimeError("Keep original Read in book action intact")
    return source


def patch_reader(source: str) -> str:
    flash = '''/** Nonpersistent reader-only cue, never stored as a bookmark or highlight. */
private data class ReaderQuoteFlash(val blockId: String, val text: String)
private val LocalQuoteFlash = compositionLocalOf<ReaderQuoteFlash?> { null }

'''
    source = one(
        source, '@OptIn(ExperimentalMaterial3Api::class)\n@Composable\nfun ReaderScreen(',
        flash + '@OptIn(ExperimentalMaterial3Api::class)\n@Composable\nfun ReaderScreen(',
        "transient reader quote scope",
    )
    anchor = '''    val foregroundOpacity = remember(chapter.id, animateEntrance) {'''
    insert = '''    val deepLinkBlockKey = remember(route.anchor) {
        route.anchor?.substringBefore(".quote:")
    }
    val quoteFocus = remember(chapter.id, route.anchor) {
        featuredQuoteForDeepLink(chapter.id, route.anchor)
    }
    var quoteVisible by remember(chapter.id, route.anchor) {
        mutableStateOf(quoteFocus != null)
    }
    // The highlight is purely visual. It disappears after one reading glance.
    LaunchedEffect(chapter.id, route.anchor, initialJumpDone) {
        if (initialJumpDone && quoteFocus != null) {
            kotlinx.coroutines.delay(2700L)
            quoteVisible = false
        }
    }

'''
    source = one(source, anchor, insert + anchor, "quote flash timer")
    source = one(
        source, 'chapter.blocks\n                    .indexOfFirst { it.anchor == route.anchor }',
        'chapter.blocks\n                    .indexOfFirst { it.anchor == deepLinkBlockKey || it.id == deepLinkBlockKey }',
        "exact fragment ID or page anchor",
    )
    source = one(
        source, 'store.addHistory(chapter.id, route.anchor)',
        'store.addHistory(chapter.id, deepLinkBlockKey)',
        "history uses canonical block key",
    )
    source = one(
        source, '                ) { group ->\n                    val index = groupStarts[group]',
        '''                ) { group ->
                    CompositionLocalProvider(
                        LocalQuoteFlash provides if (quoteVisible && quoteFocus != null) {
                            ReaderQuoteFlash(quoteFocus.first, quoteFocus.second)
                        } else null
                    ) {
                    val index = groupStarts[group]''',
        "only lazy paragraph groups inherit quote flash",
    )
    source = one(
        source, '''                }

                item(key = "chapter-study") {''',
        '''                    }
                }

                item(key = "chapter-study") {''',
        "close transient paragraph provider",
    )
    # Existing source segments locate precisely the matching substring, even
    # where several original source blocks were visually joined.
    source = one(
        source, '''    val notes = segments.flatMap { segment ->''',
        '''    val temporaryQuote = LocalQuoteFlash.current
    val temporaryHighlightColor = Color(0xFF937252).copy(alpha = 0.30f).toArgb()
    val temporaryRanges = remember(temporaryQuote, segments, displayText) {
        if (temporaryQuote == null) emptyList<Pair<Int, Int>>() else segments.mapNotNull { segment ->
            if (segment.block.id != temporaryQuote.blockId) null else {
                val sourceOffset = segment.block.text.indexOf(temporaryQuote.text)
                if (sourceOffset < 0) null else {
                    val from = maxOf(sourceOffset, segment.sourceStart)
                    val to = minOf(sourceOffset + temporaryQuote.text.length,
                        segment.sourceStart + segment.visibleLength)
                    if (to > from) {
                        (segment.start + from - segment.sourceStart) to
                            (segment.start + to - segment.sourceStart)
                    } else null
                }
            }
        }
    }
    val notes = segments.flatMap { segment ->''',
        "quote exact text spans",
    )
    source = one(
        source, '''    val styledText = remember(displayText, highlights, notes, highlightColor, segments) {''',
        '''    val styledText = remember(
        displayText, highlights, notes, highlightColor, segments,
        temporaryRanges, temporaryHighlightColor
    ) {''',
        "invalidate native span when cue expires",
    )
    source = one(
        source, '''            notes.forEach { (from, to) ->''',
        '''            temporaryRanges.forEach { (from, to) ->
                span.setSpan(BackgroundColorSpan(temporaryHighlightColor),
                    from, to, Spannable.SPAN_EXCLUSIVE_EXCLUSIVE)
            }
            notes.forEach { (from, to) ->''',
        "apply temporary brown span",
    )
    source = one(
        source, '''        highlights,
        notes,
    ) {
        listOf(''',
        '''        highlights,
        notes,
        temporaryRanges,
        temporaryHighlightColor,
    ) {
        listOf(''',
        "native render key dependencies",
    )
    source = one(
        source, '''            highlights.hashCode(),
            notes.hashCode(),''',
        '''            highlights.hashCode(),
            notes.hashCode(),
            temporaryRanges.hashCode(),
            temporaryHighlightColor,''',
        "native TextView rebind after 2.7 seconds",
    )
    return source


def patch_reader_title(source: str) -> str:
    # Exact-scoped heading replacement; body reading font remains unchanged.
    old='''                    fontFamily = WebLiterataFont,
                    fontSize = (if (chapter.title.length > 60) 18 else 20).sp,'''
    return one(source, old,
        old.replace("WebLiterataFont", "WebCompactFont"), "reader title only")


def patch_speech(source: str) -> str:
    old='''                    shape = androidx.compose.foundation.shape.RoundedCornerShape(9.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (dark) MaterialTheme.colorScheme.primary else Color(0xFF826246),
                        contentColor = Color(0xFFFFF6E9)),
                    contentPadding = PaddingValues(horizontal = 10.dp, vertical = 6.dp),'''
    new='''                    shape = androidx.compose.foundation.shape.RoundedCornerShape(0.dp),
                    colors = ButtonDefaults.textButtonColors(
                        containerColor = Color.Transparent, contentColor = ink),
                    contentPadding = PaddingValues(horizontal = 2.dp, vertical = 4.dp),'''
    if "controller?.pause()" not in source or "active.play(chapter)" not in source:
        raise RuntimeError("Speech play/pause controls missing before styling")
    return one(source, old, new, "borderless text-only listen control")


def patch_home_titles(s: str) -> str:
    s = one(s,'Text("Книга Имана", fontFamily = WebLiterataFont, fontSize = 22.sp,',
            'Text("Книга Имана", fontFamily = WebCompactFont, fontSize = 22.sp,',
            "Home app name")
    s = one(s, '''Text("Библиотека", modifier = Modifier.padding(top = 1.dp),
                    fontFamily = WebLiterataFont, fontSize = 20.sp,''',
            '''Text("Библиотека", modifier = Modifier.padding(top = 1.dp),
                    fontFamily = WebCompactFont, fontSize = 20.sp,''',
            "library title")
    s = one(s,'title, fontFamily = WebLiterataFont, fontSize = 12.2.sp,',
            'title, fontFamily = WebCompactFont, fontSize = 12.2.sp,',
            "library image captions")
    s = one(s,'''Text(title, modifier = Modifier.weight(1f),
                    fontFamily = WebLiterataFont, fontSize = 14.5.sp,''',
            '''Text(title, modifier = Modifier.weight(1f),
                    fontFamily = WebCompactFont, fontSize = 14.5.sp,''',
            "Home resume title")
    return s


def patch_contents_titles(screens: str, style: str):
    # Screens.kt contains the *actual* current chapter row, not a mockup.
    start = screens.index("private fun ChapterRow(")
    end = screens.index("@Composable\nprivate fun MetricCard(", start)
    row = screens[start:end]
    old_count = row.count("WebLiterataFont")
    if not old_count:
        raise RuntimeError("No actual table-of-contents title font found")
    row = row.replace("WebLiterataFont", "WebCompactFont")
    screens = screens[:start] + row + screens[end:]
    # Other glossary/collection styles are left untouched; only chapter lists.
    style = style.replace(
        "Text(chapter.title, fontFamily = WebLiterataFont,",
        "Text(chapter.title, fontFamily = WebCompactFont,"
    )
    return screens, style


def patch_knowledge_ui(source: str) -> str:
    source = one(source,
        '''    val sourceExcerpt: String,
    val anchor: String,''',
        '''    val sourceExcerpt: String,
    val anchor: String,
    val explanation: String,''',
        "quiz explanation data field")
    source = one(source,
        '''                sourceExcerpt = question.optString("sourceExcerpt"),
                anchor = question.optString("anchor"),''',
        '''                sourceExcerpt = question.optString("sourceExcerpt"),
                anchor = question.optString("anchor"),
                explanation = question.optString("explanation"),''',
        "parse curated explanation")
    source = one(source,
        '''Text("Вопросы составлены из дословных фрагментов этой книги.",''',
        '''Text("Сопоставляйте доводы и выводы с прочитанной главой.",''',
        "no misleading recognition-only instruction")
    source = one(source,
        '''                                fontSize = 13.sp, lineHeight = 19.sp)''',
        '''                                fontSize = 14.5.sp, lineHeight = 21.sp)''',
        "larger answer choices")
    source = one(source,
        '''                        Text("Из текста главы: «''',
        '''                        if (item.explanation.isNotBlank()) {
                            Text("Разбор: " + item.explanation,
                                fontSize = 13.sp, lineHeight = 19.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                        Text("Из текста главы: «''',
        "show why one close option is correct")
    return source


def _digest(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_curated_questions(book: dict, dataset: dict) -> dict:
    chapters={c["id"]:c for c in book["chapters"]}
    upgraded=dataset.get("chapters", {})
    total=0
    for chapter_id, records in upgraded.items():
        if chapter_id not in chapters or not 1 <= len(records) <= 8:
            raise RuntimeError("Bad curated quiz chapter " + chapter_id)
        blocks={b["anchor"]: b for b in chapters[chapter_id]["blocks"]}
        for item in records:
            total+=1
            if len(item["options"])!=4 or not 0<=item["correctIndex"]<=3:
                raise RuntimeError("Invalid multiple-choice answer " + item["id"])
            if len(set(item["options"]))!=4 or any(len(s)<28 for s in item["options"]):
                raise RuntimeError("Distractors too easy/repeated " + item["id"])
            if len(item["prompt"])<38 or not item["explanation"].strip():
                raise RuntimeError("Question missing reasoning " + item["id"])
            ref=blocks.get(item["anchor"])
            if ref is None:
                raise RuntimeError("Quiz evidence anchor not in chapter " + item["id"])
            hint=item.get("sourceHint", "").strip()
            if len(hint)<12 or hint not in ref["text"]:
                raise RuntimeError("Quiz source hint is not in actual paragraph " + item["id"])
            position=ref["text"].index(hint)
            start=max(0, position-28)
            end=min(len(ref["text"]), position+len(hint)+115)
            item["sourceExcerpt"]=ref["text"][start:end].strip()
            if len(item["sourceExcerpt"])<23:
                raise RuntimeError("Quiz excerpt too short " + item["id"])
            if item["options"][item["correctIndex"]] not in item["options"]:
                raise RuntimeError("Invalid correct choice")
    return {"chapters":len(upgraded),"questions":total,"invalid":0}


def apply_meaningful_quizzes(kit: Path, dest: Path):
    book_path=dest/"app/src/main/assets/book.json"
    quiz_path=dest/"app/src/main/assets/quiz.json"
    book=json.loads(book_path.read_text("utf-8"))
    quiz=json.loads(quiz_path.read_text("utf-8"))
    curated=json.loads((kit/"assets/quiz_meaning_v472.json").read_text("utf-8"))
    report=validate_curated_questions(book,curated)
    if len(book["chapters"])!=131 or len(quiz["chapters"])!=131:
        raise RuntimeError("Original book/quiz inventory changed")
    for key, records in curated["chapters"].items():
        quiz["chapters"][key]=records
    quiz["kind"]="source-grounded-comprehension-with-curated-batch"
    quiz_path.write_text(json.dumps(quiz, ensure_ascii=False, separators=(",",":")),encoding="utf-8")
    return report


def build_v472(kit: Path, dest: Path) -> None:
    build_v471(kit,dest)
    java=dest/APP
    assets=dest/"app/src/main/assets"
    book_before=_digest(assets/"book.json")
    quotes_before=_digest(assets/"featured_quotes.json")
    app_before=_digest(java/"App.kt")
    images=dest/"app/src/main/res/drawable-nodpi"
    image_before={p.name:_digest(p) for p in images.glob("iman_v*.webp")}

    q_path=java/"ImanQuoteCarousel.kt"
    q_path.write_text(patch_quote(q_path.read_text("utf-8")),"utf-8")
    reader_path=java/"Reader.kt"
    reader=reader_path.read_text("utf-8")
    reader=patch_reader(reader)
    reader=patch_reader_title(reader)
    reader=patch_speech(reader)
    reader_path.write_text(reader,"utf-8")

    home=java/"ModernEditorialHome.kt"
    home.write_text(patch_home_titles(home.read_text("utf-8")),"utf-8")
    screens=java/"Screens.kt"
    styles=java/"IbnQayyimStyle.kt"
    contents,styled=patch_contents_titles(screens.read_text("utf-8"),styles.read_text("utf-8"))
    screens.write_text(contents,"utf-8")
    styles.write_text(styled,"utf-8")
    web=java/"WebDesign.kt"
    web.write_text(one(web.read_text("utf-8"),
        '''                        title,
                        fontFamily = WebLiterataFont,''',
        '''                        title,
                        fontFamily = WebCompactFont,''',
        "native screen header only"),"utf-8")
    stats=java/"ReadingStatisticsV36.kt"
    stats.write_text(one(stats.read_text("utf-8"),
        'Text("Статистика чтения", fontFamily = WebLiterataFont,',
        'Text("Статистика чтения", fontFamily = WebCompactFont,',
        "stat heading"),"utf-8")
    study=java/"FaithStudy.kt"
    study.write_text(patch_knowledge_ui(study.read_text("utf-8")),"utf-8")
    summary=apply_meaningful_quizzes(kit,dest)

    if _digest(assets/"book.json")!=book_before or _digest(assets/"featured_quotes.json")!=quotes_before:
        raise RuntimeError("Original chapters or 79 quotes altered")
    if _digest(java/"App.kt")!=app_before:
        raise RuntimeError("Native five-tab navigation changed")
    for name,checksum in image_before.items():
        if _digest(images/name)!=checksum:
            raise RuntimeError("Approved illustration recolored/replaced: "+name)

    gradle=dest/"app/build.gradle"
    code=gradle.read_text("utf-8")
    for old,new in (
        ("versionCode 71","versionCode 72"),
        ("versionName '0.46.11'","versionName '0.46.12'"),
        ("applicationIdSuffix '.preview471'","applicationIdSuffix '.preview472'"),
    ):
        code=one(code,old,new,"isolated reading and study upgrade")
    gradle.write_text(code,"utf-8")
    print("PASS v472: exact timed excerpt highlight; 50dp graphics and book unchanged; reading test upgrades",summary)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dest",type=Path,required=True)
    opts=p.parse_args()
    build_v472(Path(__file__).resolve().parents[1],opts.dest)
