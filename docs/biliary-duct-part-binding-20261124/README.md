# Binding the two duct parts of the biliary reader (2026-11-24)

## The decision

The project owner asked for the two duct parts to be bound. They are the two parts of BodyParts3D 4.3 object FJ3079 that
the biliary reader shows since the division of the same day (`docs/bp3d-biliary-duct-partition-20261124`).

**One part binds. The other does not.** The rules are those of the body-reader pass of 2026-11-19, unchanged.

| Part | Result |
| --- | --- |
| Common hepatic duct (above the cystic duct) | Recorded, and bound to `gallbladder.ducts.common_hepatic_duct` in `ra.ultrasound-gallbladder` |
| Common bile duct (below the cystic duct) | Not bound |

Bound structures and parts go from 1,404 to 1,405 of 57,985. Coverage is partial, and nothing is anatomically approved.
No radiologist has reviewed the division or the binding.

## Why the upper part binds

- The source's own label for the object is "Common hepatic duct". It fits the upper part, so the rule that a mesh's own
  label names the requirement is met.
- The gallbladder ultrasound investigation shows the biliary reader, and its ductal distribution names the common hepatic
  duct as a part of its own.
- The record's basis says that the mesh is a part of the source object, where and when it was divided, and that the
  division is unreviewed.

## Why the lower part does not bind

- The source's label does not name it. Its name comes from this project's division.
- Every requirement of the reader's two investigations that names the common bile duct asks for less than the whole duct:
  - `ra.biliary-duct-pathology` splits it into supraduodenal, retroduodenal, intrapancreatic and intramural segments,
    each with a lumen, a wall, margins and a junction. The source object marks none of these segments.
  - `ra.ultrasound-gallbladder` asks for the visible segment and the distal segment.
- A whole is not bound to its parts, and a BodyParts3D surface shows neither lumen nor wall alone.

`review.json` lists each candidate requirement with its reason under `candidates_not_bound`.

## What would let the lower part bind

- A requirement that names the common bile duct as one structure in an investigation that shows this reader. The liver
  investigations have one, but they do not show the biliary reader.
- Or a reviewed division of the duct into its four segments.

Both are decisions for the project owner and an anatomical reviewer, not for this pass.

## Files

- `tools/anatomy_sources/bind_biliary_duct_part.py`: checks the row with the body-reader pass's rules, adds the record as
  one literal edit and provides the exact inverse.
- `review.json`, `inverse.json`.
- `data/radiology/radiology-asset-evidence.json`: one record added.
- `tools/anatomy_sources/bind_body_reader_models.py`: its history link peels this newer link first.
- `docs/body-reader-model-bindings-20261119/review.json`: a second amendment.
