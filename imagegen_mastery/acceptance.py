"""Repeatable acceptance checks for a decoded candidate, independent of the inspector."""

from dataclasses import dataclass
from pathlib import Path

from PIL import ImageChops

from .evaluation import MAX_PIXELS, MAX_SIDE, load_image, visible
from .localization import pixel_box, validate_localization
from .reporting import recognize


@dataclass(frozen=True)
class EditPolicy:
    feather: int = 0
    protected: tuple[tuple[float, ...], ...] = ()
    max_boundary_jump: float | None = None
    required_text: tuple[str, ...] = ()
    expected_size: tuple[int, int] | None = None

    def validate(self) -> None:
        validate_localization(self.feather, self.protected, self.max_boundary_jump)
        if any(not isinstance(t, str) or not t.strip() for t in self.required_text):
            raise ValueError("Required OCR text must be nonblank.")
        if self.expected_size is not None:
            if (len(self.expected_size) != 2 or any(type(n) is not int or not 1 <= n <= MAX_SIDE
                                                    for n in self.expected_size)
                    or self.expected_size[0] * self.expected_size[1] > MAX_PIXELS):
                raise ValueError("Expected dimensions exceed the supported image bounds.")


def check_candidate(candidate: Path, policy: EditPolicy, *, baseline: Path, previous: Path | None,
                    bounds: list[float] | None) -> dict:
    info, img = load_image(candidate)
    checks = {"expected_dimensions": policy.expected_size is None or img.size == policy.expected_size}
    data = {"sha256": info["sha256"], "dimensions": list(img.size), "checks": checks}
    if previous is not None:
        _, prior = load_image(previous)
        checks["same_dimensions"] = prior.size == img.size
        if checks["same_dimensions"]:
            if bounds is None:
                raise ValueError("A revised candidate needs edit bounds.")
            delta = ImageChops.difference(img.convert("RGBA"), prior.convert("RGBA"))
            delta.paste((0, 0, 0, 0), pixel_box(img.size, bounds))
            checks["outside_edit_unchanged"] = delta.getbbox(alpha_only=False) is None
        if policy.protected:
            _, original = load_image(baseline)
            source_rgba, candidate_rgba = original.convert("RGBA"), img.convert("RGBA")
            checks["protected_regions_unchanged"] = original.size == img.size and all(
                candidate_rgba.crop(box).tobytes() == source_rgba.crop(box).tobytes()
                for box in (pixel_box(img.size, region) for region in policy.protected))
    if policy.required_text:
        text = recognize(visible(img))
        data["ocr"] = [{"required": term, "found": term in text} for term in policy.required_text]
        checks["required_text"] = all(item["found"] for item in data["ocr"])
    data["passed"] = all(checks.values())
    return data
