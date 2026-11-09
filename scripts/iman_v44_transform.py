"""Unify actual generated native Compose subpages without changing the approved Home.

Only styling, section backgrounds and reader heading sizes are touched. Parsed
Material3 container calls keep their onClick, state and content lambdas intact.
"""
import re
from pathlib import Path

COLOR = "androidx.compose.ui.graphics.Color.Transparent"

def one(s, old, new, label):
    count=s.count(old)
    if count != 1:
        raise RuntimeError(f"v44 {label}: expected one source anchor, found {count}")
    return s.replace(old,new,1)

def matching(s, start):
    depth=0
    quote=None
    escape=False
    for i in range(start,len(s)):
        ch=s[i]
        if quote:
            if escape: escape=False
            elif ch=="\\": escape=True
            elif ch==quote: quote=None
            continue
        if ch in ('"',"'"): quote=ch; continue
        if ch=="(": depth+=1
        if ch==")":
            depth-=1
            if depth==0: return i
    raise RuntimeError("v44 unbalanced Material3 call")

def split_args(args):
    result=[];depth=0;quote=None;escape=False;start=0
    for i,ch in enumerate(args):
        if quote:
            if escape:escape=False
            elif ch=="\\":escape=True
            elif ch==quote:quote=None
            continue
        if ch in ('"',"'"):quote=ch;continue
        if ch in "([{":depth+=1
        elif ch in ")]}":depth-=1
        elif ch=="," and depth==0:
            result.append(args[start:i].strip());start=i+1
    if args[start:].strip():result.append(args[start:].strip())
    return result

def flatten_material_containers(source):
    regex=re.compile(r"(?<![\w.])(OutlinedCard|ElevatedCard|Card|Surface)\s*\(")
    edits=[]
    for m in regex.finditer(source):
        kind=m.group(1)
        start=source.index("(",m.start());end=matching(source,start)
        if edits and m.start()<edits[-1][1]:continue
        options=split_args(source[start+1:end])
        out=[];named=set()
        for opt in options:
            key=opt.split("=",1)[0].strip() if "=" in opt else None
            if key in ("colors","border","elevation","tonalElevation","shadowElevation","color"):
                named.add(key)
                if key=="border":opt="border = null"
                elif key=="colors":opt=f"colors = CardDefaults.cardColors(containerColor = {COLOR})"
                elif key=="elevation":opt="elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)"
                elif key in ("tonalElevation","shadowElevation"):opt=f"{key} = 0.dp"
                elif key=="color":
                    value=opt.split("=",1)[1]
                    # Preserve highlight on functional active/selected choices.
                    if not any(tag in value for tag in (
                            "active","selected","picked","correct",
                            "backgroundColor","unanswered","answered")):
                        opt=f"color = {COLOR}"
            out.append(opt)
        newkind="Card" if kind in ("Card","OutlinedCard","ElevatedCard") else "Surface"
        if newkind=="Card":
            if "colors" not in named:out.append(f"colors = CardDefaults.cardColors(containerColor = {COLOR})")
            if "border" not in named:out.append("border = null")
            if "elevation" not in named:out.append("elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)")
        elif "color" not in named:
            out.append(f"color = {COLOR}")
        edits.append((m.start(),end+1,newkind+"("+", ".join(out)+")"))
    for a,b,value in reversed(edits):
        source=source[:a]+value+source[b:]
    return source,len(edits)

def patch_app(s):
    s=one(s,"if (seamlessHome) {",
        "if (MaterialTheme.colorScheme.background.red >= 0.25f) {","shared wallpaper")
    s=one(s,
        "screenStateHolder.SaveableStateProvider(routeStateKey(route)) {\n                when (route) {",
        "screenStateHolder.SaveableStateProvider(routeStateKey(route)) {\n                ImanUnifiedRouteTheme(isHome = route == Route.Home) {\n                when (route) {",
        "non-home theme scope")
    s=one(s,
        "                }\n            }\n        }\n            StandaloneBottomNav(",
        "                }\n                }\n            }\n        }\n            StandaloneBottomNav(",
        "non-home theme ending")
    s=one(s,
        "seamlessHome = seamlessHome,\n                modifier = Modifier.align(Alignment.BottomCenter),",
        "seamlessHome = seamlessHome || current != Route.Home,\n                modifier = Modifier.align(Alignment.BottomCenter),",
        "shared bottom navbar")
    return s

def patch_screens(s):
    s,n=flatten_material_containers(s)
    if n<12: raise RuntimeError("v44 insufficient inner screen containers inspected")
    start=s.index("fun SearchScreen(");end=s.index("fun BookmarksScreen(",start)
    area=s[start:end]
    area=one(area,"        OutlinedTextField(\n            value = query,",
        "        TextField(\n            value = query,","flat search field")
    area=one(area,
        "            singleLine = true\n        )\n        ScrollableTabRow(",
        f"            singleLine = true,\n            colors = TextFieldDefaults.colors(focusedContainerColor = {COLOR},\n                unfocusedContainerColor = {COLOR}),\n        )\n        ScrollableTabRow(",
        "flat search input colors")
    return s[:start]+area+s[end:]

def patch_reader(s):
    a=s.index("        if (MaterialTheme.colorScheme.background.red >= 0.25f) {\n            // Keep the original antique paper asset unchanged.")
    b=s.index("        // The page, status-bar area",a)
    s=s[:a]+"        // App.kt paints the same shared parchment behind the Reader.\n"+s[b:]
    s=one(s,"(if (chapter.title.length > 60) 21 else 24).sp",
        "(if (chapter.title.length > 60) 18 else 20).sp","reader chapter headings")
    s=one(s,"(if (chapter.title.length > 60) 26 else 29).sp",
        "(if (chapter.title.length > 60) 23 else 25).sp","reader heading line height")
    old="""            .background(
                MaterialTheme.colorScheme.primary.copy(alpha = 0.065f),
                androidx.compose.foundation.shape.RoundedCornerShape(10.dp),
            ),"""
    s=one(s,old,",","flat hadith/verse/footnote presentation")
    scripture='''.background(MaterialTheme.colorScheme.primary.copy(alpha = 0.065f),
                            androidx.compose.foundation.shape.RoundedCornerShape(9.dp))'''
    s=one(s,scripture,"","flatten cited-verse paragraph paper")
    s=s.replace("            .height(IntrinsicSize.Min)\n,",
                "            .height(IntrinsicSize.Min),")
    s,n=flatten_material_containers(s)
    if n<2:raise RuntimeError("v44 missing Reader card sections")
    return s

def patch_web(s):
    s=one(s,"color = if (compact) Color.Transparent else MaterialTheme.colorScheme.background,",
          "color = Color.Transparent,","flat subpage headers")
    s=one(s,
          'Column(modifier.fillMaxSize().background(MaterialTheme.colorScheme.background)) {\n        WebHeader("Настройки чтения", back = back)',
          'Column(modifier.fillMaxSize()) {\n        WebHeader("Настройки чтения", back = back)',
          "settings background")
    a=s.index('@Composable\nprivate fun PaperBackgroundChoices(store: AppStore) {')
    b=s.index('@Composable\nfun WebReaderSettingsSheet(',a)
    note="""@Composable
private fun PaperBackgroundChoices(store: AppStore) {
    // Persisted settings are untouched. The app now has one background.
    Text("Единый пергаментный фон книги",
        color = MaterialTheme.colorScheme.onSurfaceVariant,
        fontFamily = WebSansFont, fontSize = 12.sp)
}

"""
    s=s[:a]+note+s[b:]
    # This legacy menu is not the main Route.More, but must not repaint the paper.
    s=s.replace('Column(modifier.fillMaxSize().background(MaterialTheme.colorScheme.background)) {\\n        WebHeader("Ещё"', 'Column(modifier.fillMaxSize()) {\\n        WebHeader("Ещё"')
    s,n=flatten_material_containers(s)
    if n<7:raise RuntimeError("v44 settings container inventory shrank")
    return s

def patch_contents(s):
    s=one(s,
       "Column(modifier.fillMaxSize().background(if (dark) MaterialTheme.colorScheme.background else SepiaPaper)) {",
       "Column(modifier.fillMaxSize()) {",
       "toc paper background")
    s,n=flatten_material_containers(s)
    s=one(s,"color = if (active) Color.White else ink",
       "color = if (active) MaterialTheme.colorScheme.primary else ink",
       "toc selected filter contrast")
    return s

def patch_statistics(s):
    s=one(s,"Column(modifier.fillMaxSize().background(paper)) {",
       "Column(modifier.fillMaxSize()) {","statistics opaque background")
    s,n=flatten_material_containers(s)
    return s

PATCHES={
    "App.kt":patch_app,
    "Screens.kt":patch_screens,
    "Reader.kt":patch_reader,
    "WebDesign.kt":patch_web,
    "IbnQayyimStyle.kt":patch_contents,
    "IbnV38StudyEngine.kt":patch_statistics,
    "FaithStudy.kt":lambda s:flatten_material_containers(s)[0],
}

def patch_all(java: Path):
    result={}
    for name,update in PATCHES.items():
        path=java/name
        before=path.read_text("utf-8")
        after=update(before)
        if after==before:raise RuntimeError("v44 produced no changes in "+name)
        path.write_text(after,"utf-8")
        result[name]=(len(before),len(after))
    return result
