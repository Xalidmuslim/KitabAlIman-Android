@Composable
internal fun V38ReaderStatus(chapter: Chapter, store: AppStore) {
    val context = LocalContext.current
    val ledger = remember(context) { V38ReadingLedger(context) }
    val current = chapterReadFraction(chapter, store)
    @Suppress("UNUSED_VARIABLE") val rev = ledger.version
    val today = ledger.todayMs() / 60_000L
    val dark = MaterialTheme.colorScheme.background.red < 0.25f
    // Transparent compact layer: same original paper as the chapter reader.
    Column(Modifier.fillMaxWidth().padding(horizontal = 19.dp, vertical = 4.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically) {
            Text(((current*100).toInt()).toString()+"% главы",
                fontSize = 10.sp, fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.primary)
            Text(today.toString()+" мин сегодня", fontSize = 10.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        Spacer(Modifier.height(4.dp))
        LinearProgressIndicator(
            progress = { current },
            modifier = Modifier.fillMaxWidth().height(2.dp),
            color = if (dark) MaterialTheme.colorScheme.primary else Color(0xFF987454),
            trackColor = MaterialTheme.colorScheme.outline.copy(alpha = 0.24f),
        )
    }
}

