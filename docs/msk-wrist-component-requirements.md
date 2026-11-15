# Wrist component requirements

Reviewed against sources on 2026-09-26. Status: **anatomical requirement draft;
MSK radiologist review remains required. No asset is approved by this change.**

## Bounded change

Only the `required_parts` arrays of these existing parents were populated in
both `ra.wrist-instability` and `ra.wrist-fractures`:

- `wrist.scapholunate_interosseous_ligament`
- `wrist.lunotriquetral_interosseous_ligament`
- `wrist.triangular_fibrocartilage_complex`

The earlier arrays were empty, so the completeness gate treated a parent label
as the entire required target. The existing gate already rejects parent-only
coverage when explicit subparts exist; this change supplies the missing
anatomical granularity without changing that gate.

All existing structures, parent fields, report references, checklist snapshots,
report templates, investigation modalities and source-scope cautions are
preserved. Each new part has a stable ID beneath its existing parent and its
own supporting article URL. The same anatomy has the same IDs in both paths.

## SL and LT: three components each

Both ligaments now require:

| ID suffix | Required component |
| --- | --- |
| `.dorsal_component` | Dorsal component |
| `.volar_component` | Volar (palmar) component |
| `.proximal_membranous_component` | Proximal membranous component |

[Okoro et al., 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10381215/) describe
these three components for both ligaments. Their figures 20/23 distinguish the
parts schematically; figures 22/24 demonstrate normal dorsal SL and volar LT
appearances on MR arthrography. The dorsal SL and volar LT have different
functional importance, while the proximal membranous parts have variable
appearances. A single thick band or one normal ligament panel therefore cannot
prove coverage of the other portions. The source's normal-appearance caveats
must remain relevant during image review; a poorly seen membranous portion is
not automatically a tear.

These component requirements support the existing instability/avulsion
explanation. They do not add a patient-specific ligament-integrity field to a
radiographic report.

## TFCC: gross components and clinically distinct attachments

Under `wrist.triangular_fibrocartilage_complex`, the required suffixes are:

| ID suffix | Required target |
| --- | --- |
| `.articular_disc` | Articular disc (TFC proper) |
| `.radial_attachment` | Radial attachment |
| `.ulnar_styloid_attachment` | Ulnar styloid attachment (superficial lamina) |
| `.foveal_attachment` | Ulnar foveal attachment (deep lamina) |
| `.dorsal_radioulnar_ligament` | Dorsal distal radioulnar ligament |
| `.volar_radioulnar_ligament` | Volar (palmar) distal radioulnar ligament |
| `.dorsal_capsular_attachment` | Dorsal capsular attachment |
| `.volar_capsular_attachment` | Volar capsular attachment |
| `.ulnolunate_ligament` | Ulnolunate ligament |
| `.ulnotriquetral_ligament` | Ulnotriquetral ligament |
| `.ulnocapitate_ligament` | Ulnocapitate ligament |
| `.ulnomeniscal_homologue` | Ulnomeniscal homologue |
| `.ecu_subsheath` | Extensor carpi ulnaris subsheath |

[Cerezal et al., 2026, anatomy section and figure 1](https://link.springer.com/article/10.1186/s13244-026-02356-8)
support this gross decomposition. Separating disc, radial/ulnar attachments,
radioulnar ligaments, capsular attachments and peripheral supporting structures
prevents a disc-only mesh from being counted as the whole TFCC. Foveal and
styloid attachment requirements remain distinct; an ECU tendon representation
does not satisfy its subsheath. This is an anatomical distinction, not an
implementation of the paper's proposed injury classification.

The current mixed Cerezal figure has clinical MRI and drawing panels. Some
ulnocarpal components are established only by the schematic panels in that
asset. The requirements do not relabel those drawings as direct MRI evidence
or assume that all listed structures are adequately depicted by one composite.
The earlier [healthy-volunteer 7 T/3 T study, figure 2](https://link.springer.com/article/10.1007/s00330-021-08165-5/figures/2)
provides additional reference images of the radial, styloid and foveal
attachments; it likewise does not certify whole-complex coverage.

This bounded change does not introduce arterial microbranches, histological
zones, innervation, Sharpey fibres or four-way ulnomeniscal-homologue subdivisions
as new report targets. The prestyloid recess remains an adjacent normal landmark
for source-image interpretation, rather than a newly required TFCC tissue
component. Additional detail would need a separate reporting-scope review.

## Modality and reporting boundaries remain intact

Both parents and every resulting leaf retain their existing examined-side
condition. Direct clinical-image evidence remains restricted to **MRI and MR
arthrography** through the unchanged parent `modality_scope`. Their unchanged
condition explicitly states that routine radiographs provide indirect
alignment/avulsion signs, not SL/LT/TFCC fibre continuity.

`ra.wrist-instability` remains **Radiography**. Its component requirements remain
linked to the existing Carpal Angles and Bones checklist rows. `ra.wrist-fractures`
remains **Multimodality**, with its existing radiographs/CT reporting scope and
Articular Surface/Carpal Alignment links. Those fields concern alignment,
congruity and avulsion clues, not a direct soft-tissue verdict. Source scope is
retained from [Radiology Assistant: carpal instability](https://radiologyassistant.nl/musculoskeletal/wrist/carpal-instability)
and [wrist fractures](https://radiologyassistant.nl/musculoskeletal/wrist/fractures).

Schematic and 3D components explain anatomy; they cannot replace an acquired
MRI/MR-arthrogram examination or establish a patient's ligament integrity.
Conditional requirements do not imply that every wrist radiograph needs all
soft-tissue components to be directly visible.

## Verification

`tests/test_msk_wrist_components.py` checks:

- Exact bounded component IDs and source citations, shared across both paths.
- Preservation of the MRI/MR-arthrogram conditions, laterality and report links.
- Existing reporting snapshots against the effective catalogue.
- Actual gate behavior: an asset naming only the three parent structures leaves
  every new component missing; the test fixture grants no clinical approval.

The new tests, existing scope-correction tests and fidelity-gate tests pass:
**38 passed**. A one-time structural diff also verified that resetting just the
six changed arrays reconstructs the complete pre-change requirement object.

There are 19 component targets per wrist entry: 3 SL, 3 LT and 13 TFCC. Replacing
three parent-level targets with those leaves adds 16 targets per path. Across
the complete inventory, required leaves change from 1,658 to 1,690, and the
three-representation requirement count increases by 96. These counts describe
more precise requirements; they do not claim completed assets or validation.

## Reviews bind to representation scope as well as bytes

The fidelity gate now requires `review_scope_sha256` in **both** the anatomical
and visual review records, alongside the existing file `sha256`. The scope
fingerprint covers every non-review asset field, including evidence ID, kind,
exact structure/investigation bindings, panel selection, modality, observed
structures, context, source and license claims. The same composite figure bytes
cannot transfer an MRI-panel approval to its schematic panel or another anatomy
claim. New metadata fields are covered automatically rather than needing an
allowlist update.

The fingerprint also covers the matched current parent/component definitions,
inherited conditions, laterality, modality boundaries, report references,
investigation/reporting context and inventory conventions. Requirement review
flags, reviewer metadata and review timestamps are excluded, preventing the act
of approving an unchanged inventory from invalidating its anatomical scope.
Unrelated structures and investigations do not invalidate the asset's review.
Canonical JSON ignores object-key order; declaration order inside lists remains
part of the conservative review target.

`review_scope_fingerprint(asset, requirements)` and the audit JSON's
`review_scope_sha256` map expose the current target for a review packet; neither
is an approval. Changed claims or definitions require a new review against that
target, not automatic replacement of stale review fingerprints. Existing real
evidence records have not been approved or rewritten. The gate, wrist-component
and scope-correction tests pass (**66 tests**), including changed anatomy,
modality and report conditions, shared-byte panel separation, unchanged scope,
and independent inventory-review bookkeeping.
