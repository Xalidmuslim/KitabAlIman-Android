"""Keep original reader anchors/selection; suppress duplicate heading visually.

Only short, reliably attributed verse/hadith/scholar passages are card-styled.
Long mixed author arguments are never automatically rewritten.
"""
def _one(s, old, new, label):
    if s.count(old) != 1:
        raise RuntimeError("Pinned Reader changed: " + label)
    return s.replace(old, new, 1)


def patch_reader(source):
    start = '    if (block.type == "footnote") {'
    end = '    if (block.type == "hadith") {'
    if source.count(start) != 1 or source.count(end) != 1:
        raise RuntimeError("Original footnote UI insertion changed")
    a = source.index(start)
    b = source.index(end, a)
    source = source[:a] + source[b:]
    helper = '''internal fun sameChapterHeading(title: String, body: String): Boolean {
    fun normalize(value: String): String =
        value.trim().trimEnd('.', ' ', ':')
            .replace(Regex("\\\\s+"), " ").lowercase()
    return normalize(title) == normalize(body)
}

@Composable
private fun FaithSourceCard(chapter: Chapter, block: BookBlock, store: AppStore) {
    val heading = when (block.type) {
        "verse" -> "АЯТ КОРАНА"
        "verse_context" -> "АЯТ И ПОЯСНЕНИЕ"
        "hadith" -> "ХАДИС · ЦИТАТА ИЗ КНИГИ"
        "scholar" -> "СЛОВА УЧЁНОГО"
        else -> "СНОСКА ИЗДАНИЯ"
    }
    val icon = when (block.type) {
        "verse", "verse_context" -> Icons.Outlined.MenuBook
        "scholar" -> Icons.Outlined.PersonOutline
        else -> Icons.Outlined.FormatQuote
    }
    Row(
        Modifier.fillMaxWidth().padding(vertical = 5.dp)
            .height(IntrinsicSize.Min)
            .background(
                MaterialTheme.colorScheme.primary.copy(alpha = 0.065f),
                androidx.compose.foundation.shape.RoundedCornerShape(10.dp),
            ),
    ) {
        Box(Modifier.width(4.dp).fillMaxHeight().background(MaterialTheme.colorScheme.primary))
        Column(Modifier.weight(1f).padding(start = 12.dp, end = 11.dp, top = 10.dp, bottom = 11.dp)) {
            SemanticReaderHeading(icon, heading)
            Spacer(Modifier.height(6.dp))
            SelectableNativeText(chapter, block, store)
        }
    }
}

'''
    source = _one(source, '@Composable\nprivate fun SemanticReaderHeading(',
                  helper + '@Composable\nprivate fun SemanticReaderHeading(', 'quote helpers')
    source = _one(source, '    if (block.type == "hadith") {',
                  '''    if (block.type in setOf("verse", "verse_context", "hadith", "scholar", "footnote")) {
        FaithSourceCard(chapter, block, store)
        return
    }

    if (block.type == "hadith") {''', 'quote dispatcher')
    source = _one(source, '                    if (end > index + 1) {',
                  '''                    if (index == 0 && sameChapterHeading(chapter.title, block.text)) {
                        Spacer(Modifier.height(0.dp))
                    } else if (end > index + 1) {''', 'duplicate heading')
    source = _one(source, '''                Text(
                    chapter.section,
                    color = MaterialTheme.colorScheme.primary,
                    fontFamily = WebSansFont,
                    fontWeight = FontWeight.SemiBold,
                    fontSize = 12.sp,
                )
                Spacer(Modifier.height(4.dp))''',
                  '''                if (chapter.section.isNotBlank()) {
                    Text(
                        chapter.section,
                        color = MaterialTheme.colorScheme.primary,
                        fontFamily = WebSansFont,
                        fontWeight = FontWeight.SemiBold,
                        fontSize = 12.sp,
                    )
                    Spacer(Modifier.height(4.dp))
                }''', 'section label')
    return (source.replace('Icons.Outlined.MedicalServices', 'Icons.Outlined.MenuBook')
                  .replace('"МЕДИЦИНА ЭПОХИ"', '"ПРИМЕЧАНИЕ"')
                  .replace('"Медицина эпохи"', '"Примечание"'))


def patch_speech(source):
    return _one(source,
        'val parts = sequenceOf(title) + blocks.asSequence().filter { it.type != "quran" }.map { it.text }',
        '''val parts = sequenceOf(title) +
        blocks.asSequence().filterIndexed { index, block ->
            block.type != "quran" && (index != 0 || !sameChapterHeading(title, block.text))
        }.map { it.text }''', 'RuVoice repeated heading')
