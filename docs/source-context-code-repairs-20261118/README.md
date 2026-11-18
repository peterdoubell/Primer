# Figure-record context codes repaired (2026-11-18)

## The decision

The finding-figure pass (`docs/finding-figure-bindings-20261118`) found 404 caption matches that the
fidelity checker refused because of a malformed code in the figure record. On 2026-11-18 the project
owner asked for those codes to be repaired.

## What was wrong

For every binding, the checker reads the figure's `source_context`: setting, side, life stage,
extent, depicted state, panel selection and panel states. Some packaging scripts wrote these values
in their own words, such as an extent of `source_local_views`, a state with capital letters, a life
stage of `child` or a side of `not_applicable`. One unreadable value made the checker refuse every
binding of the figure. 256 stored figures and 3D models carried one, and none of them had a
binding.

## What was repaired

250 records in the evidence ledger, with 318 changes:

| Rule | Changes | Example |
| --- | --- | --- |
| An extent in the packaging script's own words becomes `local` | 132 | `source_local_views` → `local` |
| A state code with capital letters is written in lower case; the figure shows what the code says | 82 | `source_cardiac_CT_case` → `source_cardiac_ct_case` |
| A state that did not say what the figure shows is replaced after the caption was read | 36 | sinus variants → `normal_variant`; the normal uterus → `normal_anatomy` |
| A side outside the vocabulary becomes `not_reported` | 30 | `not_applicable` on oesophagus and swallowing figures |
| A life stage outside the vocabulary | 13 | `child` → `immature`; `mixed_or_not_reported` → `not_reported` |
| A sentence stored where a context record belongs becomes a record | 12 | BodyParts3D sella objects: `adult`, sentence kept as `source_note` |
| A figure-level state and its panel state said the same thing in different words | 5 | epilepsy case images |
| The record's own selected panels show different states, so the figure is `mixed` | 4 | benign and malignant nodes |
| An illustration has the setting `conceptual` | 2 | `illustration` → `conceptual` |
| A side the record called publisher-assigned, which the caption states | 2 | epilepsy figures 1 (right) and 6 (left) of PMC4557590 |

The checker now reads 241 of these records without an issue. On the 105 captioned figures among them,
375 caption matches (318 structure, 57 finding) are no longer refused and can be reviewed for binding.
The 69 3D models can be reviewed too. Bound structures stay at 739 of 57,985, because this pass binds
nothing.

## How each value was chosen

- Vocabulary repairs follow the ledger's own conventions. 745 records record no side as
  `not_reported`, 56 schematics have the extent `local`, 48 have the setting `conceptual`, and 18
  records use the state `mixed`.
- Where a code might hide what a figure shows, the caption was read and the figure looked at. All 21
  cardiovascular CT figures and all 16 orbit MRI figures show disease, so lower-casing keeps their
  meaning. Of the 17 sinus figures, 15 show anatomical variants of operative anatomy, one shows normal
  anatomy (the anterior ethmoidal arteries) and one shows atelectasis of the maxillary sinus.
- A normal figure now carries a normal state, so the checker refuses it as a pathology example, as
  intended. Lower-casing `published_normal_T2_zonal_anatomy` would have let it pass.
- A side is set only where the published caption states it. Where "(left)" and "(right)" name image
  columns, as in epilepsy figure 4 of PMC8353251, the side stays `not_reported`.

## What was not changed

- **Empty panel selections (6 figures).** These figures select no panel, in both the ledger and the
  app's catalog. Choosing which panels to credit is a content decision for a binding review, so the
  checker still refuses them.
- **Context-only panels (9 figures).** Five appendix figures, three prostate MRI planes and one
  anorectal figure mark their panel as context only, or as "case or illustration", and that disagrees
  with their figure-level state. The restriction is kept. Their other codes were repaired, and the
  checker still refuses them.
- **The app's figure catalog.** `data/radiology/radiology-open-images.json` keeps the original codes.
  The app reads none of the repaired fields, and the catalog copy is pinned by reader digests, lesson
  contracts and the saved fidelity scope. `catalog_view()` in the tool turns a repaired ledger record
  back into the catalog's copy, so checks that compare the two still compare like with like.
- **The packaging scripts.** They are historical. Re-running one would rewrite its records with the
  old codes and drop the later passes.

## Limits

- This is a check of records against captions and figures, not a radiologist review. No binding was
  added and nothing is approved.
- A readable code is not evidence that a figure fits any requirement. Each of the 375 matches still
  needs the same review as a binding pass.

## Files

- `review.json`: every change with its old value, new value and rule; reasons for the reviewed
  decisions; the records left unchanged; the records still refused.
- `inverse.json`: exact byte edits and hashes for the evidence file.
- Tool: `tools/anatomy_sources/repair_source_context_codes.py`.
- Tests: `tests/test_source_context_code_repairs.py`.
