# Elbow reporting wording audit

Reviewed 2026-09-26. This is a bounded source and reporting-content reconciliation, not clinical approval of the guide or anatomical assets.

## Source-supported correction

The [official Radiology Assistant elbow chapter](https://radiologyassistant.nl/musculoskeletal/elbow/mri-examination), under **Common Extensor Tendon** and **Common Flexor Tendon**, places their origins at the lateral and medial epicondyles. **Brachialis tendon / Chronic avulsion** describes the brachialis attachment and injury. **Tear of distal biceps tendon** warns that axial coverage stopping before the radial tuberosity can miss a tear. These support correcting the checklist's collective “insertions” wording, explicitly naming brachialis in the existing tendon field, and adding a distal-biceps acquisition-coverage prompt.

The chapter's **Tendon attachments** subsection calls the LUCL a tendon once, while **Lateral Collateral Ligament** identifies it as part of the ligament complex. That inconsistent wording must not determine tissue classification.

## Current implementation and scope

Before this change, Primer already classified `elbow.lateral_ulnar_collateral_ligament` as `ligament` and placed it in **LIGAMENT COMPLEXES**. No runtime relabelling of a tendon as LUCL is justified. The suitability matrix records its attachments and complete course as `not_identified`; the current Z-Anatomy elbow registry has RCL, UCL and annular objects but no separately identified LUCL. An absent mesh remains absent.

The actual reporting defect was narrower: “Assess common flexor/extensor, distal biceps and triceps at their insertions” conflated proximal common-tendon origins with distal insertions. The existing requirement inventory also already included brachialis tendon, but its checklist and worksheet did not name it. The correction retains the same five checklist headings and five reporting sections. It adds no indication, new structure or component target.

All **38 parent structures and 83 component requirements** remain unchanged, including source URLs, tissue classes, laterality, acquired-coverage conditions, modality limits and required representations. Only the matching report text references and checklist fingerprint are synchronized. Canonical SHA-256 of the ordered structure records excluding `report_refs`, before and after: `a159ef175d02aa323c240dea2ac20203fdbd8163c93346167e824d00ae9d3f06`.

The source-wording caveat is independently confirmed here. Its existing gate classification is not changed by this reporting correction. No mesh, image evidence, suitability finding, asset review or clinical-validation status is promoted. The existing coarse/source-material geometry limitations remain in [the suitability matrix](msk-elbow-wrist-suitability-matrix.json) and [geometry audit](msk-elbow-wrist-geometry-audit.json).

## Verification

Focused checks load the final catalogue guide and worksheet, require explicit epicondylar origins and brachialis assessment, verify distal-biceps axial coverage, reconcile the live report with its requirement snapshots, and compare the unchanged anatomy-scope fingerprint. This checks content consistency and preservation of scope; it does not validate clinical diagnostic performance.
