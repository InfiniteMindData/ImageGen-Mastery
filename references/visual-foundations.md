# Visual foundations

Use the brief to choose which checks matter. A fisheye room, an off-balance leap, a character with a limb difference, and a two-tone cel can each be correct. Inspect the supplied reference and candidate before applying an expectation. The example numbers below demonstrate ways to measure a brief. Set tolerances from the actual deliverable.

## Anatomy, gesture and contact

Start with the action. In a standing pose, locate the supporting foot or feet and the apparent distribution of weight. In a seated pose, include the seat as a support. In a running pose, establish the phase of the stride. Trace shoulder, elbow, wrist and palm on each visible arm. When a forearm points toward the camera, foreshortening can make it very short in projection. Overlap, apparent width and landmarks distinguish foreshortening from a disconnected limb.

For hands, establish the palm plane and the wearer's thumb side. Follow visible digits from knuckle to tip and record where each disappears behind the object. Forearm rotation changes palm orientation. Think through the hand's actual task. A mug hangs differently from fingertips through its handle than it does when both palms cradle the body. Use the subject's own proportions or model sheet. Age, anatomy, design and camera position all change projected proportions. [OpenStax, Types of Body Movements](https://github.com/openstax/osbooks-anatomy-physiology/blob/main/modules/m46398/index.cnxml)

| Visible symptom | Inspect | Targeted revision | Check |
| --- | --- | --- | --- |
| Grip looks loose | Gap between handle and finger pads, which side of handle occludes each finger | “Thumb rests on top of the loop. Index and middle fingers curl through it, partly hidden by the near rim.” | Trace each visible contact and occlusion once. Report hidden parts as unobservable. |
| Head appears pasted on | Angle of jaw, neck, clavicles and shirt opening | “Turn the head toward the window. Show the far side of the neck disappearing behind the raised collar.” | Neck enters the collar opening and visible contours agree with the turn. |
| Figure appears to float | Sole angle, receiving surface, contact shadow and compressed clothing at the support | Name the bearing surface and which part carries the weight. | Inspect the specified support points at native size and record any visible gap. |

## Composition and perspective

At the intended display size, identify the first subject you notice, the secondary read and any competing high-contrast shape. Reduce a copy to three broad value groups or inspect a small grayscale preview. Check the subject's silhouette where it overlaps the background. Two edges meeting at a single point can merge objects unintentionally. A small overlap or a clear gap often solves the problem while preserving the framing.

Locate the horizon from a level set of parallel edges receding in depth. Compare lines that share a direction in the **same object or aligned objects**. A turned table and a wall can have different vanishing points on the same horizon. In a level camera view, vertical architectural edges stay parallel. Tilting the camera can introduce vertical convergence. In an orthographic reference, equivalent parallel edges keep their direction and near/far copies keep their scale. Curved lenses and deliberately mixed projections need their own reference. [Physically Based Rendering, perspective and orthographic camera implementations](https://github.com/mmp/pbrt-v4/blob/master/src/pbrt/cameras.cpp)

| Visible symptom | Likely cause to test | Revision and check |
| --- | --- | --- |
| Subject buried in clutter | Fine contrast peaks in background near face | Group distant detail into a quieter midtone. Inspect at delivery size and identify the strongest remaining contrast. |
| Required copy space disappears | Focal figure crosses the reserved band | Request the subject on image right with the leftmost quarter as open wall. Measure intrusion into that quarter against the brief. |
| Furniture looks tilted | Top, feet and floor suggest different orientations | Extend two front-to-back edges of the tabletop and similarly oriented floor edges. Specify the shared horizon. Verify another edge pair that was outside the correction. |
| Back row appears miniature | Relative size and ground contact disagree | Locate both rows on one ground plane. Compare projected heights only for objects known to be the same size at the stated depths. |

## Lighting and color

Map each important source to a location, apparent size and color. A nearby broad window gives a different cast shadow from a small distant lamp. Shadow edges generally soften farther from the blocker under an extended source. A form shadow belongs to the turning surface. A cast shadow records the blocker on another surface. Near-contact darkening can help seat an object, with strength dependent on the available light. Highlights move with the view and surface orientation. Catchlights can reflect several sources.

Read color through hue, lightness and saturation. Reserve the strongest separation for the intended read. A white shirt in shade can be darker than a lit brown table. A white balance choice can neutralize one illuminant while retaining a warm/cool split under mixed light. Use a known neutral patch under the chosen source for a color-cast check. In a sunset painting, a colored neutral can be intentional. RGB codes in a final render also reflect exposure, shading and color processing. [Filament, physically based rendering and lighting](https://github.com/google/filament/blob/main/docs/Filament.md.html)

| Visible symptom | Revision cue | Acceptance check |
| --- | --- | --- |
| Flat nose and cheek under a claimed side window | “Broad window camera-left, cheek facing it bright, far cheek held in softer fill, nose shadow falls to image right.” | Inspect lit/shaded cheek relationship and the nose shadow. Allow independent practical lights where visible. |
| Subject and table feel separately composited | Specify one shared lamp and the object's shadow on the table, including its contact point | Compare shadow origins and directions on the same receiving plane, allowing divergence from a close light. |
| Product's accent gets lost | Give the adjacent backing a different lightness, retaining the protected accent hue | View the labeled accent at target size in both color and grayscale. For exact brand color, sample a specified flat, unshaded patch in the target color space. |
| Blown texture in a focal region | Lower exposure on the bright fabric or broaden fill on the dark fold, according to the observed loss | Inspect the specific region at native scale. Count clipped pixels there if a limit was specified. Bright glints may be intentional. |

## Photography and optical realism

Describe the photographer's position and framing before the equipment. At a fixed camera position, changing focal length changes field of view. Moving closer to keep a face large changes the relative projection of nose and ears. Give the model the visible result alongside any focal-length cue. A caption such as “85 mm” expresses intent. Actual acquisition settings require independent evidence.

Name the focus plane and the direction of subject motion. Depth of field depends on aperture, focus distance, focal length, sensor format and acceptable blur at display size. Objects at comparable depth usually share comparable optical defocus. Motion blur follows projected motion during exposure. In a tracking shot, a cyclist's torso can be sharp while the background streaks. Aperture blades, processing and compositing can alter the appearance of bokeh. [Physically Based Rendering, camera ray generation and focus distance](https://github.com/mmp/pbrt-v4/blob/master/src/pbrt/cameras.cpp)

| Problem | Prompt edit | Inspect after rendering |
| --- | --- | --- |
| Environmental portrait has exaggerated facial depth | Move the camera back to conversational distance and use tighter framing. Preserve headroom. | Compare nose-to-ear projection to a reference from a similar viewpoint. Verify crop separately. |
| Mask-like blur cuts through hair and glasses | Place both eyes and the bridge of the glasses in one sharp plane. Place the far wall several steps behind. | Compare neighboring contours at similar depth, including gaps through the frames. |
| Image feels unnaturally processed | Specify texture appropriate to subject scale, mild highlight roll-off and restrained local contrast | At native size, look for edge halos and duplicated pore clusters. At delivery size, check whether the face still reads naturally. |

## Materials, texture and physical realism

Choose cues that distinguish the two materials most likely to be confused. For a neutral dielectric such as clear-coated wood, the surface reflection takes the light color while grain remains visible through the finish. Bare copper colors its reflection. Painted copper can read as ordinary paint until a chip exposes metal. A rough surface spreads reflections. Broad lights also broaden highlights, so inspect another material under the same source before attributing a highlight solely to roughness. Brushed metal stretches reflections along a direction determined by its microstructure. [Filament, dielectrics, conductors and roughness](https://github.com/google/filament/blob/main/docs/Filament.md.html)

| Material | Prompt cues | Failure to inspect |
| --- | --- | --- |
| Woven cloth | Weave follows folds, seam changes the pattern direction, compressed fabric bunches at elbow | Uniform screen-space noise, weave continuing across a gap, highlights resembling lacquer |
| Glazed ceramic | Broad colored body, coherent glaze reflections, exposed clay at unglazed foot if visible | Metallic mirror across the entire mug, random identical chips over all faces |
| Glass | Visible thickness at rim, background displaced through curved walls, reflections at grazing angles | Background running uninterrupted through a thick curved base, duplicate rims inconsistent with the profile |
| Wood | End grain on crosscuts, long grain along the board, joints interrupt grain | One grain image smeared across several separately assembled parts |
| Skin | Plane changes at brow and cheek, local texture varies by region and scale, highlights respond to the light | Identical high-frequency stipple everywhere or loss of eyelid and lip transitions |

For realism, inspect how parts were made and used. Verify that a hinge joins two parts, a strap passes behind its buckle, a repeating fastener pattern follows the panel plane, and wear occurs at plausible contacts for the item's history. Ask for a localized correction naming that joint, overlap or edge. A convincing render can still depict an unbuildable object. Geometry, dimensions and material maps need separate validation when a production asset is the deliverable. [Khronos glTF 2.0, materials and textures](https://github.com/KhronosGroup/glTF/blob/main/specification/2.0/Specification.adoc)
