# Medium-specific workflows

Choose the workflow that matches what the user will receive. Establish the purpose, dimensions, reference roles and any literal constraints before adopting the example's artistic choices. Record whether the deliverable is an illustration, a reference sheet, a texture, or an imported runtime asset. Each example includes a short prompt passage, a check at delivery size and a correction tied to a visible defect.

## Photorealism

1. Pick the photographic task, such as documenting an object for a catalogue or catching an unposed interaction. Select a camera position that reveals the specified features. For a catalogue shot, request a focus range that includes all details the buyer needs.
2. Describe one lighting setup and how two different surfaces receive it. Specify the object's contact with the set and how much of the background should resolve. Add only imperfections supported by the object's use and scale.
3. Inspect the silhouette at delivery size, then zoom in on contact points, optical transitions and repeating texture. Verify any requested lettering character by character.

**Example passage.** “Catalogue photograph of an ivory stoneware teapot on a pale oak table, camera just above the spout. The foot touches the tabletop. A tall window on image left reflects as a continuous soft stripe around the glaze. Both the spout tip and the wrapped cane handle resolve clearly. The wall behind falls softly out of focus.”

**Local correction.** If the teapot floats, anchor its foot on the board and add a narrow shadow at their junction under the same window. Recheck the spout and handle. Acceptance requires both named details to remain visible and the unwanted gap to close. The image can communicate optical intent. It cannot verify real-world dimensions or acquisition metadata. [pbrt camera models](https://github.com/mmp/pbrt-v4/blob/master/src/pbrt/cameras.cpp)

## Cinematic imagery

1. State the story beat as an observable action. Choose the shot size, camera height and what the audience should learn first. Anchor each actor's screen position, eyeline and movement to the same camera.
2. Assign foreground, action plane and background. Motivate the brightest light with a source in or near the scene. Leave room on the gaze or travel side when the shot needs it.
3. For a sequence, record the line of action, subject screen sides, entrances, wardrobe and lighting state per shot. Decide whether a camera crossing or costume change is part of the story. Check successive frames together.

**Example passage.** “Wide night platform shot from the bench side of the tracks. A commuter on image left lowers a folded note and looks into the empty right half of the frame. One overhead fixture lights the note and the near cheek. A departing train streaks across the background.”

**Local correction.** If the viewer first notices a bright advertisement behind the commuter, dim that sign and keep the note in the fixture's pool. At thumbnail size, record what drew the eye first. In a reverse angle, check the direction of the eyeline against the preceding shot. A still can establish implied movement. Timing and cuts require a sequence to assess.

## Anime illustration

1. Identify the design grammar in the reference. Compare head-to-body proportion, eye spacing, nose marks, taper of contours, number of shadow bands and where highlights break. For a character match, specify the visible anchors in the current view.
2. Establish the gesture and resolve large hair masses, clothing overlaps and negative spaces before line details. Pick the treatment for the focal subject and the background separately.
3. Check the design at delivery size and in silhouette. At full size compare the near/far eye in the chosen head turn, the side of asymmetrical pieces and the consistency of ink and shadow boundaries.

**Example passage.** “Three-quarter bust of the courier looking over her left shoulder. The amber clip sits above the wearer's right temple where visible. Her bob divides into three broad masses. Tapered dark contours frame the face, one crisp violet cel-shadow shape crosses the far cheek, and the station background uses soft painted edges.”

**Local correction.** If the cheek has a smooth beauty-render gradient, replace it with the single specified cel-shadow shape and retain the tapered chin contour. Count the reference's shadow bands on that cheek under comparable light. A hidden clip in a rear view can be recorded as occluded. A multi-view sheet still needs inspection for handedness and design drift between panels.

## 3D product and character renders

1. Define the intended output, such as a single hero render or a modeling sheet. Give the object a construction and approximate scale. Identify joins, edge radii, material boundaries and where labels sit. For orthographic views, request aligned centers and shared scale.
2. Choose an environment that makes the materials legible. A long softbox can describe curvature on glossy enamel. A dark reflection card can separate a polished edge from a pale background. Specify contact with a plinth or floor.
3. Inspect curved highlights across joins and compare the appearance of adjacent finishes under the same source. On a turnaround, compare shared heights and widths in matching views, locate the same part on each sheet and count major pieces.

**Example passage.** “Three-quarter studio render of a palm-sized enamel desk timer. The molded face meets a brushed aluminum rim at a narrow seam. A long strip light sweeps around the rim, the satin face carries a soft reflection, and two rubber feet settle onto the plinth.”

**Local correction.** If the rim and face both resemble chrome, broaden and weaken the face reflection while retaining the directional brushing on the rim. Check both finishes against the same light. A rendered sheet supplies modeling evidence. Watertight geometry, UVs, normals, topology and physically based rendering (PBR) map contents need inspection in a 3D application. [Filament material model](https://github.com/google/filament/blob/main/docs/Filament.md.html) · [glTF material specification](https://github.com/KhronosGroup/glTF/blob/main/specification/2.0/Specification.adoc)

## Roblox assets

1. Identify the asset class and camera distance. An inventory icon, environment prop, rigid avatar accessory and layered garment each require different deliverables. For a prop reference, request front and side orthographic views at one scale and a separate three-quarter view. Include a recognizable scale cue or a dimension supplied in studs.
2. Specify the features that survive the in-experience camera. Favor a clear profile and restrained surface detail when the prop will occupy few pixels. For an attachment, identify its wearer-relative side and intended location. For a mesh, show the base and connection surfaces needed by the modeler.
3. Inspect the artwork at estimated on-screen size. Check silhouette, feature count and agreement between projections. For actual production acceptance, import the model into Studio and check dimensions, pivot, orientation, collisions and class-specific requirements. For an accessory, check fit and attachments on each target rig.

**Example passage.** “Modeling reference for a four-stud-tall station lantern. Front and right-side orthographic views share a baseline, plus a separate three-quarter view. A large square cap, one raised carrying loop and four chunky amber panes read from across the platform. Show the flat mounting foot.”

**Local correction.** If the side view loses the loop or changes the mounting plate height, align those landmarks with the front view and preserve the specified projection. Count each view's visible parts and compare base-to-cap height. The artwork shows design intent. A PNG cannot establish Studio import success, triangle count, alignment of attachments, or collision behavior. Recheck current platform limits for the target class. Texture maps affect surface appearance while the mesh supplies silhouette. [Roblox mesh specifications](https://github.com/Roblox/creator-docs/blob/main/content/en-us/art/modeling/specifications.md) · [Roblox SurfaceAppearance maps](https://github.com/Roblox/creator-docs/blob/main/content/en-us/art/modeling/surface-appearance.md)

## Game art

1. Start with the player's action and the delivery format. For icons, specify the smallest display size and backgrounds. For tiles, specify cell dimensions, projection and intended adjacencies. For animation, record frame size, frame order, pivot and the moving body parts. A painted environment concept can instead prioritize play space, landmarks and the gameplay camera.
2. At gameplay scale, compare the subject with competing elements. Shape and value should carry any required identification across the target backgrounds. For a sprite sheet, align pivots and baselines. For tileable art, plan edge continuity as well as the distribution of distinctive marks across repetitions.
3. Preview an icon at the exact target pixel size on each background. For a tile, build a 3×3 repeat at 100% and inspect horizontal/vertical seams and the four-corner junction. For transitions, test every intended neighbor combination. Inspect transparent borders on both light and dark backgrounds. For animation, play the sequence with its intended timing.

**Example passage.** “Single top-down meadow ground tile for a 32×32-pixel cell, diffuse midday light and three compact grass values. Quiet center for a moving unit. Broken grass runs continue across opposite edges, with sparse blades of varied length and no dominant isolated flower.”

**Local correction.** If an obvious dark vertical stripe repeats every cell, inspect both the left/right edge join and the intra-tile distribution of dark blades. Fix the cause and rebuild the repeat. Verify file dimensions after export and test the engine's actual filter, atlas padding and camera zoom for edge bleeding. A large concept image can inform pixel art. Exact grids, alpha, animation timing and atlas configuration require asset-level verification. [Godot, using TileSets and terrain sets](https://github.com/godotengine/godot-docs/blob/master/tutorials/2d/using_tilesets.rst)
