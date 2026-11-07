"""Targeted native visual corrections after comparing actual v38 and v0.12 screenshots."""
from pathlib import Path
import argparse
from scripts.build_iman_v12 import build_v12
JAVA = Path("app/src/main/java/com/xalid/meditsinaproroka/nativeapp")
NAV = "@Composable\nprivate fun StandaloneBottomNav("

def one(s, old, new, label):
    n=s.count(old)
    if n!=1: raise RuntimeError(f"{label}: {n} anchors")
    return s.replace(old,new,1)

def section(s, start, end, replacement, label):
    if s.count(start)!=1 or s.count(end)!=1:
        raise RuntimeError(label+" boundaries missing")
    i=s.index(start);j=s.index(end)
    if j<=i: raise RuntimeError(label+" inverted")
    return s[:i]+replacement+s[j:]

QUOTE = '''            item(key = "quote") {
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    color = if (dark) MaterialTheme.colorScheme.surface else Color(0xFF4B392D),
                    shape = androidx.compose.foundation.shape.RoundedCornerShape(19.dp),
                    border = androidx.compose.foundation.BorderStroke(1.dp,
                        if (dark) MaterialTheme.colorScheme.outline else Color(0xFF987552)),
                ) {
                    Box(Modifier.fillMaxWidth().background(
                        if (dark) Brush.horizontalGradient(
                            listOf(MaterialTheme.colorScheme.surface, MaterialTheme.colorScheme.surface))
                        else Brush.linearGradient(listOf(
                            Color(0xFF44342B), Color(0xFF684B36), Color(0xFF8A6549))))) {
                        if (!dark) Image(
                            painter = MedicineHomeArtwork.painter(R.drawable.antique_open_book_detail),
                            contentDescription = null,
                            modifier = Modifier.align(Alignment.BottomEnd)
                                .size(width = 164.dp, height = 142.dp),
                            contentScale = ContentScale.Fit, alpha = 0.16f,
                        )
                        Column(Modifier.fillMaxWidth().padding(horizontal = 19.dp, vertical = 18.dp)) {
                            Text("НАПОМИНАНИЕ ИЗ КНИГИ · ИБН ТАЙМИЙЯ",
                                fontFamily = WebSansFont, fontSize = 9.sp,
                                letterSpacing = 1.1.sp, fontWeight = FontWeight.Bold,
                                color = Color(0xFFE2CBA7))
                            Spacer(Modifier.height(11.dp))
                            Text("«Знай, что понятия «Иман» и «Ислам» объединяют в себе всю религию»",
                                fontFamily = WebLiterataFont,
                                fontSize = 19.sp, lineHeight = 26.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = Color(0xFFFFF1DB))
                            Spacer(Modifier.height(8.dp))
                            Text("Книга Имана · начало книги",
                                fontFamily = WebSansFont, fontSize = 11.sp,
                                color = Color(0xFFE6D2BB))
                            Spacer(Modifier.height(9.dp))
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                TextButton(onClick = {
                                    chapters.firstOrNull { it.order == 3 }?.let {
                                        navigate(Route.Reader(it.id))
                                    }
                                }, contentPadding = PaddingValues(0.dp)) {
                                    Text("Открыть цитату →", fontWeight = FontWeight.Bold,
                                        fontSize = 12.sp, color = Color(0xFFFFE8C4))
                                }
                                Spacer(Modifier.weight(1f))
                                TextButton(onClick = {
                                    first?.let { navigate(Route.Reader(it.id, resume = last != null)) }
                                }, contentPadding = PaddingValues(0.dp)) {
                                    Text("Продолжить →", fontSize = 12.sp,
                                        fontWeight = FontWeight.SemiBold,
                                        color = Color(0xFFFFE8C4))
                                }
                            }
                        }
                    }
                }
            }
'''

def patch_style(s):
    s=one(s, "import androidx.compose.ui.graphics.Color",
        "import androidx.compose.ui.graphics.Brush\nimport androidx.compose.ui.graphics.Color", "brush import")
    s=one(s, "import androidx.compose.ui.Alignment",
        "import androidx.compose.ui.Alignment\nimport androidx.compose.ui.platform.LocalContext", "context import")
    start="@Composable\ninternal fun IbnStyleHomeScreen("
    end="@Composable\nprivate fun IbnHomeLink("
    i=s.index(start);j=s.index(end,i)
    home=s[i:j]
    home=section(home,'            item(key = "quote") {',
        '            item(key = "reading-progress") {',QUOTE,"quote hero")
    home=one(home,"    val dark = sepiaDark()\n    val ink = if (dark)",
        """    val context = LocalContext.current
    val ledger = remember(context) { V38ReadingLedger(context) }
    @Suppress("UNUSED_VARIABLE") val readingRevision = ledger.version
    val dark = sepiaDark()
    val ink = if (dark)""","reading time")
    home=one(home,'SepiaMiniStat(store.bookmarks.size.toString(), "Закладок", Modifier.weight(1f))',
        'SepiaMiniStat((ledger.totalMs / 60_000L).toString() + " мин", "Время", Modifier.weight(1f))',
        "time stat")
    home=one(home,
        'val percent = if (chapters.isEmpty()) 0 else ((done * 100f) / chapters.size).toInt().coerceIn(0, 100)',
        '''val percent = (v38WeightedFraction(chapters.map {
        it.blocks.size to chapterReadFraction(it, store)
    }) * 100f).toInt().coerceIn(0, 100)''',"weighted progress")
    s=s[:i]+home+s[j:]
    start="@Composable\ninternal fun IbnStyleContentsScreen("
    i=s.index(start)
    toc=s[i:]
    toc=one(toc,'Text("Оглавление", modifier = Modifier.weight(1f)',
        'Text("Книга Имана", modifier = Modifier.weight(1f)',"no double title")
    toc=one(toc,"fontSize = 27.sp,","fontSize = 25.sp,","title size")
    toc=one(toc,"fontSize = 14.5.sp, lineHeight = 18.sp",
        "fontSize = 14.sp, lineHeight = 18.sp","TOC row font")
    toc=one(toc,"Modifier.fillMaxWidth().padding(horizontal = 11.dp, vertical = 10.dp)",
        "Modifier.fillMaxWidth().padding(horizontal = 11.dp, vertical = 8.dp)","TOC row padding")
    return s[:i]+toc

def patch_app(s):
    if NAV not in s: raise RuntimeError("Bottom nav anchor missing")
    old=s[s.index(NAV):]
    s=one(s,"Route.More -> WebMoreScreen(screenModifier, ::navigate)",
        "Route.More -> ImanV38MoreScreen(screenModifier, ::navigate)","More route")
    if old!=s[s.index(NAV):]: raise RuntimeError("BOTTOM NAV MODIFIED")
    return s

def build_v13(kit,dest):
    build_v12(kit,dest)
    gradle=dest/"app/build.gradle"
    g=gradle.read_text("utf-8")
    for a,b in (("versionCode 12","versionCode 13"),
        ("versionName '0.12.0'","versionName '0.13.0'"),
        ("applicationIdSuffix '.preview12'","applicationIdSuffix '.preview13'")):
        g=one(g,a,b,"version")
    gradle.write_text(g,"utf-8")
    j=dest/JAVA
    unchanged={p.name:p.read_bytes() for p in j.glob("*.kt")
               if p.name not in ("App.kt","IbnQayyimStyle.kt")}
    res=dest/"app/src/main/res"
    icons={str(p.relative_to(res)):p.read_bytes() for p in res.rglob("*")
           if p.is_file() and (p.name.startswith("nav_") or p.name.startswith("ic_nav_"))}
    app=j/"App.kt";app.write_text(patch_app(app.read_text("utf-8")),"utf-8")
    style=j/"IbnQayyimStyle.kt";style.write_text(patch_style(style.read_text("utf-8")),"utf-8")
    (j/"ImanV38More.kt").write_text((kit/"scripts/iman_v38_more.kt").read_text("utf-8"),"utf-8")
    for n,b in unchanged.items():
        if (j/n).read_bytes()!=b: raise RuntimeError("Changed reader or store: "+n)
    for n,b in icons.items():
        if (res/n).read_bytes()!=b: raise RuntimeError("Changed bottom icon: "+n)
    if list((dest/"app/src/main").rglob("*.pdf")):raise RuntimeError("Unexpected PDF")
    print("v0.13: visible home, TOC, More corrections; bottom nav protected")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--dest",type=Path,required=True)
    opt=parser.parse_args()
    build_v13(Path(__file__).resolve().parents[1],opt.dest)
