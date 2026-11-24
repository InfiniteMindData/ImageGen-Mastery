# ImageGen-Mastery

An AI image-generation skill for agents that create, edit or critique images. The agent uses its existing image tools. Start with [SKILL.md](SKILL.md) and load the visual guides that fit the request. The core workflow needs no Python installation or provider credentials.

## Use the skill

Place the checkout in your agent's supported skills directory under the name `imagegen-mastery`. Keep its subdirectories together. In a host that can read files but has no skill discovery, ask the agent to follow `SKILL.md` directly. The host supplies viewing and image creation capabilities.

Try a short request such as “Make a lantern icon for a Roblox inventory. It needs to read at 48 pixels.” The skill guides the agent to choose a readable silhouette, generate with an available tool, and inspect the handle opening at the intended size. For an edit, attach the source and specify what should change. For prompt help alone, ask for the prompt.

| Where to start | What it contains |
| --- | --- |
| [SKILL.md](SKILL.md) | Intent, workflow selection, tool use, inspection and stopping rules |
| [Visual references](references/reference-review.md) | Source roles, visible anchors, uncertainty and preservation |
| [Prompt direction](references/prompt-direction.md) | Converting a short request into concrete visual choices |
| [Photo editing](references/photo-editing.md) | Portrait realism, materials, relighting, clothing and background changes |
| [Foundations](references/visual-foundations.md) and [medium workflows](references/workflows.md) | Composition, photography, cinematography, illustration, 3D and game assets |
| [Worked scenarios](examples/agent-scenarios.md) | A small icon, a portrait edit and a three-shot sequence |
| `imagegen_mastery/` and `tests/` | Optional Python tools and offline regression checks |

## Optional Python toolkit

Use Python 3.10 or newer when you want executable measurements, repeatable briefs or provider adapters.

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
| `audit IMAGE [IMAGE ...] --output-dir NEW` | Offline candidate contact sheet, delivery gates, transparency statistics, optional tile repeats and reference comparison | Offline |
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

## Production QA and candidate selection

The [production playbook](references/production-quality.md) provides visual contracts, asset-specific acceptance checks and a candidate selection workflow for agents using any available image tool.

```sh
imagegen-mastery audit examples/fixtures/candidate.png examples/fixtures/reference.png \
  --reference examples/fixtures/reference.png --output-dir candidate-audit
imagegen-mastery audit texture.png --tile --max-tile-seam 0.1 --output-dir tile-audit
imagegen-mastery audit icon.png --expected-size 512 512 --require-transparency --output-dir icon-audit
```

Open `contact-sheet.png` to compare candidates on light and dark backgrounds. `audit.json` contains input hashes, explicit gates, alpha statistics and optional alignment metrics. The optional `--max-reference-mae` threshold uses the larger of white- and black-composite RGB errors; candidates with different aspect ratios are not ranked. `--tile` adds opposing-edge measurements and reduced 3×3 repeat previews. Repeatable `--protect-region LEFT TOP RIGHT BOTTOM` requires a reference and checks exact decoded RGBA (including alpha and hidden RGB) in normalized regions of identically sized images. The JSON records the complete policy and per-region results. Thresholds are user-selected heuristics, not guarantees of visual quality. Exit 2 means at least one candidate failed a requested gate (the evidence is still saved), exit 1 means an input or execution error, and exit 0 means no requested gate failed. Without gates, delivery status is unassessed. Inspect originals at delivery and native size.

## Local enhancement

```sh
imagegen-mastery enhance examples/fixtures/candidate.png --output sign-2x.png --scale 2 --sharpen 40
```

Add `--denoise` for median filtering. Upscaling interpolates pixels, denoising can remove texture, and sharpening can create halos. The optional ComfyUI node runs these same operations locally. [Enhancement controls and node installation](references/enhancements.md)

## Reading the measurements

`evaluate` uses EXIF display orientation, a white transparency background and 256-pixel thumbnails. Its 64×64 RGB comparison is sensitive to alignment. It lists up to three changed grid cells. Anatomy, composition, artifacts and continuity remain unassessed in the offline rubric.

`report` compares visible pixels on the same sampling grid. Block SSIM measures local grayscale structure. The 64-bit difference hash measures coarse brightness gradients. Either can miss a color change. OCR checks exact, case-sensitive substrings and can misread stylized lettering. Coordinates use normalized left, top, right, bottom from the displayed top-left corner. All metrics include their limits in the JSON and HTML. Pixel differences cannot establish identity, adherence to the brief or semantic quality.

`inspect` sends previews of up to 1024 pixels per side. It returns a completed inspection only after receiving a valid model response grounded in those submitted images. Its confidence is self-reported. Incomplete or refused responses fail without producing findings.

## Development

The optional compiler renders the fields supplied by the author. An agent can write a brief after using the skill to reason about the request. Use `constraints` for mandatory conditions and `creative_options` for suggestions. Suggestions appear in the generation prompt and are excluded from the inspection requirement list.

```sh
python -m unittest discover -s tests -v
python examples/compare_tiles.py
python examples/make_sign_fixtures.py
```

The [opt-in live provider suite](integration_live/README.md) is separate from CI and requires explicit authorization per provider. Offline provider tests use simulated HTTP responses. CI runs the offline suite and installed CLI on Python 3.10, 3.12 and 3.13, and runs local Tesseract on the sign fixture. The repository is distributed under the [MIT license](LICENSE).
