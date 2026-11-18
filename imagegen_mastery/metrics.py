"""Bounded offline metrics on visible pixels; all scores describe alignment or appearance."""

import math

from PIL import Image, ImageChops, ImageStat

LIMITATIONS = {
    "comparison_size": "Metrics use the candidate crop reduced to a maximum side of 256. "
                       "The reference is stretched to that frame. Changes in pose, crop or aspect ratio affect all scores.",
    "rgb_mae": "Mean absolute difference across RGB channels divided by 255. Fine details can vanish in sampling. "
               "Pixel difference does not establish semantic quality.",
    "ssim": "Area-weighted SSIM over nonoverlapping 8×8 luminance blocks (partial blocks at edges). "
            "Population moments, L=255, K1=.01, K2=.03. One means identical sampled luminance. "
            "Color, meaning and feature identity can differ. Other SSIM implementations can give different values.",
    "dhash_distance": "Differing horizontal brightness comparisons in a 9×8 grayscale thumbnail, from 0 to 64. "
                      "Similar shapes can collide and small shifts can change the hash.",
    "ocr": "Tesseract English OCR, automatic page segmentation. Checks are exact case-sensitive substrings, "
           "including internal whitespace. Recognition can miss stylized, small or multiline lettering or misread it.",
    "change_map": "RGB absolute channel differences on the comparison grid, shown without amplification. "
                  "Black represents equal sampled pixels. It cannot identify why a change occurred.",
}


def crop_bounds(image: Image.Image, bounds: list[float]) -> Image.Image:
    return image.crop((math.floor(bounds[0] * image.width), math.floor(bounds[1] * image.height),
                       math.ceil(bounds[2] * image.width), math.ceil(bounds[3] * image.height)))


def _block_ssim(candidate: Image.Image, reference: Image.Image) -> float:
    a, b = candidate.convert("L"), reference.convert("L")
    c1, c2 = (255 * .01) ** 2, (255 * .03) ** 2
    total = 0.0
    for y in range(0, a.height, 8):
        for x in range(0, a.width, 8):
            box = (x, y, min(x+8, a.width), min(y+8, a.height))
            first, second = a.crop(box).tobytes(), b.crop(box).tobytes()
            count = len(first)
            ma, mb = sum(first)/count, sum(second)/count
            va = sum((p-ma)**2 for p in first)/count
            vb = sum((p-mb)**2 for p in second)/count
            cov = sum((p-ma)*(q-mb) for p, q in zip(first, second))/count
            total += count * (2*ma*mb + c1)*(2*cov + c2) / ((ma*ma + mb*mb + c1)*(va+vb+c2))
    return total / (a.width*a.height)


def _dhash(image: Image.Image) -> list[bool]:
    data = image.convert("L").resize((9, 8), Image.Resampling.LANCZOS).tobytes()
    return [data[y*9+x] > data[y*9+x+1] for y in range(8) for x in range(8)]


def measure_pair(candidate: Image.Image, reference: Image.Image, *, ssim: bool,
                 perceptual: bool) -> tuple[dict, Image.Image]:
    sample = candidate.copy()
    sample.thumbnail((256, 256), Image.Resampling.LANCZOS)
    baseline = reference.resize(sample.size, Image.Resampling.LANCZOS)
    diff = ImageChops.difference(sample, baseline)
    metrics = {"comparison_size": list(sample.size),
               "rgb_mae": sum(ImageStat.Stat(diff).mean) / (3*255)}
    if ssim:
        metrics["ssim"] = _block_ssim(sample, baseline)
    if perceptual:
        metrics["dhash_distance"] = sum(a != b for a, b in zip(_dhash(sample), _dhash(baseline)))
    return metrics, diff

