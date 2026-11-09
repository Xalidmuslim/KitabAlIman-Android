"""Color-match the approved manuscript illustration to the four library relief icons.

Runs at build time: does not redraw the shape, change the screenshot, or alter the
original source artwork. Alpha/transparency and the existing soft shadow survive.
Target palette comes from *real* v35 library icon pixels, not arbitrary sepia.
"""
from pathlib import Path
from PIL import Image
import numpy as np

LIBRARY = (
    "iman_v35_contents.webp",
    "iman_v35_collections.webp",
    "iman_v35_glossary.webp",
    "iman_v35_bookmarks.webp",
)
LUMINANCE = np.array([0.299, 0.587, 0.114], dtype=np.float32)


def _chroma_stats(image: Image.Image):
    rgba = np.asarray(image.convert("RGBA"), dtype=np.float32)
    pixels = rgba[..., :3]
    original_alpha = rgba[..., 3].astype(np.uint8)
    light = np.tensordot(pixels, LUMINANCE, axes=([2], [0]))
    # Exclude the empty background, tiny shadow wisps, and almost-white pixels.
    mask = (original_alpha > 90) & (light > 38) & (light < 245)
    if mask.sum() < 40:
        raise RuntimeError("v452 expected opaque relief icon pixels")
    chroma = pixels - light[..., None]
    return pixels, original_alpha, light, chroma, mask


def build_matte_artwork(original: Path, reference_folder: Path, output: Path):
    if not original.is_file():
        raise RuntimeError("v452 approved original parchment source missing")
    refs = []
    for name in LIBRARY:
        path = reference_folder / name
        if not path.is_file():
            raise RuntimeError("v452 missing approved library style reference: " + name)
        with Image.open(path) as image:
            _, _, _, ch, mask = _chroma_stats(image)
            refs.append(np.mean(ch[mask], axis=0))
    reference_chroma = np.mean(refs, axis=0)

    with Image.open(original) as base:
        source = base.convert("RGBA")
    pixels, original_alpha, light, chroma, mask = _chroma_stats(source)
    source_chroma = np.mean(chroma[mask], axis=0)
    before_distance = float(np.linalg.norm(source_chroma - reference_chroma))

    # Match mean chromatic tone to library and soften overly saturated variation.
    source_intensity = float(np.mean(np.linalg.norm(chroma[mask], axis=1)))
    target_intensity = float(np.mean(np.linalg.norm(np.stack(refs), axis=1)))
    chroma_scale = float(np.clip(target_intensity / max(source_intensity, 0.01), 0.56, 0.78))
    adjusted_chroma = (chroma - source_chroma) * chroma_scale + reference_chroma

    # Slightly compressed highlight and shadow range: matte rather than lacquer.
    matte_light = (light - 128.0) * 0.94 + 128.0
    graded = np.clip(matte_light[..., None] + adjusted_chroma, 0, 255).astype(np.uint8)
    combined = np.dstack((graded, original_alpha))
    rendered = Image.fromarray(combined, mode="RGBA")

    output.parent.mkdir(parents=True, exist_ok=True)
    rendered.save(output, "WEBP", quality=92, method=6, exact=True)

    # Regression: geometry, boundaries and alpha survive the palette conversion.
    with Image.open(output) as saved:
        if saved.size != source.size or saved.mode != "RGBA":
            raise RuntimeError("v452 corrupted artwork dimensions/transparency")
        out_pixels, out_alpha, _, out_chroma, out_mask = _chroma_stats(saved)
        after_distance = float(np.linalg.norm(np.mean(out_chroma[out_mask], axis=0) - reference_chroma))
        if not np.array_equal(out_alpha, original_alpha):
            # WebP alpha may differ by a least-significant bit due to encoding.
            if np.max(np.abs(out_alpha.astype(int) - original_alpha.astype(int))) > 1:
                raise RuntimeError("v452 altered the approved illustration alpha")
        if after_distance > before_distance + 0.6:
            raise RuntimeError("v452 palette became further from the library assets")
        if float(np.std(out_pixels[out_mask])) < float(np.std(pixels[mask])) * 0.68:
            raise RuntimeError("v452 artwork lost too much image definition")
    print("PASS v452 matte palette: original/reference/after color distance",
          round(before_distance, 2), round(after_distance, 2), "chroma scale", round(chroma_scale, 2))
    return output
