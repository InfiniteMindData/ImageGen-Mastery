"""Image generation through the OpenAI Images and Google Gemini REST APIs.

API contracts:
https://platform.openai.com/docs/api-reference/images/create
https://ai.google.dev/gemini-api/docs/image-generation
https://github.com/googleapis/python-genai#with-text-content-input-image-output
"""

import base64
import binascii
import io
import json
import os
import re
import struct
from http.client import HTTPException
from urllib import request
from urllib.error import HTTPError

from PIL import Image, ImageOps

from .evaluation import MAX_FILE_BYTES, MAX_PIXELS, MAX_SIDE


class ProviderError(RuntimeError):
    """An image generation request could not produce a usable PNG."""


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Credentials are scoped to the original HTTPS endpoint.
        return None


_MAX_RESPONSE_BYTES = 48 * 1024 * 1024


def _credential(variable: str) -> str:
    key = os.getenv(variable, "").strip()
    if not key or not key.isascii() or not key.isprintable():
        raise ProviderError(f"Set {variable} to a valid API key.")
    return key


def _post(url: str, headers: dict, payload: dict) -> dict:
    req = request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with request.build_opener(_NoRedirect()).open(req, timeout=300) as response:
            body = response.read(_MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        exc.close()
        raise ProviderError(f"The image provider returned HTTP {exc.code}.") from None
    except (OSError, HTTPException):
        raise ProviderError("The image provider connection failed.") from None

    if len(body) > _MAX_RESPONSE_BYTES:
        raise ProviderError("The image provider response exceeded the size limit.")
    try:
        return json.loads(body)
    except (ValueError, RecursionError):
        raise ProviderError("The image provider returned invalid JSON.") from None


def _openai(model: str, prompt: str) -> bytes:
    result = _post(
        "https://api.openai.com/v1/images/generations",
        {"Authorization": "Bearer " + _credential("OPENAI_API_KEY")},
        {"model": model, "prompt": prompt, "n": 1, "output_format": "png"},
    )
    return _as_png(result["data"][0]["b64_json"], ["PNG"])


def _google(model: str, prompt: str) -> bytes:
    result = _post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        {"x-goog-api-key": _credential("GEMINI_API_KEY")},
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["IMAGE"]},
        },
    )
    return _google_image(result)


def _google_image(result: dict) -> bytes:
    for part in result["candidates"][0]["content"]["parts"]:
        if isinstance(part, dict) and not part.get("thought") and "inlineData" in part:
            return _as_png(part["inlineData"]["data"], ["PNG", "JPEG", "WEBP"])
    raise ProviderError("The image provider returned no image.")


def _as_png(encoded: str, formats: list[str]) -> bytes:
    try:
        data = base64.b64decode(encoded, validate=True)
        with Image.open(io.BytesIO(data), formats=formats) as image:
            if image.width * image.height > MAX_PIXELS or max(image.size) > MAX_SIDE:
                raise ProviderError("The generated image exceeds the supported dimensions.")
            if getattr(image, "is_animated", False):
                raise ProviderError("The image provider returned an animation.")
            image.verify()
        # verify() checks PNG chunk integrity. Loading separately also checks the pixels.
        with Image.open(io.BytesIO(data), formats=formats) as image:
            image.load()
            if image.format == "PNG":
                return data
            with io.BytesIO() as output:
                oriented = ImageOps.exif_transpose(image)
                mode = "RGBA" if oriented.has_transparency_data else "RGB"
                oriented.convert(mode).save(output, format="PNG")
                if output.tell() > MAX_FILE_BYTES:
                    raise ProviderError("The generated PNG exceeds the supported file size.")
                return output.getvalue()
    except (ValueError, TypeError, binascii.Error, OSError, EOFError,
            SyntaxError, struct.error, Image.DecompressionBombError):
        raise ProviderError("The image provider returned invalid image data.") from None


def generate(provider: str, model: str, prompt: str) -> bytes:
    """Generate one still PNG with a GPT Image or Gemini image model."""
    adapters = {"openai": _openai, "google": _google}
    if provider not in adapters:
        raise ProviderError("Choose an image provider from openai or google.")
    if not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", model):
        raise ProviderError("Provide a valid model identifier.")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ProviderError("Provide a nonempty image prompt.")
    try:
        return adapters[provider](model, prompt)
    except (IndexError, KeyError, TypeError):
        raise ProviderError("The image provider returned no image.") from None
