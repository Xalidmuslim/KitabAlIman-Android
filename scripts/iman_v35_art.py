"""v0.35 matte book artwork finishing (offline, once during Android build).

Reduce upper and side shadow halos but preserve crisp opaque object details,
art-specific alpha and gold ornament. Never crop from an app screenshot.
No Compose RenderEffect, per-frame blur, GPU color matrix or added cards.
"""
from PIL import Image, ImageEnhance, ImageChops

ICONS=("contents","collections","glossary","bookmarks")

def _tone(src:Image.Image, *, saturation:float, contrast:float, brightness:float)->Image.Image:
    im=src.convert("RGBA")
    rgb=im.convert("RGB")
    rgb=ImageEnhance.Color(rgb).enhance(saturation)
    rgb=ImageEnhance.Contrast(rgb).enhance(contrast)
    rgb=ImageEnhance.Brightness(rgb).enhance(brightness)
    rgb=Image.blend(rgb,Image.new("RGB",im.size,(242,226,203)),0.035)
    rgb.putalpha(im.getchannel("A"))
    return rgb

def _quiet_fringe(src:Image.Image, *, top:float, outside:float)->Image.Image:
    im=src.convert("RGBA")
    w,h=im.size
    alpha=bytearray(im.getchannel("A").tobytes())
    for y in range(h):
        top_factor=top+(1-top)*min(1.0,y/max(1,h*.60))
        for x in range(w):
            i=y*w+x
            a=alpha[i]
            if a==0 or a>=210:
                continue  # keep opaque object edges, preserve transparent corners
            strength=outside+(1-outside)*(a/210.0)**2
            alpha[i]=min(255,round(a*strength*top_factor))
    im.putalpha(Image.frombytes("L",(w,h),bytes(alpha)))
    return im

def soften_icon(source:Image.Image)->Image.Image:
    # Existing independent book/scroll art contains diffuse opaque-looking
    # "upper" shadows. Reduce ONLY low-alpha pixels there, never the object.
    im=_tone(source,saturation=.81,contrast=.925,brightness=1.055)
    return _quiet_fringe(im,top=.48,outside=.43)

def soften_reminder(source:Image.Image)->Image.Image:
    im=source.convert("RGBA")
    w,h=im.size
    # Preserve the finely illustrated arch, while removing the bright square
    # plume and improving the visual occupancy of the book/feather.
    a=im.getchannel("A")
    bbox=a.point(lambda v:255 if v>=42 else 0).getbbox()
    if bbox is None:
        raise ValueError("Reminder artwork is transparent")
    left,top,right,bottom=bbox
    padx=max(6,round((right-left)*.047))
    pady=max(5,round((bottom-top)*.047))
    box=(max(0,left-padx),max(0,top-pady),
         min(w,right+padx),min(h,bottom+pady))
    crop=im.crop(box)
    tw=int(w*.93)
    th=int(h*.93)
    scale=min(tw/crop.width,th/crop.height)
    # Resizing is a pre-build operation; not re-rasterized per frame.
    crop=crop.resize((max(1,round(crop.width*scale)),
                      max(1,round(crop.height*scale))),Image.Resampling.LANCZOS)
    canvas=Image.new("RGBA",(w,h),(0,0,0,0))
    canvas.alpha_composite(crop,((w-crop.width)//2,(h-crop.height)//2))
    canvas=_tone(canvas,saturation=.91,contrast=.985,brightness=1.025)
    canvas=_quiet_fringe(canvas,top=.72,outside=.70)
    canvas.putpixel((0,0),(0,0,0,0))
    return canvas

def install(input_folder,output_folder):
    output_folder.mkdir(parents=True,exist_ok=True)
    for name in (*ICONS,"reminder"):
        original=input_folder/f"iman_v32_{name}.webp"
        with Image.open(original) as im:
            result=(soften_icon(im) if name!="reminder" else soften_reminder(im))
        result.save(output_folder/f"iman_v35_{name}.webp","WEBP",quality=96,method=6)
        if (output_folder/f"iman_v35_{name}.webp").stat().st_size<2400:
            raise ValueError("v35 matte output unexpectedly small: "+name)
