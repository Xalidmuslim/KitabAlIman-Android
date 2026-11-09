"""Bounded matte contact shadow; no cropped rectangular edges (v0.45.4).

Use the previously approved v0.45.2 matte drawing as foreground.
The shadow fades to zero BEFORE all bitmap boundaries. No Compose overlays,
shape changes, extra background cards or per-frame image effects.
"""
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import numpy as np


def _smoothstep(value):
    p = np.clip(value, 0.0, 1.0)
    return p * p * (3.0 - 2.0 * p)


def add_contact_shadow(original: Image.Image) -> Image.Image:
    art = original.convert("RGBA")
    width, height = art.size
    bottom_pad = max(10, round(height * 0.12))
    canvas_size = (width, height + bottom_pad)
    source_alpha = np.asarray(art.getchannel("A"), dtype=np.uint8)
    y, x = np.nonzero(source_alpha >= 180)
    if len(x) < 32:
        raise ValueError("v454 requires an approved opaque scroll illustration")

    lo, hi = int(y.min()), int(y.max())
    span = max(1, hi - lo)
    foot = (y >= lo + 0.82 * span) & (y <= hi - 2)
    foot_x = x[foot] if np.any(foot) else x
    cx = float((int(foot_x.min()) + int(foot_x.max())) / 2.0)
    cx = max(width * 0.37, min(width * 0.63, cx))
    cy = min(hi + 1.5, height + 1)

    alpha_mask = Image.new("L", canvas_size, 0)
    # Two soft ellipses: ambient warmth and shallow contact relief.
    for half_width, half_height, radius, strength in (
        (min(width * 0.35, 44), max(3.5, bottom_pad * 0.40), max(2.5, width * 0.042), 62),
        (min(width * 0.26, 33), max(2.8, bottom_pad * 0.28), max(1.9, width * 0.026), 72),
    ):
        layer = Image.new("L", canvas_size, 0)
        ImageDraw.Draw(layer).ellipse(
            (round(cx - half_width), round(cy - half_height),
             round(cx + half_width), round(cy + half_height)), fill=strength
        )
        layer = layer.filter(ImageFilter.GaussianBlur(radius))
        alpha_mask = ImageChops.lighter(alpha_mask, layer)

    yy, xx = np.ogrid[:canvas_size[1], :canvas_size[0]]
    edge_x = np.minimum(xx, width - 1 - xx).astype(np.float32)
    edge_y = np.minimum(yy, canvas_size[1] - 1 - yy).astype(np.float32)
    # Critical regression fix: fade the blur BEFORE it touches bitmap edges.
    # Without this, Android shows a straight rectangular shadow boundary.
    fade = _smoothstep(edge_x / max(6.0, width * 0.10)) * _smoothstep(
        edge_y / max(9.0, bottom_pad * 1.15)
    )
    alpha_mask = Image.fromarray(
        np.rint(np.asarray(alpha_mask, dtype=np.float32) * fade).astype(np.uint8),
        mode="L",
    )
    shadow = Image.new("RGBA", canvas_size, (108, 82, 61, 0))
    shadow.putalpha(alpha_mask)
    foreground = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    foreground.alpha_composite(art, (0, 0))
    return Image.alpha_composite(shadow, foreground)


def assert_shadow_boundaries(original: Image.Image, rendered: Image.Image) -> None:
    before = original.convert("RGBA")
    after = rendered.convert("RGBA")
    w, h = before.size
    if after.size != (w, h + max(10, round(h * 0.12))):
        raise RuntimeError("v454 must not resize the 20%-reduced scroll silhouette")

    alpha_before = np.asarray(before.getchannel("A"))
    alpha_after = np.asarray(after.getchannel("A"))
    if int(alpha_after[-1].max()) != 0:
        raise RuntimeError("v454 clipped-shadow regression: visible horizontal bitmap edge")
    if int(alpha_after[:, 0].max()) > int(alpha_before[:, 0].max()) + 1:
        raise RuntimeError("v454 clipped-shadow regression: visible left bitmap edge")
    if int(alpha_after[:, -1].max()) > int(alpha_before[:, -1].max()) + 1:
        raise RuntimeError("v454 clipped-shadow regression: visible right bitmap edge")

    rgb_before = np.asarray(before)
    rgb_after = np.asarray(after)[:h, :w]
    opaque = rgb_before[..., 3] == 255
    if np.any(opaque) and not np.array_equal(rgb_before[opaque], rgb_after[opaque]):
        raise RuntimeError("v454 changed approved opaque colors or artwork details")
    if int(alpha_after[h:min(after.height, h + 4), w // 2].max()) < 5:
        raise RuntimeError("v454 removed the contact shadow instead of feathering it")
