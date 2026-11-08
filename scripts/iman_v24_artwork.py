"""Four hand-drawn, original matte book icons for the v24 Library.

No image extraction/cropping: all art is rendered independently from geometric
primitives on a transparent canvas, using the existing Pillow build dependency.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math

S=3
SIZE=(240,180)
CLEAR=(0,0,0,0)
INK=(87,52,32,255)
GOLD=(212,162,95,255)
BROWN=(121,72,43,255)
TOP=(168,111,74,255)
DARK=(91,51,32,255)
PAPER=(243,216,169,255)
PAGE=(255,236,197,255)

class Painter:
    def __init__(self):
        self.image=Image.new("RGBA",tuple(v*S for v in SIZE),CLEAR)
        self.d=ImageDraw.Draw(self.image,"RGBA")
    def cv(self,pts):
        return [(round(x*S),round(y*S)) for x,y in pts]
    def poly(self,pts,fill,outline=None,width=1):
        self.d.polygon(self.cv(pts),fill=fill)
        if outline:self.d.line(self.cv(pts+[pts[0]]),fill=outline,
                               width=round(width*S),joint="curve")
    def ell(self,xy,fill,outline=None,width=1):
        bounds=tuple(round(v*S) for v in xy)
        self.d.ellipse(bounds,fill=fill,outline=outline,
                       width=max(1,round(width*S)))
    def line(self,pts,fill,width=1):
        self.d.line(self.cv(pts),fill=fill,width=max(1,round(width*S)),joint="curve")
    def arc(self,xy,start,end,fill,width=1):
        self.d.arc(tuple(round(v*S) for v in xy),start=start,end=end,
                   fill=fill,width=max(1,round(width*S)))
    def shadow(self,xy):
        layer=Image.new("RGBA",self.image.size,CLEAR)
        ImageDraw.Draw(layer).ellipse(tuple(round(v*S) for v in xy),
                                      fill=(48,26,12,49))
        layer=layer.filter(ImageFilter.GaussianBlur(9*S))
        self.image=Image.alpha_composite(self.image,layer)
        self.d=ImageDraw.Draw(self.image,"RGBA")
    def export(self,path):
        self.image.resize(SIZE,Image.Resampling.LANCZOS).save(
            path,format="WEBP",quality=95,method=6)

def rosette(p,cx,cy,r=15):
    for degrees in range(0,360,45):
        angle=math.radians(degrees)
        x=cx+r*math.cos(angle)
        y=cy+r*.60*math.sin(angle)
        p.line([(cx,cy),(x,y)],(224,179,112,240),1.5)
        p.ell((x-2,y-2,x+2,y+2),(222,179,117,255))
    p.ell((cx-7,cy-5,cx+7,cy+5),None,(217,171,106,245),1.2)
    p.ell((cx-2,cy-2,cx+2,cy+2),GOLD)

def small_book(p,offx=0,offy=0,light=False):
    ox,oy=offx,offy
    def pt(points):return [(x+ox,y+oy) for x,y in points]
    p.poly(pt([(47,68),(169,49),(197,72),(75,95)]),
           (180,126,81,255) if light else TOP,(103,62,38,255),2.2)
    p.poly(pt([(75,95),(197,72),(195,90),(75,113)]),
           PAPER,(123,78,47,255),1.7)
    p.poly(pt([(75,103),(195,81),(195,84),(75,107)]),PAGE)
    for i in (0,3,6):
        p.line(pt([(79,103+i),(189,82+i)]),(205,167,116,170),.5)
    p.poly(pt([(47,68),(75,95),(75,113),(47,86)]),DARK,
           (83,49,31,245),1.8)
    p.poly(pt([(47,68),(169,49),(197,72),(75,95)]),
           (187,141,100,255) if light else TOP,(97,58,36,255),2)
    p.line(pt([(54,71),(76,89),(184,70)]),(220,170,109,255),1.4)
    p.line(pt([(54,83),(68,94),(68,104)]),(197,134,74,255),2)
    p.line(pt([(60,75),(73,84),(179,65)]),(230,181,115,175),.7)
    rosette(p,131+ox,71+oy,9)

def contents():
    p=Painter()
    p.shadow((41,142,205,161))
    small_book(p,-20,35)
    small_book(p,-12,13,True)
    small_book(p,1,-11)
    return p

def collections():
    p=Painter()
    p.shadow((28,130,199,154))
    p.poly([(43,66),(156,45),(185,77),(72,105)],
           (243,211,162,255),(183,131,85,255),1.4)
    for i in range(8):
        p.line([(71,77+i*3),(158,56+i*2.8)],(192,141,89,70),.6)
    p.poly([(72,101),(184,74),(182,107),(67,132)],
           (223,183,131,255),(164,108,66,255),1.6)
    p.ell((43,67,92,132),(206,155,101,255),(143,89,56,255),2.4)
    p.ell((49,74,87,126),(240,204,151,255),(175,121,79,255),1.5)
    p.ell((61,86,81,114),(184,134,89,255),(141,91,58,255),1.2)
    p.ell((65,91,77,108),(237,201,146,255),(159,105,66,255),1)
    p.ell((158,45,189,110),(239,204,153,255),(163,115,69,255),2)
    p.ell((162,50,184,104),(202,150,99,255),(160,103,67,255),1.1)
    p.ell((169,62,179,91),(241,208,158,255),(191,135,87,255),1)
    p.line([(113,55),(124,80),(115,106),(132,127)],(125,68,37,255),4)
    p.line([(117,52),(130,79),(119,105),(135,129)],(213,164,91,255),2)
    p.ell((107,64,139,95),(164,87,51,255),(116,63,38,255),2)
    p.ell((114,69,132,87),(218,145,78,255),(243,194,111,255),1)
    p.line([(133,123),(153,144),(157,139)],(154,88,52,255),2.5)
    p.line([(132,123),(116,145),(108,138)],(211,150,74,255),2.5)
    return p

def glossary():
    p=Painter()
    p.shadow((42,133,210,157))
    p.poly([(29,90),(102,77),(111,114),(45,134)],
           (204,152,104,255),(139,93,61,255),2)
    p.poly([(111,114),(185,86),(206,115),(120,143)],
           (203,152,109,255),(147,100,66,255),2)
    p.poly([(31,76),(100,63),(116,102),(45,122)],
           PAGE,(177,125,84,255),2)
    p.poly([(116,102),(188,68),(210,102),(123,131)],
           (251,224,180,255),(174,124,83,255),2)
    p.poly([(31,76),(101,63),(116,102),(104,111),(46,120)],
           (251,226,181,255),(199,154,108,255),1.2)
    p.line([(114,102),(123,129)],(154,105,65,255),2)
    for i in range(7):
        p.line([(44,83+i*4),(94,74+i*4)],(163,111,76,180),.9)
        p.line([(128,110+i*3),(185,88+i*2.5)],(170,119,81,160),.9)
    p.line([(158,74),(203,134)],(114,70,45,255),9)
    p.line([(160,76),(202,129)],(219,166,100,255),4)
    p.ell((116,43,173,98),(151,88,46,255),(104,61,36,255),2.5)
    p.ell((122,49,167,92),(255,250,219,80),(244,196,121,255),3)
    p.arc((126,51,164,88),215,325,(255,239,188,255),3)
    return p

def bookmarks():
    p=Painter()
    p.shadow((38,140,213,161))
    p.poly([(42,66),(159,40),(199,73),(85,101)],
           DARK,(78,47,29,255),2)
    p.poly([(85,101),(198,74),(198,110),(85,140)],
           PAPER,(115,73,47,255),1.5)
    for i in (3,8,14,20,26):
        p.line([(88,103+i),(193,80+i)],(197,151,100,200),.75)
    p.poly([(42,68),(85,100),(86,140),(44,108)],BROWN,
           (87,52,32,255),2)
    p.poly([(42,66),(159,40),(199,73),(85,101)],TOP,
           (97,58,38,255),2.4)
    p.poly([(147,113),(167,107),(168,161),(156,153),(146,165)],
           (188,120,63,255),(117,72,40,255),1.6)
    p.line([(42,70),(86,103),(194,76)],(230,181,113,255),2)
    p.line([(52,74),(86,96),(186,72)],(232,190,128,255),1.2)
    p.line([(47,88),(81,116),(81,132)],(207,152,96,255),2)
    rosette(p,131,71,17)
    p.poly([(125,53),(142,56),(149,67),(140,86),(121,85),(115,69)],
           None,(220,171,109,255),1.6)
    return p

FACTORY={"contents":contents,"collections":collections,
         "glossary":glossary,"bookmarks":bookmarks}
def install(root:Path):
    root.mkdir(parents=True,exist_ok=True)
    for name,fn in FACTORY.items():
        fn().export(root/f"iman_v24_{name}.webp")
