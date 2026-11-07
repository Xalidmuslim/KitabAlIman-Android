@Composable
private fun ReaderChapterSpeechBar(
    chapter: Chapter,
    controller: ChapterSpeechController?,
    createController: () -> ChapterSpeechController,
) {
    val context = LocalContext.current
    val status = controller?.status ?: ChapterVoiceStatus.Ready
    val playing = status == ChapterVoiceStatus.Playing
    val dark = MaterialTheme.colorScheme.background.red < 0.25f
    val ink = if (dark) MaterialTheme.colorScheme.onSurface else Color(0xFF785C45)
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = androidx.compose.foundation.shape.RoundedCornerShape(11.dp),
        border = BorderStroke(0.8.dp,
            if (dark) MaterialTheme.colorScheme.outline else Color(0xFFD8BFA3)),
        color = if (dark) MaterialTheme.colorScheme.surface else Color(0xFFF9F1E6),
    ) {
        Column(Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 4.dp)) {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(3.dp)) {
                Button(
                    onClick = {
                        if (playing) controller?.pause() else {
                            val active = if (controller == null ||
                                status == ChapterVoiceStatus.Error) createController() else controller
                            active.play(chapter)
                        }
                    },
                    modifier = Modifier.heightIn(min = 36.dp),
                    shape = androidx.compose.foundation.shape.RoundedCornerShape(9.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (dark) MaterialTheme.colorScheme.primary else Color(0xFF826246),
                        contentColor = Color(0xFFFFF6E9)),
                    contentPadding = PaddingValues(horizontal = 10.dp, vertical = 6.dp),
                ) {
                    Icon(if (playing) Icons.Default.Pause else Icons.Default.PlayArrow,
                        contentDescription = null, modifier = Modifier.size(17.dp))
                    Spacer(Modifier.width(3.dp))
                    Text(when (status) {
                        ChapterVoiceStatus.Playing -> "Пауза"
                        ChapterVoiceStatus.Paused -> "Продолжить"
                        ChapterVoiceStatus.Preparing -> "Готовится…"
                        else -> "Слушать"
                    }, fontSize = 11.5.sp, fontFamily = WebSansFont,
                        fontWeight = FontWeight.SemiBold, maxLines = 1)
                }
                if (playing || status == ChapterVoiceStatus.Paused ||
                    status == ChapterVoiceStatus.Preparing) {
                    IconButton(onClick = { controller?.stop() },
                        modifier = Modifier.size(35.dp)) {
                        Icon(Icons.Default.Stop, contentDescription = "Остановить",
                            modifier = Modifier.size(18.dp), tint = ink)
                    }
                }
                Spacer(Modifier.weight(1f))
                TextButton(enabled = controller != null,
                    onClick = { controller?.cycleRate() },
                    contentPadding = PaddingValues(horizontal = 4.dp, vertical = 0.dp)) {
                    Text(String.format(java.util.Locale.ROOT, "%.2f×",
                        controller?.rate ?: CHAPTER_SPEECH_DEFAULT_RATE),
                        fontFamily = WebSansFont, fontSize = 10.5.sp, color = ink)
                }
                TextButton(
                    onClick = {
                        try {
                            context.startActivity(Intent(Intent.ACTION_MAIN).setClassName(
                                RUVOICE_ENGINE_PACKAGE, "ru.kost.ruvoice.SettingsActivity"))
                        } catch (_: Exception) {
                            Toast.makeText(context, "Настройки голоса недоступны",
                                Toast.LENGTH_LONG).show()
                        }
                    }, contentPadding = PaddingValues(horizontal = 5.dp, vertical = 0.dp),
                ) {
                    Text("Голос", fontFamily = WebSansFont, fontSize = 10.5.sp, color = ink)
                }
            }
            controller?.errorMessage?.let { error ->
                Text(error, fontSize = 11.sp, color = MaterialTheme.colorScheme.error)
            }
        }
    }
}

