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
    val compactScreen = androidx.compose.ui.platform.LocalConfiguration.current.screenWidthDp <= 380
    val isDark = MaterialTheme.colorScheme.background.red < 0.25f
    val ink = if (isDark) MaterialTheme.colorScheme.onSurface else Color(0xFF382D24)
    val muted = if (isDark) MaterialTheme.colorScheme.onSurfaceVariant else Color(0xFF83705B)
    val accent = if (isDark) MaterialTheme.colorScheme.primary else Color(0xFF795D43)
    // Approved compact scroll and quill share the parchment background.
    // Keep all 79 original texts and their handwriting unchanged.

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
                // Fade the manuscript into the right edge of the background.
                // Long quotes retain full width: the artwork becomes more subtle.
                Box(
                    modifier = Modifier.fillMaxWidth().heightIn(min = if (compactScreen) 111.dp else 133.dp),
                ) {
                    Image(
                        painter = MedicineHomeArtwork.painter(R.drawable.iman_v43_approved_scroll),
                        contentDescription = null,
                        modifier = Modifier.align(Alignment.BottomEnd)
                            .width(if (compactScreen) 112.dp else 148.dp)
                            .height(if (compactScreen) 103.dp else 137.dp)
                            .offset(x = if (compactScreen) 12.dp else 9.dp, y = (-3).dp),
                        contentScale = ContentScale.Fit,
                        alpha = if (q.text.length > 125) 0.27f else 0.68f,
                        colorFilter = if (isDark)
                            androidx.compose.ui.graphics.ColorFilter.tint(
                                Color(0xFFD6BCA0),
                                androidx.compose.ui.graphics.BlendMode.SrcIn
                            ) else null,
                    )
                    Column(
                        Modifier.fillMaxWidth(if (q.text.length <= 125) 0.68f else 0.94f)
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
                length <= 80 -> 22.5.sp
                length <= 150 -> 20.5.sp
                length <= 240 -> 19.sp
                else -> 17.5.sp
            },
            lineHeight = when {
                length <= 80 -> 26.5.sp
                length <= 150 -> 24.5.sp
                length <= 240 -> 22.5.sp
                else -> 21.5.sp
            },
            fontWeight = FontWeight.Normal,
            color = ink,
        )
    }
}
