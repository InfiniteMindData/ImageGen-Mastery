# Provider contracts and spending limits

The registry is a conservative list of combinations implemented here. Account access and provider availability can vary. Checked against provider documentation on 2026-11-18. Unit tests simulate HTTP responses.

| Adapter | Inputs and output controls exposed by this toolkit | Contract |
| --- | --- | --- |
| OpenAI GPT Image 2.5 Flare and Sunburst | Up to four source/reference PNGs total. JSON Images edits with ordered `images[].image_url` and optional `mask.image_url` on the first image. The adapter sends base64 data URLs. The mask must have alpha, at least one fully transparent pixel, and the same displayed dimensions as the source. The CLI exposes square, portrait and landscape sizes, plus auto, and low/medium/high/auto quality. | [Edit endpoint](https://developers.openai.com/api/reference/resources/images/methods/edit) · [Image generation guide](https://developers.openai.com/api/docs/guides/image-generation) |
| Gemini 3.1 Flash Image | Up to four input images total. Text and inline PNG parts in `generateContent`, with `generationConfig.imageConfig` for aspect ratio and 1K/2K/4K resolution. | [Gemini image generation](https://ai.google.dev/gemini-api/docs/image-generation) · [Model limits](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image) |
| Gemini 3.1 Flash Lite Image | One input image and explicit aspect ratio. This adapter exposes the default output resolution. Both Gemini adapters reject native masks and quality flags. | [Lite model](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-image) |
| OpenAI vision | GPT-5.4 mini snapshot, Chat Completions JSON mode, image URL parts containing actual PNG pixels. Responses require a completed, non-refused message and local schema validation. | [Model card](https://developers.openai.com/api/docs/models/gpt-5.4-mini) · [Chat Completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create) |

The toolkit re-encodes oriented inputs and removes metadata. It enforces an aggregate inline input cap of 16 MiB and a mask cap under 4 MB. `capabilities` lists the exact options. A provider can reinterpret a mask. The revision loop separately copies pixels outside the evidenced rectangle from the previous version.

## Revision budget

The automated loop uses only Gemini 3.1 Flash Image for rendering and the GPT-5.4 mini snapshot for inspection. Neither request enables paid tools. The budget uses conservative reservations at published standard USD API rates, per run, before each call. No network operation retries automatically.

| Operation | Basis | Reserved USD |
| --- | --- | --- |
| Generate or edit one candidate | 131,072 input tokens at $0.50/M plus 32,768 output tokens at the highest applicable rate of $60/M. Rounded up. | 2.04 |
| Inspect a candidate | 272,000 input tokens at $0.75/M plus the requested limit of 2,048 output tokens at $4.50/M. Standard service tier, global endpoint. Rounded up. | 0.22 |

A generated candidate and its inspection require $2.26 of remaining authorization. Beginning with an existing image requires $0.22 for its first inspection. A new revision requires enough room for both the edit and its inspection. A reservation remains consumed after an ambiguous failure. The manifest records reserved amounts. The provider dashboard supplies actual charges. These bounds assume the published standard rates in this profile, exclude taxes and other account activity, and require updating when rates or limits change. Each invocation must use a new directory, so the CLI cannot silently replay an interrupted run. Inspect its manifest before authorizing another.

[Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.1-flash-image) · [Gemini token limits](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image) · [OpenAI model limits and pricing](https://developers.openai.com/api/docs/models/gpt-5.4-mini)
