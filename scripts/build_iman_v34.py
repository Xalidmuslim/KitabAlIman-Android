"""v34 minimal fix for clock/book overlap observed on real Android emulator.

Native base v33 keeps shared paper and clipped five-tab layout. Only add one
statusBarsPadding to the Home header; all 131 chapters and user state unchanged.
"""
from pathlib import Path
import argparse,hashlib
from scripts.build_iman_v33 import build_v33
from scripts.build_iman_v20 import APP,replace_one

def build_v34(kit:Path,dest:Path):
    build_v33(kit,dest)
    gradle=dest/"app/build.gradle"
    gradle_text=gradle.read_text("utf-8")
    for old,new in (
        ("versionCode 33","versionCode 34"),
        ("versionName '0.33.0'","versionName '0.34.0'"),
        ("applicationIdSuffix '.preview33'","applicationIdSuffix '.preview34'"),
    ):
        gradle_text=replace_one(gradle_text,old,new,"v34 package identity")
    gradle.write_text(gradle_text,"utf-8")
    java=dest/APP
    home=java/"ModernEditorialHome.kt"
    app=java/"App.kt"
    reader=java/"Reader.kt"
    app_before=app.read_bytes()
    reader_before=reader.read_bytes()
    prior=home.read_text("utf-8")
    book_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (dest/"app/src/main/assets").iterdir() if p.is_file()}
    other_sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in java.glob("*.kt") if p.name!="ModernEditorialHome.kt"}

    updated=(kit/"scripts/ReferenceHomeV34.kt").read_text("utf-8")
    old_header="Modifier.fillMaxWidth()\n            .padding(start = 18.dp, end = 12.dp, top = 4.dp, bottom = 0.dp)"
    new_header="Modifier.fillMaxWidth().statusBarsPadding()\n            .padding(start = 18.dp, end = 12.dp, top = 4.dp, bottom = 0.dp)"
    if prior.replace(old_header,new_header)!=updated:
        raise RuntimeError("v34 Home changes beyond single system status-bar clearance")
    if updated.count(".statusBarsPadding()")!=1:
        raise RuntimeError("v34 missing/duplicate statusbar insets")
    if "modifier.fillMaxSize().padding(bottom = 76.dp).clipToBounds()" not in updated:
        raise RuntimeError("v34 clipped navigation safe region missing")
    home.write_text(updated,"utf-8")

    if app.read_bytes()!=app_before or reader.read_bytes()!=reader_before:
        raise RuntimeError("v34 unexpected native app / book reader modification")
    for name,digest in other_sources.items():
        if hashlib.sha256((java/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError("v34 changed unrelated Kotlin source: "+name)
    for name,digest in book_hashes.items():
        if hashlib.sha256((dest/"app/src/main/assets"/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError("v34 source book data changed: "+name)
    print("PASS v34: one top inset, no navbar overlap, preserved 79 quotes and 131 chapters")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--dest",required=True,type=Path)
    build_v34(Path(__file__).resolve().parents[1],parser.parse_args().dest)
