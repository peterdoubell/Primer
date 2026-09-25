# Radiology Assistant investigation reference

This is the current reporting-reference structure, superseding the earlier
96-module course-oriented index. The reference catalogue contains **136
investigations**, grounded in all **188 canonical Radiology Assistant articles**.
It follows the publisher's nine specialty headings. There are **22 MSK
investigations**; MRI shoulder and ultrasound shoulder are separate.

Thirteen curriculum topics without a foundation article are excluded from the
reference index and direct reference endpoint. Their learning records were not
deleted. Fixed coronary/prostate shortcuts were removed. Search and specialty
filters persist while returning from an investigation, and the compact back
control has a separate breadcrumb row and clear spacing above the title.

Each entry shows concise investigation/procedure wording and the exact source
article headings. The source's unusual `...` wrist archive heading is preserved
under the descriptive Foot and ankle cases investigation. Ninety-two scoped
guide overrides separate mixed examinations and diseases. Shared technique
sections are rebuilt from each investigation's own protocol, including genuine
fluoroscopic defecography and the separate renal cyst/solid mass workflows.

## Step-by-step reporting

Every investigation opens on a step-by-step walkthrough of its own report
template: 684 steps with finding phrases, normal statements, per-step
figures, measurement methods, a schematic 3D landmark and, for 40
investigations, highlighted source-mesh structures. Ten investigations whose
backing module showed the wrong anatomy carry a corrected 3D family. Details,
schema and validation are in [radiology-step-guide.md](radiology-step-guide.md).

## Visuals

The source-specific galleries contain **364 figures**, including 150 newly
selected, rendered and reviewed figures. Every investigation has a nonempty
gallery, and every figure belongs to an article assigned to that investigation.
Two bowel-ischaemia images are explicitly identified as video covers. Some older
publisher images are 370 pixels wide and remain at their native resolution;
resizing does not invent diagnostic detail.

The interactive viewer uses **96 registered BodyParts3D structures**, with
**660,024 triangles**, across **11 regions**. It includes six MSK regions plus
heart/coronaries, prostate and adjacent organs, renal tract, liver and brain.
Coordinates are preserved from the licensed source. Meshes total 16.94 MB and
load by region; the shoulder set is approximately 0.96 MB. Dataset attribution,
license and source limitations appear with the viewer. Fine structures absent
from the dataset are not invented. Other spatial explainers remain explicitly
labelled as simplified spatial guides.

A photorealistic shoulder-bone illustration was generated with the built-in
image-generation tool using the mesh view as reference. It is labelled as a
generated illustration and kept separate from clinical images. Prompt and
provenance are in `web/reference-media/README.md`. Earlier soft-tissue drafts
were not shipped. Detailed source diagrams remain credited to their publisher.

## Implementation and validation

- `data/radiology/reference-investigations.json`: source taxonomy.
- `primer/radiology_catalog.py`: strict source projection, scoped templates and figure selection.
- `investigation-overrides*.json`: investigation-specific clinical guides.
- `reporting-steps/*.json`: step-by-step walkthroughs, one file per specialty.
- `detailed-visuals.json` and `investigation-source-images.json`: reviewed galleries.
- `web/anatomy/bodyparts3d/`: licensed native meshes, hashes and attribution.
- `web/radiology-detailed-anatomy.js`: interactive source-mesh viewer.
- `docs/radiology-investigation-audit.json`: per-investigation source coverage.

Validation covers source-only coverage, specialty isolation, modality-specific
reporting, absence of inappropriate Bosniak classification for solid masses,
geometry file integrity, source attribution, and live rendering/control checks.
The initial targeted regression suite passed 639 tests; the two additional
scope tests also passed. Clinical content review remains a source review, not an
external clinical sign-off of the software or anatomy dataset.
