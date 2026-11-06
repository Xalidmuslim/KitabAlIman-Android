"""Compact flat contents, retaining original chapter ordering and scroll focus."""
def _one(source, old, new, description):
    if source.count(old) != 1:
        raise RuntimeError(description + ": pinned source changed")
    return source.replace(old, new, 1)


def patch_contents(source):
    start = "@Composable\nfun BookScreen("
    end = "@Composable\nfun TopicsScreen("
    if source.count(start) != 1 or source.count(end) != 1:
        raise RuntimeError("BookScreen moved in pinned engine")
    a = source.index(start)
    b = source.index(end, a)
    layout = '''@Composable
fun BookScreen(
    book: BookData,
    modifier: Modifier,
    back: () -> Unit,
    focusChapterId: String? = null,
    focusRequest: Int = 0,
    open: (String) -> Unit,
) {
    val readableChapters = remember(book) { book.chapters.filter { it.blocks.isNotEmpty() } }
    val focusIndex = remember(readableChapters, focusChapterId) {
        readableChapters.indexOfFirst { it.id == focusChapterId }.coerceAtLeast(0)
    }
    val listState = rememberLazyListState()
    LaunchedEffect(focusChapterId, focusRequest) {
        if (focusChapterId != null) listState.scrollToItem(focusIndex)
    }
    Column(modifier.fillMaxSize()) {
        PageHeader("Оглавление", readableChapters.size.toString() + " глав", back)
        LazyColumn(
            state = listState,
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(start = 12.dp, end = 12.dp, top = 8.dp, bottom = 112.dp),
            verticalArrangement = Arrangement.spacedBy(5.dp),
        ) {
            items(readableChapters, key = { it.id }) { chapter ->
                ChapterRow(chapter, { open(chapter.id) }, centeredTitle = true)
            }
        }
    }
}

'''
    source = source[:a] + layout + source[b:]
    row_start = source.index("private fun ChapterRow(")
    row_end = source.index("@Composable\nprivate fun MetricCard(", row_start)
    row = source[row_start:row_end]
    row = _one(row,
        "Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically)",
        "Row(Modifier.padding(horizontal = 12.dp, vertical = 10.dp), verticalAlignment = Alignment.CenterVertically)",
        "row padding")
    row = _one(row,
        "fontSize = if (centeredTitle) 18.sp else 16.sp,",
        "fontSize = if (centeredTitle) 17.sp else 16.sp,", "title size")
    row = _one(row,
        "lineHeight = if (centeredTitle) 23.sp else 20.sp,",
        "lineHeight = if (centeredTitle) 21.sp else 20.sp,", "title line-height")
    return source[:row_start] + row + source[row_end:]
