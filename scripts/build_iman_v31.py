"""v0.31: keep the reference's uninterrupted paper while reserving navbar viewport.

The v30 emulator screenshot showed the second topic row rendered underneath
bottom tabs. This corrects only LazyColumn's viewport, not its contents.
"""
from pathlib import Path
import argparse,hashlib
from scripts.build_iman_v30 import build_v30
from scripts.build_iman_v20 import APP,replace_one

def build_v31(kit:Path,dest:Path):
    build_v30(kit,dest)
    gradle=dest/"app/build.gradle"
    g=gradle.read_text("utf-8")
    for old,new in (("versionCode 30","versionCode 31"),
                    ("versionName '0.30.0'","versionName '0.31.0'"),
                    ("applicationIdSuffix '.preview30'","applicationIdSuffix '.preview31'")):
        g=replace_one(g,old,new,"v31 package")
    gradle.write_text(g,"utf-8")
    src=dest/APP
    h=src/"ModernEditorialHome.kt"
    protected={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
               for p in src.glob("*.kt") if p.name!="ModernEditorialHome.kt"}
    assets=dest/"app/src/main/assets"
    data={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in assets.iterdir() if p.is_file()}
    s=h.read_text("utf-8")
    s=replace_one(s,
        "modifier = Modifier.fillMaxSize(),\n            contentPadding = PaddingValues(start = 17.dp, end = 17.dp, top = 0.dp, bottom = 102.dp)",
        "modifier = Modifier.fillMaxSize().padding(bottom = 76.dp),\n            contentPadding = PaddingValues(start = 17.dp, end = 17.dp, top = 0.dp, bottom = 26.dp)",
        "v31 stop content drawing behind navbar while preserving seamless root wallpaper")
    h.write_text(s,"utf-8")
    for name,digest in protected.items():
        assert hashlib.sha256((src/name).read_bytes()).hexdigest()==digest,name
    for name,digest in data.items():
        assert hashlib.sha256((assets/name).read_bytes()).hexdigest()==digest,name
    assert "book.collections.take(2)" in s
    assert "Modifier.fillMaxSize().padding(bottom = 76.dp)" in s
    print("PASS v31: nav safe viewport, unchanged wallpaper, book and navigation")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dest",type=Path,required=True)
    build_v31(Path(__file__).resolve().parents[1],p.parse_args().dest)
