# Reference study and review record

Use one row per observable feature. Give each reference a short local identifier and a role. Mark evidence as supplied by the user, observed by the reviewer, or unknown. If two references disagree, ask which governs the disputed feature before treating either as a requirement.

| Role | Inspect | Record as a transferable anchor | Allow to vary |
| --- | --- | --- | --- |
| Character | Face shape, silhouette, side-specific accessories, garment seams | “The crescent clasp sits on the wearer's left collar.” Disambiguate anatomical left from image left. | Pose and expression if the brief permits |
| Environment | Camera position, horizon, landmarks, occlusion order | “Viewed from the doorway, the tall window is behind the counter on the right.” | Weather or time of day when requested |
| Style | Value grouping, edge treatment, mark scale, palette relationships | “Shadows form one flat cool shape with a hard boundary.” | Subject identity and composition unless separately locked |

**Method.** First view the whole frame. Inspect distinguishing regions at full size, then return to intended display size to check readability. Describe visible evidence before inferring material or intent. A hidden hand is unobservable. A change in perspective can move landmarks across the frame. Compare character proportions only in similar views and poses. Keep protected anchors separate from the user's requested transformations.

**Example acceptance contract.** For a turnaround with three locked accessories, list each accessory, anatomical side, and whether it should be visible in each view. Count matched, violated, and unobservable instances separately. Report “2 matched, 1 occluded” with the individual entries. For framing, express margins as a fraction of image width or height and use the tolerance the brief calls for. A numerical mismatch can be intentional.

**Review record** (copy once per criterion)

    Candidate ID / digest:
    Reference ID / digest and role:
    Reviewer and actual viewing method:
    Criterion and tolerance:
    Status: matched | issue | unobservable | unassessed
    Region (side and landmark, or normalized x/y):
    Visible evidence:
    Expected appearance / source:
    Smallest proposed change:

Review each generation independently. Keep observations out of the final positive description if repeating the defect would encourage it. Store source imagery only when authorized. Provider prompts can disclose descriptive details even when no image is uploaded.

## Map sources to decisions before sending them

For each supplied file record its role and whether the current agent could actually open it. Separately record whether the generator will receive its pixels. An agent may be able to see three references while the selected generator accepts one. Describe the remaining visible anchors as text and disclose the reduced reference coverage. A description alone cannot verify identity.

For a character reference, distinguish persistent features (hair part, jaw silhouette, collar fastening) from the state of this shot (smile, head turn, wind). For clothing, name a seam, closure or overlap that can be found again. For the camera, identify eye level, near-to-far size changes and the side of the face visible. For lighting, follow a cast shadow or highlight to infer a likely source, and label that inference. Sample a color relationship in similarly lit regions before deciding that a new frame changed the wardrobe.

For a style reference, translate one visible decision at each scale that matters: large value groups, edge transitions and mark spacing at delivery size. If B supplies brushwork, a tree appearing in B need not enter the scene. When A and B disagree on a feature, follow the user's assigned role; clarify only unresolved conflicts that affect the deliverable.
