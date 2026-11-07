package com.xalid.meditsinaproroka.nativeapp

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.BookmarkBorder
import androidx.compose.material.icons.filled.Brightness4
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// Adapted from the actual IbnKayim v38 HTML/CSS screens, without WebView.
// Scope all palette/styling to these screens. App bottom nav + icon resources
// must remain exactly as in the existing "Книга Имана" app.
private val SepiaPaper = Color(0xFFF6EDDE)
private val SepiaSurface = Color(0xFFFFF8EB)
private val SepiaInk = Color(0xFF382C20)
private val SepiaMuted = Color(0xFF786650)
private val SepiaAccent = Color(0xFF785B3E)
private val SepiaLine = Color(0xFFDEC9AA)
private val SepiaNumber = Color(0xFFEAD6B6)

private fun isChapterComplete(chapter: Chapter, lastBlock: Int?): Boolean =
    lastBlock != null && chapter.blocks.isNotEmpty() &&
        lastBlock.toFloat() >= (chapter.blocks.size - 1).toFloat() * 0.96f

@Composable
private fun sepiaDark() = MaterialTheme.colorScheme.background.red < 0.25f

@Composable
private fun SepiaPanel(
    modifier: Modifier = Modifier,
    onClick: (() -> Unit)? = null,
    content: @Composable ColumnScope.() -> Unit,
) {
    val dark = sepiaDark()
    Surface(
        modifier = modifier.then(if (onClick == null) Modifier else Modifier.clickable(onClick = onClick)),
        color = if (dark) MaterialTheme.colorScheme.surface else SepiaSurface,
        shape = RoundedCornerShape(14.dp),
        border = BorderStroke(1.dp, if (dark) MaterialTheme.colorScheme.outline else SepiaLine),
        shadowElevation = 0.dp,
    ) {
        Column(content = content)
    }
}

@Composable
private fun SepiaTopBar(
    title: String,
    subtitle: String,
    onSearch: () -> Unit,
    onTheme: () -> Unit,
) {
    val dark = sepiaDark()
    Row(
        Modifier.fillMaxWidth().statusBarsPadding()
            .padding(horizontal = 18.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Image(
            painter = MedicineHomeArtwork.painter(R.drawable.medicine_launcher_book),
            contentDescription = null,
            modifier = Modifier.size(43.dp),
            contentScale = ContentScale.Fit,
        )
        Spacer(Modifier.width(11.dp))
        Column(Modifier.weight(1f)) {
            Text(title, fontFamily = WebLiterataFont,
                fontSize = 17.sp, lineHeight = 20.sp, fontWeight = FontWeight.Bold,
                maxLines = 1, overflow = TextOverflow.Ellipsis,
                color = if (dark) MaterialTheme.colorScheme.onSurface else SepiaInk)
            Text(subtitle, fontFamily = WebSansFont, fontSize = 10.5.sp,
                maxLines = 1, overflow = TextOverflow.Ellipsis,
                color = if (dark) MaterialTheme.colorScheme.onSurfaceVariant else SepiaMuted)
        }
        SepiaToolButton(onClick = onSearch) {
            Icon(Icons.Default.Search, contentDescription = "Поиск",
                modifier = Modifier.size(20.dp))
        }
        Spacer(Modifier.width(7.dp))
        SepiaToolButton(onClick = onTheme) {
            Icon(Icons.Default.Brightness4, contentDescription = "Сменить тему",
                modifier = Modifier.size(20.dp))
        }
    }
}

@Composable
private fun SepiaToolButton(onClick: () -> Unit, content: @Composable () -> Unit) {
    Surface(
        modifier = Modifier.size(39.dp).clickable(onClick = onClick),
        color = if (sepiaDark()) MaterialTheme.colorScheme.surface else SepiaSurface,
        shape = RoundedCornerShape(12.dp),
        border = BorderStroke(1.dp,
            if (sepiaDark()) MaterialTheme.colorScheme.outline else SepiaLine),
    ) {
        Box(contentAlignment = Alignment.Center) { content() }
    }
}

@Composable
private fun SepiaMiniStat(number: String, label: String, modifier: Modifier) {
    SepiaPanel(modifier) {
        Column(Modifier.fillMaxWidth().padding(vertical = 11.dp, horizontal = 7.dp),
            horizontalAlignment = Alignment.CenterHorizontally) {
            Text(number, fontSize = 22.sp, fontFamily = WebLiterataFont,
                fontWeight = FontWeight.Bold,
                color = if (sepiaDark()) MaterialTheme.colorScheme.onSurface else SepiaInk)
            Text(label, fontSize = 11.sp, fontFamily = WebSansFont,
                color = if (sepiaDark()) MaterialTheme.colorScheme.onSurfaceVariant else SepiaMuted)
        }
    }
}

@Composable
internal fun IbnStyleHomeScreen(
    book: BookData,
    store: AppStore,
    modifier: Modifier,
    navigate: (Route) -> Unit,
    onGlobalSearch: () -> Unit,
    onToggleTheme: () -> Unit,
) {
    val chapters = remember(book) { book.chapters.filter { it.blocks.isNotEmpty() } }
    val done = chapters.count { isChapterComplete(it, store.progress[it.id]) }
    val percent = if (chapters.isEmpty()) 0 else ((done * 100f) / chapters.size).toInt().coerceIn(0, 100)
    val last = store.lastChapterId?.let { id -> chapters.firstOrNull { it.id == id } }
    val first = last ?: chapters.firstOrNull()
    val dark = sepiaDark()
    val ink = if (dark) MaterialTheme.colorScheme.onSurface else SepiaInk
    val muted = if (dark) MaterialTheme.colorScheme.onSurfaceVariant else SepiaMuted

    Column(modifier.fillMaxSize().background(
        if (dark) MaterialTheme.colorScheme.background else SepiaPaper)) {
        SepiaTopBar("Книга Имана", "Ибн Таймийя · Книга и упражнения",
            onSearch = onGlobalSearch, onTheme = onToggleTheme)
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(start = 19.dp, end = 19.dp, top = 4.dp, bottom = 114.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            item(key = "welcome") {
                Column {
                    Text("ПУТЬ К ПОНИМАНИЮ", fontFamily = WebSansFont,
                        fontSize = 10.5.sp, letterSpacing = 1.3.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = if (dark) MaterialTheme.colorScheme.primary else SepiaAccent)
                    Spacer(Modifier.height(5.dp))
                    Text("Читать и размышлять.", fontFamily = WebLiterataFont,
                        fontSize = 27.sp, lineHeight = 32.sp,
                        fontWeight = FontWeight.Bold, color = ink)
                    Text("«Книга Имана» · Осмысленное чтение и проверка знаний",
                        fontFamily = WebSansFont, fontSize = 12.sp,
                        lineHeight = 17.sp, color = muted)
                }
            }
            item(key = "quote") {
                SepiaPanel {
                    Column(Modifier.fillMaxWidth().padding(17.dp)) {
                        Text("НАПОМИНАНИЕ ИЗ КНИГИ", fontFamily = WebSansFont,
                            fontSize = 10.sp, letterSpacing = 1.1.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (dark) MaterialTheme.colorScheme.primary else SepiaAccent)
                        Spacer(Modifier.height(8.dp))
                        Text("«Знай, что понятия «Иман» и «Ислам» объединяют в себе всю религию»",
                            fontFamily = WebLiterataFont, fontWeight = FontWeight.SemiBold,
                            fontSize = 19.sp, lineHeight = 26.sp, color = ink)
                        Spacer(Modifier.height(7.dp))
                        Text("Книга Имана · начало книги",
                            fontFamily = WebSansFont, fontSize = 11.sp, color = muted)
                        Spacer(Modifier.height(11.dp))
                        TextButton(
                            onClick = { chapters.firstOrNull()?.let { navigate(Route.Reader(it.id)) } },
                            contentPadding = PaddingValues(0.dp),
                        ) {
                            Text("Открыть раздел →", color = if (dark) MaterialTheme.colorScheme.primary else SepiaAccent,
                                fontSize = 12.sp, fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
            item(key = "reading-progress") {
                SepiaPanel {
                    Column(Modifier.fillMaxWidth().padding(horizontal = 15.dp, vertical = 13.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("Ваш путь по книге", Modifier.weight(1f),
                                fontFamily = WebSansFont, fontWeight = FontWeight.Bold,
                                fontSize = 13.sp, color = ink)
                            Text(percent.toString() + "%", fontSize = 13.sp,
                                fontWeight = FontWeight.Bold, color = if (dark) MaterialTheme.colorScheme.primary else SepiaAccent)
                        }
                        Spacer(Modifier.height(10.dp))
                        LinearProgressIndicator(
                            progress = { percent / 100f },
                            modifier = Modifier.fillMaxWidth().height(5.dp),
                            color = if (dark) MaterialTheme.colorScheme.primary else SepiaAccent,
                            trackColor = if (dark) MaterialTheme.colorScheme.outline else SepiaNumber,
                            drawStopIndicator = {},
                        )
                        Spacer(Modifier.height(7.dp))
                        Text("Прогресс сохраняется на устройстве",
                            fontFamily = WebSansFont, fontSize = 11.sp, color = muted)
                    }
                }
            }
            item(key = "statistics") {
                Row(horizontalArrangement = Arrangement.spacedBy(7.dp)) {
                    SepiaMiniStat(chapters.size.toString(), "Глав", Modifier.weight(1f))
                    SepiaMiniStat(done.toString(), "Прочитано", Modifier.weight(1f))
                    SepiaMiniStat(store.bookmarks.size.toString(), "Закладок", Modifier.weight(1f))
                }
            }
            item(key = "resume") {
                SepiaPanel {
                    Column(Modifier.fillMaxWidth().padding(15.dp)) {
                        Text("НА ЧЁМ ОСТАНОВИЛИСЬ", fontFamily = WebSansFont,
                            fontSize = 10.sp, letterSpacing = 1.sp,
                            fontWeight = FontWeight.Bold, color = muted)
                        Spacer(Modifier.height(5.dp))
                        Text(first?.title ?: "Начать с первой главы",
                            fontFamily = WebLiterataFont, fontWeight = FontWeight.Bold,
                            fontSize = 18.sp, lineHeight = 23.sp,
                            maxLines = 2, overflow = TextOverflow.Ellipsis, color = ink)
                        Spacer(Modifier.height(11.dp))
                        Surface(
                            modifier = Modifier.fillMaxWidth()
                                .clickable { first?.let { navigate(Route.Reader(it.id, resume = last != null)) } },
                            color = if (dark) MaterialTheme.colorScheme.primary else SepiaAccent,
                            shape = RoundedCornerShape(11.dp),
                        ) {
                            Box(Modifier.padding(vertical = 13.dp), contentAlignment = Alignment.Center) {
                                Text(if (last == null) "Начать чтение →" else "Продолжить чтение →",
                                    fontFamily = WebLiterataFont, fontWeight = FontWeight.Bold,
                                    color = Color(0xFFFFF6E8), fontSize = 16.sp)
                            }
                        }
                    }
                }
            }
            item(key = "links-heading") {
                Text("Разделы приложения", fontFamily = WebLiterataFont,
                    fontWeight = FontWeight.Bold, fontSize = 20.sp, color = ink)
            }
            item(key = "links-one") {
                Row(horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                    IbnHomeLink("Оглавление", chapters.size.toString() + " глав",
                        R.drawable.antique_books_detail, Modifier.weight(1f)) { navigate(Route.Book) }
                    IbnHomeLink("Подборки", book.collections.size.toString() + " разделов",
                        R.drawable.antique_scroll_detail, Modifier.weight(1f)) { navigate(Route.Collections) }
                }
            }
            item(key = "links-two") {
                Row(horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                    IbnHomeLink("Понятия", book.glossary.size.toString() + " терминов",
                        R.drawable.iman_glossary_detail, Modifier.weight(1f)) { navigate(Route.Glossary) }
                    IbnHomeLink("Закладки", store.bookmarks.size.toString() + " сохранено",
                        R.drawable.antique_bookmark_detail, Modifier.weight(1f)) { navigate(Route.Bookmarks) }
                }
            }
            item(key = "collection-heading") {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Быстрые подборки", modifier = Modifier.weight(1f),
                        fontFamily = WebLiterataFont, fontSize = 20.sp,
                        fontWeight = FontWeight.Bold, color = ink)
                    TextButton(onClick = { navigate(Route.Collections) }) { Text("Все") }
                }
            }
            items(book.collections.take(4).chunked(2), key = { row -> "coll:" + row.first().id }) { row ->
                Row(horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                    row.forEach { collection ->
                        IbnCollectionLink(collection, Modifier.weight(1f)) {
                            navigate(Route.CollectionDetail(collection.id))
                        }
                    }
                    if (row.size == 1) Spacer(Modifier.weight(1f))
                }
            }
            item(key = "study-links") {
                SepiaPanel(onClick = { navigate(Route.Progress) }) {
                    Row(Modifier.fillMaxWidth().padding(15.dp),
                        verticalAlignment = Alignment.CenterVertically) {
                        Text("Статистика и проверка знаний",
                            modifier = Modifier.weight(1f), fontFamily = WebLiterataFont,
                            fontWeight = FontWeight.SemiBold, color = ink, fontSize = 15.sp)
                        Icon(Icons.Default.ChevronRight, null, tint = muted)
                    }
                }
            }
        }
    }
}

@Composable
private fun IbnHomeLink(
    label: String, count: String, icon: Int, modifier: Modifier, onClick: () -> Unit,
) {
    val dark = sepiaDark()
    val ink = if (dark) MaterialTheme.colorScheme.onSurface else SepiaInk
    val muted = if (dark) MaterialTheme.colorScheme.onSurfaceVariant else SepiaMuted
    SepiaPanel(modifier.heightIn(min = 118.dp), onClick) {
        Box(Modifier.fillMaxWidth().heightIn(min = 118.dp)) {
            if (!dark) {
                Image(MedicineHomeArtwork.painter(icon), contentDescription = null,
                    modifier = Modifier.align(Alignment.BottomEnd)
                        .size(width = 113.dp, height = 88.dp),
                    contentScale = ContentScale.Fit, alpha = 0.48f)
            }
            Column(Modifier.align(Alignment.CenterStart)
                .fillMaxWidth(0.8f).padding(12.dp)) {
                Text(label, fontFamily = WebLiterataFont, fontSize = 16.sp,
                    fontWeight = FontWeight.Bold, color = ink)
                Spacer(Modifier.height(5.dp))
                Text(count, fontFamily = WebSansFont, fontSize = 11.sp, color = muted)
            }
            Icon(Icons.Default.ChevronRight, null,
                Modifier.align(Alignment.CenterEnd).size(20.dp), tint = muted)
        }
    }
}

@Composable
private fun IbnCollectionLink(collection: BookCollection, modifier: Modifier, onClick: () -> Unit) {
    SepiaPanel(modifier.heightIn(min = 118.dp), onClick) {
        Column(Modifier.fillMaxWidth().padding(13.dp)) {
            Text(collection.title, fontFamily = WebLiterataFont, fontSize = 16.sp,
                fontWeight = FontWeight.SemiBold, maxLines = 2,
                overflow = TextOverflow.Ellipsis, lineHeight = 20.sp)
            Spacer(Modifier.height(8.dp))
            Text(collection.description, fontFamily = WebSansFont, fontSize = 11.sp,
                maxLines = 3, overflow = TextOverflow.Ellipsis,
                color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
internal fun IbnStyleContentsScreen(
    book: BookData, store: AppStore, modifier: Modifier, back: () -> Unit,
    focusChapterId: String? = null, focusRequest: Int = 0, open: (String) -> Unit,
) {
    val chapters = remember(book) { book.chapters.filter { it.blocks.isNotEmpty() } }
    var filter by rememberSaveable { mutableIntStateOf(0) }
    val shown = chapters.filter { chapter ->
        val pos = store.progress[chapter.id]
        when (filter) {
            1 -> pos != null && !isChapterComplete(chapter, pos)
            2 -> isChapterComplete(chapter, pos)
            else -> true
        }
    }
    val listState = rememberLazyListState()
    LaunchedEffect(focusChapterId, focusRequest, filter, shown.size) {
        if (focusChapterId != null) {
            val i = shown.indexOfFirst { it.id == focusChapterId }
            listState.scrollToItem(if (i >= 0) i + 1 else 0)
        }
    }
    val dark = sepiaDark()
    val ink = if (dark) MaterialTheme.colorScheme.onSurface else SepiaInk
    val muted = if (dark) MaterialTheme.colorScheme.onSurfaceVariant else SepiaMuted
    Column(modifier.fillMaxSize().background(if (dark) MaterialTheme.colorScheme.background else SepiaPaper)) {
        Row(Modifier.fillMaxWidth().statusBarsPadding()
            .padding(horizontal = 13.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = back) {
                Icon(Icons.Default.ArrowBack, contentDescription = "Назад")
            }
            Text("Оглавление", modifier = Modifier.weight(1f), textAlign = TextAlign.Center,
                fontFamily = WebLiterataFont, fontWeight = FontWeight.Bold, fontSize = 19.sp,
                color = ink)
            Spacer(Modifier.width(44.dp))
        }
        LazyColumn(
            state = listState,
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(start = 17.dp, end = 17.dp, top = 4.dp, bottom = 114.dp),
            verticalArrangement = Arrangement.spacedBy(7.dp),
        ) {
            item(key = "contents-heading") {
                Column {
                    Text("ПУТЬ К ПОНИМАНИЮ", fontFamily = WebSansFont, fontSize = 10.sp,
                        fontWeight = FontWeight.Bold, letterSpacing = 1.4.sp,
                        color = if (dark) MaterialTheme.colorScheme.primary else SepiaAccent)
                    Spacer(Modifier.height(5.dp))
                    Text("Оглавление", fontFamily = WebLiterataFont, fontSize = 27.sp,
                        fontWeight = FontWeight.Bold, color = ink)
                    Spacer(Modifier.height(5.dp))
                    Text(chapters.size.toString() + " глав. Выберите тему для чтения.",
                        fontFamily = WebSansFont, fontSize = 12.sp, color = muted)
                    Spacer(Modifier.height(14.dp))
                    Row(
                        Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        listOf("Все разделы", "В процессе", "Завершённые").forEachIndexed { index, label ->
                            val active = index == filter
                            Surface(
                                modifier = Modifier.clickable { filter = index }.heightIn(min = 39.dp),
                                color = if (active) {
                                    if (dark) MaterialTheme.colorScheme.primary else SepiaAccent
                                } else if (dark) MaterialTheme.colorScheme.surface else SepiaSurface,
                                border = BorderStroke(1.dp,
                                    if (active) SepiaAccent else if (dark) MaterialTheme.colorScheme.outline else SepiaLine),
                                shape = RoundedCornerShape(11.dp),
                            ) {
                                Box(Modifier.padding(horizontal = 12.dp, vertical = 9.dp),
                                    contentAlignment = Alignment.Center) {
                                    Text(label, fontSize = 11.sp, fontFamily = WebSansFont,
                                        color = if (active) Color.White else ink)
                                }
                            }
                        }
                    }
                    Spacer(Modifier.height(5.dp))
                }
            }
            if (shown.isEmpty()) {
                item(key = "empty") {
                    Text("Для этого фильтра пока нет глав.", fontSize = 13.sp, color = muted,
                        modifier = Modifier.padding(vertical = 25.dp))
                }
            }
            items(shown, key = { it.id }) { chapter ->
                val pos = store.progress[chapter.id]
                val complete = isChapterComplete(chapter, pos)
                SepiaPanel(Modifier.fillMaxWidth(), onClick = { open(chapter.id) }) {
                    Row(
                        Modifier.fillMaxWidth().padding(horizontal = 11.dp, vertical = 10.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        Surface(
                            modifier = Modifier.size(38.dp),
                            color = if (dark) MaterialTheme.colorScheme.surfaceVariant else SepiaNumber,
                            shape = RoundedCornerShape(9.dp),
                            border = BorderStroke(1.dp,
                                if (dark) MaterialTheme.colorScheme.outline else SepiaLine),
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Text(chapter.order.toString().padStart(2, '0'),
                                    fontFamily = WebLiterataFont, fontWeight = FontWeight.Bold,
                                    fontSize = 13.sp, color = ink)
                            }
                        }
                        Column(Modifier.weight(1f)) {
                            Text(chapter.title, fontFamily = WebLiterataFont,
                                fontWeight = FontWeight.SemiBold,
                                fontSize = 14.5.sp, lineHeight = 18.sp,
                                color = ink, maxLines = 4, overflow = TextOverflow.Ellipsis)
                            Spacer(Modifier.height(4.dp))
                            Text(when {
                                complete -> "✓ Завершено"
                                pos != null -> "Открывали"
                                else -> "Не начинали"
                            }, fontFamily = WebSansFont, fontSize = 10.5.sp, color = muted)
                        }
                        Icon(Icons.Default.ChevronRight, null, Modifier.size(18.dp), tint = muted)
                    }
                }
            }
        }
    }
}
