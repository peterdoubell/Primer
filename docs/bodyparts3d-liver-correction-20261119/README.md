# BodyParts3D liver atlas: segments VII and VIII and the portal vein corrected (2026-11-19)

## The decision

The body-reader binding pass of the same day (`docs/body-reader-model-bindings-20261119`) decoded the liver meshes of the
BodyParts3D 4.0 atlas and found three whose labels did not match their geometry. The project owner asked for them to be
fixed. The 3D tab of the two liver investigations (`ra.liver-masses`, `ra.liver-lirads`) shows this atlas.

## What was wrong

BodyParts3D coordinates are in millimetres: −X is the body's right, −Y is anterior, +Z is up.

| Label the app showed | What the mesh was | Evidence |
| --- | --- | --- |
| hepatovenous segment vii (`FJ2409.bin`) | a second mesh of segment VI | Its bounds equal those of segment VI (`FJ2822.bin`) to within 0.325 mm, and its vertices lie a median 0.8 mm from segment VI's and 31 mm from the true segment VII's. The BodyParts3D 4.3 object table lists FJ2409 as hepatovenous segment VI. |
| hepatovenous segment viii (`FMA15746.bin`) | segments VII and VIII in one mesh | The mesh united objects FJ2823 and FJ2824, two separate pieces. FJ2823 lies posterior and superior, where segment VII lies. The 4.3 table lists FJ2823 as segment VII and FJ2824 as segment VIII. |
| trunk of portal vein (`FMA14329.bin`) | the left and right portal trunks | The mesh united objects FJ3102 and FJ3122. The official 4.0 table lists them as the trunk of the left and of the right portal vein. "Trunk of portal vein" is the class of both, and read as the main portal trunk. |

So the liver view showed no true segment VII, and showed segment VI twice.

The first two are errors in the official 4.0 concept table (`isa_element_parts.txt`). The third is not: the table is right,
and the atlas had chosen the class instead of its two members.

## What changed

`tools/build_detailed_anatomy.py` rebuilds the atlas from the official archive:

- **Segment VII** is object FJ2823 (`FJ2823.bin`), and **segment VIII** is object FJ2824 (`FJ2824.bin`). The builder states
  these two corrections to the official table, and stops if the table changes under them. The manifest records the official
  assignment and the reason under `source_correction` for both meshes.
- **FJ2409 is no longer delivered.** Segment VI stays `FJ2822.bin`.
- **The portal vein is three meshes**, each a concept of the official table:
  - the pre-hepatic portal vein (`FJ3082.bin`), which is the main trunk;
  - the trunk of the right portal vein (`FJ3122.bin`);
  - the trunk of the left portal vein (`FJ3102.bin`).

The atlas has 98 meshes instead of 96. The reporting steps of the two liver investigations highlight the corrected meshes:
their part lists name `FJ2823` and `FJ2824` instead of `FJ2409` and `FMA15746`, and the three portal meshes instead of
`FMA14329`.

## What was checked

- **The same geometry.** Segments VII and VIII and the two portal trunks are split, not rebuilt. Joining `FJ2823.bin` and
  `FJ2824.bin` in source order reproduces the removed `FMA15746.bin` byte for byte, and the two trunks reproduce
  `FMA14329.bin`. A test repeats this from the delivered files.
- **Positions.** Segment VII lies above segment VI and behind segment VIII. Segment VIII lies above segment V and in front
  of segment VII. All four lie on the body's right, and segments II and III on its left. Each of the two meshes is one
  connected piece. No two segment meshes now have the same bounds.
- **The portal vein.** The three meshes meet at the top of the main vein: they come within 0.6 mm of one another there.
  The main vein rises 49 mm to that point. The right trunk runs to the body's right, and the left trunk to its left.
- **The tables.** The quoted rows of the official 4.0 table are stored in `evidence/`, with the hash of the complete file.
  The BodyParts3D 4.3 object table was already stored (`docs/cardiac-wall-context-review-20261016/obj2FMA-4.3.html`).
- **Nothing else changed.** The other 93 meshes are byte-identical, and every region except the liver is identical. Before
  the change, the builder was run unmodified and reproduced all 96 delivered meshes and the manifest byte for byte.
- **The app.** The liver view was opened in a browser after the change (see the pull request).

`review.json` holds the table rows, the measurements, and the hashes of the removed and added meshes.

## The source registry is unchanged

`data/radiology/source-anatomy-references.json` pins the hash of this atlas's manifest for the whole-brain reference of
`ra.brain-anatomy`. Many evidence records and review guards pin that registry in turn. Changing its line would have
re-opened reviews of unrelated atlases that this change does not touch.

The registry therefore keeps the reviewed hash. `primer/source_mesh_integrity.py` names the corrected manifest as the one
successor of the reviewed manifest, and the catalogue accepts either. A test restores the reviewed manifest from the
corrected one with the exact inverse and checks that:

- only the liver region and the three removed and five added mesh records differ;
- every brain mesh is the same file as before;
- any other manifest is still refused.

## Bindings

The evidence records for these meshes are part of the body-reader pass, which was re-run on the corrected atlas. Segments
VII and VIII and the two portal trunks are bound. The pre-hepatic portal vein is recorded as not bound, because the liver
requirements split the main portal vein into lumen and wall.

## Limits

- This compares source tables and mesh positions. It is not a radiologist review, and nothing here is anatomically approved.
- A source label boundary is not a validated anatomical boundary. The trunk of the left portal vein is one source object;
  its transverse and umbilical portions are not separated.
- The atlas is one adult male reference body.

## Files

- `review.json`: the decision, the table rows, the measurements and the mesh hashes.
- `inverse.json`: the exact line inverse of the five pinned text files that changed.
- `evidence/bodyparts3d-4.0-isa-element-parts-excerpt.json`: the quoted rows of the official table.
- `tools/liver_atlas_compatibility.py`: restores the earlier bytes, and the earlier reporting contracts, for the older
  history checks. Three older links call it first.
- Tests: `tests/test_bodyparts3d_liver_correction.py`.
