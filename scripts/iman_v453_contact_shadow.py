"""Add a soft contact shadow below the approved matte parchment artwork.

Object colors and opacity remain unchanged. Extra transparent bottom padding
avoids clipping the diffuse shadow; the Compose view grows only vertically so
the visible scroll remains the already approved 20%-reduced size.
"""
from PIL import Image, ImageDraw, ImageFilter
import numpy as np


def add_contact_shadow(original: Image.Image) -> Image.Image:
    """Preserve object pixels, adding two blurred shadow layers underneath."""
    art = original.convert("RGBA")
    width, height = art.size
    extra_bottom = max(10, round(height * 0.12))
    size = (width, height + extra_bottom)
    alpha = np.asarray(art.getchannel("A"), dtype=np.uint8)
    y, x = np.nonzero(alpha >= 110)
    if len(x) < 32:
        raise ValueError("Opaque parchment outline not found")
    top, bottom = int(y.min()), int(y.max())
    span = max(1, bottom - top)
    foot = (y >= top + span * 0.52) & (y <= bottom - span * 0.08)
    foot_x = x[foot] if foot.any() else x
    left, right = int(foot_x.min()), int(foot_x.max())
    cx = (left + right) / 2.0
    foot_width = max(8, right - left + 1)
    cy = bottom + extra_bottom * 0.23

    def oval_shadow(rgb, opacity, half_width, half_height, radius):
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((round(cx - half_width), round(cy - half_height),
                      round(cx + half_width), round(cy + half_height)), fill=opacity)
        mask = mask.filter(ImageFilter.GaussianBlur(radius))
        shade = Image.new("RGBA", size, rgb + (0,))
        shade.putalpha(mask)
        return shade

    ambient = oval_shadow((110, 82, 58), 56, foot_width * 0.59,
                          extra_bottom * 0.74, max(2, width * 0.038))
    contact = oval_shadow((86, 62, 43), 89, foot_width * 0.44,
                          extra_bottom * 0.46, max(1.5, width * 0.022))
    shadow = Image.alpha_composite(ambient, contact)
    foreground = Image.new("RGBA", size, (0, 0, 0, 0))
    foreground.alpha_composite(art, (0, 0))
    return Image.alpha_composite(shadow, foreground)
