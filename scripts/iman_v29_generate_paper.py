"""One-time generation of v29 parchment from approved sample's EMPTY paper region.

No UI text, logos or icons are cut out of the reference. A high-frequency grain
patch is used as a stochastic paper *material* overlay over the single existing
continuous wallpaper, retaining the original softly curved navigation boundary.
"""
from pathlib import Path
from urllib.request import Request, urlopen
from io import BytesIO
from PIL import Image, ImageFilter
import numpy as np

REFERENCE_URL = "https://pikaso.cdnpk.net/private/production/5974181197/3839874915.png?token=exp=1794441600~hmac=5bb58b82afecd5eb26932f3b0a6bb6bf047e63c4d7469134dbdf9a99adeda362"
TARGET = Path("assets/ui/v29/iman_v29_unified_home.webp")
SOURCE = Path("assets/ui/v27/iman_v27_unified_home.webp")

def prepare_paper(base:Image.Image, reference:Image.Image)->Image.Image:
    src=np.asarray(base.convert("RGB"),dtype=np.float32)
    ref_img=reference.convert("RGB")
    if ref_img.size!=(941,1672):
        raise RuntimeError("Unexpected approved portrait reference size")
    ref=np.asarray(ref_img,dtype=np.float32)
    # Untouched parchment: no graphic/text objects in these exact coordinates.
    patch=ref[1399:1490,210:605]
    low=np.asarray(Image.fromarray(np.uint8(patch)).filter(
        ImageFilter.GaussianBlur(5)),dtype=np.float32)
    details=patch-low
    h,w=src.shape[:2]
    sh,sw=details.shape[:2]
    mirrored_x=np.concatenate((details,details[:,::-1,:]),axis=1)
    mirrored=np.concatenate((mirrored_x,mirrored_x[::-1,:,:]),axis=0)
    repeats=((h//(sh*2))+2,(w//(sw*2))+2,1)
    grain=np.tile(mirrored,repeats)[:h,:w]
    phase=np.roll(np.roll(grain,137,axis=1),163,axis=0)
    fine=np.random.default_rng(20261108).normal(0,.85,(h,w))[:,:,None]
    detail=(grain*.68+phase*.42)+fine
    toned=np.empty_like(src)
    toned[:,:,0]=src[:,:,0]*.965+2.3
    toned[:,:,1]=src[:,:,1]*.985+2.2
    toned[:,:,2]=src[:,:,2]*1.035-3.1
    return Image.fromarray(np.clip(toned+detail*1.35,0,255).astype("uint8"),"RGB")

def run():
    if not SOURCE.exists():raise RuntimeError("Base wallpaper not found")
    request=Request(REFERENCE_URL,headers={"User-Agent":"Mozilla/5.0"})
    with urlopen(request,timeout=75) as response:
        remote=response.read()
    if len(remote)<100000:raise RuntimeError("Reference texture returned empty response")
    with Image.open(BytesIO(remote)) as reference, Image.open(SOURCE) as base:
        paper=prepare_paper(base,reference)
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    paper.save(TARGET,"WEBP",quality=87,method=6)
    if TARGET.stat().st_size<20000:
        raise RuntimeError("Output parchment was unexpectedly tiny")
    print("Saved approved paper:",str(TARGET),TARGET.stat().st_size)

if __name__=="__main__":run()
