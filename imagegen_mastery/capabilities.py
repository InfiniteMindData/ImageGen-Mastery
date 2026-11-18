"""Documented subset of model capabilities exposed by this CLI."""

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ImageSettings:
    source: Path | None = None
    references: tuple[Path, ...] = ()
    mask: Path | None = None
    aspect_ratio: str | None = None
    size: str | None = None
    quality: str | None = None


@dataclass(frozen=True)
class Capability:
    input_limit: int  # Local limit, including the edit source
    mask: bool
    ratios: tuple[str, ...]
    sizes: tuple[str, ...]
    qualities: tuple[str, ...]
    documentation: str


OPENAI_SIZES = {"1:1": "1024x1024", "3:2": "1536x1024", "2:3": "1024x1536"}
GOOGLE_RATIOS = ("1:1", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9")
GOOGLE_DOC = "https://ai.google.dev/gemini-api/docs/image-generation"
OPENAI = Capability(4, True, tuple(OPENAI_SIZES), (*OPENAI_SIZES.values(), "auto"),
                    ("low", "medium", "high", "auto"), "https://developers.openai.com/api/reference/resources/images/methods/edit")
REGISTRY = {
    ("openai", "gpt-image-2.5-flare"): OPENAI,
    ("openai", "gpt-image-2.5-sunburst"): OPENAI,
    ("google", "gemini-3.1-flash-image"): Capability(4, False, GOOGLE_RATIOS, ("1K", "2K", "4K"), (), GOOGLE_DOC),
    ("google", "gemini-3.1-flash-lite-image"): Capability(1, False, GOOGLE_RATIOS, (), (), GOOGLE_DOC),
}


def capabilities() -> list[dict]:
    return [{"provider": provider, "model": model, **asdict(caps)} for (provider, model), caps in REGISTRY.items()]


def validate(provider: str, model: str, settings: ImageSettings) -> None:
    caps = REGISTRY.get((provider, model))
    if caps is None:
        raise ValueError(f"No advanced capabilities registered for {provider}/{model}. See capabilities.")
    if len(settings.references) + int(settings.source is not None) > caps.input_limit:
        raise ValueError(f"This adapter accepts at most {caps.input_limit} input images for {model}.")
    if settings.mask is not None and (not caps.mask or settings.source is None):
        raise ValueError("A mask requires an edit source and a model with native mask support.")
    for name, value, allowed in (("aspect ratio", settings.aspect_ratio, caps.ratios),
                                 ("size", settings.size, caps.sizes), ("quality", settings.quality, caps.qualities)):
        if value is not None and value not in allowed:
            raise ValueError(f"Unsupported {name} for {model}: {value}. Supported: {', '.join(allowed) or 'none'}.")
    if provider == "openai" and settings.aspect_ratio and settings.size not in (None, OPENAI_SIZES[settings.aspect_ratio]):
        raise ValueError("The specified aspect ratio and output size conflict.")

