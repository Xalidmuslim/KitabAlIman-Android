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
    val lightSurface = Color(0xFFF1E3D2)

    Surface(
        modifier = Modifier.fillMaxWidth(),
        color = if (isDark) MaterialTheme.colorScheme.surface else lightSurface,
        shape = RoundedCornerShape(18.dp),
        border = BorderStroke(0.8.dp, if (isDark)
            MaterialTheme.colorScheme.outline else Color(0xFFD6BE9E)),
        shadowElevation = if (isDark) 0.dp else 2.dp,
    ) {
        Box(
            Modifier.fillMaxWidth().background(
                if (isDark) Brush.horizontalGradient(listOf(
                    MaterialTheme.colorScheme.surface,
                    MaterialTheme.colorScheme.surface,
                )) else Brush.horizontalGradient(listOf(
                    Color(0xFFF9F0E3), Color(0xFFF1E1CD), Color(0xFFE8D0AE),
                ))
            )
        ) {
            Column(
                Modifier.fillMaxWidth().padding(start = 14.dp, end = 11.dp, top = 9.dp, bottom = 7.dp)
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
                        modifier = Modifier.heightIn(min = 40.dp),
                        contentPadding = PaddingValues(start = 8.dp, end = 2.dp),
                    ) {
                        Text("Другая ↻", fontFamily = WebSansFont,
                            fontSize = 11.sp, color = accent)
                    }
                }
                Row(
                    modifier = Modifier.fillMaxWidth().heightIn(min = 118.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(Modifier.weight(1f)) {
                        androidx.compose.animation.Crossfade(
                            targetState = current,
                            animationSpec = androidx.compose.animation.core.tween(180),
                            label = "quote-rotation",
                        ) { itemIndex ->
                            Text(
                                imanExcerpts[itemIndex].text,
                                fontFamily = WebLiterataFont,
                                fontSize = 16.sp, lineHeight = 22.sp,
                                fontWeight = FontWeight.SemiBold,
                                maxLines = 5,
                                overflow = TextOverflow.Ellipsis,
                                color = ink,
                            )
                        }
                    }
                    Spacer(Modifier.width(7.dp))
                    if (!isDark) {
                        Image(
                            painter = MedicineHomeArtwork.painter(R.drawable.iman_v17_quote),
                            contentDescription = null,
                            modifier = Modifier.size(width = 120.dp, height = 130.dp),
                            contentScale = ContentScale.Fit,
                            alpha = 0.94f,
                        )
                    } else {
                        Spacer(Modifier.width(8.dp))
                    }
                }
                HorizontalDivider(thickness = 0.65.dp, color = Color(0xFFD6BE9E).copy(alpha = 0.72f))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        "Глава " + (q.chapterId.substringAfterLast('-').toIntOrNull() ?: 0),
                        fontFamily = WebSansFont, fontSize = 10.5.sp,
                        color = muted, modifier = Modifier.weight(1f),
                    )
                    TextButton(
                        onClick = { navigate(Route.Reader(q.chapterId, q.blockId)) },
                        modifier = Modifier.heightIn(min = 40.dp),
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
}
