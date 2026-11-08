"""v0.26: deterministic pre-baked paper grain and natural matte illustrations.

This is an offline asset build, not per-frame Compose graphics effects.
Uses previously generated independent pictures, never UI screenshot crops.
"""
from pathlib import Path
import random
from PIL import Image, ImageChops, ImageFilter, ImageDraw, ImageStat

PARTS=("reminder","library_contents","library_collections",
       "library_glossary","library_bookmarks")

def _layer(size, granularity:int, amplitude:float, seed:int)->Image.Image:
    width,height=size
    sw=max(4,(width+granularity-1)//granularity)
    sh=max(4,(height+granularity-1)//granularity)
    rng=random.Random(seed)
    noise=Image.frombytes("L",(sw,sh),rng.randbytes(sw*sh))
    if (sw,sh)!=(width,height):
        noise=noise.resize(size,Image.Resampling.BICUBIC)
    noise=noise.point(lambda k: min(255,max(0,round(128+(k-127.5)*amplitude/127.5))))
    return Image.merge("RGB",(noise,noise,noise))

def finish_paper(source:Image.Image)->Image.Image:
    """Strengthen paper microtexture without tiling or losing the lower wave."""
    base=source.convert("RGB")
    size=base.size
    # Low, middle and fine frequencies model natural imperfect pulp fibers.
    for spacing,strength,seed in (
        (53,7.5,2608),
        (13,8.5,2609),
        (3,5.4,2610),
        (1,4.6,2611),
    ):
        base=ImageChops.add(base,_layer(size,spacing,strength,seed),offset=-128)
    # Sparse fine fibers, extremely low contrast; not procedural UI decoration.
    w,h=size
    rng=random.Random(2612)
    veil=Image.new("RGBA",size,(0,0,0,0))
    brush=ImageDraw.Draw(veil)
    for _ in range(max(600,(w*h)//850)):
        x=rng.randrange(w)
        y=rng.randrange(h)
        dx=rng.randrange(-2,5)
        dy=rng.randrange(1,5)
        brush.line([(x,y),(x+dx,y+dy)],
                   fill=(141,105,76,rng.randrange(4,13)),width=1)
    base=Image.alpha_composite(base.convert("RGBA"),veil).convert("RGB")
    return base

def finish_illustration(source:Image.Image)->Image.Image:
    """Keep detailed subjects opaque; bake only ambient and contact shadows."""
    src=source.convert("RGBA")
    w,h=src.size
    alpha=src.getchannel("A")
    # A very soft golden diffusion follows the silhouette, not a rectangle.
    soft=alpha.filter(ImageFilter.GaussianBlur(max(7,round(w*0.032))))
    warm=Image.new("RGBA",(w,h),(207,165,118,0))
    warm.putalpha(soft.point(lambda a: round(a*0.11)))
    # Contact shade follows the subject bottom and does not cover text.
    shifted=Image.new("L",(w,h),0)
    shifted.paste(alpha,(0,max(2,round(h*0.012))))
    shade=shifted.filter(ImageFilter.GaussianBlur(max(4,round(w*0.018))))
    shadow=Image.new("RGBA",(w,h),(97,67,43,0))
    shadow.putalpha(shade.point(lambda a: round(a*0.17)))
    canvas=Image.alpha_composite(warm,shadow)

    # Only fade the outer transparent fringe; keep the book/scroll ink sharp.
    fade=max(2,round(min(w,h)*0.047))
    edge=Image.new("L",(w,h),255)
    edge_data=bytearray(w*h)
    for y in range(h):
        v=min(y,h-1-y)
        for x in range(w):
            d=min(x,w-1-x,v)
            t=min(1.0,d/fade)
            edge_data[y*w+x]=round(255*t*t*(3-2*t))
    edge=Image.frombytes("L",(w,h),bytes(edge_data))
    src.putalpha(ImageChops.multiply(alpha,edge))
    canvas=Image.alpha_composite(canvas,src)
    canvas.putpixel((0,0),(0,0,0,0))
    return canvas

def generate_assets(source_dir:Path,dest_dir:Path)->None:
    dest_dir.mkdir(parents=True,exist_ok=True)
    original=Image.open(source_dir/"unified_home.webp")
    paper=finish_paper(original)
    paper.save(dest_dir/"iman_v26_unified_home.webp","WEBP",
               quality=95,method=6)
    for part in PARTS:
        original=Image.open(source_dir/(part+".webp"))
        image=finish_illustration(original)
        name=part if part=="reminder" else part.removeprefix("library_")
        image.save(dest_dir/f"iman_v26_{name}.webp","WEBP",
                   quality=96,method=6)
