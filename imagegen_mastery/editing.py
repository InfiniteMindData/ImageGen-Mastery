"""Provider-specific generation and editing with actual reference images."""

import base64
import io
from pathlib import Path

from .capabilities import OPENAI_SIZES, ImageSettings, validate
from .evaluation import load_image
from .inspection import require_authorization
from .providers import ProviderError, _as_png, _credential, _google_image, _post

# Local cap on all encoded inputs leaves room for JSON in an inline request.
MAX_INLINE = 16 * 1024 * 1024


def _encode(path: Path, *, mask_size: tuple[int, int] | None = None) -> tuple[str, tuple[int, int]]:
    info, image = load_image(path)
    if mask_size is not None:
        if (info["format"] != "PNG" or image.size != mask_size or not image.has_transparency_data
                or image.convert("RGBA").getchannel("A").getextrema()[0] != 0):
            raise ValueError("The mask must be a matching-size PNG with fully transparent edit pixels.")
    image = image.convert("RGBA" if image.has_transparency_data else "RGB")
    image.info.clear()
    with io.BytesIO() as stream:
        image.save(stream, format="PNG")
        if stream.tell() > (MAX_INLINE * 3 // 4) or (mask_size is not None and stream.tell() >= 4_000_000):
            raise ValueError("Encoded input exceeds the adapter upload limit.")
        return base64.b64encode(stream.getvalue()).decode("ascii"), image.size


def render(provider: str, model: str, prompt: str, settings: ImageSettings, *, authorized: bool = False) -> bytes:
    require_authorization(authorized)
    validate(provider, model, settings)
    if not prompt.strip() or len(prompt.encode("utf-8")) > 32000:
        raise ValueError("The advanced adapter requires a nonempty prompt of at most 32000 UTF-8 bytes.")
    paths = ([settings.source] if settings.source else []) + list(settings.references)
    encoded = []
    total = len(prompt.encode("utf-8"))
    source_size = None
    for path in paths:
        data, size = _encode(path)
        total += len(data)
        if total > MAX_INLINE:
            raise ValueError("Combined image inputs exceed the adapter upload limit.")
        encoded.append(data)
        if source_size is None:
            source_size = size

    try:
        if provider == "openai":
            payload = {"model": model, "prompt": prompt, "n": 1, "output_format": "png"}
            size = settings.size or OPENAI_SIZES.get(settings.aspect_ratio)
            if size:
                payload["size"] = size
            if settings.quality:
                payload["quality"] = settings.quality
            if encoded:
                payload["images"] = [{"image_url": "data:image/png;base64," + data} for data in encoded]
            if settings.mask:
                mask, _ = _encode(settings.mask, mask_size=source_size)
                if total + len(mask) > MAX_INLINE:
                    raise ValueError("Combined image inputs exceed the adapter upload limit.")
                payload["mask"] = {"image_url": "data:image/png;base64," + mask}
            operation = "edits" if encoded else "generations"
            result = _post("https://api.openai.com/v1/images/" + operation,
                           {"Authorization": "Bearer " + _credential("OPENAI_API_KEY")}, payload)
            return _as_png(result["data"][0]["b64_json"], ["PNG"])

        parts = [{"text": prompt}]
        parts.extend({"inlineData": {"mimeType": "image/png", "data": data}} for data in encoded)
        config = {"responseModalities": ["IMAGE"]}
        image_config = {key: value for key, value in (("aspectRatio", settings.aspect_ratio),
                        ("imageSize", settings.size)) if value}
        if image_config:
            config["imageConfig"] = image_config
        result = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                       {"x-goog-api-key": _credential("GEMINI_API_KEY")},
                       {"contents": [{"parts": parts}], "generationConfig": config})
        return _google_image(result)
    except (IndexError, KeyError, TypeError):
        raise ProviderError("The image provider returned no image.") from None

