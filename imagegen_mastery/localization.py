"""Composite a provider edit inside a normalized display-oriented rectangle."""

import math
from collections.abc import Sequence
from pathlib import Path

from PIL import Image, ImageChops, ImageMath

from .evaluation import load_image

Box = tuple[int, int, int, int]


def _validate_bounds(bounds: Sequence[float]) -> None:
    if (not isinstance(bounds, Sequence) or isinstance(bounds, (str, bytes)) or len(bounds) != 4
            or any(type(x) not in (float, int) or not 0 <= x <= 1 for x in bounds)
            or bounds[0] >= bounds[2] or bounds[1] >= bounds[3]):
        raise ValueError("Bounds must be ordered normalized [left, top, right, bottom] coordinates.")


def pixel_box(size: tuple[int, int], bounds: Sequence[float]) -> Box:
    """Return the half-open pixel rectangle covering the supplied normalized bounds."""
    _validate_bounds(bounds)
    w, h = size
    return math.floor(bounds[0]*w), math.floor(bounds[1]*h), math.ceil(bounds[2]*w), math.ceil(bounds[3]*h)


def validate_localization(feather: int, protected: Sequence[Sequence[float]],
                          max_boundary_jump: float | None) -> None:
    if type(feather) is not int or feather < 0:
        raise ValueError("Feather must be a nonnegative integer pixel width.")
    if not isinstance(protected, Sequence) or isinstance(protected, (str, bytes)):
        raise ValueError("Protected regions must be a sequence of normalized rectangles.")
    for bounds in protected:
        _validate_bounds(bounds)
    if max_boundary_jump is not None and (type(max_boundary_jump) not in (int, float)
                                          or not 0 <= max_boundary_jump <= 1):
        raise ValueError("The maximum boundary jump must be between 0 and 1.")


def _mask(box: Box, size: tuple[int, int], holes: list[Box], feather: int) -> Image.Image:
    x0, y0, x1, y1 = box
    w, h = x1-x0, y1-y0
    if not feather:
        mask = Image.new("L", (w, h), 255)
        for left, top, right, bottom in holes:
            mask.paste(0, (left-x0, top-y0, right-x0, bottom-y0))
        return mask

    def ramp(distances, horizontal, shape):
        values = bytes(min(255, (255*d + (feather+1)//2)//(feather+1)) for d in distances)
        line = Image.frombytes("L", (len(values), 1) if horizontal else (1, len(values)), values)
        return line.resize(shape, Image.Resampling.NEAREST)

    def inside(lo, hi, limit):
        return (min(i-lo+1 if lo else feather+1, hi-i if hi < limit else feather+1) for i in range(lo, hi))

    mask = ImageChops.darker(ramp(inside(x0, x1, size[0]), True, (w, h)),
                             ramp(inside(y0, y1, size[1]), False, (w, h)))
    for left, top, right, bottom in holes:
        a, b = max(x0, left-feather), max(y0, top-feather)
        c, d = min(x1, right+feather), min(y1, bottom+feather)
        if a >= c or b >= d:
            continue
        shape = c-a, d-b
        across = ramp((max(left-x, 0, x-right+1) for x in range(a, c)), True, shape)
        down = ramp((max(top-y, 0, y-bottom+1) for y in range(b, d)), False, shape)
        subbox = a-x0, b-y0, c-x0, d-y0
        mask.paste(ImageChops.darker(mask.crop(subbox), ImageChops.lighter(across, down)), subbox)
    return mask


def _blend(base: Image.Image, patch: Image.Image, mask: Image.Image) -> Image.Image:
    result = Image.composite(patch, base, mask)
    partial = mask.point([0] + [255]*254 + [0])
    region = partial.getbbox()
    if region is None or (base.getchannel("A").getextrema()[0] == patch.getchannel("A").getextrema()[0] == 255):
        return result

    # Interpolate premultiplied channels before dividing by the blended alpha.
    # Use full integer precision, including for nearly transparent input pixels.
    left, top, right, bottom = region
    rows = max(1, 262144 // (right-left))
    for y in range(top, bottom, rows):
        box = left, y, right, min(bottom, y+rows)
        weight = mask.crop(box)
        start, end = base.crop(box), patch.crop(box)
        wa = ImageMath.lambda_eval(lambda e: (255-e["m"])*e["a"], m=weight, a=start.getchannel("A"))
        wb = ImageMath.lambda_eval(lambda e: e["m"]*e["a"], m=weight, a=end.getchannel("A"))
        total = ImageMath.lambda_eval(lambda e: e["a"]+e["b"], a=wa, b=wb)
        channels = []
        for channel in "RGB":
            mixed = ImageMath.lambda_eval(
                lambda e: (e["u"]*e["a"] + e["v"]*e["b"] + e["t"]/2) / e["max"](e["t"], 1),
                u=start.getchannel(channel), v=end.getchannel(channel), a=wa, b=wb, t=total,
            ).convert("L")
            channels.append(mixed)
        channels.append(result.crop(box).getchannel("A"))
        covered = ImageChops.lighter(start.getchannel("A"), end.getchannel("A")).point([0] + [255]*255)
        result.paste(Image.merge("RGBA", channels), box, ImageChops.darker(partial.crop(box), covered))
    return result


def _edges(box: Box, size: tuple[int, int]):
    l, t, r, b = box
    w, h = size
    for x in (l, r):
        if 0 < x < w:
            yield (x-1, t, x, b), (x, t, x+1, b)
    for y in (t, b):
        if 0 < y < h:
            yield (l, y-1, r, y), (l, y, r, y+1)


def _jump_exceeds(base, canvas, boxes, threshold):
    # Compare adjacent pixels over both black and white to include alpha. Existing
    # source edges can remain. Only an increase in contrast counts as a new seam.
    for box in boxes:
        for a, b in _edges(box, base.size):
            for matte in ("black", "white"):
                contrasts = []
                for image in (base, canvas):
                    pair = []
                    for strip in (a, b):
                        pixels = image.crop(strip)
                        flat = Image.new("RGB", pixels.size, matte)
                        flat.paste(pixels, mask=pixels.getchannel("A"))
                        pair.append(flat)
                    contrasts.append(ImageChops.difference(*pair))
                increase = ImageChops.subtract(contrasts[1], contrasts[0])
                if max(peak for _, peak in increase.getextrema()) / 255 > threshold:
                    return True
    return False


def localize(source: Path, proposed: Path, bounds: Sequence[float], target: Path, *,
             feather: int = 0, protected: Sequence[Sequence[float]] = (),
             max_boundary_jump: float | None = None) -> str:
    """Save a candidate and return changed, unchanged_region, or boundary_discontinuity.

    A dimension_mismatch produces no candidate. Feather is measured inward from
    transitions to preserved pixels. max_boundary_jump limits the largest increase
    in an adjacent channel contrast across those transitions, on a 0–1 scale.
    """
    validate_localization(feather, protected, max_boundary_jump)
    _, base = load_image(Path(source))
    _, patch = load_image(Path(proposed))
    if base.size != patch.size:
        return "dimension_mismatch"
    box = pixel_box(base.size, bounds)
    holes = [pixel_box(base.size, region) for region in protected]
    canvas = base.convert("RGBA")
    before = canvas.crop(box)
    after = _blend(before, patch.crop(box).convert("RGBA"), _mask(box, base.size, holes, feather))
    canvas.paste(after, box)
    canvas.save(target, format="PNG")
    # Premultiplication ignores hidden RGB and includes coverage changes.
    delta = ImageChops.difference(before.convert("RGBa"), after.convert("RGBa"))
    if not delta.getbbox(alpha_only=False):
        return "unchanged_region"
    if max_boundary_jump is not None and _jump_exceeds(base.convert("RGBA"), canvas, [box, *holes], max_boundary_jump):
        return "boundary_discontinuity"
    return "changed"
