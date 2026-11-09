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

    # Interlocked eight-point rosettes and small inlaid rhombi.
    for row,cy in enumerate((26,53,80,107,132)):
        for col in range(11):
            cx=9+col*43+(row%2)*20
            if not (16<cx<420):
                continue
            star=[]
            for k in range(17):
                a=math.pi*k/8
                radius=16 if k%2==0 else 8.5
                star.append((cx+math.cos(a)*radius,
                             cy+math.sin(a)*radius*.71))
            stroke(star,112,2.25)
            for radius,alpha,line in ((8.4,88,1.8),(3.6,75,1.35)):
                polygon([(cx,cy-radius*.73),(cx+radius,cy),
                         (cx,cy+radius*.73),(cx-radius,cy)],alpha,line)
    # Thread-thin diagonal lattice between medallions.
    for row in range(1,5):
        y=row*27+11
        stroke([(12,y),(sw-12,y)],52,1.3)
        for cx in range(12,sw-12,43):
            stroke([(cx,y-11),(cx+20,y+11)],56,1.3)

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
    return ground.resize((OUTPUT_W,h),Image.Resampling.LANCZOS)


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
