"""Port active reading stats and memory review from reference v38 into native Compose.

Bottom navigation icons, routes, reader anchors, user notes and source texts remain unchanged.
"""
from pathlib import Path
import argparse, base64, lzma, hashlib
from scripts.build_iman_v11 import build_v11
JAVA = Path('app/src/main/java/com/xalid/meditsinaproroka/nativeapp')

def one(s, old, new, name):
    n = s.count(old)
    if n != 1: raise RuntimeError(f'{name} unexpected anchor count: {n}')
    return s.replace(old,new,1)

def build_v12(kit, dest):
    build_v11(kit,dest)
    gradle=dest/'app/build.gradle'
    g=gradle.read_text(encoding='utf-8')
    for old,new in [('versionCode 11','versionCode 12'),("versionName '0.11.0'","versionName '0.12.0'"),("applicationIdSuffix '.preview11'","applicationIdSuffix '.preview12'")]:
        g=one(g,old,new,'version')
    gradle.write_text(g,encoding='utf-8')
    src=dest/JAVA
    app=src/'App.kt'; a=app.read_text(encoding='utf-8')
    nav_start=a.index('@Composable\nprivate fun StandaloneBottomNav(')
    original_nav=a[nav_start:]
    a=one(a,'Route.Progress -> FaithProgressScreen(', 'Route.Progress -> V38StatisticsScreen(', 'statistics screen')
    if a[a.index('@Composable\nprivate fun StandaloneBottomNav('):] != original_nav:
        raise RuntimeError('Protected bottom navigation changed')
    app.write_text(a,encoding='utf-8')
    reader=src/'Reader.kt'
    s=reader.read_text(encoding='utf-8')
    s=one(s,'FaithReadingProgress(chapter = chapter, store = store)',
          'V38ReadingSession(chapter = chapter, scrollState = scrollState)\n            V38ReaderStatus(chapter = chapter, store = store)',
          'reader session tracker')
    reader.write_text(s,encoding='utf-8')
    payload=(kit/'scripts/v12_engine.b64').read_text(encoding='ascii').strip()
    kotlin=lzma.decompress(base64.b64decode(payload,validate=True))
    expected='a3578b8c0ee786675a3ead7e15b576adaad046062086b260093123fb1080f759'
    if hashlib.sha256(kotlin).hexdigest()!=expected:
        raise RuntimeError('v38 native study engine source checksum failed')
    source = kotlin.decode('utf-8')
    # Compose's Modifier.background extension is an explicit import.
    source = one(source,
        'import androidx.compose.foundation.clickable',
        'import androidx.compose.foundation.background\nimport androidx.compose.foundation.clickable',
        'background extension import')
    (src/'IbnV38StudyEngine.kt').write_text(source, encoding='utf-8')
    tests=dest/'app/src/test/java/com/xalid/meditsinaproroka/nativeapp'
    tests.mkdir(parents=True,exist_ok=True)
    (tests/'IbnV38StudyEngineTest.kt').write_text((kit/'scripts/IbnV38StudyEngineTest.kt').read_text(encoding='utf-8'),encoding='utf-8')
    if list((dest/'app/src/main').rglob('*.pdf')): raise RuntimeError('PDF resource forbidden')
    print('Native v38 reading session + memory review + weekly stats transferred with navigation invariant')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--dest',type=Path,required=True)
    args=ap.parse_args();build_v12(Path(__file__).resolve().parents[1],args.dest)
