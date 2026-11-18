# Live provider integration tests

From the checkout, install the project with `python -m pip install -e .`. Offline CI discovers only `tests/`. To list the seven live cases as skips, run this command with the authorization variable unset.

```sh
python -m unittest discover -s integration_live -v
```

Each selected test makes one real API request. The edit and inspection tests upload the repository's synthetic storefront sign fixtures. The mask case uploads the source and a transparent PNG mask. The suite checks the CLI's decoded image size and format, or the inspection's provider, model, input hashes and evidence structure. Visual correctness still requires review.

## Run a provider

Provide the selected service's key in the environment. Set the two switches on the command you intend to run. These examples stop after the first failure.

```sh
# Requires OPENAI_API_KEY. Up to four paid requests.
IMAGEGEN_LIVE_AUTHORIZE_PAID=yes IMAGEGEN_LIVE_PROVIDER=openai \
  python -m unittest -fv integration_live.test_live.OpenAILiveTests

# Requires GEMINI_API_KEY. Up to three paid requests.
IMAGEGEN_LIVE_AUTHORIZE_PAID=yes IMAGEGEN_LIVE_PROVIDER=google \
  python -m unittest -fv integration_live.test_live.GeminiLiveTests
```

To authorize a single operation, append its test name to the class. For example, this sends only the native mask edit.

```sh
IMAGEGEN_LIVE_AUTHORIZE_PAID=yes IMAGEGEN_LIVE_PROVIDER=openai \
  python -m unittest -v integration_live.test_live.OpenAILiveTests.test_native_mask
```

| Case | Inputs | OpenAI | Gemini |
| --- | --- | --- | --- |
| `test_generation` | Compiled sign brief | GPT Image 2.5 Flare | Gemini 3.1 Flash Image |
| `test_reference_edit` | Brief, source and reference PNGs | GPT Image 2.5 Flare | Gemini 3.1 Flash Image |
| `test_native_mask` | Brief, source and mask PNGs | GPT Image 2.5 Flare | No native mask adapter |
| `test_vision` | Brief, candidate and reference PNGs | GPT-5.4 mini (2026-03-17) | Gemini 3.1 Flash Lite |

## Cost and results

OpenAI requests three low-quality 1024 × 1024 image outputs and one vision review for a full run. Estimate the image portion with the [OpenAI image pricing calculator](https://developers.openai.com/api/docs/guides/image-generation) and check the review model's [token rates](https://developers.openai.com/api/docs/pricing).

Gemini requests two square 1K image outputs and one vision review for a full run. At the published standard rate of about $0.067 per 1K image, the two image outputs alone total about $0.134 before input, other token usage and inspection charges. Check current rates for your account. [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing)

A failed assertion can follow a successfully billed request. Each command invocation starts a new run. Check the provider's usage dashboard before repeating a failed test. The test runner reports each case as passed, failed or skipped and removes temporary output images afterward.
