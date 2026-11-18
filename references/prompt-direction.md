# Turning intent into a picture

Choose detail by asking which visible decision is still unresolved. A material cue helps distinguish a stone figure from a living animal. A lens brand seldom helps. If the request already resolves the important decisions, use its wording directly.

| Request | Useful direction | Leave open |
| --- | --- | --- |
| “A cat watching rain.” | “A cat sits inside a window watching raindrops run down the glass. Frame from just behind its shoulder so the viewer follows its gaze.” | Breed, time of day and furnishings. The point of view is an artistic choice. |
| “A cozy samurai game menu. Leave room for Play and Settings.” | “A lone samurai faces a lantern-lit temple. Put the figure and the entrance on the right; keep the left side quiet for the menu overlay.” | Letter rendering if the game draws its own UI. Match the character proportions to the supplied game style. |
| “Ink drawing of my shop. Sign must say ‘Half Moon’.” | Keep the exact mixed-case string. Choose a view where the entire sign face reads; keep roof hatching lighter behind the letters. | Decorative signage and invented slogans. |

## Assemble a portable prompt

Keep a private distinction between requirements, reference-derived facts, and choices the agent makes. Only user requirements and explicitly locked anchors are grounds for rejecting an otherwise good result. A suggestion may trade off against another suggestion.

For a loose brief, try two mentally different framings. Pick the one that best reveals the specified action. For “returning a borrowed key,” a close view of two hands passing the key makes the exchange legible. A wide street view serves a request about the neighborhood. Send one coherent direction unless the user requests alternatives.

For a conflicting brief, identify the physical conflict. A face-filling close-up cannot also show the person's shoes in that single view. Ask which framing matters if both are mandatory. If the shoe detail is merely optional, use the close-up and drop it.

Use plain visual language with the host generator. Put exact output dimensions, number of images, masks and ordered references into documented tool controls when available. When a requested ratio is unavailable, explain the delivery option and allow room for an authorized crop. Never invent parameter names, weighting syntax, deterministic seeds or provider-specific negative-prompt support.
