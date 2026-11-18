"""Local measurements and a manual review rubric for generated still images."""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

from PIL import Image, ImageChops, ImageOps, ImageStat, UnidentifiedImageError


MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_PIXELS = 16_777_216
MAX_SIDE = 16_384
SAMPLE_SIDE = 256
COMPARISON_SIZE = (64, 64)
FORMATS = ("JPEG", "PNG", "WEBP", "GIF", "BMP", "PPM")


def _measure(path: Path) -> tuple[dict, Image.Image]:
    """Decode one bounded file and measure its visible, EXIF-oriented pixels."""
    try:
        if not path.is_file():
            raise ValueError(f"Expected a regular image file at {path}")
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError(f"{path} exceeds the {MAX_FILE_BYTES} byte limit")
        with path.open("rb") as stream:
            data = stream.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            raise ValueError(f"{path} exceeds the {MAX_FILE_BYTES} byte limit")
        with Image.open(io.BytesIO(data), formats=FORMATS) as source:
            if source.width * source.height > MAX_PIXELS or max(source.size) > MAX_SIDE:
                raise ValueError(
                    f"{path} exceeds the {MAX_PIXELS} pixel or {MAX_SIDE} pixel side limit"
                )
            if getattr(source, "is_animated", False):
                raise ValueError(f"{path} is animated. Supply a still image.")
            oriented = ImageOps.exif_transpose(source)
            width, height = oriented.size
            rgba = oriented.convert("RGBA")
            rgba.thumbnail((SAMPLE_SIDE, SAMPLE_SIDE), Image.Resampling.LANCZOS)
            sample = Image.new("RGB", rgba.size, "white")
            sample.paste(rgba, mask=rgba.getchannel("A"))
            image_format = source.format
    except UnidentifiedImageError as exc:
        raise ValueError(f"Unrecognized image at {path}. Supported formats include {', '.join(FORMATS)}.") from exc
    except Image.DecompressionBombError as exc:
        raise ValueError(f"{path} exceeds the pixel limit") from exc
    except (OSError, SyntaxError) as exc:
        raise ValueError(f"Cannot read image at {path}. {exc}") from exc

    rgb = ImageStat.Stat(sample)
    luma = ImageStat.Stat(sample.convert("L"))
    return {
        "path": str(path),
        "sha256": hashlib.sha256(data).hexdigest(),
        "format": image_format,
        "width": width,
        "height": height,
        "sample_size": list(sample.size),
        "mean_rgb": [round(value, 3) for value in rgb.mean],
        "luma_stddev": round(luma.stddev[0], 3),
    }, sample


def _normalized_rgb_difference(difference: Image.Image) -> float:
    return sum(ImageStat.Stat(difference).mean) / (3 * 255)


def _most_changed_regions(difference: Image.Image) -> list[dict]:
    """Rank nonzero cells of a 4×4 grid by score, retaining reading order for ties."""
    regions = []
    for row in range(4):
        for column in range(4):
            bounds = [column / 4, row / 4, (column + 1) / 4, (row + 1) / 4]
            pixel_box = (
                column * difference.width // 4, row * difference.height // 4,
                (column + 1) * difference.width // 4, (row + 1) * difference.height // 4,
            )
            score = _normalized_rgb_difference(difference.crop(pixel_box))
            if score > 0:
                regions.append({"bounds": bounds, "normalized_mean_absolute_rgb_difference": score})
    regions.sort(key=lambda cell: cell["normalized_mean_absolute_rgb_difference"], reverse=True)
    return regions[:3]


def evaluate(image: Path, reference: Path | None = None) -> dict:
    """Measure a still image and optionally compare it to a reference.

    Each file is limited to 64 MiB, 16,777,216 pixels and 16,384 pixels per
    side. Animated files are rejected. RGB and luma statistics use an
    EXIF-oriented thumbnail on white, with a maximum side of 256 pixels.
    All channel statistics use Pillow's encoded 0–255 values. Reference
    comparisons rank the three most changed nonzero cells of a 4×4 grid on
    the shared 64×64 frame. Region bounds use normalized display coordinates.
    """
    measured, sample = _measure(Path(image))
    comparison = None
    if reference is not None:
        baseline, reference_sample = _measure(Path(reference))
        target = sample.resize(COMPARISON_SIZE, Image.Resampling.LANCZOS)
        original = reference_sample.resize(COMPARISON_SIZE, Image.Resampling.LANCZOS)
        difference = ImageChops.difference(target, original)
        comparison = {
            "reference": baseline,
            "aspect_ratio_match": measured["width"] * baseline["height"]
            == measured["height"] * baseline["width"],
            "normalized_mean_absolute_rgb_difference": _normalized_rgb_difference(difference),
            "most_changed_regions": _most_changed_regions(difference),
            "method": (
                "Each thumbnail is resized to 64 by 64 across its full frame. "
                "The mean absolute RGB channel difference is divided by 255. "
                "Zero indicates equal sampled pixels. Changes in crop or position affect the result. "
                "Up to three nonzero cells from a 4 by 4 grid are listed by decreasing mean "
                "difference. Ties follow reading order, left to right within rows, starting at the top. "
                "Bounds are [left, top, right, bottom] fractions of the displayed frame."
            ),
        }

    checks = {
        "anatomy": "Inspect visible limbs, joints, digits and contact points. Record the location of each issue or mark inapplicable.",
        "artifacts": "Inspect edges, textures, lettering and repeated details at native resolution. Record the affected regions.",
        "composition": "Check the focal point, crop, negative space and placement against the intended composition.",
        "consistency": (
            "Compare identities, clothing, materials and recurring details with the reference. Record specific differences."
            if comparison else
            "Supply a reference or another image in the series to review identity and recurring details."
        ),
    }
    return {
        "image": measured,
        "measurement_method": (
            "Statistics use a thumbnail with up to 256 pixels per side, EXIF display orientation "
            "and a white background under transparent pixels. Mean RGB and luma standard deviation use the 0–255 scale."
        ),
        "comparison": comparison,
        "rubric": {
            name: {"status": "unassessed", "evidence": [], "inspect": instructions}
            for name, instructions in checks.items()
        },
    }
