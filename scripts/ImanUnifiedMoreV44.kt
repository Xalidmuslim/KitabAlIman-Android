package com.xalid.meditsinaproroka.nativeapp

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private data class ImanFlatMenuLink(val icon: String, val title: String, val subtitle: String, val route: Route)

/** Shared parchment carries the visuals; rows retain their existing routes. */
@Composable
internal fun ImanV38MoreScreen(modifier: Modifier, navigate: (Route) -> Unit) {
    val ink = MaterialTheme.colorScheme.onSurface
    val muted = MaterialTheme.colorScheme.onSurfaceVariant
    val accent = MaterialTheme.colorScheme.primary
    val groups = listOf(
        "ЧТЕНИЕ И ИЗУЧЕНИЕ" to listOf(
            ImanFlatMenuLink("▤", "Оглавление", "131 глава книги", Route.Book),
            ImanFlatMenuLink("◷", "Прогресс чтения", "Цели, время и повторение", Route.Progress),
            ImanFlatMenuLink("◈", "Подборки по вере", "Тематическое изучение", Route.Collections),
            ImanFlatMenuLink("Aa", "Словарь понятий", "Разъяснение терминов", Route.Glossary),
            ImanFlatMenuLink("≡", "Хадисы и источники", "Цитаты из книги", Route.Hadiths),
        ),
        "ЛИЧНАЯ БИБЛИОТЕКА" to listOf(
            ImanFlatMenuLink("✎", "Мои заметки", "Выделения и записи", Route.Notes),
            ImanFlatMenuLink("◷", "История чтения", "Недавно открытые главы", Route.History),
        ),
        "НАСТРОЙКИ И ИНФОРМАЦИЯ" to listOf(
            ImanFlatMenuLink("⚙", "Настройки чтения", "Шрифт и оформление", Route.Settings),
            ImanFlatMenuLink("i", "О книге", "Об авторе и издании", Route.About),
            ImanFlatMenuLink("§", "Об издании", "Сведения об источниках", Route.Source),
        ),
    )
    Column(modifier.fillMaxSize()) {
        Row(Modifier.fillMaxWidth().padding(start = 24.dp, end = 18.dp, top = 9.dp, bottom = 5.dp),
            verticalAlignment = Alignment.CenterVertically) {
            Text("Ещё", modifier = Modifier.weight(1f), fontFamily = WebLiterataFont,
                fontSize = 23.sp, fontWeight = FontWeight.Bold, color = ink)
            IconButton(onClick = { navigate(Route.Settings) }) {
                Icon(Icons.Default.Settings, contentDescription = "Настройки", tint = accent)
            }
        }
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(start = 20.dp, end = 20.dp, top = 5.dp, bottom = 110.dp),
            verticalArrangement = Arrangement.spacedBy(2.dp),
        ) {
            groups.forEachIndexed { groupIndex, (title, entries) ->
                item(key = "group-label-$groupIndex") {
                    Text(title, fontFamily = WebSansFont, fontSize = 10.sp,
                        fontWeight = FontWeight.Bold, letterSpacing = 0.8.sp,
                        color = accent, modifier = Modifier.padding(top = 16.dp, bottom = 7.dp))
                }
                entries.forEachIndexed { index, entry ->
                    item(key = "menu-$groupIndex-$index") {
                        Column {
                            Row(
                                Modifier.fillMaxWidth()
                                    .clickable { navigate(entry.route) }
                                    .padding(horizontal = 1.dp, vertical = 11.dp),
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                Text(entry.icon, fontFamily = WebSerifFont,
                                    fontSize = 19.sp, color = accent,
                                    modifier = Modifier.width(37.dp))
                                Column(Modifier.weight(1f)) {
                                    Text(entry.title, fontFamily = WebSansFont,
                                        fontWeight = FontWeight.SemiBold,
                                        fontSize = 14.sp, color = ink)
                                    Text(entry.subtitle, fontFamily = WebSansFont,
                                        fontSize = 11.sp, color = muted,
                                        maxLines = 1, overflow = TextOverflow.Ellipsis)
                                }
                                Icon(Icons.Default.ChevronRight, contentDescription = null,
                                    tint = muted, modifier = Modifier.size(17.dp))
                            }
                            if (index != entries.lastIndex) HorizontalDivider(
                                color = MaterialTheme.colorScheme.outlineVariant,
                                thickness = 0.6.dp)
                        }
                    }
                }
            }
        }
    }
}
