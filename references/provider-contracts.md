# Provider contracts and spending limits

The registry is a conservative list of combinations implemented here. Account access and provider availability can vary. Checked against provider documentation on 2026-11-18. Unit tests simulate HTTP responses.

| Adapter | Inputs and output controls exposed by this toolkit | Contract |
| --- | --- | --- |
| OpenAI GPT Image 2.5 Flare and Sunburst | Up to four source/reference PNGs total. JSON Images edits with ordered `images[].image_url` and optional `mask.image_url` on the first image. The adapter sends base64 data URLs. The mask must have alpha, at least one fully transparent pixel, and the same displayed dimensions as the source. The CLI exposes square, portrait and landscape sizes, plus auto, and low/medium/high/auto quality. | [Edit endpoint](https://developers.openai.com/api/reference/resources/images/methods/edit) · [Image generation guide](https://developers.openai.com/api/docs/guides/image-generation) |
| Gemini 3.1 Flash Image | Up to four input images total. Text and inline PNG parts in `generateContent`, with `generationConfig.imageConfig` for aspect ratio and 1K/2K/4K resolution. | [Gemini image generation](https://ai.google.dev/gemini-api/docs/image-generation) · [Model limits](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image) |
| Gemini 3.1 Flash Lite Image | One input image and optional aspect ratio. This adapter exposes the default output resolution. Both Gemini adapters reject native masks and quality flags. | [Lite model](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-image) |
| OpenAI vision | GPT-5.4 mini and nano snapshots, Chat Completions JSON mode, and image URL parts containing PNG pixels. Both inspectors require a completed, non-refused message that passes local schema validation. | [Mini](https://developers.openai.com/api/docs/models/gpt-5.4-mini.md) · [Nano](https://developers.openai.com/api/docs/models/gpt-5.4-nano) · [Chat Completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create) |
| Google vision | Gemini 3.1 Flash-Lite accepts ordered labels and inline PNGs in `generateContent`. The adapter requests JSON, requires a STOP finish, ignores thought parts and validates the same evidence schema. | [Model card](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite) · [GenerateContent](https://ai.google.dev/api/generate-content) |

The toolkit re-encodes oriented inputs and removes metadata. It enforces an aggregate inline input cap of 16 MiB and a mask cap under 4 MB. `capabilities` lists the exact options. A provider can reinterpret a mask. The revision loop separately copies pixels outside the evidenced rectangle from the previous version.

## Revision budget

Choose the editor and reviewer independently using `--image-provider`, `--image-model`, `--vision-provider` and `--vision-model`. A standalone `inspect` accepts `--provider` and `--model`. The default editor is Gemini 3.1 Flash Image and the default inspector is GPT-5.4 mini. Selecting Google for inspection defaults to Gemini 3.1 Flash-Lite. Google-only runs use `GEMINI_API_KEY`. OpenAI inspections use `OPENAI_API_KEY`.

The following table gives the full pre-request reservations. Prices are Standard USD per million tokens, checked on 2026-11-18. The editor reserves its full input and output windows at the highest applicable rates. GPT inspectors reserve the input bound and the requested 2,048 completion tokens, including reasoning. Google inspection also requests 2,048 output tokens and reserves the whole output window to cover thinking. Each request produces at most one candidate and has no enabled paid tools.

| Operation and model | Maximum input × USD/M | Output bound × USD/M | Reservation |
| --- | ---: | ---: | ---: |
| Edit/generate · [gemini-3.1-flash-image](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image) | 131,072 × 0.50 | 32,768 × 60.00 | $2.04 |
| Edit/generate · [gemini-3.1-flash-lite-image](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-image) | 65,536 × 0.25 | 4,096 × 30.00 | $0.14 |
| Inspect · [gpt-5.4-mini-2026-03-17](https://developers.openai.com/api/docs/models/gpt-5.4-mini.md) | 272,000 × 0.75 | 2,048 × 4.50 | $0.22 |
| Inspect · [gpt-5.4-nano-2026-03-17](https://developers.openai.com/api/docs/models/gpt-5.4-nano) | 400,000 × 0.20 | 2,048 × 1.25 | $0.09 |
| Inspect · [gemini-3.1-flash-lite](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite) | 1,048,576 × 0.25 | 65,536 × 1.50 | $0.37 |

The nano profile uses the entire context window as a conservative input bound. Gemini Flash Lite Image accepts one input image in this adapter. When revisions are enabled, that slot is reserved for the edit source. [Gemini Standard pricing](https://ai.google.dev/gemini-api/docs/pricing) · [OpenAI Standard pricing](https://developers.openai.com/api/docs/pricing)

OpenAI publishes per-token prices and per-image estimates for GPT Image 2.5 Flare and Sunburst. The Images API does not expose a maximum output token parameter and the reviewed contracts give no maximum billable token count for each edit. The loop rejects these combinations before network access. For an individually authorized edit, run `imagegen-mastery edit source.png brief.json --provider openai --model gpt-image-2.5-flare --output edited.png --authorize-paid`. [Cost calculation](https://developers.openai.com/api/docs/guides/image-generation#calculating-costs) · [Flare model card](https://developers.openai.com/api/docs/models/gpt-image-2.5-flare.md)

Starting with an existing image requires one inspection reservation. Each new candidate requires room for both rendering and inspection. For example, the default pair needs $2.26 before rendering and the Google Lite editor/inspector pair needs $0.51. The bound includes only this run's Standard API requests on the global endpoints and excludes taxes and other account activity. Recheck rates and limits before using a different pricing tier or after provider changes.

The manifest identifies each request's provider, model, reservation and return status. Its `cost_basis` is `reservations_only`. A returned request and an ambiguous failure each retain their full reservation. Valid inspection reports also include any recognized provider-reported token counts in `provider_usage`. The provider billing dashboard supplies actual charges. Network operations never retry automatically and a fresh directory is required for each run.
