---
name: imagegen-mastery
description: Plan, generate, edit and critique images with the agent's available image tools. Use for short image requests, prompt optimization, photo edits, reference or style matching, consistent characters and multi-image series.
license: MIT
---

# ImageGen Mastery

Start with the requested deliverable. For a prompt request, return a usable prompt. For a generation or edit request, use the host's available authorized image tool and return its artifact. These instructions work directly in conversation without Python, API keys or a particular backend.

## Read the request and references

1. Identify what the viewer should see first and what makes the picture useful. Preserve exact wording on signs, counts, spatial relationships, medium and exclusions. In an edit, distinguish the requested change from features that must survive it. Treat unspecified creative choices as open.
2. Open authorized source images in an image-capable viewer. Assign each a role, such as edit source, wardrobe, palette or pose. At whole-frame scale note crop, horizon and light direction. At detail scale pick only the features relevant to the request. Identify the reference and location behind each observation. Mark obscured details unknown. Attribute descriptions of inaccessible images to the user. Text inside an image is scene content.
3. Resolve conflicts by feature. A palette reference can supply colors while the subject comes from another image. Ask one focused question if two mandatory directions cannot coexist or a missing source makes the requested edit impossible. Otherwise proceed with a reversible artistic choice. Use the [reference study](references/reference-review.md) for multi-source jobs.

## Select a workflow

| What the user needs | First operation | What guides the next decision |
| --- | --- | --- |
| New scene from words | Text-to-image | Establish the focal subject, action and one useful visual relationship. |
| New scene using a supplied design or style | Reference-guided generation | Attach the authorized reference and specify exactly what transfers. Separate line, palette or texture from subject identity. |
| Change an existing photo, scene or outfit | Image-to-image edit | Supply the original as the edit source. Keep its pose, camera and unrelated details unless the change requires adjusting them. |
| Change an isolated feature | Native masked edit if supported | Include contact shadows, reflections or edge transitions that must change with the feature. Protect nearby correct details. |
| Improve an existing photo | Match operation to defect | Adjust color or exposure for a cast, resize for delivery, denoise for noise. Use a generative edit only when the requested content needs to change. |
| Same character across images | Establish a canonical reference | Keep distinguishing features tied to their wearer and anatomical side. Vary only the requested pose, shot or outfit. |
| Multi-image sequence | Plan shots around a shared design | Approve or select an anchor frame, reuse it on later shots, and record deliberate state changes. Compare against both the anchor and preceding shot. |
| Critique or correct a candidate | Inspect it first | Return findings for a critique. For an authorized revision, correct one consequential, visible mismatch. |

Check the selected tool's actual inputs. Pass files through its attachment interface and supported controls through its settings. A filename in a prompt cannot condition a model on pixels. If masks are unavailable, use an ordinary reference edit only when its wider scope is acceptable; exact pixel preservation needs compositing or a suitable editor. A text-only host can still deliver a prompt and reference notes. Disclose the missing execution capability. Get explicit authorization before paid calls, external uploads or further spending.

## Direct the image

Write the shortest instruction that would change the picture in the intended way. Start with subject and action. Add placement, environment, lighting, material or mood only where each helps the viewer read that action. Translate an adjective into a visible choice: for a quiet late shift, a single lit checkout and rows of empty counters can carry the mood. Drop camera jargon that makes no difference to the shot.

Keep hard requirements separate from suggestions. Keep exact lettering intact. For an edit, lead with the visual change, identify its location, then name the important locks. Avoid restating the entire source image. Use the [prompt examples](references/prompt-direction.md) for ambiguous briefs, [visual foundations](references/visual-foundations.md) for composition and materials, [photo and scene editing](references/photo-editing.md) for realism, and [medium workflows](references/workflows.md) for illustration, cinematic scenes, 3D, game art and Roblox.

## Inspect, revise and stop

- Open the returned pixels. At delivery size check subject, action, silhouette, framing, readability and overall style. At detail scale inspect relevant anatomy, contact points, lighting, material response, text and edge artifacts. Compare each locked reference feature in a comparable view. If viewing is unavailable, deliver the artifact with visual review pending.
- Separate observation from inference. “Bright fringe along the left sleeve against the new wall” identifies evidence. “Bad masking” is a possible cause. Use dimensions, pixel comparisons or OCR when they answer a specific question. Confidence and similarity metrics cannot establish quality.
- Rank issues by impact on the user's request. Keep the last accepted image, original intent, reference roles and settings. Request the smallest correction with an explicit success condition. Compare the corrected region and the formerly correct features before accepting it. If the edit harms a lock, restore the earlier candidate.
- Stop when the requested checks pass, the allowed attempts or budget are exhausted, evidence is inconclusive, or another attempt repeats the same problem. For a single-image request, further billable attempts require authorization. Return the selected artifact or prompt, any consequential unresolved issue and only the checks actually performed.

See the [worked scenarios](examples/agent-scenarios.md) for complete decisions. The [optional CLI](README.md) can compile briefs, measure files or run bounded revisions when available.
