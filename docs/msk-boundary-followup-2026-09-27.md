# Fixed elbow and hip boundary record — 27 September 2026

This is a reporting-boundary classification, not anatomical or clinical
approval. It retains every structure, component, modality condition, required
representation and site-expansion obligation. Neither an image nor a mesh is
approved by this record.

## Elbow: source terminology

The [Radiology Assistant elbow chapter](https://radiologyassistant.nl/musculoskeletal/elbow/mri-examination)
was rechecked. Its Tendon attachments subsection uses tendon terminology for
the LUCL once; its Lateral Collateral Ligament subsection explicitly identifies
the LUCL within the ligament complex. The current Primer requirement classifies
the LUCL as a ligament and the effective worksheet places it in LIGAMENT
COMPLEXES. The reporting guide names the collateral components.

Therefore `historical_source_wording` is a documented source-interpretation
boundary, not an outstanding runtime tissue-classification defect. It remains
visible so source wording cannot later drive a tendon/ligament substitution.
The [earlier wording audit](msk-elbow-reporting-audit.md) independently corrected
common-tendon origins and named existing brachialis requirements; those changes
are not repeated here. All 38 parent structures and 83 components remain.
The missing separately identified LUCL mesh remains missing, with both
attachments and complete course still required.

## Hip FAI: acquisition conditions

The [Radiology Assistant FAI chapter](https://radiologyassistant.nl/musculoskeletal/hip/femoroacetabular-impingement-syndrome)
distinguishes radiographic osseous assessment from its MRI/MR-arthrography
examples of labral and chondral findings. The current Primer checklist and
worksheet explicitly condition labral, cartilage-lesion and periarticular
soft-tissue assessment on an acquired MRI, and offer not-assessed states.

Therefore `modality_condition_required` records a boundary that the effective
guide already implements. It is not a continuing unconditional radiograph
claim. All 20 parents and 50 components remain; relevant soft tissues still
require their own suitable representations. A radiograph-only illustration
does not satisfy their MRI requirements. The separate
[FAI wording correction](msk-hip-reporting-correction.md) remains in force.

## Exact-scope binding

Each documented boundary now records both its evidence-document hash and a
fingerprint of its investigation's report and anatomical definitions. The
fingerprint includes reporting checklists/templates, modality, laterality,
structures, component definitions, acquisition conditions and expansion rules.
It also includes the specific boundary claim and its classification. Other
issue records and the documentation/hash fields themselves are excluded to
avoid recursive hashing; review-status metadata are excluded. It is not a
review approval.

The five previously documented ankle, thoracolumbar and wrist boundaries retain
their original evidence document and classifications. Their current reporting
snapshots were checked against the effective guides before adding the same
scope binding. Their source conditions and anatomical requirements are not
waived or rewritten. The [binding inventory](msk-boundary-scope-bindings-2026-09-27.json)
records all seven scopes and evidence-document hashes.

Any subsequent change to a report or anatomical definition makes the boundary
classification stale until that exact scope is re-reviewed. Missing/invalid
bindings, unknown issues and unresolved reporting defects remain blocking.
Image, schematic, model, rights and anatomical-review gates remain independent.
