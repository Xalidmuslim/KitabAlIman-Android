"""v0.46.3 — seamless parchment branding and a fully visible reminder illustration.

Preserve all native reader/content/state/routes; retain v462's original More
menu and the exact supplied icon drawing. Fix only resource compositing and
two Compose illustration placements. No generated prose or book text changes.
"""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

from scripts.build_iman_v462 import build_v462, SOURCE, SOURCE_SHA
from scripts.build_iman_v461 import digest
from scripts.build_iman_v20 import APP, NAV, replace_one

# Hand-guided foreground zones of the user's own 1254px illustration,
# normalized to its original square. GrabCut refines each pixel contour
# without altering the calligraphy or drawing.
POLYGONS=[
 [(180,208),(240,194),(301,211),(353,230),(883,218),(935,224),(959,262),(961,320),
  (924,364),(925,793),(895,847),(890,909),(852,951),(405,997),(311,985),
  (272,957),(279,854),(283,752),(276,608),(270,460),(238,417),(200,388),(182,344)],
 [(93,514),(293,489),(356,503),(381,530),(371,629),(372,896),(319,929),
  (109,925),(81,879),(84,700),(90,650)],
 [(900,800),(885,702),(908,632),(948,568),(1011,509),(1080,468),
  (1190,441),(1207,441),(1187,501),(1150,568),(1108,648),(1035,736),(950,799)],
 [(881,763),(948,757),(988,791),(999,819),(1029,839),(1062,880),(1064,949),
  (1050,981),(998,1002),(819,1000),(790,968),(800,884),(820,848),(864,816)]
]


def alpha_extract(source: Image.Image) -> Image.Image:
    w,h=source.size
    if w!=h:
        raise RuntimeError("Brand source unexpectedly non-square")
    polygons=np.zeros((h,w),dtype=np.uint8)
    for region in POLYGONS:
        vertices=np.array([(int(x*w/1254),int(y*h/1254))
                           for x,y in region],dtype=np.int32)
        cv2.fillPoly(polygons,[vertices],255)
    radius=max(3,round(w/50))
    kernel=np.ones((radius,radius),dtype=np.uint8)
    inside=cv2.erode(polygons,kernel,iterations=1)
    outside=cv2.dilate(polygons,kernel,iterations=1)
    mask=np.full((h,w),cv2.GC_PR_BGD,dtype=np.uint8)
    mask[outside==0]=cv2.GC_BGD
    mask[polygons>0]=cv2.GC_PR_FGD
    mask[inside>0]=cv2.GC_FGD
    bgr=cv2.cvtColor(np.array(source.convert("RGB")),cv2.COLOR_RGB2BGR)
    bg=np.zeros((1,65),dtype=np.float64)
    fg=np.zeros((1,65),dtype=np.float64)
    cv2.grabCut(bgr,mask,None,bg,fg,5,cv2.GC_INIT_WITH_MASK)
    binary=np.uint8((mask==cv2.GC_FGD)|(mask==cv2.GC_PR_FGD))*255
    count,labels,areas,_=cv2.connectedComponentsWithStats(binary,connectivity=8)
    cleaned=np.zeros_like(binary)
    for i in range(1,count):
        if areas[i,cv2.CC_STAT_AREA]>=20:
            cleaned[labels==i]=255
    alpha=Image.fromarray(cleaned,"L").filter(ImageFilter.GaussianBlur(0.6))
    result=source.convert("RGBA")
    result.putalpha(alpha)
    result=ImageEnhance.Color(result).enhance(.93)
    result=ImageEnhance.Contrast(result).enhance(1.07)
    return result


def centered_cutout(art: Image.Image, dimension: int, fraction: float) -> Image.Image:
    bounds=art.getchannel("A").getbbox()
    if bounds is None:
        raise RuntimeError("Icon foreground unexpectedly empty")
    crop=art.crop(bounds)
    limit=dimension*fraction
    factor=min(limit/crop.width,limit/crop.height)
    crop=crop.resize((max(1,round(crop.width*factor)),
                      max(1,round(crop.height*factor))),Image.Resampling.LANCZOS)
    result=Image.new("RGBA",(dimension,dimension),(0,0,0,0))
    result.alpha_composite(crop,((dimension-crop.width)//2,(dimension-crop.height)//2))
    return result


def enhance_reminder(source: Path, destination: Path) -> None:
    with Image.open(source) as original:
        if original.size!=(180,122) or original.mode!="RGBA":
            raise RuntimeError("Previously approved reminder source changed")
        pic=original.copy()
    rgb=ImageEnhance.Contrast(pic.convert("RGB")).enhance(1.23)
    rgb=ImageEnhance.Color(rgb).enhance(.88)
    rgb=ImageEnhance.Brightness(rgb).enhance(.83)
    pixels=np.asarray(rgb,dtype=np.float32)
    luminance=pixels[:,:,0]*.21+pixels[:,:,1]*.72+pixels[:,:,2]*.07
    opacity=np.asarray(pic.getchannel("A"),dtype=np.float32)
    alpha=Image.fromarray(
        np.uint8(np.clip(opacity*(1.2+np.maximum(0,170-luminance)/600),0,255)),
        "L"
    )
    revised=rgb.convert("RGBA")
    revised.putalpha(alpha)
    destination.parent.mkdir(parents=True,exist_ok=True)
    revised.save(destination,"WEBP",lossless=True,method=6,exact=True)


def prepare_artwork(kit: Path, res: Path) -> None:
    source=kit/SOURCE
    if digest(source)!=SOURCE_SHA:
        raise RuntimeError("Do not replace or regenerate the user's uploaded image")
    with Image.open(source) as original:
        if original.size!=(192,192) or original.mode!="RGB":
            raise RuntimeError("User's image source dimensions changed")
        cutout=alpha_extract(original)
    drawable=res/"drawable-nodpi"
    mipmap=res/"mipmap-anydpi"
    drawable.mkdir(parents=True,exist_ok=True)
    mipmap.mkdir(parents=True,exist_ok=True)

    header=centered_cutout(cutout,320,.96)
    header.save(drawable/"iman_v463_header.webp","WEBP",lossless=True,method=6,exact=True)
    # Adaptive Android masks expose only the center 66% of their 108dp surface.
    # A 55% bounded subject preserves all scroll/feather contours on round icons.
    foreground=centered_cutout(cutout,512,.55)
    foreground.save(drawable/"iman_v39_launcher_foreground.webp","WEBP",
                    lossless=True,method=6,exact=True)
    oldpaper=drawable/"iman_v38_flat_paper.webp"
    with Image.open(oldpaper) as p:
        paper=p.convert("RGB")
        pw,ph=paper.size
        paper=paper.crop((int(pw*.26),int(ph*.37),
                          int(pw*.74),int(ph*.60))).resize((512,512),Image.Resampling.BICUBIC)
    beige=Image.new("RGB",(512,512),(247,234,215))
    background=Image.blend(paper,beige,.80).convert("RGBA")
    background.alpha_composite(centered_cutout(cutout,512,.77))
    background.convert("RGB").save(mipmap/"iman_v39_launcher.webp",
                                   "WEBP",quality=95,method=6)
    enhance_reminder(kit/"assets/ui/v459/iman_v459_integrated_manuscript.webp",
                     drawable/"iman_v463_reminder_depth.webp")


def patch_home(file: Path):
    text=file.read_text("utf-8")
    for old,new in (
        ("R.drawable.iman_v462_brand_icon","R.drawable.iman_v463_header"),
        ("contentDescription = null, modifier = Modifier.size(40.dp),",
         "contentDescription = null, modifier = Modifier.size(46.dp),"),
        ("Spacer(Modifier.width(11.dp))","Spacer(Modifier.width(8.dp))"),
    ):
        if text.count(old)!=1:
            raise RuntimeError("Home header layout contract changed: "+old)
        text=text.replace(old,new,1)
    file.write_text(text,"utf-8")


def patch_quote(file: Path):
    text=file.read_text("utf-8")
    replacements=(
        (".width(if (compactScreen) 80.dp else 99.dp)\n"
         "                            .height(if (compactScreen) 86.dp else 103.dp)",
         ".width(if (compactScreen) 112.dp else 128.dp)\n"
         "                            .height(if (compactScreen) 100.dp else 110.dp)"),
        (".requiredWidth(if (compactScreen) 132.dp else 170.dp)\n"
         "                                .height(if (compactScreen) 86.dp else 103.dp)",
         ".fillMaxSize()"),
        ("R.drawable.iman_v459_integrated_manuscript",
         "R.drawable.iman_v463_reminder_depth"),
    )
    for old,new in replacements:
        if text.count(old)!=1:
            raise RuntimeError("Reminder image sizing contract changed: "+old)
        text=text.replace(old,new,1)
    if ".requiredWidth(" in text or "R.drawable.iman_v459_integrated_manuscript" in text:
        raise RuntimeError("Clipped reminder illustration still present")
    file.write_text(text,"utf-8")


def build_v463(kit: Path,dest: Path):
    build_v462(kit,dest)
    java=dest/APP
    res=dest/"app/src/main/res"
    assets=dest/"app/src/main/assets"
    manifest=dest/"app/src/main/AndroidManifest.xml"
    gradle=dest/"app/build.gradle"

    app_before=(java/"App.kt").read_bytes()
    more_before=(java/"ImanV38More.kt").read_bytes()
    manifest_before=manifest.read_bytes()
    protected={p.name:digest(p) for p in java.glob("*.kt") if p.name not in
               ("ModernEditorialHome.kt","ImanQuoteCarousel.kt")}
    content={p.name:digest(p) for p in assets.iterdir() if p.is_file()}
    protected_res={str(p.relative_to(res)):digest(p) for p in res.rglob("*") if p.is_file()}
    excluded={"drawable-nodpi/iman_v39_launcher_foreground.webp",
              "mipmap-anydpi/iman_v39_launcher.webp"}

    version=gradle.read_text("utf-8")
    for old,new in (
        ("versionCode 62","versionCode 63"),
        ("versionName '0.46.2'","versionName '0.46.3'"),
        ("applicationIdSuffix '.preview462'","applicationIdSuffix '.preview463'"),
    ):
        version=replace_one(version,old,new,"v463 standalone preview")
    gradle.write_text(version,"utf-8")

    patch_home(java/"ModernEditorialHome.kt")
    patch_quote(java/"ImanQuoteCarousel.kt")
    prepare_artwork(kit,res)

    if (java/"App.kt").read_bytes()!=app_before or NAV not in app_before.decode("utf-8"):
        raise RuntimeError("Five-tab navigation altered")
    if (java/"ImanV38More.kt").read_bytes()!=more_before:
        raise RuntimeError("Do not remove original More icons or Settings gear")
    if manifest.read_bytes()!=manifest_before:
        raise RuntimeError("Android manifest altered")
    for name,sha in protected.items():
        if digest(java/name)!=sha:
            raise RuntimeError("Unrelated Kotlin changed: "+name)
    for name,sha in content.items():
        if digest(assets/name)!=sha:
            raise RuntimeError("Protected book/quiz/bookmarks asset changed: "+name)
    for name,sha in protected_res.items():
        if name not in excluded and digest(res/name)!=sha:
            raise RuntimeError("Unrelated resource changed: "+name)
    book=json.loads((assets/"book.json").read_text("utf-8"))
    quiz=json.loads((assets/"quiz.json").read_text("utf-8"))
    excerpts=json.loads((assets/"featured_quotes.json").read_text("utf-8"))
    if len(book["chapters"])!=131 or len(quiz["chapters"])!=131 or len(excerpts)!=79:
        raise RuntimeError("131 chapters, quiz and 79 reminders must stay intact")
    print("PASS v463: borderless Home icon, safe launcher, fully fitted contrast reminder; More unchanged")


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--dest",required=True,type=Path)
    args=ap.parse_args()
    build_v463(Path(__file__).resolve().parents[1],args.dest)
