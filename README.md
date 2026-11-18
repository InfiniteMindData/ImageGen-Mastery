# ImageGen-Mastery

A Python CLI and agent skill for compiling image briefs, editing with reference pixels, inspecting candidates and reviewing changes. Prompt compilation, measurements and comparison reports run offline. Provider calls are optional.

## Try the offline workflow

From the checkout, use Python 3.10 or newer.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
imagegen-mastery optimize examples/sign-brief.json
imagegen-mastery evaluate examples/fixtures/candidate.png --reference examples/fixtures/reference.png
imagegen-mastery report examples/fixtures/candidate.png --reference examples/fixtures/reference.png \
  --ssim --perceptual --region 0 0 0.25 1 --output-dir sign-report
```

Open `sign-report/report.html`. The original fixtures differ in the color of one square. The right side of the sign and its lettering match. The report includes side-by-side previews, an RGB change map, regional measurements, and JSON. To check lettering, install Tesseract and its English language data, then add `--require-text OPEN` and choose a new output directory. Each requested region and the full candidate get a separate OCR result.

| Command | Result | Network |
| --- | --- | --- |
| `optimize BRIEF` | Deterministic text preserving user constraints, literal wording, reference notes and locks | Offline |
| `evaluate IMAGE [--reference PATH]` | Original JSON measurements, 4×4 changed-region ranking and manual rubric | Offline |
| `report IMAGE --reference PATH --output-dir NEW` | Local report bundle. Optional block SSIM, difference hash, OCR and normalized regions | Offline |
| `capabilities` | Model names, local input limits, size, ratio, quality, mask support and contract links | Offline |
| `enhance SOURCE --output NEW.png` | Optional local upscale, noise reduction and sharpening, also available as a ComfyUI node | Offline |
| `profiles` | Budgeted revision models and per-call USD reservations by operation | Offline |
| `inspect IMAGE` | Model observations with requirement index, candidate bounding box, confidence, uncertainty, input hashes and inspected preview sizes | OpenAI or Gemini |
| `generate BRIEF`, `edit SOURCE BRIEF` | One still PNG at a new output path | Selected provider |
| `revise BRIEF --run-dir NEW` | Versioned, budgeted generate/import → inspect → edit workflow | Selected image and vision profiles |

Use `python -m imagegen_mastery` in place of the console script. Each command has `--help`. Windows PowerShell users can activate their environment with `.venv\Scripts\Activate.ps1`.

## Reference images and paid requests

Use `OPENAI_API_KEY` and/or `GEMINI_API_KEY` through your environment. Only the chosen provider receives a single-command request. The revision loop sends candidate and reference pixels to both providers as needed. Confirm the authorized files, providers and spending scope before running any paid operation.

A brief's `references[].image` is a label. To upload its pixels, use `--named-reference "Exact label" path.png`. Repeat for additional labels. `--reference path.png` supplies an anonymous image when the brief has no unbound named references. Text-only generation continues to work with reference notes alone. Automated revision requires every declared reference label to be bound. The skill never opens paths inferred from brief text.

```sh
imagegen-mastery capabilities
imagegen-mastery inspect examples/fixtures/candidate.png --brief examples/sign-brief.json \
  --named-reference "Target sign" examples/fixtures/reference.png --authorize-paid
imagegen-mastery edit examples/fixtures/candidate.png examples/sign-brief.json \
  --provider openai --model gpt-image-2.5-flare --mask examples/fixtures/mask.png \
  --quality medium --aspect-ratio 3:2 --output corrected.png --authorize-paid
imagegen-mastery generate examples/sign-brief.json --provider google --model gemini-3.1-flash-image \
  --reference examples/fixtures/reference.png --aspect-ratio 16:9 --size 2K --output variation.png --authorize-paid
```

Every paid command requires explicit user consent and the flag `--authorize-paid`. Existing text-only generation scripts must add that flag. Python callers pass `authorized=True`. Plain generation accepts user-selected model IDs as before. Advanced options require an entry in the model registry. Credentials are read from the environment. New image uploads use re-encoded pixels with metadata removed.

## Controlled revisions

```sh
imagegen-mastery revise examples/sign-brief.json --start examples/fixtures/candidate.png \
  --reference examples/fixtures/reference.png --max-revisions 1 --budget-usd 2.48 \
  --run-dir sign-run --authorize-paid
```

Omit `--start` to generate the first image from the brief. The example authorizes up to one edit and two inspections at standard USD rates. Starting from generation needs another $2.04 of reservation. Each request reserves its conservative upper bound immediately before dispatch. The run stops if the next edit and its review cannot both fit. Failed or interrupted requests are never retried automatically. The [provider contracts](references/provider-contracts.md) explain the budget calculation and assumptions.

The default editor and inspector keep the previous model choices. Run `profiles` to see budgeted combinations and reservations. Choose them with `--image-provider`, `--image-model`, `--vision-provider`, and `--vision-model`. Single-image inspection accepts `--provider` and `--model`. Availability for your account requires a live request.

Put semantic locks in `locked_attributes`. For an exact pixel lock, pass a repeatable normalized `--protect-region LEFT TOP RIGHT BOTTOM`. Use `--feather 8` to blend inward over eight pixels around preserved areas; the default zero keeps the original hard cut. `--max-boundary-jump 0.12` rejects an increase above 0.12 in normalized adjacent-channel contrast across a checked edge. A real object boundary can trigger this heuristic, and a gradual mismatch can pass it.

`--expected-size WIDTH HEIGHT` and repeatable `--require-text OPEN` add acceptance checks before each paid inspection. A failed check stops the run, including when the starting image already fails. OCR requires local English Tesseract and can misread lettering. The saved `vNNN.checks.json` records the result. Revised candidates are checked against the previous frame outside the edit box and against the initial frame inside protected regions, including alpha. A provider proposal with different dimensions is rejected before compositing. Model confidence remains uncalibrated. Human review is still needed for likeness, style and other semantic requirements.

The run directory contains the brief and settings in `manifest.json`, the submitted generation/edit prompts, reference snapshots, all original provider versions, localized candidates and per-version inspection JSON. `accepted` identifies the most recently reviewed usable candidate, which can still have outstanding defects at a budget or iteration stop. A null value means no candidate passed the acceptance checks. A failed run retains its evidence and reservations. The CLI refuses to reuse the directory.

## Local enhancement

```sh
imagegen-mastery enhance examples/fixtures/candidate.png --output sign-2x.png --scale 2 --sharpen 40
```

Add `--denoise` for median filtering. Upscaling interpolates pixels, denoising can remove texture, and sharpening can create halos. The optional ComfyUI node runs these same operations locally. [Enhancement controls and node installation](references/enhancements.md)

## Reading the measurements

`evaluate` uses EXIF display orientation, a white transparency background and 256-pixel thumbnails. Its 64×64 RGB comparison is sensitive to alignment. It lists up to three changed grid cells. Anatomy, composition, artifacts and continuity remain unassessed in the offline rubric.

`report` compares visible pixels on the same sampling grid. Block SSIM measures local grayscale structure. The 64-bit difference hash measures coarse brightness gradients. Either can miss a color change. OCR checks exact, case-sensitive substrings and can misread stylized lettering. Coordinates use normalized left, top, right, bottom from the displayed top-left corner. All metrics include their limits in the JSON and HTML. Pixel differences cannot establish identity, adherence to the brief or semantic quality.

`inspect` sends previews of up to 1024 pixels per side. It returns a completed inspection only after receiving a valid model response grounded in those submitted images. Its confidence is self-reported. Incomplete or refused responses fail without producing findings.

## Agent skill and development

To use the skill, copy or symlink the checkout into the agent's skills directory under `imagegen-mastery`. Keep the [skill](SKILL.md), [reference review protocol](references/reference-review.md), [visual foundations](references/visual-foundations.md), [medium workflows](references/workflows.md) and examples together. Install the CLI in the agent's Python environment.

```sh
python -m unittest discover -s tests -v
python examples/compare_tiles.py
python examples/make_sign_fixtures.py
```

The [opt-in live provider suite](integration_live/README.md) is separate from CI and requires explicit authorization per provider. Offline provider tests use simulated HTTP responses. CI runs the offline suite and installed CLI on Python 3.10, 3.12 and 3.13, and runs local Tesseract on the sign fixture. The repository is distributed under the [MIT license](LICENSE).
