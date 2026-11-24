"""Offline, evidence-based candidate selection and delivery checks."""

from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageChops, ImageDraw, ImageOps, ImageStat

from .evaluation import MAX_PIXELS, MAX_SIDE, load_image
from .metrics import measure_pair


@dataclass(frozen=True)
class DeliveryPolicy:
    expected_size: tuple[int, int] | None = None
    require_transparency: bool = False
    max_reference_mae: float | None = None
    max_tile_seam: float | None = None

    def validate(self, reference: Path | None) -> None:
        if self.expected_size is not None:
            size = self.expected_size
            if (len(size) != 2 or any(type(n) is not int or not 1 <= n <= MAX_SIDE for n in size)
                    or size[0] * size[1] > MAX_PIXELS):
                raise ValueError("Expected dimensions exceed supported image bounds.")
        for value in (self.max_reference_mae, self.max_tile_seam):
            if value is not None and (type(value) not in (int, float) or not 0 <= value <= 1):
                raise ValueError("Thresholds must be finite numbers between zero and one.")
        if self.max_reference_mae is not None and reference is None:
            raise ValueError("A reference threshold requires a reference image.")


def _on_background(image: Image.Image, color: str) -> Image.Image:
    background = Image.new("RGB", image.size, color)
    background.paste(image, mask=image.getchannel("A"))
    return background


def _mae(a: Image.Image, b: Image.Image) -> float:
    return sum(ImageStat.Stat(ImageChops.difference(a, b)).mean) / (3 * 255)


def _seams(image: Image.Image) -> dict:
    width, height = image.size
    scores = {"left_right": 0.0, "top_bottom": 0.0}
    # Two backgrounds expose alpha discontinuities without comparing invisible RGB.
    for color in ("black", "white"):
        rgb = _on_background(image, color)
        scores["left_right"] = max(scores["left_right"], _mae(
            rgb.crop((0, 0, 1, height)), rgb.crop((width-1, 0, width, height))))
        scores["top_bottom"] = max(scores["top_bottom"], _mae(
            rgb.crop((0, 0, width, 1)), rgb.crop((0, height-1, width, height))))
    return scores


def _preview(image: Image.Image, background: str, size: int = 224) -> Image.Image:
    thumb = image.copy()
    thumb.thumbnail((size, size), Image.Resampling.LANCZOS)
    tile = Image.new("RGB", (size, size), background)
    tile.paste(thumb, ((size-thumb.width)//2, (size-thumb.height)//2), thumb.getchannel("A"))
    return tile


def audit_candidates(candidates, directory: Path, *, reference: Path | None = None,
                     policy: DeliveryPolicy = DeliveryPolicy(), tile: bool = False) -> dict:
    """Write a bounded contact sheet and JSON. No network or source modifications."""
    candidates = tuple(Path(p) for p in candidates)
    directory = Path(directory)
    if not 1 <= len(candidates) <= 32:
        raise ValueError("Supply one through 32 candidate images.")
    if directory.exists():
        raise FileExistsError(f"Choose a new audit directory: {directory}")
    policy.validate(reference)
    baseline_info = baseline = None
    if reference is not None:
        baseline_info, baseline = load_image(Path(reference))
        baseline = baseline.convert("RGBA")
    rows = []
    # One row per candidate, two contrasting backgrounds. Bounded previews only.
    sheet = Image.new("RGB", (480, 254 * len(candidates)), "#e5e7eb")
    draw = ImageDraw.Draw(sheet)
    with TemporaryDirectory(dir=directory.parent) as stage:
        tmp = Path(stage)
        for index, path in enumerate(candidates, 1):
            info, image = load_image(path)
            rgba = image.convert("RGBA")
            histogram = rgba.getchannel("A").histogram()
            pixels = rgba.width * rgba.height
            alpha = {"transparent_fraction": histogram[0]/pixels,
                     "partial_fraction": sum(histogram[1:255])/pixels,
                     "opaque_fraction": histogram[255]/pixels}
            checks = {}
            if policy.expected_size is not None:
                checks["expected_size"] = rgba.size == policy.expected_size
            if policy.require_transparency:
                checks["visible_and_transparent"] = histogram[255] + sum(histogram[1:255]) > 0 and histogram[255] < pixels
            row = {"index": index, "image": info, "alpha": alpha, "checks": checks}
            if baseline is not None:
                same_aspect = rgba.width * baseline.height == rgba.height * baseline.width
                # Never silently stretch incompatible aspect ratios for ranking.
                comparison = {"aspect_ratio_match": same_aspect}
                if same_aspect:
                    white, _ = measure_pair(_on_background(rgba, "white"),
                                            _on_background(baseline, "white"), ssim=True, perceptual=True)
                    black, _ = measure_pair(_on_background(rgba, "black"),
                                            _on_background(baseline, "black"), ssim=False, perceptual=False)
                    comparison.update(white)
                    comparison["dual_background_mae"] = max(white["rgb_mae"], black["rgb_mae"])
                row["reference"] = comparison
                if policy.max_reference_mae is not None:
                    checks["reference_mae"] = same_aspect and comparison["dual_background_mae"] <= policy.max_reference_mae
            if tile or policy.max_tile_seam is not None:
                seams = _seams(rgba)
                row["tile_seams"] = seams
                if policy.max_tile_seam is not None:
                    checks["tile_seam"] = max(seams.values()) <= policy.max_tile_seam
                thumb = rgba.copy()
                thumb.thumbnail((256, 256), Image.Resampling.LANCZOS)
                repeat = Image.new("RGB", (3*thumb.width, 3*thumb.height), "#808080")
                for y in range(3):
                    for x in range(3):
                        repeat.paste(thumb, (x*thumb.width, y*thumb.height), thumb.getchannel("A"))
                filename = f"tile-{index:02d}.png"
                repeat.save(tmp / filename)
                row["tile_preview"] = filename
            row["status"] = "passed" if checks and all(checks.values()) else "failed" if checks else "unassessed"
            rows.append(row)
            top = (index-1)*254
            draw.text((8, top+5), f"Candidate {index:02d} | {rgba.width} x {rgba.height} | {row['status']}", fill="black")
            sheet.paste(_preview(rgba, "white"), (8, top+24))
            sheet.paste(_preview(rgba, "#202020"), (248, top+24))
        if baseline is not None:
            comparable = [row for row in rows if row["reference"]["aspect_ratio_match"] and row["status"] != "failed"]
            ranked = sorted(comparable, key=lambda row: (row["reference"]["dual_background_mae"], row["index"]))
        else:
            ranked = []
        report = {"schema_version": 1, "reference": baseline_info, "candidates": rows,
                  "reference_similarity_order": [row["index"] for row in ranked],
                  "visual_review": "unassessed",
                  "limitations": [
                      "Passed means only the explicitly requested delivery checks passed; it is not visual approval.",
                      "Reference metrics compare aligned sampled pixels, not identity, aesthetics or semantic quality.",
                      "Dual-background MAE is the larger black/white composite error; SSIM and dHash use white.",
                      "Opposite-edge MAE is a seam heuristic; inspect repeats at native scale and in the target engine.",
                      "Transparency requires at least one nonopaque and one nontransparent pixel; it does not verify cutout quality.",
                      "Contact sheet and tile previews are reduced to bounded sizes; inspect originals for fine detail."
                  ]}
        sheet.save(tmp / "contact-sheet.png")
        (tmp / "audit.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n", encoding="utf-8")
        directory.mkdir(mode=0o700, exist_ok=False)
        for file in tmp.iterdir():
            file.replace(directory / file.name)
    return report
