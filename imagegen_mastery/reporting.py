"""Static, offline comparison bundles with optional local text recognition."""

import io
import json
import subprocess
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Sequence

from PIL import Image, ImageOps

from .evaluation import load_image, visible
from .inspection import valid_bounds
from .metrics import LIMITATIONS, crop_bounds, measure_pair


def recognize(image: Image.Image) -> str:
    with io.BytesIO() as stream:
        image.save(stream, format="PNG")
        try:
            result = subprocess.run(["tesseract", "stdin", "stdout", "-l", "eng", "--psm", "3"],
                                    input=stream.getvalue(), capture_output=True, timeout=30, check=True)
        except FileNotFoundError:
            raise ValueError("OCR requires the local tesseract executable and its English language data.") from None
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            raise ValueError("Tesseract failed or timed out. Check the English language installation.") from None
    return result.stdout.decode("utf-8").rstrip("\r\n")


def _html(report: dict) -> str:
    def h(value: object) -> str:
        return escape(str(value))
    rows = []
    for name, metrics in [("Full frame", report["frame"]), *((str(r["bounds"]), r) for r in report["regions"])]:
        cells = [h(name)]
        for key in ("rgb_mae", "ssim", "dhash_distance"):
            value = metrics.get(key)
            cells.append("—" if value is None else h(f"{value:.5g}"))
        rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")
    notes = "".join(f"<li>{h(value)}</li>" for value in report["limitations"].values())
    data = h(json.dumps(report, ensure_ascii=False, indent=2))
    return f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Image comparison</title>
<style>body{{font:1rem/1.55 system-ui;max-width:65rem;margin:auto;padding:1rem;color:#182431}}
img{{display:block;max-width:100%;height:auto}}figure{{margin:1.5rem 0}}td,th{{text-align:left;padding:.4rem .8rem}}
table{{border-collapse:collapse}}tr{{border-bottom:1px solid #ccc}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}</style>
<h1>Image comparison</h1><figure><img src="preview.png" alt="Reference at left, candidate at right">
<figcaption>Reference (left) · Candidate (right)</figcaption></figure>
<table><thead><tr><th>Region</th><th>RGB difference</th><th>Block SSIM</th><th>dHash distance</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<figure><img src="changes.png" alt="Absolute RGB change map"><figcaption>Absolute RGB difference</figcaption></figure>
<h2>Interpretation</h2><ul>{notes}</ul><details><summary>Measurements, OCR and input provenance</summary>
<pre>{data}</pre></details></html>"""


def make_report(candidate: Path, reference: Path, directory: Path, *, ssim: bool = False, perceptual: bool = False,
                regions: Sequence[list[float]] = (), required_text: Sequence[str] = ()) -> dict:
    if directory.exists():
        raise FileExistsError(f"Choose a new report directory: {directory}")
    if not all(valid_bounds(r) for r in regions):
        raise ValueError("Regions must be nonempty normalized left, top, right, bottom rectangles.")
    if any(not text.strip() for text in required_text):
        raise ValueError("Required OCR text cannot be blank.")
    candidate_info, source = load_image(candidate)
    reference_info, original = load_image(reference)
    source, original = visible(source), visible(original)
    keys = ["comparison_size", "rgb_mae", "change_map"]
    if ssim:
        keys.append("ssim")
    if perceptual:
        keys.append("dhash_distance")
    if required_text:
        keys.append("ocr")
    report = {"candidate": candidate_info, "reference": reference_info, "visual_inspection": "unassessed",
              "aspect_ratio_match": source.width * original.height == source.height * original.width,
              "regions": [], "limitations": {key: LIMITATIONS[key] for key in keys}}
    with TemporaryDirectory(dir=directory.parent) as stage:
        tmp = Path(stage)
        for bounds in (None, *regions):
            a = crop_bounds(source, bounds) if bounds else source
            b = crop_bounds(original, bounds) if bounds else original
            metrics, change = measure_pair(a, b, ssim=ssim, perceptual=perceptual)
            if required_text:
                text = recognize(a)
                metrics["ocr"] = {"recognized": text, "checks": [
                    {"required": term, "found": term in text} for term in required_text]}
            if bounds is None:
                report["frame"] = metrics
                change.save(tmp / "changes.png")
            else:
                report["regions"].append({"bounds": bounds, **metrics})
        preview = Image.new("RGB", (1024, 512), "#ebedf0")
        for index, img in enumerate((original, source)):
            tile = ImageOps.contain(img, (512, 512), Image.Resampling.LANCZOS)
            preview.paste(tile, (index * 512 + (512-tile.width)//2, (512-tile.height)//2))
        preview.save(tmp / "preview.png")
        (tmp / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
        (tmp / "report.html").write_text(_html(report), encoding="utf-8")
        directory.mkdir(mode=0o700)
        for filename in ("changes.png", "preview.png", "report.json", "report.html"):
            (tmp / filename).replace(directory / filename)
    return report

