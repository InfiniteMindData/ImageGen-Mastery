"""Rebuild the original comparison fixtures beside this script using Pillow."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main() -> None:
    directory = Path(__file__).parent / "fixtures"
    directory.mkdir(exist_ok=True)
    for name, color in (("reference", "#18877f"), ("candidate", "#c15b40")):
        image = Image.new("RGB", (640, 240), "#fff5d8")
        draw = ImageDraw.Draw(image)
        draw.rectangle((54, 82, 124, 152), fill=color)
        draw.text((170, 120), "OPEN", font=ImageFont.load_default(size=92), fill="#15314b", anchor="lm")
        image.save(directory / f"{name}.png")
    mask = Image.new("RGBA", (640, 240), "white")
    ImageDraw.Draw(mask).rectangle((54, 82, 124, 152), fill=(0, 0, 0, 0))
    mask.save(directory / "mask.png")


if __name__ == "__main__":
    main()
