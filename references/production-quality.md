# Production image direction and acceptance

Use this guide when the request is for a finished asset, a close reference match, a series, or multiple candidates. Do not turn simple requests into a questionnaire. Work with the host's actual tools and keep the original source intact.

## Visual contract

Record a compact contract before creating an image:
- Deliverable: what the file is for, target dimensions/aspect, alpha and file format if specified.
- Nonnegotiable requirements: literal text, object counts, placements, requested medium, exact exclusions.
- Reference roles: source to edit, identity/design, camera, pose, palette, materials, typography or layout. Do not transfer unrelated details.
- Locks: immutable features with wearer-relative sides or explicit frame coordinates; mark a lock pixel-exact only when the editor can enforce it.
- Flexible choices: select a coherent direction without inventing user constraints.
- Review conditions: what is inspectable from pixels and what requires runtime, geometry, physical measurements or manual approval.

## Direct by visual hierarchy

Establish the largest masses, silhouette, subject and camera first. Then choose a motivated lighting arrangement, material response, edge treatment and background density. Every adjective should cause a visible change. Avoid generic quality modifiers or mutually incompatible lens, lighting and style tags. Prefer a short prompt with an explicit spatial relationship over a long catalogue of adjectives.

For realistic photography, check that highlights, shadows, reflections and depth cues agree with the chosen lighting and camera. Preserve natural skin texture where relevant; avoid applying indiscriminate smoothing. For style matching, specify the observable rules of the reference (line taper, shape language, value grouping, palette, texture and perspective), not just its name.

## Production playbooks

| Deliverable | Direct the generation | Review before delivery |
| --- | --- | --- |
| Transparent game icon | Clear silhouette, consistent viewing angle, restrained details, enough transparent padding | Alpha on light and dark backgrounds; exact target size; readability at 32/48/64 px when relevant |
| Tileable material reference | Orthographic framing, even lighting, no directional baked shadows when the texture is intended for albedo | 3x3 repeat, both seams, four corners, repeated large features; validate actual maps separately |
| PBR material set | Establish physically meaningful material classes and aligned surface features | Albedo without baked highlights; roughness/metallic are data, not arbitrary grayscale; normal orientation and engine color space; no claim of valid PBR from a beauty render |
| Character or costume sheet | Canonical silhouette, fixed proportions, wearer-relative asymmetric anchors, shared scale | Compare front/side/back landmarks, accessories, palette and costume layer order; hidden features remain unknown |
| UI or marketing graphic | Fixed content hierarchy, safe areas, literal copy and target ratio | Read at delivery size, verify every string, margins, contrast and export dimensions; use layout tools for exact typesetting when possible |
| Product reference | Same object geometry, construction seams and label placement; controlled set and reflections | Compare silhouette and part counts at comparable angles; check fine print and contact shadows |
| Environment concept | Ground plane, traversal route, scale cues, focal landmark, motivated light | Check perspective, path readability, repeated props and scale; runtime checks require engine import |

## Candidate tournament

Generate alternatives only within the authorized count and budget. Change one meaningful decision between alternatives when diagnosing a problem; keep locks and reference roles fixed. Assign stable candidate IDs. Do not choose a favorite before checking the hard requirements.

1. Reject outputs with wrong dimensions, missing required alpha or failed explicit numerical gates. Mark unverified requirements as unknown, not passed.
2. Review the survivors side by side at delivery size, then inspect the original pixels in consequential regions.
3. Evaluate each hard requirement as met, violated, uncertain or not applicable, with visible evidence and location. Separate optional artistic preferences.
4. When exact reference alignment is intended, use offline similarity metrics to help shortlist. Do not use pixel distance as a proxy for aesthetic quality or for style/pose changes.
5. Pick the candidate that meets the request best. Save it before editing. If no candidate meets the mandatory requirements, report the unresolved defects rather than calling one complete.

The optional audit command writes a contact sheet on white and dark backgrounds, normalized transparency measurements, explicitly selected gates, a reference-similarity ordering and optional 3x3 tile previews. It does not use network services or produce semantic judgments.

## Targeted repair and delivery

Identify the defect, its region and a checkable replacement. Include only context that needs to change, such as the affected contact shadow. Keep the previous accepted version and compare the new output at the same scale. Revert edits that introduce defects or violate locks. Stop at the authorized budget, repeated failure, or insufficient evidence. Do not claim an inspection if the tool cannot open the actual result.

Deliver the requested artifact first. For substantial production work, include concise notes on selected candidate, checks performed, known limitations and any necessary engine-side verification. Never describe an untested generation as a verified production asset.
