package com.xalid.meditsinaproroka.nativeapp

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Brightness4
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlin.math.roundToInt

// v0.19: book-first editorial home. No modifications to the navigation shell.
private val Paper = Color(0xFFF7F3EC)
private val Ivory = Color(0xFFFFFCF7)
private val Ink = Color(0xFF352D27)
private val Subtle = Color(0xFF81705E)
private val Bronze = Color(0xFF78614C)
private val Stroke = Color(0xFFDDD0BE)
private val Track = Color(0xFFE8DDCE)

@Composable private fun isEditorialDark() = MaterialTheme.colorScheme.background.red < 0.25f
@Composable private fun editorialInk() =
    if (isEditorialDark()) MaterialTheme.colorScheme.onSurface else Ink
@Composable private fun editorialMuted() =
    if (isEditorialDark()) MaterialTheme.colorScheme.onSurfaceVariant else Subtle
@Composable private fun editorialBronze() =
    if (isEditorialDark()) MaterialTheme.colorScheme.primary else Bronze

@Composable
private fun EditorialPaperCard(
    modifier: Modifier = Modifier,
    click: (() -> Unit)? = null,
    contents: @Composable ColumnScope.() -> Unit,
) {
    Surface(
        modifier = modifier.then(if (click == null) Modifier else Modifier.clickable(onClick = click)),
        color = if (isEditorialDark()) MaterialTheme.colorScheme.surface else Ivory,
        shape = RoundedCornerShape(16.dp),
        border = BorderStroke(0.8.dp, if (isEditorialDark()) MaterialTheme.colorScheme.outline else Stroke),
        shadowElevation = 0.dp,
    ) { Column(content = contents) }
}

@Composable
private fun EditorialBookHeader(search: () -> Unit, changeTheme: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().statusBarsPadding()
            .padding(start = 18.dp, end = 12.dp, top = 6.dp, bottom = 9.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Image(
            painter = MedicineHomeArtwork.painter(R.drawable.medicine_launcher_book),
            contentDescription = null, modifier = Modifier.size(40.dp),
            contentScale = ContentScale.Fit,
        )
        Spacer(Modifier.width(11.dp))
        Column(Modifier.weight(1f)) {
            Text("Книга Имана", fontFamily = WebLiterataFont, fontSize = 19.sp,
                fontWeight = FontWeight.Bold, color = editorialInk(), maxLines = 1)
            Text("Ибн Таймийя", fontFamily = WebSansFont,
                fontSize = 11.sp, color = editorialMuted())
        }
        IconButton(onClick = search, modifier = Modifier.size(46.dp)) {
            Icon(Icons.Default.Search, contentDescription = "Поиск",
                modifier = Modifier.size(21.dp), tint = editorialInk())
        }
        IconButton(onClick = changeTheme, modifier = Modifier.size(46.dp)) {
            Icon(Icons.Default.Brightness4, contentDescription = "Тема",
                modifier = Modifier.size(20.dp), tint = editorialInk())
        }
    }
}

@Composable
private fun EditorialResumeCard(
    title: String, readingStarted: Boolean, percent: Int,
    goRead: () -> Unit, goProgress: () -> Unit,
) {
    EditorialPaperCard(click = goRead) {
        Column(Modifier.fillMaxWidth().padding(start = 15.dp, end = 12.dp, top = 10.dp, bottom = 7.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(if (readingStarted) "ПРОДОЛЖИТЬ ЧТЕНИЕ" else "НАЧАТЬ ЧТЕНИЕ",
                    modifier = Modifier.weight(1f),
                    fontFamily = WebSansFont, fontWeight = FontWeight.SemiBold,
                    fontSize = 10.sp, letterSpacing = 0.8.sp, color = editorialMuted())
                Text(percent.toString() + "%", fontFamily = WebSansFont,
                    fontSize = 11.sp, fontWeight = FontWeight.Bold,
                    color = editorialBronze())
            }
            Spacer(Modifier.height(5.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(title, modifier = Modifier.weight(1f),
                    fontFamily = WebLiterataFont, fontSize = 15.sp, lineHeight = 20.sp,
                    fontWeight = FontWeight.SemiBold, maxLines = 2,
                    overflow = TextOverflow.Ellipsis, color = editorialInk())
                Icon(Icons.Default.ChevronRight, contentDescription = "Открыть главу",
                    modifier = Modifier.size(22.dp), tint = editorialBronze())
            }
            Spacer(Modifier.height(9.dp))
            LinearProgressIndicator(
                progress = { (percent / 100f).coerceIn(0f, 1f) },
                modifier = Modifier.fillMaxWidth().height(3.dp),
                color = editorialBronze(),
                trackColor = if (isEditorialDark()) MaterialTheme.colorScheme.outline else Track,
                drawStopIndicator = {},
            )
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Text(if (readingStarted) "С сохранённого места" else "С первой главы",
                    modifier = Modifier.weight(1f), fontFamily = WebSansFont,
                    fontSize = 10.sp, color = editorialMuted())
                TextButton(
                    onClick = goProgress, modifier = Modifier.heightIn(min = 40.dp),
                    contentPadding = PaddingValues(horizontal = 4.dp),
                ) {
                    Text("Мой прогресс", fontFamily = WebSansFont,
                        fontSize = 11.sp, color = editorialBronze())
                }
            }
        }
    }
}

@Composable
private fun EditorialBookSection(
    title: String, subtitle: String, icon: Int,
    modifier: Modifier, go: () -> Unit,
) {
    EditorialPaperCard(modifier.heightIn(min = 76.dp), click = go) {
        Row(
            Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 7.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Image(
                painter = MedicineHomeArtwork.painter(icon),
                contentDescription = null,
                modifier = Modifier.size(width = 47.dp, height = 52.dp),
                contentScale = ContentScale.Fit,
                alpha = if (isEditorialDark()) 0.70f else 0.89f,
            )
            Spacer(Modifier.width(4.dp))
            Column(Modifier.weight(1f)) {
                Text(title, fontFamily = WebLiterataFont, fontSize = 12.sp,
                    lineHeight = 16.sp, fontWeight = FontWeight.SemiBold,
                    maxLines = 2, overflow = TextOverflow.Ellipsis, color = editorialInk())
                Spacer(Modifier.height(3.dp))
                Text(subtitle, fontFamily = WebSansFont, fontSize = 9.5.sp,
                    maxLines = 1, overflow = TextOverflow.Ellipsis, color = editorialMuted())
            }
        }
    }
}

@Composable
private fun EditorialCollection(
    entry: BookCollection, onClick: () -> Unit,
) {
    Row(
        Modifier.fillMaxWidth().clickable(onClick = onClick)
            .padding(horizontal = 2.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f)) {
            Text(entry.title, fontFamily = WebLiterataFont, fontSize = 14.sp,
                lineHeight = 18.sp, fontWeight = FontWeight.SemiBold,
                color = editorialInk(), maxLines = 1, overflow = TextOverflow.Ellipsis)
            Text(entry.chapterIds.size.toString() + " глав", fontFamily = WebSansFont,
                fontSize = 10.sp, color = editorialMuted())
        }
        Icon(Icons.Default.ChevronRight, contentDescription = null,
            modifier = Modifier.size(18.dp), tint = editorialMuted())
    }
}

@Composable
internal fun ModernEditorialHomeScreen(
    book: BookData, store: AppStore, modifier: Modifier,
    navigate: (Route) -> Unit, onGlobalSearch: () -> Unit,
    onToggleTheme: () -> Unit,
) {
    val chapters = remember(book) { book.chapters.filter { it.blocks.isNotEmpty() } }
    val last = store.lastChapterId?.let { id -> chapters.firstOrNull { it.id == id } }
    val target = last ?: chapters.firstOrNull()
    val fraction = v38WeightedFraction(chapters.map {
        it.blocks.size to chapterReadFraction(it, store)
    })
    val percent = (fraction * 100f).roundToInt().coerceIn(0, 100)
    val dark = isEditorialDark()
    Column(modifier.fillMaxSize().background(
        if (dark) MaterialTheme.colorScheme.background else Paper
    )) {
        EditorialBookHeader(search = onGlobalSearch, changeTheme = onToggleTheme)
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(start = 17.dp, end = 17.dp, top = 2.dp, bottom = 114.dp),
            verticalArrangement = Arrangement.spacedBy(9.dp),
        ) {
            item(key = "featured-reminder") { ImanFeaturedQuoteCarousel(navigate) }
            item(key = "resume-with-progress") {
                EditorialResumeCard(
                    title = target?.title ?: "Предисловие издателя",
                    readingStarted = last != null, percent = percent,
                    goRead = { target?.let { navigate(Route.Reader(it.id, resume = last != null)) } },
                    goProgress = { navigate(Route.Progress) },
                )
            }
            item(key = "sections-title") {
                Text("Разделы", modifier = Modifier.padding(top = 4.dp),
                    fontFamily = WebLiterataFont, fontSize = 20.sp,
                    fontWeight = FontWeight.Bold, color = editorialInk())
            }
            item(key = "sections-a") {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    EditorialBookSection("Оглавление", chapters.size.toString() + " глав",
                        R.drawable.iman_v17_contents, Modifier.weight(1f)) { navigate(Route.Book) }
                    EditorialBookSection("Подборки", book.collections.size.toString() + " разделов",
                        R.drawable.iman_v17_collections, Modifier.weight(1f)) { navigate(Route.Collections) }
                }
            }
            item(key = "sections-b") {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    EditorialBookSection("Понятия", book.glossary.size.toString() + " терминов",
                        R.drawable.iman_v17_glossary, Modifier.weight(1f)) { navigate(Route.Glossary) }
                    EditorialBookSection("Закладки", store.bookmarks.size.toString() + " сохранено",
                        R.drawable.iman_v17_bookmarks, Modifier.weight(1f)) { navigate(Route.Bookmarks) }
                }
            }
            item(key = "collection-title") {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Подборки", modifier = Modifier.weight(1f),
                        fontFamily = WebLiterataFont, fontSize = 19.sp,
                        fontWeight = FontWeight.Bold, color = editorialInk())
                    TextButton(onClick = { navigate(Route.Collections) },
                        modifier = Modifier.heightIn(min = 44.dp)) {
                        Text("Все", fontFamily = WebSansFont,
                            fontSize = 12.sp, color = editorialBronze())
                    }
                }
            }
            item(key = "collections") {
                EditorialPaperCard {
                    Column(Modifier.fillMaxWidth().padding(horizontal = 14.dp)) {
                        book.collections.take(3).forEachIndexed { index, entry ->
                            EditorialCollection(entry) {
                                navigate(Route.CollectionDetail(entry.id))
                            }
                            if (index < 2 && index < book.collections.size - 1) {
                                HorizontalDivider(
                                    thickness = 0.6.dp,
                                    color = if (dark) MaterialTheme.colorScheme.outline else Stroke,
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}
