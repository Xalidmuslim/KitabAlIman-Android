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
        primary = if (dark) Color(0xFFD6B58D) else Color(0xFF76583F),
        onPrimary = if (dark) Color(0xFF241D18) else Color(0xFFFFF8EE),
        primaryContainer = if (dark) Color(0xFF4A3C2D) else Color(0xFFE7D5BE),
        onPrimaryContainer = if (dark) Color(0xFFF6E7D4) else Color(0xFF2B241E),
        secondary = if (dark) Color(0xFFC8AB8B) else Color(0xFF80634B),
        onSecondary = if (dark) Color(0xFF241D18) else Color(0xFFFFF8EE),
        secondaryContainer = if (dark) Color(0xFF44372C) else Color(0xFFE4D3BD),
        onSecondaryContainer = if (dark) Color(0xFFF3E4D4) else Color(0xFF32271F),
        tertiary = if (dark) Color(0xFFC9AC89) else Color(0xFF836448),
        onTertiary = if (dark) Color(0xFF241D18) else Color(0xFFFFF8EE),
        tertiaryContainer = if (dark) Color(0xFF47382A) else Color(0xFFE2D0B8),
        onTertiaryContainer = if (dark) Color(0xFFF3E4D4) else Color(0xFF31271F),
        onBackground = if (dark) Color(0xFFF2E8DB) else Color(0xFF2B241F),
        onSurface = if (dark) Color(0xFFF2E8DB) else Color(0xFF2B241F),
        onSurfaceVariant = if (dark) Color(0xFFCEB9A1) else Color(0xFF665442),
        inversePrimary = if (dark) Color(0xFF745B42) else Color(0xFFCBA781),
        surfaceTint = if (dark) Color(0xFFC8AB8B) else Color(0xFF80634B),
        surface = Color.Transparent,
        surfaceVariant = Color.Transparent,
        surfaceContainerLowest = Color.Transparent,
        surfaceContainerLow = Color.Transparent,
        surfaceContainer = Color.Transparent,
        surfaceContainerHigh = Color.Transparent,
        surfaceContainerHighest = Color.Transparent,
        surfaceBright = Color.Transparent,
        surfaceDim = Color.Transparent,
        outline = if (dark) Color(0xFF8C7560) else Color(0x90765B42),
        outlineVariant = if (dark) Color(0x665F4C3A) else Color(0x35765B42),
    )
    MaterialTheme(colorScheme = scheme,
        typography = MaterialTheme.typography,
        shapes = MaterialTheme.shapes,
        content = content)
}
