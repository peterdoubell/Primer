# NIH mediastinal node source acquisition and cross-format review

MED_LYMPH_001 from [TCIA CT Lymph Nodes](https://www.cancerimagingarchive.net/collection/ct-lymph-nodes/) now supplies the complete converted CT series, its DICOM SEG and the original manual NIfTI mask. Source version 5 was released on 2023-03-31. CC BY 3.0 applies to these released data; source-page/API fingerprints, mask-member CRC, byte identities and required citations are preserved in the review folder. This is a separate source case, not a new acquisition or label correction for LNQ case_0571 or NSCLC-Radiogenomics R01-001.

All 666 original CT files (349,917,034 uncompressed bytes) and the one SEG file (972,470 bytes) passed the publisher per-file MD5 manifests and ZIP CRC checks. Independent SHA-256 fingerprints bind every file/archive. The manual mask was acquired from the original source ZIP, CRC checked and verified byte-identical to its extracted member. Its archive SHA is a local fingerprint, not a claimed publisher whole-archive checksum. Downloads completed and no source acquisition process remains live.

The supplied mask grid is 512 × 512 × 666 at 0.853515625 × 0.853515625 × 1 mm spacing. Original qform and sform matrices agree exactly. Every CT position was compared with its corresponding original mask-grid position. All positions agree within 0.000006104 mm, without fitting or changing either source. Decimal serialization causes observed CT step values between approximately 0.999990 and 1.000004 mm, rather than mathematically exact ones. Missing, duplicated or physically displaced planes are rejected by comparison against each original expected plane.

The SEG pixel-spacing values differ by 0.000000025 mm and agree at the original NIfTI float32 precision. These differences are recorded, not used to infer scanner accuracy or anatomical registration. The collection states that CT DICOM files were converted from Analyze/NIfTI volumes. The converted CT lacks original slice-thickness tags and scanner/protocol information. Thus this is a finer **supplied slice grid** than LNQ's 2.5 mm grid, not proof of finer original acquisition resolution, a particular contrast phase or calibrated intensity accuracy. No source resampling or invented finer anatomy was introduced by this work.

The 29 encoded SEG frames reference their exact CT source instances and match all original mask labels with zero pixel differences. Every positive original-mask voxel is retained:

| Original label | Positive voxels | Occupied source planes | Interpretation status |
|---|---:|---:|---|
| 1 | 2,701 | 19 | Source-defined label, not an independently verified node/station |
| 2 | 73 | 1 | Single-plane annotation; complete 3D extent unproven |
| 3 | 1,732 | 9 | Source-defined label, not an independently verified node/station |

All three SEG entries are manually coded mediastinal lymph node (SCT 62683002). Numeric labels are not silently converted into clinical individual-node IDs. Original label 2 is retained in full; no tiny-label pruning, thickening, connection to label 1, anatomical node-volume claim or closed-surface promotion is performed. The three numeric selections are disconnected in the source under both six- and twenty-six-neighbour connectivity, with no cross-label face contacts. That does not establish anatomical node count, an annotation error or the full extent of any real node.

The [collection source](https://www.cancerimagingarchive.net/collection/ct-lymph-nodes/) explicitly warns that manual segmentation mask indices do not align with the independently produced centroid annotation indices. No centroid annotation file was acquired or mapped. The source collection's non-cancer lymphadenopathy classification does not prove each case or annotated node is benign; diagnosis, histology and station boundaries remain unverified. This source cannot be credited as a lung-cancer nodal-metastasis example merely because it depicts nodes.

Marked/unmarked native axial, coronal and sagittal detail views are retained for every original label at two display windows. The three marked figures were inspected directly. Per-label crop bounds, source plane indices and image hashes are preserved. These limited sections support source review, not complete anatomical boundary approval. Original scanner lineage, all relevant acquired/unlabelled anatomy, station-specific adjacent landmarks and diagnostic context still require review.

Eight scientific checks passed for original-grid plane validation and source archive integrity. They distinguish small declared-coordinate serialization differences from missing, duplicated or displaced planes and preserve complete source checksums. Complete CT/SEG/NIfTI correspondence was also verified on the acquired files. No runtime representation, model or clinical fidelity binding was added. The full all-radiology goal remains active and unproven; the known floor remains 8,163 obligations and the complete denominator remains unknown.

## Reader source-image integration, 2026-10-02

Three unmarked source CT figures are now packaged in the local mediastinal reader. Each preserves its numeric original mask-label identity, source attribution and copyright version, original-source section/crop provenance and pixel dimensions. The single-plane label has an explicit visible extent warning. Scanner thickness, phase, diagnostic identity, named station and full anatomical extent remain unverified. No source model, malignancy assertion or negative diagnostic finding is added.

The catalogue validates the known dataset/case, publisher MD5 verification record, original-mask comparison, fixed source shape, actual licence, preserved provenance hash and figure pixel contract. Licence relabelling, invented publisher figure numbering, changed provenance or dimensions are rejected. All three assets are intentionally unbound to structural requirements; rights clearance alone cannot provide anatomical coverage. The 978 mediastinal obligations remain missing.

Desktop and mobile reader checks passed: all three images and source-volume/licence links appear; the older key-image example remains; the single-plane warning is visible; the native full-size image is 1800 × 1200; the 390 px mobile document has no horizontal overflow. API and image requests returned 200 and browser runtime errors were empty. Screenshots and `reader/browser-checks.json` preserve the evidence. All owned QA processes were stopped.

122 relevant tests passed. The full all-radiology known floor remains 9,141, with 109 investigations still unexpanded and no clinical readiness established. Static figure rights inventory is now 541 resources, 98 cleared and 443 unverified. This integration is local and undeployed.
