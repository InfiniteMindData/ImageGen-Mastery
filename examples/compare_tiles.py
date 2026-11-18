"""Run an offline reference comparison using a controlled tile variation."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw

from imagegen_mastery.evaluation import evaluate


def main():
    with TemporaryDirectory() as directory:
        reference = Path(directory) / "reference.png"
        candidate = Path(directory) / "candidate.png"
        # Both tiles have the same palette, color counts, and dimensions.
        tile = Image.new("RGB", (64, 64), "#444850")
        ImageDraw.Draw(tile).rectangle((8, 8, 23, 23), fill="#ffcc70")
        tile.save(reference)
        tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(candidate)
        report = evaluate(candidate, reference)
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
