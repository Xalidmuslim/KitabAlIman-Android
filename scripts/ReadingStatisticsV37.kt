package com.xalid.meditsinaproroka.nativeapp

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale
import kotlin.math.roundToInt

private val StatInk = Color(0xFF392B22)
private val StatMuted = Color(0xFF756354)
private val StatBronze = Color(0xFF766143)
private val StatTrack = Color(0xFFD8C8B3)

@Composable
internal fun ImanReadingStatistics(book: BookData, store: AppStore, openMore: () -> Unit) {
    val context = LocalContext.current
    val ledger = remember(context) { V38ReadingLedger(context) }
    var revision by remember { mutableIntStateOf(0) }
    // The ledger persists to preferences; refresh when returning from the reader
    // and periodically while this home screen is visible.
    LaunchedEffect(ledger) { while (true) { delay(12000); revision++ } }
    @Suppress("UNUSED_VARIABLE") val snapshot = revision + ledger.version
    val dark = MaterialTheme.colorScheme.background.red < 0.25f
    val ink = if (dark) MaterialTheme.colorScheme.onSurface else StatInk
    val muted = if (dark) MaterialTheme.colorScheme.onSurfaceVariant else StatMuted
    val bronze = if (dark) MaterialTheme.colorScheme.primary else StatBronze
    val track = if (dark) MaterialTheme.colorScheme.outline.copy(alpha = 0.33f) else StatTrack

    // Source of truth: existing daily active reading time (not fake chapter counts).
    val daily = (6 downTo 0).map { ledger.daysAgo(it) / 60000f }
    val dayNames = (6 downTo 0).map { offset ->
        val cal = Calendar.getInstance()
        cal.add(Calendar.DAY_OF_YEAR, -offset)
        SimpleDateFormat("EE", Locale("ru")).format(cal.time)
            .replace(".", "").take(2).replaceFirstChar { it.uppercaseChar() }
    }
    val byId = remember(book) { book.chapters.associateBy { it.id } }
    val topics = book.collections.take(3).map { collection ->
        val chapters = collection.chapterIds.mapNotNull(byId::get)
        val part = v38WeightedFraction(chapters.map { chapter ->
            chapter.blocks.size to chapterReadFraction(chapter, store)
        }).coerceIn(0f, 1f)
        collection.title to part
    }
    val results = store.quizBestPercent.values.filter { it in 0..100 }
    val tested = results.size
    val strong = results.count { it >= 80 }
    val mastery = if (tested == 0) 0f else strong.toFloat() / tested
    val average = if (tested == 0) null else results.average().roundToInt()

    Column(Modifier.fillMaxWidth().padding(start = 2.dp, end = 2.dp, top = 0.dp)) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Text("Статистика чтения", fontFamily = WebLiterataFont,
                fontWeight = FontWeight.Bold, fontSize = 20.sp, color = ink,
                modifier = Modifier.weight(1f))
            Text("Подробнее", fontFamily = WebSansFont, fontSize = 10.5.sp,
                color = bronze, modifier = Modifier.clickable(onClick = openMore)
                    .padding(horizontal = 4.dp, vertical = 2.dp))
        }
        Spacer(Modifier.height(1.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(13.dp)) {
            Column(Modifier.weight(1f)) {
                StatSectionTitle("По дням", ink)
                Text("Минуты чтения", fontFamily = WebSansFont, fontSize = 10.sp, color = muted)
                Spacer(Modifier.height(2.dp))
                Canvas(Modifier.fillMaxWidth().height(42.dp).clipToBounds()) {
                    val top = 7.dp.toPx()
                    val bottom = size.height - 7.dp.toPx()
                    val max = maxOf(1f, daily.maxOrNull() ?: 0f)
                    val pts = daily.mapIndexed { i, minutes ->
                        Offset(i * size.width / 6f, bottom - (bottom - top) * (minutes / max))
                    }
                    drawLine(track, Offset(0f, bottom), Offset(size.width, bottom), 1.dp.toPx())
                    pts.zipWithNext().forEach { (a,b) ->
                        drawLine(bronze, a, b, 1.4.dp.toPx(), cap = StrokeCap.Round)
                    }
                    pts.forEach { p ->
                        drawCircle(bronze, 2.6.dp.toPx(), p)
                        drawCircle(if (dark) Color(0xFF302820) else Color(0xFFF8EEDC),
                            1.4.dp.toPx(), p)
                    }
                }
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    dayNames.forEach { day ->
                        Text(day, fontFamily = WebSansFont, fontSize = 8.sp, color = muted)
                    }
                }
                // The full seven-day total is available in the detailed progress screen.
            }
            Column(Modifier.weight(1f)) {
                StatSectionTitle("По темам", ink)
                Text("Доля прочитанного", fontFamily = WebSansFont, fontSize = 10.sp, color = muted)
                Spacer(Modifier.height(2.dp))
                topics.forEach { (name, fraction) ->
                    // Reference: title, progress and percentage live on one baseline.
                    Row(Modifier.fillMaxWidth().heightIn(min = 18.dp),
                        verticalAlignment = Alignment.CenterVertically) {
                        Text(name, fontFamily = WebSansFont, fontSize = 10.2.sp,
                            lineHeight = 12.sp, color = ink, maxLines = 2,
                            overflow = TextOverflow.Ellipsis,
                            modifier = Modifier.weight(1.3f))
                        Spacer(Modifier.width(4.dp))
                        Box(Modifier.weight(.70f).height(5.dp)
                            .background(track, RoundedCornerShape(4.dp))) {
                            Box(Modifier.fillMaxWidth(fraction).fillMaxHeight()
                                .background(bronze, RoundedCornerShape(4.dp)))
                        }
                        Spacer(Modifier.width(4.dp))
                        Text("${(fraction * 100).roundToInt()}%",
                            fontFamily = WebSansFont, fontSize = 10.5.sp, color = ink,
                            textAlign = TextAlign.End, modifier = Modifier.width(32.dp))
                    }
                }
            }
        }
        Spacer(Modifier.height(0.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(13.dp)) {
            Column(Modifier.weight(1f)) {
                StatSectionTitle("Усвоение", ink)
                Text("По результатам тестов", fontFamily = WebSansFont,
                    fontSize = 10.sp, color = muted)
                Spacer(Modifier.height(2.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(Modifier.size(52.dp), contentAlignment = Alignment.Center) {
                        Canvas(Modifier.fillMaxSize()) {
                            val width = 6.dp.toPx()
                            val inset = width / 2f
                            drawArc(track, -90f, 360f, false,
                                topLeft = Offset(inset,inset),
                                size = androidx.compose.ui.geometry.Size(
                                    size.width - width, size.height - width),
                                style = Stroke(width, cap = StrokeCap.Round))
                            if (mastery > 0f) drawArc(bronze, -90f, mastery * 360f, false,
                                topLeft = Offset(inset,inset),
                                size = androidx.compose.ui.geometry.Size(
                                    size.width - width, size.height - width),
                                style = Stroke(width, cap = StrokeCap.Round))
                        }
                        Text(if (tested == 0) "—" else "${(mastery * 100).roundToInt()}%",
                            fontFamily = WebLiterataFont, fontWeight = FontWeight.Bold,
                            fontSize = 17.sp, color = ink)
                    }
                    Spacer(Modifier.width(7.dp))
                    Column {
                        Text("$strong из $tested", fontFamily = WebSansFont,
                            fontWeight = FontWeight.SemiBold, fontSize = 11.sp, color = ink)
                        Text("глав ≥ 80%", fontFamily = WebSansFont,
                            fontSize = 9.sp, color = muted)
                    }
                }
            }
            Column(Modifier.weight(1f)) {
                StatSectionTitle("Викторины", ink)
                Text("Проверка знаний", fontFamily = WebSansFont,
                    fontSize = 10.sp, color = muted)
                Spacer(Modifier.height(6.dp))
                Text("Проверено глав: $tested", fontFamily = WebSansFont,
                    fontSize = 11.sp, color = ink)
                Spacer(Modifier.height(2.dp))
                Text("Средний лучший: " + (average?.let { "$it%" } ?: "—"),
                    fontFamily = WebSansFont, fontSize = 10.sp, color = ink)
                Spacer(Modifier.height(2.dp))
                Text("Подробнее →", fontFamily = WebSansFont,
                    fontSize = 10.sp, color = bronze,
                    modifier = Modifier.clickable(onClick = openMore))
            }
        }
        Spacer(Modifier.height(6.dp))
    }
}

@Composable
private fun StatSectionTitle(text: String, color: Color) {
    Text(text, fontFamily = WebLiterataFont, fontStyle = FontStyle.Italic,
        fontSize = 14.sp, lineHeight = 18.sp, color = color)
}
