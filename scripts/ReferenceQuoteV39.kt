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
    // Always render the relief for all excerpts; fade it behind long text, never remove it.

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
                // A baked-on-parchment bas-relief always sits under the text.
                // Its alpha is reduced, but it is not removed, for longer citations.
                Box(
                    modifier = Modifier.fillMaxWidth().heightIn(min = 100.dp),
                ) {
                    Image(
                        painter = MedicineHomeArtwork.painter(R.drawable.iman_v39_relief),
                        contentDescription = null,
                        modifier = Modifier.align(Alignment.BottomEnd)
                            .width(228.dp).height(116.dp)
                            .offset(x = 16.dp, y = 4.dp),
                        contentScale = ContentScale.Fit,
                        alpha = if (q.text.length > 125) 0.35f else 0.82f,
                        colorFilter = if (isDark)
                            androidx.compose.ui.graphics.ColorFilter.tint(
                                Color(0xFFD6BCA0),
                                androidx.compose.ui.graphics.BlendMode.SrcIn
                            ) else null,
                    )
                    Column(
                        Modifier.fillMaxWidth(if (q.text.length <= 125) 0.70f else 1f)
                            .align(Alignment.TopStart)
                            .padding(top = 7.dp, bottom = 9.dp),
                    ) {
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
        val length = imanExcerpts[itemIndex].text.length
        Text(
            imanExcerpts[itemIndex].text,
            fontFamily = ImanCaveatFont,
            fontSize = when {
                length <= 80 -> 21.sp
                length <= 150 -> 19.sp
                length <= 240 -> 17.5.sp
                else -> 16.sp
            },
            lineHeight = when {
                length <= 80 -> 25.sp
                length <= 150 -> 23.sp
                length <= 240 -> 21.sp
                else -> 20.sp
            },
            fontWeight = FontWeight.Normal,
            color = ink,
        )
    }
}
