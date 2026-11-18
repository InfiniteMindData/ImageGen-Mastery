"""Published Standard USD rates for the bounded loop. See references/provider-contracts.md."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING

PRICING_VERSION = "standard-usd-2026-11-18"
REVIEW_OUTPUT_LIMIT = 2048
IMAGE_DEFAULTS = {"google": "gemini-3.1-flash-image"}
VISION_DEFAULTS = {"openai": "gpt-5.4-mini-2026-03-17", "google": "gemini-3.1-flash-lite"}
CREDENTIALS = {"google": "GEMINI_API_KEY", "openai": "OPENAI_API_KEY"}


@dataclass(frozen=True)
class PriceProfile:
    provider: str
    model: str
    input_limit: int
    output_limit: int
    input_usd_per_million: str
    output_usd_per_million: str

    @property
    def reserve(self) -> Decimal:
        cost = (self.input_limit * Decimal(self.input_usd_per_million)
                + self.output_limit * Decimal(self.output_usd_per_million)) / 1_000_000
        return cost.quantize(Decimal("0.01"), rounding=ROUND_CEILING)


IMAGE_PROFILES = {(p.provider, p.model): p for p in (
    PriceProfile("google", IMAGE_DEFAULTS["google"], 131072, 32768, "0.50", "60"),
    PriceProfile("google", "gemini-3.1-flash-lite-image", 65536, 4096, "0.25", "30"),
)}

VISION_PROFILES = {(p.provider, p.model): p for p in (
    PriceProfile("openai", VISION_DEFAULTS["openai"], 272000, REVIEW_OUTPUT_LIMIT, "0.75", "4.50"),
    PriceProfile("openai", "gpt-5.4-nano-2026-03-17", 400000, REVIEW_OUTPUT_LIMIT, "0.20", "1.25"),
    # Include the whole Gemini output window as a conservative allowance for thinking.
    PriceProfile("google", VISION_DEFAULTS["google"], 1048576, 65536, "0.25", "1.50"),
)}


def get_profile(operation: str, provider: str, model: str | None) -> PriceProfile:
    if operation == "image":
        defaults, registry = IMAGE_DEFAULTS, IMAGE_PROFILES
    elif operation == "vision":
        defaults, registry = VISION_DEFAULTS, VISION_PROFILES
    else:
        raise ValueError(f"Unknown price profile operation: {operation}.")
    if model is None:
        model = defaults.get(provider)
    profile = registry.get((provider, model))
    if profile is None:
        if operation == "image" and provider == "openai":
            raise ValueError("The bounded loop has no verified maximum cost for OpenAI image requests. "
                             "Use a registered Google image model, or authorize a single OpenAI edit "
                             "with 'edit --provider openai --model MODEL --authorize-paid'.")
        raise ValueError(f"No verified {operation} price profile for {provider}/{model}.")
    return profile
