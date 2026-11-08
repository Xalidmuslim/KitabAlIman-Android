@Composable
internal fun ImanFeaturedQuoteCarousel(navigate: (Route) -> Unit) {
    val context = LocalContext.current
    val preferences = remember(context) {
        context.getSharedPreferences("iman_featured_quotes_v1", Context.MODE_PRIVATE)
    }
    val first = remember(preferences) {
        val index = (preferences.getInt("last_shown", -1) + 1) % imanExcerpts.size
        preferences.edit().putInt("last_shown", index).apply()
        index
    }
    var current by remember { mutableIntStateOf(first) }
    val q = imanExcerpts[current]
    val isDark = MaterialTheme.colorScheme.background.red < 0.25f
    val ink = if (isDark) MaterialTheme.colorScheme.onSurface else Color(0xFF382D24)
    val muted = if (isDark) MaterialTheme.colorScheme.onSurfaceVariant else Color(0xFF83705B)
    val accent = if (isDark) MaterialTheme.colorScheme.primary else Color(0xFF795D43)
    // Short excerpts share a larger hero illustration. Longer excerpts use the full text width.
    val showIllustration = !isDark && q.text.length <= 120

    Surface(
        modifier = Modifier.fillMaxWidth(),
        color = Color.Transparent,
        shape = RoundedCornerShape(0.dp),
        border = null,
        shadowElevation = 0.dp,
    ) {
        Column(
            Modifier.fillMaxWidth().padding(start = 5.dp, end = 4.dp, top = 0.dp, bottom = 0.dp)
        ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        "НАПОМИНАНИЕ ИЗ КНИГИ",
                        modifier = Modifier.weight(1f),
                        fontFamily = WebSansFont,
                        fontSize = 9.5.sp,
                        letterSpacing = 0.6.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = muted,
                    )
                    Text(
                        (current + 1).toString() + "/" + imanExcerpts.size,
                        fontFamily = WebSansFont,
                        fontSize = 10.sp, color = muted,
                    )
                    TextButton(
                        onClick = {
                            current = (current + 1) % imanExcerpts.size
                            preferences.edit().putInt("last_shown", current).apply()
                        },
                        modifier = Modifier.height(36.dp),
                        contentPadding = PaddingValues(start = 8.dp, end = 2.dp),
                    ) {
                        Text("Другая ↻", fontFamily = WebSansFont,
                            fontSize = 11.sp, color = accent)
                    }
                }
                if (showIllustration) {
                    // The reference art is wide and fades into the page. Rendering it
                    // in a Row with weight/ContentScale.Fit made it tiny while still
                    // forcing a huge 174dp Row. A fixed-height Box gives the art
                    // independent width without letting it dictate vertical rhythm.
                    Box(
                        modifier = Modifier.fillMaxWidth().height(100.dp),
                    ) {
                        Image(
                            painter = MedicineHomeArtwork.painter(R.drawable.iman_v36_reminder),
                            contentDescription = null,
                            modifier = Modifier.align(Alignment.BottomEnd)
                                .width(238.dp).height(142.dp)
                                .offset(x = 24.dp, y = 2.dp),
                            contentScale = ContentScale.Fit,
                        )
                        Column(
                            Modifier.fillMaxWidth(0.58f)
                                .align(Alignment.TopStart).padding(top = 8.dp),
                        ) {
                            ImanQuoteAnimatedText(current, ink)
                        }
                    }
                } else {
                    Box(Modifier.fillMaxWidth().heightIn(min = 120.dp),
                        contentAlignment = Alignment.CenterStart) {
                        ImanQuoteAnimatedText(current, ink)
                    }
                }
                HorizontalDivider(
                    thickness = 0.6.dp,
                    color = if (isDark) MaterialTheme.colorScheme.outline
                            else Color(0xFFE2D0BE),
                )
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        "Глава " + (q.chapterId.substringAfterLast('-').toIntOrNull() ?: 0),
                        fontFamily = WebSansFont, fontSize = 10.5.sp,
                        color = muted, modifier = Modifier.weight(1f),
                    )
                    TextButton(
                        onClick = { navigate(Route.Reader(q.chapterId, q.blockId)) },
                        modifier = Modifier.height(36.dp),
                        contentPadding = PaddingValues(horizontal = 3.dp),
                    ) {
                        Text("Читать в книге", fontFamily = WebSansFont,
                            fontSize = 11.5.sp,
                            fontWeight = FontWeight.SemiBold, color = accent)
                        Icon(
                            Icons.Default.ChevronRight,
                            contentDescription = null,
                            modifier = Modifier.size(17.dp), tint = accent,
                        )
                    }
                }
        }
    }
}

@Composable
private fun ImanQuoteAnimatedText(current: Int, ink: Color) {
    androidx.compose.animation.Crossfade(
        targetState = current,
        animationSpec = androidx.compose.animation.core.tween(180),
        label = "quote-rotation",
    ) { itemIndex ->
        Text(
            imanExcerpts[itemIndex].text,
            fontFamily = if (imanExcerpts[itemIndex].text.length <= 120) ImanCaveatFont else WebLiterataFont,
            fontSize = if (imanExcerpts[itemIndex].text.length <= 120) 22.sp else 15.5.sp,
            lineHeight = if (imanExcerpts[itemIndex].text.length <= 120) 25.5.sp else 21.sp,
            fontWeight = FontWeight.Normal,
            maxLines = 5,
            overflow = TextOverflow.Ellipsis,
            color = ink,
        )
    }
}
