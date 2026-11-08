        // One wallpaper behind BOTH the home content and its navigation.
        // Do not tile, crop or draw another card-sized paper rectangle.
        val seamlessHome = current == Route.Home &&
            MaterialTheme.colorScheme.background.red >= 0.25f
        if (seamlessHome) {
            Image(
                painter = MedicineHomeArtwork.painter(R.drawable.iman_v25_unified_home),
                contentDescription = null,
                modifier = Modifier.matchParentSize(),
                contentScale = ContentScale.FillBounds,
            )
        }
