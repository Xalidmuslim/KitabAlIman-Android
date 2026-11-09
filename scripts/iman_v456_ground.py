"""v0.45.6: fine matte Persian ornament with no broad brown ground patch.

Builds only a transparent additive layer: the approved scroll remains untouched.
Resolution/aspect ratio match the real 174:103 dp Image view with ContentScale.Fit.
"""
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import math

SOURCE_W, SOURCE_H, SCALE = 440, 145, 4
CANVAS_W, CANVAS_H = 684, 496
OUTPUT_W = 842
INK = (129, 95, 62)


def _smooth(t):
    u=np.clip(t,0.0,1.0)
    return u*u*(3-2*u)


def _inverse_perspective(src, dst):
    m=[]; b=[]
    for (x,y),(u,v) in zip(src,dst):
        m.extend([[x,y,1,0,0,0,-x*u,-y*u],
                  [0,0,0,x,y,1,-x*v,-y*v]])
        b.extend([u,v])
    c=np.linalg.solve(np.array(m,float),np.array(b,float))
    h=np.array([[c[0],c[1],c[2]],[c[3],c[4],c[5]],[c[6],c[7],1.]])
    inv=np.linalg.inv(h)
    inv/=inv[2,2]
    return (inv[0,0],inv[0,1],inv[0,2],
            inv[1,0],inv[1,1],inv[1,2],inv[2,0],inv[2,1])


def make_ground():
    f=SCALE
    w,h=CANVAS_W,CANVAS_H
    sw,sh=SOURCE_W,SOURCE_H
    image=Image.new("RGBA",(sw*f,sh*f),(0,0,0,0))
    draw=ImageDraw.Draw(image)

    def points(seq):
        return [(round(x*f),round(y*f)) for x,y in seq]
    def stroke(seq, alpha=90, thick=2):
        draw.line(points(seq),fill=INK+(alpha,),
                  width=max(1,round(thick*f)),joint="curve")
    def polygon(seq,alpha=80,thick=2):
        stroke(seq+[seq[0]],alpha,thick)

    # Open-ended parallel bands; no opaque tile, border or card.
    for margin,alpha,thick in ((5,126,3.4),(12,94,2.4),(23,72,1.7)):
        stroke([(4+margin,8+margin),(sw-10-margin,8+margin)],alpha,thick)
        stroke([(4+margin,sh-11-margin),(sw-10-margin,sh-11-margin)],alpha,thick)

    # Fewer large ornamental medallions: remain legible at 103dp image height.
    # The earlier 55 tiny rosettes collapsed into speckled texture on Android.
    for row,cy in enumerate((39,106)):
        for col in range(5):
            cx=52+col*84+(row%2)*15
            if cx>410:
                continue
            star=[]
            for k in range(17):
                angle=math.pi*k/8
                radius=30 if k%2==0 else 18
                star.append((cx+math.cos(angle)*radius,
                             cy+math.sin(angle)*radius*.66))
            stroke(star,130,2.6)
            for radius,alpha,line in ((17,108,2.0),(7,87,1.7)):
                polygon([(cx,cy-radius*.73),(cx+radius,cy),
                         (cx,cy+radius*.73),(cx-radius,cy)],alpha,line)
    # Two long woven bands, with wide gaps between distinctive rosettes.
    for margin,alpha in ((3,123),(9,80)):
        stroke([(15,15+margin),(sw-15,15+margin)],alpha,2.6)
        stroke([(15,sh-15-margin),(sw-15,sh-15-margin)],alpha,2.5)
    for cx in (92,176,260,344):
        for cy in (65,80):
            stroke([(cx-25,cy),(cx,cy-9),(cx+25,cy)],78,2.2)
            stroke([(cx-25,cy),(cx,cy+9),(cx+25,cy)],64,2.0)

    source=[(0,0),(sw*f,0),(sw*f,sh*f),(0,sh*f)]
    quad=[(50,370),(460,301),(673,410),(168,471)]
    motif=image.transform(
        (w,h),Image.Transform.PERSPECTIVE,
        _inverse_perspective(source,quad),
        resample=Image.Resampling.BICUBIC,
        fillcolor=(0,0,0,0))
    rgba=np.asarray(motif).copy()
    yy,xx=np.mgrid[:h,:w]
    margin_x=np.minimum(xx,w-1-xx)
    margin_y=np.minimum(yy,h-1-yy)
    fade=_smooth(margin_x/68.0)*_smooth(margin_y/38.0)
    rgba[...,3]=np.uint8(np.clip(rgba[...,3].astype(float)*fade*.97,0,255))
    motif=Image.fromarray(rgba,"RGBA")

    # A small diffused contact shadow. No wide opaque oval is permitted.
    shade_mask=Image.new("L",(w,h),0)
    ImageDraw.Draw(shade_mask).ellipse((330,385,645,446),fill=40)
    shade_mask=shade_mask.filter(ImageFilter.GaussianBlur(30))
    alpha=np.asarray(shade_mask).astype(float)*fade
    shadow=Image.new("RGBA",(w,h),INK+(0,))
    shadow.putalpha(Image.fromarray(np.uint8(alpha),"L"))
    ground=Image.alpha_composite(motif,shadow)
    # Match the Image view's actual 174:103 aspect ratio to avoid invisible
    # horizontal Fit padding and keep the motif under the approved scroll.
    # Smooth only subpixel ornament aliasing at Android size; preserve the
    # dominant medallion strokes, contrast and transparent image edges.
    return ground.resize((OUTPUT_W,h),Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(1.2))


def verify_ground(image):
    if image.size!=(OUTPUT_W,CANVAS_H) or image.mode!="RGBA":
        raise RuntimeError("v456 rug geometry wrong")
    a=np.asarray(image.getchannel("A"))
    if any(int(v.max())>0 for v in (a[0],a[-1],a[:,0],a[:,-1])):
        raise RuntimeError("v456 rectangular boundary is visible")
    if np.count_nonzero(a[325:470,20:270]>75)<1800:
        raise RuntimeError("v456 left ornament too faint")
    if float(a[335:470,260:585].mean())>46:
        raise RuntimeError("v456 artificial opaque shadow blob")
    if np.count_nonzero(a[:190,:180])>0:
        raise RuntimeError("v456 ornament would overlap quote above it")
    return True
