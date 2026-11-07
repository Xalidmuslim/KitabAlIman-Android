package com.xalid.meditsinaproroka.nativeapp

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// Smaller, editorial-style More page based on Ibn Kayyim v38.
// The inherited five bottom tabs and their icons are never changed.
private data class FaithMoreLink(val icon: String, val title: String, val subtitle: String, val route: Route)

@Composable
internal fun ImanV38MoreScreen(modifier: Modifier, navigate: (Route) -> Unit) {
    val dark = MaterialTheme.colorScheme.background.red < 0.25f
    val paper = if (dark) MaterialTheme.colorScheme.background else Color(0xFFF6EFE3)
    val card = if (dark) MaterialTheme.colorScheme.surface else Color(0xFFFFF8ED)
    val ink = if (dark) MaterialTheme.colorScheme.onSurface else Color(0xFF382D24)
    val muted = if (dark) MaterialTheme.colorScheme.onSurfaceVariant else Color(0xFF806C58)
    val line = if (dark) MaterialTheme.colorScheme.outline else Color(0xFFDDCBB1)
    val accent = if (dark) MaterialTheme.colorScheme.primary else Color(0xFF76593C)
    val iconPaper = if (dark) MaterialTheme.colorScheme.surfaceVariant else Color(0xFFEAD8BA)
    val groups = listOf(
        "ЧТЕНИЕ И ИЗУЧЕНИЕ" to listOf(
            FaithMoreLink("▤", "Оглавление", "131 глава книги", Route.Book),
            FaithMoreLink("◷", "Прогресс чтения", "Цели, время и повторение", Route.Progress),
            FaithMoreLink("◈", "Подборки по вере", "Тематическое изучение", Route.Collections),
            FaithMoreLink("Aa", "Словарь понятий", "Разъяснение терминов", Route.Glossary),
            FaithMoreLink("≡", "Хадисы и источники", "Цитаты из книги", Route.Hadiths),
        ),
        "ЛИЧНАЯ БИБЛИОТЕКА" to listOf(
            FaithMoreLink("✎", "Мои заметки", "Выделения и записи", Route.Notes),
            FaithMoreLink("◷", "История чтения", "Недавно открытые главы", Route.History),
        ),
        "НАСТРОЙКИ И ИНФОРМАЦИЯ" to listOf(
            FaithMoreLink("⚙", "Настройки чтения", "Шрифт и оформление", Route.Settings),
            FaithMoreLink("i", "О книге", "Об авторе и издании", Route.About),
            FaithMoreLink("§", "Об издании", "Сведения об источниках", Route.Source),
        ),
    )
    Column(modifier.fillMaxSize().background(paper)) {
        Row(Modifier.fillMaxWidth().padding(horizontal = 18.dp, vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically) {
            Text("Ещё", modifier = Modifier.weight(1f),
                fontFamily = WebLiterataFont, fontWeight = FontWeight.Bold,
                fontSize = 23.sp, color = ink)
            Surface(
                modifier = Modifier.size(40.dp).clickable { navigate(Route.Settings) },
                color = card, shape = RoundedCornerShape(12.dp),
                border = BorderStroke(1.dp, line),
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Text("⚙", fontSize = 21.sp, color = accent)
                }
            }
        }
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 4.dp, bottom = 115.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            groups.forEachIndexed { groupIndex, (heading, links) ->
                item(key = "heading-" + groupIndex) {
                    Text(heading, fontFamily = WebSansFont,
                        color = accent, fontSize = 10.sp,
                        letterSpacing = 1.2.sp, fontWeight = FontWeight.Bold)
                }
                item(key = "group-" + groupIndex) {
                    Surface(
                        modifier = Modifier.fillMaxWidth(),
                        color = card, shape = RoundedCornerShape(15.dp),
                        border = BorderStroke(1.dp, line),
                    ) {
                        Column {
                            links.forEachIndexed { index, link ->
                                Row(
                                    modifier = Modifier.fillMaxWidth()
                                        .clickable { navigate(link.route) }
                                        .padding(horizontal = 13.dp, vertical = 10.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                ) {
                                    Surface(
                                        color = iconPaper,
                                        shape = RoundedCornerShape(10.dp),
                                        border = BorderStroke(1.dp, line),
                                    ) {
                                        Box(Modifier.size(39.dp), contentAlignment = Alignment.Center) {
                                            Text(link.icon, fontFamily = WebSerifFont,
                                                fontSize = if (link.icon == "Aa") 18.sp else 19.sp,
                                                color = accent, fontWeight = FontWeight.SemiBold)
                                        }
                                    }
                                    Spacer(Modifier.width(12.dp))
                                    Column(Modifier.weight(1f)) {
                                        Text(link.title, fontFamily = WebSansFont, fontSize = 14.sp,
                                            fontWeight = FontWeight.SemiBold, color = ink)
                                        Spacer(Modifier.height(2.dp))
                                        Text(link.subtitle, fontFamily = WebSansFont, fontSize = 10.5.sp,
                                            maxLines = 1, overflow = TextOverflow.Ellipsis, color = muted)
                                    }
                                    androidx.compose.material3.Icon(Icons.Default.ChevronRight,
                                        contentDescription = null, modifier = Modifier.size(18.dp),
                                        tint = muted)
                                }
                                if (index < links.lastIndex)
                                    HorizontalDivider(color = line, thickness = 0.6.dp)
                            }
                        }
                    }
                }
            }
        }
    }
}
