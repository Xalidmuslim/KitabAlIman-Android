package com.xalid.meditsinaproroka.nativeapp

import android.content.Context
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private data class FeaturedExcerpt(val chapterId: String, val blockId: String, val text: String)
private val imanExcerpts = listOf(
    FeaturedExcerpt("iman-chapter-003", "iman-chapter-003-b0004",
        "Знай, что понятия «Иман» и «Ислам» объединяют в себе всю религию."),
    FeaturedExcerpt("iman-chapter-007", "iman-chapter-007-b0002",
        "Тот, кто исправит свое тайное, Аллах исправит его явное."),
    FeaturedExcerpt("iman-chapter-011", "iman-chapter-011-b0004",
        "Поистине упование на Аллаха является одной из важнейших обязанностей, так же как и искренность."),
    FeaturedExcerpt("iman-chapter-084", "iman-chapter-084-b0020",
        "Имеется в виду, что недостаточно лишь веры, необходимо наличие праведных деяний."),
    FeaturedExcerpt("iman-chapter-111", "iman-chapter-111-b0145",
        "Иман увеличивается при поклонении и уменьшается при совершении греха."),
    FeaturedExcerpt("iman-chapter-007", "iman-chapter-007-b0002",
        "Тот, кто исправит то, что между ним и Аллахом, Аллах исправит то, что между ним и людьми."),
    FeaturedExcerpt("iman-chapter-065", "iman-chapter-065-b0011",
        "Соблюдение обязательных предписаний является следствием полноценного Имана, а отсутствие следствия является показателем отсутствия причины."),
)

@Composable
internal fun ImanFeaturedQuoteCarousel(navigate: (Route) -> Unit) {
    val context = LocalContext.current
    val prefs = remember(context) { context.getSharedPreferences("iman_featured_quotes_v1", Context.MODE_PRIVATE) }
    val initial = remember(prefs) {
        val next = (prefs.getInt("last_shown", -1) + 1) % imanExcerpts.size
        prefs.edit().putInt("last_shown", next).apply()
        next
    }
    var current by remember { mutableIntStateOf(initial) }
    val q = imanExcerpts[current]
    val dark = MaterialTheme.colorScheme.background.red < 0.25f
    val ink = if (dark) MaterialTheme.colorScheme.onSurface else Color(0xFF3A2B21)
    val muted = if (dark) MaterialTheme.colorScheme.onSurfaceVariant else Color(0xFF80644A)
    val accent = if (dark) MaterialTheme.colorScheme.primary else Color(0xFF745238)
    Surface(
        color = if (dark) MaterialTheme.colorScheme.surface else Color(0xFFF0DCC2),
        shape = RoundedCornerShape(16.dp),
        border = BorderStroke(1.dp, if (dark) MaterialTheme.colorScheme.outline else Color(0xFFC7A57E)),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Box(Modifier.fillMaxWidth()) {
            if (!dark) Image(
                painter = MedicineHomeArtwork.painter(R.drawable.iman_quote_background),
                contentDescription = null, modifier = Modifier.matchParentSize(),
                contentScale = ContentScale.FillBounds)
            Column(Modifier.fillMaxWidth().padding(horizontal = 15.dp, vertical = 14.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("НАПОМИНАНИЕ ИЗ КНИГИ", fontFamily = WebSansFont, fontSize = 10.sp,
                        letterSpacing = 0.6.sp, fontWeight = FontWeight.SemiBold,
                        color = accent, modifier = Modifier.weight(1f))
                    Text((current+1).toString()+"/"+imanExcerpts.size, fontSize = 10.sp, color = muted)
                }
                Spacer(Modifier.height(12.dp))
                Text(q.text, modifier = Modifier.fillMaxWidth(0.79f),
                    fontFamily = WebLiterataFont, fontSize = 16.5.sp, lineHeight = 23.sp,
                    fontWeight = FontWeight.Bold, color = ink,
                    maxLines = 8, overflow = TextOverflow.Ellipsis)
                Spacer(Modifier.height(9.dp))
                Text("Книга Имана · глава "+(q.chapterId.substringAfterLast('-').toIntOrNull() ?: 0),
                    fontFamily = WebSansFont, fontSize = 10.5.sp, color = muted)
                Spacer(Modifier.height(9.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Surface(
                        modifier = Modifier.clickable { navigate(Route.Reader(q.chapterId, q.blockId)) },
                        color = if (dark) MaterialTheme.colorScheme.primary else Color(0xFF795737),
                        shape = RoundedCornerShape(9.dp)) {
                        Row(Modifier.padding(horizontal = 12.dp, vertical = 9.dp),
                            verticalAlignment = Alignment.CenterVertically) {
                            Text("Открыть в книге", fontFamily = WebSansFont, fontSize = 11.sp,
                                fontWeight = FontWeight.SemiBold, color = Color(0xFFFFF5E5))
                            Icon(Icons.Default.ChevronRight, contentDescription = null,
                                modifier = Modifier.size(17.dp), tint = Color(0xFFFFF5E5))
                        }
                    }
                    Spacer(Modifier.weight(1f))
                    TextButton(onClick = {
                        current = (current + 1) % imanExcerpts.size
                        prefs.edit().putInt("last_shown", current).apply()
                    }, contentPadding = PaddingValues(horizontal = 4.dp)) {
                        Text("Другая ↻", fontSize = 11.sp, color = accent,
                            fontWeight = FontWeight.SemiBold)
                    }
                }
            }
        }
    }
}
