"""v0.10 approved main-screen sepia design, using native Compose components."""
from pathlib import Path
import argparse

def one(src,old,new,label):
    n=src.count(old)
    if n!=1: raise RuntimeError(f'Pinned UI changed at {label}: {n} matches')
    return src.replace(old,new,1)

def component(src,start,end,new,label):
    if src.count(start)!=1 or src.count(end)!=1:
        raise RuntimeError(f'Component signature changed: {label}')
    a,b=src.index(start),src.index(end,src.index(start))
    if a>=b: raise RuntimeError('Bad component order: '+label)
    return src[:a]+new+src[b:]

PAPER = '''@Composable
private fun PaperCard(
    modifier: Modifier = Modifier,
    onClick: (() -> Unit)? = null,
    content: @Composable BoxScope.() -> Unit,
) {
    val dark = MaterialTheme.colorScheme.background.red < 0.25f
    val shape = RoundedCornerShape(15.dp)
    Surface(
        modifier = modifier.then(if (onClick != null)
            Modifier.clickable(role = Role.Button, onClick = onClick) else Modifier),
        color = if (dark) MaterialTheme.colorScheme.surface else Color(0xFFF9DFBC),
        shape = shape,
        border = BorderStroke(1.dp,
            if (dark) MaterialTheme.colorScheme.outline else Color(0xFFCCA576)),
        shadowElevation = if (dark) 0.dp else 1.dp,
    ) {
        Box(Modifier.clip(shape)) {
            if (!dark) {
                Box(Modifier.matchParentSize().background(
                    Brush.horizontalGradient(
                        0f to Color(0xFFFFEDD2),
                        0.55f to Color(0xFFFFE7C7),
                        1f to Color(0xFFF2D2A8))))
                Box(Modifier.matchParentSize().padding(3.dp)
                    .border(0.6.dp, Color(0x99CBA474), RoundedCornerShape(12.dp)))
            }
            content()
        }
    }
}

'''

READING = '''@Composable
private fun ReadingCard(title: String, pct: Int, hasLast: Boolean, onContinue: () -> Unit) {
    val dark = MaterialTheme.colorScheme.background.red < 0.25f
    val animatedProgress by animateFloatAsState(
        targetValue = (pct / 100f).coerceIn(0f, 1f),
        animationSpec = tween(durationMillis = 280, easing = FastOutSlowInEasing),
        label = "readerProgress",
    )
    val bronze = Color(0xFF6B4825)
    PaperCard(Modifier.fillMaxWidth()) {
        Column(Modifier.fillMaxWidth().padding(horizontal = 11.dp, vertical = 10.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                AntiqueIcon(R.drawable.antique_open_book_detail,
                    Modifier.size(width = 104.dp, height = 84.dp), scale = ContentScale.Fit)
                Spacer(Modifier.width(5.dp))
                Column(Modifier.weight(1f)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("Продолжить чтение", Modifier.weight(1f),
                            fontFamily = WebSansFont, fontSize = 12.sp, lineHeight = 16.sp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Box(Modifier.size(37.dp), contentAlignment = Alignment.Center) {
                            CircularProgressIndicator(progress = { animatedProgress },
                                modifier = Modifier.fillMaxSize(),
                                color = if (dark) MaterialTheme.colorScheme.primary else bronze,
                                trackColor = if (dark) MaterialTheme.colorScheme.outline else Color(0xFFE3C9A6),
                                strokeWidth = 2.dp)
                            Text("$pct%", fontFamily = WebSansFont, fontSize = 11.sp,
                                color = if (dark) MaterialTheme.colorScheme.onSurface else bronze)
                        }
                    }
                    Text(title, fontFamily = WebLiterataFont, fontWeight = FontWeight.Bold,
                        fontSize = 16.sp, lineHeight = 21.sp, maxLines = 2,
                        overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis)
                }
            }
            Spacer(Modifier.height(5.dp))
            LinearProgressIndicator(
                progress = { animatedProgress },
                modifier = Modifier.fillMaxWidth().height(3.dp).clip(CircleShape),
                color = if (dark) MaterialTheme.colorScheme.primary else Color(0xFF997248),
                trackColor = if (dark) MaterialTheme.colorScheme.outline else Color(0xFFE3C9A6),
                drawStopIndicator = {},
            )
            Spacer(Modifier.height(8.dp))
            val buttonShape = RoundedCornerShape(12.dp)
            Box(
                Modifier.fillMaxWidth().heightIn(min = 47.dp)
                    .clip(buttonShape)
                    .background(
                        if (dark) Brush.horizontalGradient(
                            listOf(MaterialTheme.colorScheme.primary, MaterialTheme.colorScheme.primary))
                        else Brush.horizontalGradient(
                            listOf(Color(0xFF8E6832), Color(0xFF624421), Color(0xFF805B2E)))
                    )
                    .border(1.dp, if (dark) MaterialTheme.colorScheme.outline else Color(0xFFC9A46B), buttonShape)
                    .clickable(role = Role.Button, onClick = onContinue)
                    .padding(horizontal = 12.dp, vertical = 10.dp),
                contentAlignment = Alignment.Center,
            ) {
                Text(if (hasLast) "Продолжить чтение →" else "Начать чтение →",
                    fontFamily = WebLiterataFont, fontWeight = FontWeight.Bold,
                    fontSize = 17.sp, lineHeight = 23.sp,
                    color = if (dark) MaterialTheme.colorScheme.onPrimary else Color(0xFFFFF1DC))
            }
        }
    }
}

'''

QUICK = '''@Composable
private fun AntiqueQuickCard(@DrawableRes icon: Int, title: String, subtitle: String,
                             modifier: Modifier, onClick: () -> Unit) {
    val dark = MaterialTheme.colorScheme.background.red < 0.25f
    PaperCard(modifier.fillMaxHeight().heightIn(min = 100.dp), onClick) {
        Box(Modifier.fillMaxWidth().heightIn(min = 101.dp)) {
            if (!dark) {
                AntiqueIcon(icon, Modifier.align(Alignment.BottomEnd)
                    .padding(end = 2.dp, bottom = 2.dp)
                    .size(width = 105.dp, height = 89.dp), scale = ContentScale.Fit)
                Box(Modifier.matchParentSize().background(
                    Brush.horizontalGradient(0f to Color(0xFFFCE7C8).copy(alpha = 0.88f),
                        0.52f to Color(0xFFFCE7C8).copy(alpha = 0.20f),
                        1f to Color.Transparent)))
            }
            Column(Modifier.align(Alignment.CenterStart)
                .fillMaxWidth(0.82f)
                .padding(start = 12.dp, end = 5.dp, top = 10.dp, bottom = 10.dp)) {
                Text(title, fontFamily = WebLiterataFont, fontWeight = FontWeight.Bold,
                    fontSize = 15.5.sp, lineHeight = 19.sp,
                    color = MaterialTheme.colorScheme.onSurface)
                Spacer(Modifier.height(4.dp))
                Text(subtitle, fontFamily = WebSansFont, fontSize = 11.sp,
                    lineHeight = 14.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            Icon(Icons.Default.ChevronRight, null,
                Modifier.align(Alignment.CenterEnd).padding(end = 2.dp).size(17.dp),
                tint = if (dark) MaterialTheme.colorScheme.onSurfaceVariant else Color(0xFF6B4825))
        }
    }
}

@Composable
private fun ImanHomeCollectionCard(collection: BookCollection, modifier: Modifier, onClick: () -> Unit) {
    PaperCard(modifier.heightIn(min = 138.dp), onClick) {
        Box(Modifier.fillMaxWidth().heightIn(min = 138.dp)) {
            Image(MedicineHomeArtwork.painter(R.drawable.antique_scroll_detail), null,
                Modifier.align(Alignment.BottomEnd).size(width = 142.dp, height = 112.dp),
                contentScale = ContentScale.Fit, alpha = 0.19f)
            Column(Modifier.fillMaxWidth().padding(horizontal = 13.dp, vertical = 13.dp)) {
                Text(collection.title, fontFamily = WebLiterataFont,
                    fontWeight = FontWeight.Bold, fontSize = 16.sp, lineHeight = 20.sp,
                    maxLines = 2, overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis)
                Spacer(Modifier.height(7.dp))
                Text(collection.description, fontFamily = WebSansFont,
                    fontSize = 11.sp, lineHeight = 15.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 3, overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis)
                Spacer(Modifier.height(7.dp))
                Text(collection.chapterIds.size.toString() + " глав", fontFamily = WebSansFont,
                    fontSize = 11.sp, color = MaterialTheme.colorScheme.primary)
            }
        }
    }
}

'''

def patch_home(source):
    old = '''                Text(
                    book.title,
                    modifier = Modifier.align(Alignment.CenterStart)
                        .fillMaxWidth(0.51f)
                        .padding(start = 22.dp, top = 25.dp),
                    fontFamily = WebLiterataFont,
                    fontSize = 23.sp,
                    lineHeight = 27.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF49321F),
                )'''
    new = '''                Column(
                    modifier = Modifier.align(Alignment.TopStart)
                        .statusBarsPadding()
                        .fillMaxWidth(0.57f)
                        .padding(start = 16.dp, top = 8.dp),
                ) {
                    Text(book.title, fontFamily = WebLiterataFont,
                        fontSize = 24.sp, lineHeight = 28.sp,
                        fontWeight = FontWeight.Bold, maxLines = 1,
                        overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis,
                        color = Color(0xFF49321F))
                    Spacer(Modifier.height(4.dp))
                    Text("Шейхуль-Ислам Ибн Таймийя", fontFamily = WebLiterataFont,
                        fontSize = 10.5.sp, lineHeight = 14.sp,
                        fontStyle = androidx.compose.ui.text.font.FontStyle.Italic,
                        maxLines = 2, color = Color(0xFF6D492A))
                }'''
    source = one(source,old,new,'banner author')
    source = component(source,'@Composable\nprivate fun PaperCard(',
        '@Composable\nprivate fun AntiqueHomeHeader(',PAPER,'paper card')
    source = component(source,'@Composable\nprivate fun ReadingCard(',
        '@Composable\nprivate fun AntiqueQuickCard(',READING,'reading card')
    source = component(source,'@Composable\nprivate fun AntiqueQuickCard(',
        '@OptIn(ExperimentalLayoutApi::class)',QUICK,'quick cards')
    source = one(source,
        'AntiqueIcon(R.drawable.antique_search_detail, Modifier.size(width = 58.dp, height = 42.dp))',
        'AntiqueIcon(R.drawable.antique_search_detail, Modifier.size(width = 66.dp, height = 52.dp))',
        'search card')
    source = one(source,
        'if (first != null) WebCollectionCard(first, Modifier.weight(1f)) { navigate(Route.CollectionDetail(first.id)) }',
        'if (first != null) ImanHomeCollectionCard(first, Modifier.weight(1f)) { navigate(Route.CollectionDetail(first.id)) }',
        'collection 1')
    source = one(source,
        'if (second != null) WebCollectionCard(second, Modifier.weight(1f)) { navigate(Route.CollectionDetail(second.id)) }',
        'if (second != null) ImanHomeCollectionCard(second, Modifier.weight(1f)) { navigate(Route.CollectionDetail(second.id)) }',
        'collection 2')
    if 'val bannerHeight = maxWidth / 3f' not in source or 'ContentScale.FillBounds' not in source:
        raise RuntimeError('Unstable banner dimensions')
    if 'Color(0xFF315A46)' in source: raise RuntimeError('Old green CTA survives')
    return source

def build_v10(kit,destination):
    from scripts.build_iman_v9 import build_v9
    build_v9(kit,destination)
    gradle=destination/'app/build.gradle'
    s=gradle.read_text(encoding='utf-8')
    for a,b in [('versionCode 9','versionCode 10'),
        ("versionName '0.9.0'","versionName '0.10.0'"),
        ("applicationIdSuffix '.preview9'","applicationIdSuffix '.preview10'")]:
        s=one(s,a,b,'version bump')
    gradle.write_text(s,encoding='utf-8')
    home=destination/'app/src/main/java/com/xalid/meditsinaproroka/nativeapp/AntiqueDesign.kt'
    home.write_text(patch_home(home.read_text(encoding='utf-8')),encoding='utf-8')
    if list((destination/'app/src/main').rglob('*.pdf')):
        raise RuntimeError('Unexpected PDF in application')
    print('Applied v0.10: integrated paper cards, author, bronze CTA')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--dest',type=Path,required=True)
    o=p.parse_args()
    build_v10(Path(__file__).resolve().parents[1],o.dest)
