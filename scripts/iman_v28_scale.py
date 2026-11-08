"""Reframe individual v27 sepia illustrations, preserving their feathered alpha edges.

The v27 illustration import unnecessarily embedded the subject in oversized
transparent canvas; Compose fit scaling then made it look miniature.
This processor only crops empty/almost-empty margins. No UI screenshot use.
"""
from PIL import Image

def fill_artwork(source:Image.Image,pad:float=0.07)->Image.Image:
    src=source.convert("RGBA")
    w,h=src.size
    alpha=src.getchannel("A")
    high=alpha.point(lambda v:255 if v>=180 else 0)
    bbox=high.getbbox()
    if not bbox:
        raise ValueError("Original illustration has no opaque pixels")
    x0,y0,x1,y1=bbox
    mx=max(8,round((x1-x0)*.09))
    my=max(8,round((y1-y0)*.12))
    bbox=(max(0,x0-mx),max(0,y0-my),
          min(w,x1+mx),min(h,y1+my))
    art=src.crop(bbox)
    # Distribute visual weight evenly without painting the image's corners.
    iw=max(1,round(w*(1-2*pad)))
    ih=max(1,round(h*(1-2*pad)))
    scale=min(iw/art.width,ih/art.height)
    resized=art.resize((max(1,round(art.width*scale)),
                       max(1,round(art.height*scale))),Image.Resampling.LANCZOS)
    result=Image.new("RGBA",(w,h),(0,0,0,0))
    result.alpha_composite(resized,((w-resized.width)//2,(h-resized.height)//2))
    assert result.getpixel((0,0))[3]==0
    return result

def install(source_folder,target_folder):
    target_folder.mkdir(parents=True,exist_ok=True)
    for name in ("contents","collections","glossary","bookmarks","reminder"):
        src=source_folder/f"iman_v27_{name}.webp"
        with Image.open(src) as picture:
            result=fill_artwork(picture,pad=0 if name=="reminder" else .07)
        target=target_folder/f"iman_v28_{name}.webp"
        result.save(target,"WEBP",quality=96,method=6)
        if target.stat().st_size < 3000:
            raise ValueError("Art incorrectly exported: "+name)
