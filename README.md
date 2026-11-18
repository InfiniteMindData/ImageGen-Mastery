# ImageGen-Mastery

A Python CLI and agent skill for turning a user's brief into a generation prompt, measuring candidate images, and reviewing them against visual references. The prompt compiler and review workflow run locally. Live generation is optional.

## Quick start

From the checkout, with Python 3.10 or newer:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
imagegen-mastery optimize examples/brief.json
imagegen-mastery evaluate candidate.png --reference reference.png > report.json
python -m unittest discover -s tests -v
```

Supply your own candidate and reference files. Omit `--reference` to measure a single image. Pillow handles image decoding. The console script and `python -m imagegen_mastery` accept the same arguments.

## Use as an agent skill

Open [SKILL.md](SKILL.md) and follow its workflow. For an agent that discovers skills by directory, copy or symlink the checkout into its skills directory under the lowercase name `imagegen-mastery`. Keep the accompanying references and examples beside the skill. Install the CLI in the Python environment used by that agent for executable checks.

## From intent to a revision

1. Start with the user's own words in `intent`. Add optional composition, lighting, style, constraints, and exclusions only where the user specified or delegated them. The compiler structures supplied information deterministically. It does not call a language model.
2. Inspect each visible reference and capture only the relevant anchors. Use the [reference protocol](references/reference-review.md) for character, environment, and style continuity. Keep user-provided descriptions attributed when you cannot see the source.
3. Run `optimize`, check the wording, then use any generator that accepts text. Save the compiled prompt with the candidate. The [visual foundations](references/visual-foundations.md) and [six medium workflows](references/workflows.md) help select concrete cues and acceptance checks.
4. Run `evaluate` and retain the measurement report. Open the image before recording any visual findings. Pixel differences are sensitive to cropping, framing, lighting, and pose. A matching average color cannot establish identity. The reviewer supplies anatomy, artifact, composition, and continuity judgments.
5. For the next iteration, record the observed defect and desired change in `revisions`. Compare the new result against the same anchors. No universal passing score is defined.

## Optional generation

The two adapters send the compiled text to fixed provider endpoints. Configure the applicable key through your environment's secret manager. Each invocation makes a billable request if accepted by the service. The output path must be new and its parent directory must exist.

```sh
imagegen-mastery generate examples/brief.json --provider openai --model gpt-image-1 --output candidate.png
imagegen-mastery generate examples/brief.json --provider google --model gemini-3.1-flash-lite-image --output variation.png
```

OpenAI requires `OPENAI_API_KEY`; Google requires `GEMINI_API_KEY`. Availability depends on account access, region, and model lifecycle. Review prompts before sending proprietary details. Store credentials outside the repository. These adapters send text only. Native image conditioning, identity embeddings, and automated semantic grading are outside this release.

## Development and sources

The CLI handles files and argument parsing. The prompt compiler, image evaluator, and provider adapters can be tested independently. The Actions workflow runs the offline suite on Python 3.10, 3.12, and 3.13. Provider tests use simulated responses and do not establish live model access.

The skill layout follows the Agent Skills specification. Provider payloads were informed by the official open-source SDK definitions. [Agent Skills specification](https://agentskills.io/specification) · [OpenAI image parameters](https://github.com/openai/openai-python/blob/main/src/openai/types/image_generate_params.py) · [Google Gen AI image model implementation](https://github.com/googleapis/python-genai/blob/main/google/genai/models.py)

Released under the [MIT license](LICENSE).

## Try the evaluator without source images

After installation, run `python examples/compare_tiles.py`. It builds two temporary 64×64 tiles with identical color counts. The second tile moves a colored square to the opposite side. The report exposes the layout change through a nonzero mean absolute RGB difference. Its four visual review entries begin as `unassessed`. The exercise tests the measurement path without requiring a generator or a remote service.

The reference comparison also ranks up to three changed regions on a 4×4 grid. Bounds are fractions of displayed width and height, measured from the top left. Use them to choose regions for inspection. Alignment, resizing, or background changes can dominate this metric. Transparent pixels are composited over white and fine detail may disappear in the 64×64 comparison sample.

For restricted networks, live OpenAI generation needs HTTPS access to `api.openai.com` and Google generation needs `generativelanguage.googleapis.com`. The offline workflow needs neither endpoint.
