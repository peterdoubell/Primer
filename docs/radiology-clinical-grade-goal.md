# All-radiology clinical/commercial fidelity

The active objective covers **all radiology modules**: images, schematics and 3D models must faithfully represent every structure to be reported on. The standard sought is clinical/commercial quality at which certification could reasonably be expected; certification itself is not being claimed. This objective is not achieved.

The earlier [MSK work](msk-clinical-grade-goal.md) remains a sub-workstream. Its requirements, acquired sources, unresolved boundaries and pending reviews are retained. They do not define the limit of the expanded goal.

## Current scope

The effective application contains 137 reporting investigations across nine sections:

| Section | Investigations |
|---|---:|
| Abdomen | 41 |
| Breast | 6 |
| Cardiovascular | 11 |
| Chest | 11 |
| Head/Neck | 11 |
| Musculoskeletal | 22 |
| Neuroradiology | 17 |
| Pediatrics | 16 |
| More | 2 |

There are also 106 radiology curriculum nodes: 96 have reporting references and ten are foundational imaging lessons. Fourteen referenced curriculum nodes are not mapped into the investigation catalogue. All remain included for explicit scope reconciliation. A missing catalogue mapping does not exclude a module, and an investigation's coverage does not automatically establish coverage of its parent lesson.

`docs/radiology-fidelity-scope.json` preserves the current effective reporting contracts, templates, walkthroughs, sources and visual descriptors for every investigation, plus lesson/reference/practice/quiz/media contracts for every curriculum node. Contract hashes detect changed source requirements. These are scope records, not clinical approvals.

## Known gaps

- The 22 MSK investigations have a draft structure inventory with 5,292 representation obligations. It still has no verified complete requirements. Existing scope and modality conditions remain intact.
- The appendix investigation now has a first non-MSK draft: 56 reportable parts and 168 image/schematic/model obligations, with no verified bindings. Its full source/guide boundaries remain under review. See `appendix-fidelity-scope-2026-09-30.md`.
- The remaining 114 investigations require anatomical expansion into their reportable structures and substructures, including relevant site, laterality, developmental stage, modality, field-of-view and pathological-state conditions.
- All curriculum surfaces require explicit reconciliation with their own content and any linked investigations. Foundational/protocol lessons need a documented determination of applicable anatomical and technical requirements; they are not silently waived.
- The total all-radiology representation count is **unknown**. The 5,460 currently known obligations are a floor, not a complete denominator; requirements outside the expanded inventories are not zero.
- The current static reference inventory contains 536 distinct resources. Ninety-three have matching reviewed rights evidence; 443 are not cleared by this inventory. This does not mean every uncleared resource is necessarily unlicensed. Lesson media, procedural renderers, schematics and model geometry still require their own explicit provenance and fidelity review.

## Verification

`tools/check_radiology_fidelity.py` verifies that the saved scope matches the current application, runs the preserved MSK subaudit, and inventories reference figures across all reporting and curriculum surfaces. The default MSK-only rights collector remains unchanged for existing callers; the expanded audit explicitly selects all catalogue sections.

The `--require-complete` gate fails while the goal is unproven. UI flags such as a complete walkthrough, model availability, an image count or passing software tests cannot substitute for structure-level coverage and actual anatomical/clinical evidence. This initial all-radiology audit does not implement the still-missing non-MSK clinical approval work.

Current evidence: `docs/radiology-fidelity-audit-2026-09-30.json`. Update the scope snapshot whenever reporting or visual contracts change, without treating regeneration as approval. The native MSK CT work remains relevant to the broader objective. Its complete original archive and voxel-preserving export have now passed integrity checks; segmentation and anatomical review remain unfinished.

The first three non-MSK source figures are now present in the appendix reader, with licensed original-source provenance, preserved panels and three explicitly partial image candidates. No static frame supplies compression evidence, and the mixed US/CT composite has no CT structure binding pending localization review. See `appendix-source-review.md`. All changes remain local; complete anatomical and clinical validation is unfinished.

Native spine CT review now includes nine orthogonal sections and six boundary-face screens from the verified full array. Detailed osseous architecture is visible, while individual level identity, specimen orientation and side-boundary material remain unresolved. This evidence guides the next segmentation review without treating sampling resolution or source-title anatomy as complete coverage.

The native CT side-boundary contact was localized to a five-voxel peripheral cluster in two adjacent slices, with full-plane and unmarked-patch review. It does not demonstrate a recognizable bony boundary, but its material identity and whole-anatomy completeness remain unproven. Original voxels remain unchanged.

Neuroradiology inspection found registered ventricular meshes incorrectly highlighted for deep-grey nuclei and veins, and hemisphere meshes for spinal/optic targets. Fourteen steps now clear incorrect selections or state the limited context actually available. All reporting targets remain required. Desktop/mobile transition checks and 51 relevant tests passed. This corrects misleading presentation; the missing anatomy models and brain structure inventory still require completion. See `neuroradiology-atlas-scope-review.md`.

Official source tables and 23 dedicated brain OBJ components have now been acquired and checked, covering 15 gross source groups. Byte/CRC checks and coincident-position topology analysis passed; original source geometry remains unchanged. The reduced source resolution and unverified fine anatomical subdivisions remain explicit. These are candidates for further review, not clinical approval or complete brain coverage. See `brain-source-candidate-review.md`.
