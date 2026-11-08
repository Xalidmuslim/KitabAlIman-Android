"""One-time import of six independently generated reference images into v0.27.

Assets are downloaded once and committed as ordinary WebP files. The shipping
Android build never depends on expiring URLs or a third-party service.
"""
from pathlib import Path
from io import BytesIO
from urllib.request import Request, urlopen
from PIL import Image, ImageFilter
import numpy as np

REMOTE = {
  "unified_home": "https://pikaso.cdnpk.net/private/production/5973994785/3839787145.png?token=exp=1794441600~hmac=3a0f91f3af53ae20750f3adbacdcb087d4ec3b7896b82ec533cef94d45922ff5",
  "reminder": "https://pikaso.cdnpk.net/private/production/5974001116/3839790063.png?token=exp=1794441600~hmac=b2f8bb76019634841a22e0be38effe67d564cc6c9d4b52e68d57387928f37419",
  "contents": "https://pikaso.cdnpk.net/private/production/5974001293/3839790138.png?token=exp=1794441600~hmac=d444173bb1c58e14cb3c72e1d41dfe0b9b1088d0b8b2b189767bcf69ae496b0d",
  "collections": "https://pikaso.cdnpk.net/private/production/5974001455/3839790210.png?token=exp=1794441600~hmac=02ca6916dd60df9f0da6805524094ee68b279e96e7e1f3d23a78d7424b068e78",
  "glossary": "https://pikaso.cdnpk.net/private/production/5974001728/3839790288.png?token=exp=1794441600~hmac=9c48dfd65322879860471fe5b1db6ae5193e96396b8395ae0b200d05c35d787d",
  "bookmarks": "https://pikaso.cdnpk.net/private/production/5974001912/3839790386.png?token=exp=1794441600~hmac=4b96f43b3c5735295b094ae9c76588f035aab6982a344626523335a9493aa1ac"
}

TARGET = Path("assets/ui/v27")

def matte(source: Image.Image, size: tuple[int,int]) -> Image.Image:
    original = source.convert("RGB")
    work_size = (round(size[0]*1.8),round(size[1]*1.8))
    f = min(work_size[0]/original.width, work_size[1]/original.height)
    scaled = original.resize(
        (max(1,round(original.width*f)),max(1,round(original.height*f))),
        Image.Resampling.LANCZOS,
    )
    w,h=scaled.size
    yy,xx=np.mgrid[0:h,0:w]
    d=((xx-(w-1)/2)/(w*.5))**2+((yy-(h-1)/2)/(h*.5))**2
    fade=np.clip((1-d)/0.47,0,1)
    fade=fade*fade*(3-2*fade)
    lum=np.asarray(scaled.convert("L"),dtype=np.float32)
    ratio=np.clip((248-lum)/51,0,1)**0.8
    alpha=np.uint8(np.clip(np.maximum(fade*ratio,fade*.14)*255,0,255))
    matte=Image.fromarray(alpha,"L").filter(ImageFilter.GaussianBlur(3))
    rgba=scaled.convert("RGBA")
    rgba.putalpha(matte)
    canvas=Image.new("RGBA",work_size,(0,0,0,0))
    canvas.alpha_composite(rgba,((work_size[0]-w)//2,(work_size[1]-h)//2))
    result=canvas.resize(size,Image.Resampling.LANCZOS)
    # Preserve true full transparency around artwork (never a solid rectangle).
    assert result.getchannel("A").getpixel((0,0))==0
    return result

def execute() -> None:
    TARGET.mkdir(parents=True,exist_ok=True)
    for name,url in REMOTE.items():
        req=Request(url,headers={"User-Agent":"Mozilla/5.0 ImanReferenceImporter/1.0"})
        with urlopen(req,timeout=60) as response:
            data=response.read()
        if len(data)<50000:
            raise ValueError(f"Unexpectedly small generated image: {name}")
        src=Image.open(BytesIO(data))
        src.load()
        if src.width<900 or src.height<900:
            raise ValueError(f"Generated image is too small: {name} {src.size}")
        if name=="unified_home":
            output=src.convert("RGB").resize((648,1152),Image.Resampling.LANCZOS)
        elif name=="reminder":
            output=matte(src,(380,245))
        else:
            output=matte(src,(240,180))
        dest=TARGET/f"iman_v27_{name}.webp"
        output.save(dest,"WEBP",quality=76 if name!="unified_home" else 80,method=6)
        if dest.stat().st_size<3300:
            raise ValueError(f"Rendered asset unexpectedly small: {name}")
        print(f"Imported {name}: source={src.size}, output={output.size}, bytes={dest.stat().st_size}")
    assert len(list(TARGET.glob("iman_v27_*.webp")))==6

if __name__=="__main__":
    execute()
