"""Reader typography v0.5: left-aligned compact TOC, centered smaller chapter title.

Built on the tested v0.4 renderer; changes are layout-only. Original chapter
IDs, text, anchors, footnotes, TTS and optimized LazyColumn remain unchanged.
"""
from pathlib import Path
import argparse

JAVA = 'app/src/main/java/com/xalid/meditsinaproroka/nativeapp'


def one(source: str, original: str, replacement: str, label: str) -> str:
    count = source.count(original)
    if count != 1:
        raise RuntimeError(f'Unexpected pinned {label}: {count} anchors')
    return source.replace(original, replacement, 1)


def patch_contents_v5(source: str) -> str:
    start = source.index('private fun ChapterRow(')
    end = source.index('@Composable\nprivate fun MetricCard(', start)
    row = source[start:end]
    if 'centeredTitle: Boolean = false' not in row:
        raise RuntimeError('TOC-specific chapter-row flag is missing')
    if 'if (centeredTitle)' in row[:row.index('    Card(')]:
        raise RuntimeError('Compact TOC row was inserted twice')
    insertion = '''    if (centeredTitle) {
        Card(
            modifier = Modifier.fillMaxWidth().clickable(onClick = onClick),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
            border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outline),
            elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
            shape = androidx.compose.foundation.shape.RoundedCornerShape(12.dp),
        ) {
            Row(
                Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Surface(
                    modifier = Modifier.size(38.dp),
                    color = MaterialTheme.colorScheme.primary.copy(alpha = 0.09f),
                    shape = androidx.compose.foundation.shape.RoundedCornerShape(10.dp),
                    border = androidx.compose.foundation.BorderStroke(1.dp,
                        MaterialTheme.colorScheme.outline.copy(alpha = 0.60f)),
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Text(chapter.order.toString().padStart(2, '0'),
                            fontFamily = WebSansFont, fontSize = 13.sp,
                            fontWeight = FontWeight.SemiBold,
                            color = MaterialTheme.colorScheme.primary)
                    }
                }
                Text(
                    chapter.title,
                    modifier = Modifier.weight(1f),
                    fontFamily = WebLiterataFont,
                    fontWeight = FontWeight.Bold,
                    fontSize = 15.sp,
                    lineHeight = 19.sp,
                    textAlign = androidx.compose.ui.text.style.TextAlign.Start,
                    maxLines = 4,
                    overflow = TextOverflow.Ellipsis,
                )
                Icon(Icons.Default.ChevronRight, contentDescription = null,
                    modifier = Modifier.size(19.dp),
                    tint = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
        return
    }
'''
    row = one(row, '    Card(\n', insertion + '    Card(\n', 'compact chapter row')
    source = source[:start] + row + source[end:]
    a = source.index('@Composable\nfun BookScreen(')
    b = source.index('@Composable\nfun TopicsScreen(', a)
    toc = source[a:b]
    toc = one(toc, 'verticalArrangement = Arrangement.spacedBy(3.dp)',
              'verticalArrangement = Arrangement.spacedBy(6.dp)', 'contents row separation')
    return source[:a] + toc + source[b:]


def patch_reader_v5(source: str) -> str:
    original = '''                Text(
                    chapter.title.removeSurrounding("[", "]"),
                    fontFamily = WebLiterataFont,
                    fontSize = (if (chapter.title.length > 60) 23 else 27).sp,
                    lineHeight = (if (chapter.title.length > 60) 28 else 32).sp,
                    fontWeight = FontWeight.SemiBold,
                )'''
    replacement = '''                Text(
                    chapter.title.removeSurrounding("[", "]"),
                    modifier = Modifier.fillMaxWidth(),
                    fontFamily = WebLiterataFont,
                    fontSize = (if (chapter.title.length > 60) 21 else 24).sp,
                    lineHeight = (if (chapter.title.length > 60) 26 else 29).sp,
                    fontWeight = FontWeight.Bold,
                    textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                )'''
    return one(source, original, replacement, 'centered reading chapter title')


def build_v5(kit: Path, destination: Path) -> None:
    from scripts.build_iman_v4 import build_v4
    build_v4(kit, destination)
    gradle = destination / 'app/build.gradle'
    g = gradle.read_text(encoding='utf-8')
    g = one(g, 'versionCode 4', 'versionCode 5', 'version code')
    g = one(g, "versionName '0.4.0'", "versionName '0.5.0'", 'version name')
    g = one(g, "applicationIdSuffix '.preview4'",
            "applicationIdSuffix '.preview5'", 'separate test signing')
    gradle.write_text(g, encoding='utf-8')
    src = destination / JAVA
    for filename, patch in [('Screens.kt', patch_contents_v5), ('Reader.kt', patch_reader_v5)]:
        f = src / filename
        original = f.read_text(encoding='utf-8')
        modified = patch(original)
        assert original != modified
        f.write_text(modified, encoding='utf-8')
    if list((destination / 'app/src/main').rglob('*.pdf')):
        raise RuntimeError('Unexpected PDF resources')
    print('Prepared v0.5.0: compact left-aligned contents, centered chapter headings')


if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('--dest', type=Path, required=True)
    opt = args.parse_args()
    build_v5(Path(__file__).resolve().parents[1], opt.dest)
