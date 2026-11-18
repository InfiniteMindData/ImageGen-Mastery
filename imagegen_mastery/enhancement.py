"""Deterministic, local finishing for display-oriented still images."""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from PIL import Image, ImageFilter

from .evaluation import MAX_FILE_BYTES, MAX_PIXELS, MAX_SIDE, load_image


def output_size(size: tuple[int, int], scale: int) -> tuple[int, int]:
    if type(scale) is not int or not 1 <= scale <= 4:
        raise ValueError("Scale must be an integer from 1 to 4.")
    width, height = (side * scale for side in size)
    if min(width, height) < 1 or max(width, height) > MAX_SIDE or width * height > MAX_PIXELS:
        raise ValueError(f"Output exceeds the {MAX_PIXELS} pixel or {MAX_SIDE} pixel side limit.")
    return width, height


def _filter_color(image, operation, footprint):
    if "A" not in image.getbands():
        return image.filter(operation)
    alpha = image.getchannel("A")
    color = image.convert("L" if image.mode == "LA" else "RGB")
    filtered = color.filter(operation)
    if alpha.getextrema()[0] < 255:
        # Keep original color wherever a filter could sample a transparent neighbor.
        opaque = alpha.point([0] * 255 + [255]).filter(ImageFilter.MinFilter(footprint))
        filtered = Image.composite(filtered, color, opaque)
    filtered.putalpha(alpha)
    return filtered


def enhance_image(image: Image.Image, *, scale: int = 1, denoise: bool = False,
                  sharpen: int = 0) -> Image.Image:
    """Finish a Pillow image already in display orientation and return a new image."""
    size = output_size(image.size, scale)
    if type(denoise) is not bool:
        raise ValueError("Denoise must be true or false.")
    if type(sharpen) is not int or not 0 <= sharpen <= 200:
        raise ValueError("Sharpen must be an integer percent from 0 to 200.")
    if image.mode not in {"1", "L", "LA", "P", "PA", "RGB", "RGBA"}:
        raise ValueError(f"Convert {image.mode} to 8-bit grayscale or RGB before enhancement.")

    mode = "L" if image.mode in {"1", "L", "LA"} else "RGB"
    if image.has_transparency_data:
        mode += "A"
    result = image.convert(mode)
    if denoise:
        result = _filter_color(result, ImageFilter.MedianFilter(3), 3)
    if scale != 1:
        # Pillow's RGBA/LA resize interpolates premultiplied color at alpha edges.
        result = result.resize(size, Image.Resampling.LANCZOS)
    if sharpen:
        result = _filter_color(result, ImageFilter.UnsharpMask(radius=1, percent=sharpen, threshold=3), 7)
    result.info.clear()
    if image.info.get("icc_profile"):
        result.info["icc_profile"] = image.info["icc_profile"]
    return result


def enhance_file(source: Path, output: Path, *, scale: int = 1, denoise: bool = False,
                 sharpen: int = 0) -> dict:
    """Apply the selected operations and publish one complete PNG at a new path."""
    source, output = Path(source), Path(output)
    if output.suffix.lower() != ".png":
        raise ValueError("Choose a new .png output path.")
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Output already exists: {output}")
    provenance, original = load_image(source)
    result = enhance_image(original, scale=scale, denoise=denoise, sharpen=sharpen)
    with NamedTemporaryFile(dir=output.parent, delete=False) as stream:
        temporary = Path(stream.name)
    try:
        result.save(temporary, format="PNG")
        if temporary.stat().st_size > MAX_FILE_BYTES:
            raise ValueError(f"Encoded PNG exceeds the {MAX_FILE_BYTES} byte limit.")
        # Linking is atomic and fails if another writer has claimed this name.
        os.link(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    return {
        "source": provenance,
        "output": {"path": str(output), "format": "PNG", "width": result.width, "height": result.height},
        "settings": {"scale": scale, "denoise": denoise, "sharpen": sharpen},
    }
