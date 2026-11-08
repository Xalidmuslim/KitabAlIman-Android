"""v0.29 reference fidelity: tighten native layout without touching book data."""
from pathlib import Path
import argparse, hashlib
from scripts.build_iman_v28 import build_v28
from scripts.build_iman_v20 import APP,replace_one

def build_v29(kit:Path,dest:Path):
    build_v28(kit,dest)
    gradle=dest/"app/build.gradle"
    s=gradle.read_text("utf-8")
    for a,b in (("versionCode 28","versionCode 29"),
                ("versionName '0.28.0'","versionName '0.29.0'"),
                ("applicationIdSuffix '.preview28'","applicationIdSuffix '.preview29'")):
        s=replace_one(s,a,b,"version")
    gradle.write_text(s,"utf-8")
    java=dest/APP
    home=java/"ModernEditorialHome.kt"
    quote=java/"ImanQuoteCarousel.kt"
    app=java/"App.kt"
    reader=java/"Reader.kt"
    originals={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
               for p in java.glob("*.kt") if p.name not in
               ("ModernEditorialHome.kt","ImanQuoteCarousel.kt")}
    original_assets={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in (dest/"app/src/main/assets").iterdir() if p.is_file()}
    paper=dest/"app/src/main/res/drawable-nodpi/iman_v27_unified_home.webp"
    paper_hash=hashlib.sha256(paper.read_bytes()).hexdigest()
    h=home.read_text("utf-8")
    for a,b in (
        ("Modifier.size(width = 77.dp, height = 66.dp)","Modifier.size(width = 91.dp, height = 88.dp)"),
        ("modifier.heightIn(min = 94.dp)","modifier.heightIn(min = 122.dp)"),
        ("fontSize = 11.3.sp,","fontSize = 12.5.sp,"),
        ("lineHeight = 14.sp, fontWeight = FontWeight.Bold,","lineHeight = 16.sp, fontWeight = FontWeight.Bold,"),
        ("fontSize = 9.2.sp,","fontSize = 10.sp,"),
        ("fontSize = 20.sp,","fontSize = 21.sp,"),
        ("fontSize = 19.sp,","fontSize = 20.sp,"),
        ("horizontalArrangement = Arrangement.spacedBy(2.dp)","horizontalArrangement = Arrangement.spacedBy(0.dp)"),
    ):
        h=replace_one(h,a,b,"reference library typography and image occupancy")
    home.write_text(h,"utf-8")
    q=quote.read_text("utf-8")
    q=replace_one(q,"modifier = Modifier.weight(0.43f).height(152.dp)",
                  "modifier = Modifier.weight(0.43f).height(174.dp)",
                  "reference quote object height")
    q=replace_one(q,"fontSize = 17.sp, lineHeight = 23.sp,",
                  "fontSize = 18.sp, lineHeight = 24.sp,",
                  "reference quote typography")
    quote.write_text(q,"utf-8")
    for name,digest in originals.items():
        if hashlib.sha256((java/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError("Changed protected Kotlin file: "+name)
    for name,digest in original_assets.items():
        if hashlib.sha256((dest/"app/src/main/assets"/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError("Changed book data: "+name)
    if hashlib.sha256(paper.read_bytes()).hexdigest()!=paper_hash:
        raise RuntimeError("Unified paper changed")
    assert "R.drawable.iman_v27_unified_home" in app.read_text("utf-8")
    assert "q.text.length <= 120" in quote.read_text("utf-8")
    assert "maxLines = 5" in quote.read_text("utf-8")
    print("PASS v29: artwork scale, native typography, one continuous background; source data protected")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dest",required=True,type=Path)
    args=p.parse_args()
    build_v29(Path(__file__).resolve().parents[1],args.dest)
