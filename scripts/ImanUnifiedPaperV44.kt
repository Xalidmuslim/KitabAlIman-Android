package com.xalid.meditsinaproroka.nativeapp

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

/** Editorial colors are scoped to subpages. Never restyle the approved Home. */
@Composable
internal fun ImanUnifiedRouteTheme(isHome: Boolean, content: @Composable () -> Unit) {
    if (isHome) {
        content()
        return
    }
    val parent = MaterialTheme.colorScheme
    val dark = parent.background.red < 0.25f
    val scheme = parent.copy(
        primary = if (dark) parent.primary else Color(0xFF78614C),
        primaryContainer = if (dark) parent.primaryContainer else Color(0xFFE9DDCB),
        onPrimaryContainer = if (dark) parent.onPrimaryContainer else Color(0xFF352D27),
        onSurface = if (dark) parent.onSurface else Color(0xFF352D27),
        onSurfaceVariant = if (dark) parent.onSurfaceVariant else Color(0xFF81705E),
        surface = Color.Transparent,
        surfaceVariant = Color.Transparent,
        surfaceContainerLowest = Color.Transparent,
        surfaceContainerLow = Color.Transparent,
        surfaceContainer = Color.Transparent,
        surfaceContainerHigh = Color.Transparent,
        surfaceContainerHighest = Color.Transparent,
        surfaceBright = Color.Transparent,
        surfaceDim = Color.Transparent,
        outline = if (dark) parent.outline else Color(0x6078614C),
        outlineVariant = if (dark) parent.outlineVariant else Color(0x3078614C),
    )
    MaterialTheme(colorScheme = scheme,
        typography = MaterialTheme.typography,
        shapes = MaterialTheme.shapes,
        content = content)
}
