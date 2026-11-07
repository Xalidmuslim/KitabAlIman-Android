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
    val muted = if (dark) MaterialTheme.colorScheme.onSurfaceVariant else Color(0xFF806A55)
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = androidx.compose.foundation.shape.RoundedCornerShape(12.dp),
        border = BorderStroke(1.dp, if (dark) MaterialTheme.colorScheme.outline else Color(0xFFD8BFA3)),
        color = if (dark) MaterialTheme.colorScheme.surface else Color(0xFFF8EFE3),
    ) {
        Column(Modifier.fillMaxWidth().padding(horizontal = 10.dp, vertical = 7.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.MenuBook, contentDescription = null, tint = muted,
                    modifier = Modifier.size(15.dp))
                Spacer(Modifier.width(6.dp))
                Text("ОЗВУЧИВАНИЕ ГЛАВЫ", fontSize = 10.sp, letterSpacing = 0.45.sp,
                    fontFamily = WebSansFont, fontWeight = FontWeight.SemiBold,
                    color = muted, modifier = Modifier.weight(1f))
                TextButton(
                    onClick = {
                        try {
                            context.startActivity(Intent(Intent.ACTION_MAIN).setClassName(
                                RUVOICE_ENGINE_PACKAGE, "ru.kost.ruvoice.SettingsActivity"))
                        } catch (_: Exception) {
                            Toast.makeText(context, "Настройки голосового движка недоступны",
                                Toast.LENGTH_LONG).show()
                        }
                    }, contentPadding = PaddingValues(horizontal = 4.dp, vertical = 0.dp),
                ) {
                    Text("Голос", fontFamily = WebSansFont, fontSize = 10.5.sp,
                        color = if (dark) MaterialTheme.colorScheme.primary else Color(0xFF76563B))
                }
            }
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(5.dp)) {
                Button(
                    onClick = {
                        if (playing) controller?.pause() else {
                            val active = if (controller == null || status == ChapterVoiceStatus.Error)
                                createController() else controller
                            active.play(chapter)
                        }
                    },
                    modifier = Modifier.heightIn(min = 38.dp),
                    shape = androidx.compose.foundation.shape.RoundedCornerShape(10.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (dark) MaterialTheme.colorScheme.primary else Color(0xFF826246),
                        contentColor = Color(0xFFFFF6E9)),
                    contentPadding = PaddingValues(horizontal = 11.dp, vertical = 6.dp),
                ) {
                    Icon(if (playing) Icons.Default.Pause else Icons.Default.PlayArrow,
                        contentDescription = null, modifier = Modifier.size(17.dp))
                    Spacer(Modifier.width(4.dp))
                    Text(when (status) {
                        ChapterVoiceStatus.Playing -> "Пауза"
                        ChapterVoiceStatus.Paused -> "Продолжить"
                        ChapterVoiceStatus.Preparing -> "Готовится…"
                        else -> "Слушать"
                    }, fontFamily = WebSansFont, fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold, maxLines = 1)
                }
                if (status == ChapterVoiceStatus.Playing ||
                    status == ChapterVoiceStatus.Paused || status == ChapterVoiceStatus.Preparing) {
                    IconButton(onClick = { controller?.stop() }, modifier = Modifier.size(35.dp)) {
                        Icon(Icons.Default.Stop, contentDescription = "Остановить чтение")
                    }
                }
                Spacer(Modifier.weight(1f))
                TextButton(enabled = controller != null,
                    onClick = { controller?.cycleRate() },
                    contentPadding = PaddingValues(horizontal = 4.dp)) {
                    Text(String.format(java.util.Locale.ROOT, "%.2f×",
                        controller?.rate ?: CHAPTER_SPEECH_DEFAULT_RATE),
                        fontFamily = WebSansFont, fontSize = 11.sp, color = muted)
                }
            }
            controller?.errorMessage?.let { message ->
                Text(message, fontSize = 11.sp, color = MaterialTheme.colorScheme.error)
            }
            if (status == ChapterVoiceStatus.Playing || status == ChapterVoiceStatus.Paused) {
                Text("Фрагмент "+((controller?.segmentIndex ?: 0)+1)+" из "+
                    (controller?.segmentCount ?: 0), fontSize = 10.sp, color = muted)
            }
        }
    }
}

