# Worked requests

The first three scenarios illustrate decisions and conditional checks. The final exercise uses the two included PNG fixtures.

## A tiny inventory icon

**Request.** “Make a Roblox inventory icon of a lantern. It has to read at 48 pixels.”

**Decision.** Use text-to-image. Legibility at 48 pixels is a requirement. A squat silhouette and a dark handle against a pale background are useful choices. Leave branding and scenery open.

**Prompt.** “Single lantern inventory icon for a Roblox game. Give the raised handle a clear opening above the broad cap. Frame the whole lantern with a small margin. Group the lit panes into one warm shape that still reads at 48 pixels.”

**Inspect.** View at 48 pixels. If the handle opening closes at that size, widen just the opening and recheck the cap. A pleasing large preview alone cannot settle the question.

## Warm an existing portrait

**Request.** “Make the light a little more golden. Keep me looking like me.”

**Decision.** Open the source. Find a lit plane of the face and a nearby surface receiving the same light. A local color adjustment may suffice. Use the source as an edit input if generative relighting is needed. Without the source, request it before attempting an identity-preserving edit.

**Edit instruction.** “Warm the existing light slightly. Carry the same warmth onto nearby surfaces facing that light. Keep the face shape, hairline, pose, clothing, crop and natural variation in the skin.”

**Inspect.** Check the face against the original at the same scale. If the light reads correctly but the jawline moved, keep the source and redo the color adjustment. Extra sharpening cannot restore the original geometry.

## Three shots of a courier in the rain

**Request.** “Same courier in all three frames. Use A for the character and B for the painted style. First she waits at the crossing, then gets on the bus, then sits by the window.”

**Decision.** Inspect A for silhouette, hair shape, clothing seams and recurring accessories. Inspect B for contour behavior, shadow grouping and palette. Record only visible anchors. B supplies the rendering treatment. Any person in B has no casting role.

**Shot directions.** Establish the courier and her waiting posture in the first frame. For the second, supply the accepted first frame and A if the tool supports both; show weight transferring to the step and a hand contacting the rail. For the third, keep her design while changing to a seated pose and interior light. If one attachment is supported, prioritize A for identity and express the observed style in words. Disclose the reduced conditioning.

**Inspect.** Compare each frame to A as well as to the previous frame. A bag hidden behind a seat is unobservable. If the bag strap visibly swaps shoulders in the boarding shot, correct that shot and inspect its contact with the coat. Keep the other accepted frames.

## Inspect the storefront sign

Open [candidate.png](fixtures/candidate.png) and [reference.png](fixtures/reference.png). Treat the reference as the desired appearance. Before reading further, write a single edit instruction and identify which details should remain locked.

The smallest edit is to change the fill of the square left of OPEN from rust to teal (`#18877F`). Preserve its position, dimensions, the lettering and background. A full-frame RGB comparison of the supplied 640 × 240 fixtures places all 5,041 differing pixels in the 71 × 71 square, starting at x=54, y=82 in top-left coordinates. An exact fill is sufficient if a pixel editor is available. A fresh generation would introduce unnecessary uncertainty. These measurements describe the included files; inspect again if the inputs change.
