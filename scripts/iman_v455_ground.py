"""Fourfold rasterized, transparent oriental ornament for the approved scroll.

The ornament is etched into parchment: no opaque tile, frame or rectangular
background. The original approved scroll and its edges stay in a distinct
foreground layer. Shadow and border fade to zero at every image boundary.
"""
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import math

BASE_W, BASE_H, SCALE = 171, 124, 4
PIGMENT = (126, 91, 54)


def _smooth(t):
    a = np.clip(t, 0, 1)
    return a * a * (3 - 2 * a)


def _inverse_homography(source, destination):
    matrix, rhs = [], []
    for (sx, sy), (dx, dy) in zip(source, destination):
        matrix.append([sx, sy, 1, 0, 0, 0, -sx * dx, -sy * dx])
        rhs.append(dx)
        matrix.append([0, 0, 0, sx, sy, 1, -sx * dy, -sy * dy])
        rhs.append(dy)
    c = np.linalg.solve(np.asarray(matrix, float), np.asarray(rhs, float))
    forward = np.array([[c[0], c[1], c[2]],
                        [c[3], c[4], c[5]],
                        [c[6], c[7], 1]])
    inverse = np.linalg.inv(forward)
    inverse /= inverse[2, 2]
    return (inverse[0, 0], inverse[0, 1], inverse[0, 2],
            inverse[1, 0], inverse[1, 1], inverse[1, 2],
            inverse[2, 0], inverse[2, 1])


def make_ground():
    f = SCALE
    w, h = BASE_W * f, BASE_H * f
    sw, sh = 440, 140
    image = Image.new("RGBA", (sw * f, sh * f), (0, 0, 0, 0))
    painter = ImageDraw.Draw(image)

    def point(x, y):
        return (round(x * f), round(y * f))

    def line(vertices, alpha=88, stroke=1.5):
        painter.line([point(x, y) for x, y in vertices],
                     fill=PIGMENT + (alpha,),
                     width=max(1, round(stroke * f)), joint="curve")

    for margin, alpha, stroke in ((5, 77, 1.6),
                                  (11, 52, 1.2),
                                  (18, 38, 1.0)):
        line([(margin, margin), (sw - margin, margin),
              (sw - margin, sh - margin),
              (margin, sh - margin), (margin, margin)], alpha, stroke)

    for row, cy in enumerate((37, 71, 105)):
        for cx in (30, 83, 136, 189, 242, 295, 348, 401):
            cx += (row % 2) * 19
            if cx > 425:
                continue
            outline = []
            for k in range(17):
                angle = math.pi * k / 8
                rad = 19 if k % 2 == 0 else 9.5
                outline.append((cx + math.cos(angle) * rad,
                                cy + math.sin(angle) * rad * .83))
            line(outline, 87, 1.65)
            line([(cx, cy - 7), (cx + 8, cy),
                  (cx, cy + 7), (cx - 8, cy), (cx, cy - 7)], 69, 1.2)
            for dx, dy in ((-4, 0), (4, 0), (0, -3), (0, 3)):
                r = 1.6
                painter.ellipse(
                    (point(cx + dx - r, cy + dy - r),
                     point(cx + dx + r, cy + dy + r)),
                    fill=PIGMENT + (61,),
                )

    for y in (21, 54, 89, 124):
        line([(x, y + 3 * math.sin(2 * math.pi * x / 54))
              for x in range(0, sw + 1, 3)], 49, 1.15)

    src = [(0, 0), (sw * f, 0), (sw * f, sh * f), (0, sh * f)]
    quad = [(2 * f, 95 * f), (113 * f, 74 * f),
            (169 * f, 109 * f), (51 * f, 123 * f)]
    rug = image.transform(
        (w, h), Image.Transform.PERSPECTIVE,
        _inverse_homography(src, quad),
        Image.Resampling.BICUBIC, fillcolor=(0, 0, 0, 0),
    )

    pixels = np.asarray(rug).copy()
    yy, xx = np.mgrid[:h, :w]
    edge_x = np.minimum(xx, w - 1 - xx)
    edge_y = np.minimum(yy, h - 1 - yy)
    fade = _smooth(edge_x / (12 * f)) * _smooth(edge_y / (9 * f))
    fade *= _smooth(xx / (24 * f)) * _smooth((w - 1 - xx) / (13 * f))
    pixels[..., 3] = np.uint8(
        np.clip(pixels[..., 3].astype(float) * fade * .78, 0, 255)
    )
    rug = Image.fromarray(pixels, "RGBA")

    contact_mask = Image.new("L", (w, h), 0)
    for box, alpha, blur in (
        ((54, 94, 168, 117), 73, 7.2),
        ((76, 100, 154, 113), 77, 3.4),
    ):
        oval = Image.new("L", (w, h), 0)
        ImageDraw.Draw(oval).ellipse(tuple(round(t * f) for t in box),
                                     fill=alpha)
        oval = oval.filter(ImageFilter.GaussianBlur(blur * f))
        contact_mask = Image.fromarray(
            np.maximum(np.asarray(contact_mask), np.asarray(oval)).astype(np.uint8),
            "L",
        )
    shadow_alpha = np.asarray(contact_mask).astype(float)
    shadow_alpha *= _smooth(edge_x / (10 * f)) * _smooth(edge_y / (10 * f))
    shadow = Image.new("RGBA", (w, h), (98, 71, 46, 0))
    shadow.putalpha(
        Image.fromarray(np.uint8(np.clip(shadow_alpha, 0, 255)), "L")
    )
    return Image.alpha_composite(rug, shadow)


def verify_ground(ground):
    if ground.size != (684, 496) or ground.mode != "RGBA":
        raise RuntimeError("Wrong relief asset dimensions or format")
    a = np.asarray(ground.getchannel("A"))
    for border in (a[0], a[-1], a[:, 0], a[:, -1]):
        if int(np.max(border)) != 0:
            raise RuntimeError("Rectangular edge would be visible in the UI")
    if int(np.max(a[360:475, 40:180])) < 8:
        raise RuntimeError("Ornament is not visible below/left of the scroll")
    if int(np.max(a[360:475, 300:620])) < 15:
        raise RuntimeError("Contact shadow disappeared")
    if int(np.max(a[:180, :180])) != 0:
        raise RuntimeError("Ornament would bleed into quote text")
    return True
