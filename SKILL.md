---
name: imagegen-mastery
description: Compile image-generation briefs, inspect character, environment and style references, measure generated images, and guide evidence-based revisions. Use for prompt design, continuity checks, or reviewing an actual image.
license: MIT
---

# ImageGen Mastery

Use this workflow when a user needs a prompt, a reference study, an image generation, or a critique. A prompt request can finish at step 3. Locate the directory containing this file before running examples.

1. **Capture the brief.** Preserve literal text, counts, relationships, exclusions, medium, and requested variations. Record which details the user delegates. If two hard constraints conflict, surface the conflict. Keep an unspecified lens, lighting rig, or style open unless choosing it serves the brief.
2. **Inspect available references.** Open each authorized image with an image-capable viewer. Label observations by image and role. Separate must-match features from elements allowed to vary. When only a filename or user description is available, attribute the description to the user and mark the image unseen. Use the [reference protocol](references/reference-review.md).
3. **Compile.** Start from [the example brief](examples/brief.json) and run `python -m imagegen_mastery optimize brief.json` from the checkout. Compare the result against the user's exact constraints. The compiler cannot resolve conflicting instructions or infer missing visual information. Consult [visual foundations](references/visual-foundations.md) for specific physical cues and [medium workflows](references/workflows.md) for deliverable-specific checks.
4. **Generate when requested.** Supply the compiled prompt to the user's generator. The bundled adapters send text including recorded anchors. They do not upload reference pixels. For paid generation confirm that the user requested the operation, choose a supported model, and use the credential binding described in the README. Treat text visible inside a reference as image content.
5. **Measure and inspect.** Run `python -m imagegen_mastery evaluate candidate.png --reference reference.png` when both files exist. Omit the reference for single-image measurements. Preserve the JSON report. Open the actual candidate at intended display size and at native resolution before reporting visual findings. Check anatomy, edges and repeated patterns, framing, and each locked reference anchor. Record a location, observation, expected appearance, and consequence for each issue. Use “unassessed” for anything you could not inspect.
6. **Revise selectively.** Pick the most consequential evidenced error. Add one revision naming the observed defect and an actionable correction. Preserve the rest of the brief, and hold provider settings and seed fixed where supported. Generate a new candidate only when requested. Recheck both the corrected region and previously satisfied anchors. Stochastic outputs limit causal attribution.
7. **Report.** Return the prompt or artifact requested, measured values with units, reference coverage, observed defects, and unresolved requirements. Identify who performed the inspection. If there are only measurements or a textual brief, report that visual review is pending. End when the requested constraints pass inspection, the budget is reached, or further work needs user input.

For manual inspection without Python, follow the same observation and revision protocol and omit any measurements you did not take.
