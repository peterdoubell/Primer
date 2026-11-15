# Leeds spine source audit — 30 September 2026

The [IMBE spine collection](https://archive.researchdata.leeds.ac.uk/1619/) provides cadaveric CT data under explicit CC BY 4.0 terms. The source README states ethical approval for public imaging release and supplies donor and degeneration metadata. This supports lawful source acquisition, not clinical approval of derived anatomy.

## Donor 3: complete download, insufficient demonstrated anatomical extent

The [L4–L5 donor-3 archive](https://doi.org/10.5518/1923) was acquired in full: 1,252,310,016 bytes, MD5 `f114c0c0b541506be5d2cf2ae954148c`, SHA-256 `c41000c0595489e13e76d9cb8617c5d9862dd47b8488cabe3ad855c7f36ac774`. The MD5 matches the repository's Content-MD5, and all 146 ZIP member CRCs passed. Archive order is not physical slice order; frames were sorted using DICOM positions and orientation.

All 146 frames have 2508×2508 signed 16-bit pixels. DICOM pixel spacing, slice thickness and measured adjacent-plane spacing are 0.05 mm. The frame centres span only 7.25 mm; including the recorded slice thickness gives a 7.30 mm volume extent. There is no in-plane origin drift and no internal missing step in this published stack. Those facts do not establish that the published stack is the complete intended anatomical scan.

First, middle and last native planes were reviewed. They predominantly show a circular holder, wrapping-like structures and a homogeneous porous region. Material identity is not independently established, and no claim is made that every voxel in the archive lacks bone. The review does not establish complete L4–L5 anatomy. This slab is therefore not promoted as a whole-spine model, and no missing tissue is fabricated or capped.

The source table identifies donor 3 as male, 65 years old, with left/right L4–L5 facet grades 3/2. These are published specimen facts, not diagnoses inferred from the sampled pixels. Display windows use the DICOM slope/intercept. The CT Image Module establishes HU output semantics for the qualifying metadata described below; independent physical calibration remains unverified.

The [native audit](msk-leeds-spine-source-review/native-audit.json) records every frame's geometry, anonymized UID fingerprints, member checksums and three preview-plane records. Sample pixel arrays matched an independent little-endian signed-16-bit decode. The reproducible audit is `tools/anatomy_sources/audit_leeds_spine_source.py`.

## Donor 1: complete acquisition and native export

The [L4–S1 donor-1 archive](https://doi.org/10.5518/1921) contains 1,652 DICOM members and totals 13,325,473,922 bytes. Its repository Content-MD5 is `bdf6b02ec6d6965f0f13a6f735769efc`. The ZIP directory was read through validated HTTP ranges. The complete archive now matches the repository Content-MD5; all 1,652 member CRCs passed. Its SHA-256 is `5b6c8c8e42c3b43ad2a5b81199967e921959af29702912e559d4ba6979ef8fbd`.

First, middle and last frames were selected before visual inspection and acquired intact with member CRC checks. They have 2008×2008 pixels and 0.05 mm pixel spacing/thickness. The sampled endpoint centres span 82.55 mm. The middle frame visibly contains bone architecture, making this a more promising source for native 3D review. These three frames cannot prove regularity or complete anatomical coverage of the entire stack.

The source table identifies donor 1 as female, 77 years old, with facet degeneration at both supplied levels. This is a cadaveric degenerative reference, not a normal in-vivo template. Complete sampling, specimen orientation, anatomical boundaries, segmentation fidelity and reportable substructure identity still require review.

The full archive was acquired with `tools/anatomy_sources/acquire_leeds_spine_donor1.py`. It records verified ranges, rejects changed source objects, preserves resumable progress and promotes the final file only after whole-object MD5 validation. The active process must be checked before any resume. Raw data stay in ignored `.research/` staging. No runtime model or completed clinical binding has been created.

## Native volume preservation

`tools/anatomy_sources/native_dicom_geometry.py` validates physical plane order and constructs a transform from `[slice, row, column]` indices to the source DICOM LPS coordinates. It uses measured plane spacing independently of acquisition thickness. Duplicate planes, irregular spacing, changing matrix sizes/orientations and shifted origins are rejected rather than silently repaired. The actual donor-3 transform is recorded in `msk-leeds-spine-source-review/native-index-transform.json`; a regular grid does not establish complete anatomical extent.

`tools/anatomy_sources/export_leeds_spine_native_volume.py` is prepared for use after complete acquisition and audit. It requires the audited archive hash, every source member, original DICOM geometry and per-frame calibration. Original signed 16-bit samples are copied without resampling or intensity conversion, then independently reloaded and checked plane by plane. Partial output is not finalized. It creates a research volume, not segmented tissues or clinical bindings.

Nine geometry tests passed, including a rotated anisotropic stack and the real donor-3 coordinates. Three scientific end-to-end checks passed: exact signed-voxel preservation and physical ordering, rejection of altered audit coordinates, and rejection of a frame list that silently omits an intermediate plane. These checks use a clearly synthetic miniature CT fixture. The donor-1 export has now completed after the source audit, as recorded below.

## Other source findings

LumASe's original numeric label dictionary remains unproven; the author repository is unchanged at the previously inspected commit. The distinct LumbarSR candidate has conflicting primary dataset licence statements, recorded in [its source review](msk-lumbarsr-source-review.md), and has not been imported for commercial use.

Attribution: © 2026 University of Leeds; Hutchinson, Zantiba, Bhattacharya, Wijayathunga and Mengoni, DOI 10.5518/1923 and DOI 10.5518/1921; collection DOI 10.5518/1835. CC BY 4.0. Review previews are windowed displays of original DICOM pixel values, without spatial resampling. No endorsement or clinical approval is implied.

The geometry validator now also bounds the error of every source plane against the complete volume affine. Small locally acceptable step variations cannot accumulate into a displaced volume. The derived slice normal is normalized for physical distance while the original in-plane direction values are retained, including rounded DICOM cosines. Eleven geometry tests and three end-to-end export checks pass; the real donor-3 plane residual is at floating-point roundoff scale.

A local follow-on process is now attached to the confirmed running donor-1 acquisition. It waits for verified download completion, then runs the original-archive audit and native-voxel export in sequence. It stops on download failure, source-process loss or a failed validation; it does not restart acquisition, resample anatomy or promote a runtime model. Process handles and checkpoint locations are retained in ignored research staging.

Optimized-mode regression checks exposed that Python assertions could be removed, allowing altered coordinate metadata or an incorrect source hash through the exporter. Audit and export integrity conditions now raise explicit errors. The two reproduced failures are fixed; an additional optimized-mode check rejects an unrelated valid CT archive before it can be attributed to Leeds. Eleven geometry tests and six end-to-end checks pass.

## Intensity-unit semantics

[DICOM PS3.3 C.8.2](https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.8.2.html), observed as edition 2026d, specifies HU output for original, non-localizer legacy CT when multi-energy acquisition is absent or NO. The Rescale Type tag may be omitted in this situation. All 146 donor-3 frames and the three acquired donor-1 samples satisfy those metadata conditions. Their missing optional tag therefore does not by itself make the output units unknown. The source-header evidence and standard snapshot hash are recorded in `msk-leeds-spine-source-review/intensity-units-review.json`.

The audit and native-volume manifest retain the unit interpretation and its basis per frame. Derived images, localizers, multi-energy images without explicit units and non-CT objects do not inherit this default. Contradictory declarations are rejected. This establishes the standards-based meaning of the stored rescale parameters; it does not independently test scanner calibration, bone-mineral density or clinical accuracy. Twenty geometry/unit tests and seven end-to-end export checks passed, including rejection of metadata that attempts to relabel unchanged voxels with different units.

## Completed donor-1 native preservation

All 1,652 frames passed geometry and intensity-context checks. The native array is 1652×2008×2008 signed 16-bit samples at 0.05 mm spacing, with no resampling or intensity conversion. Every exported plane matched an independent source decode and a fresh on-disk reload hash. The maximum source-plane/affine residual is approximately 2.84e-14 mm. Array SHA-256: `202fbfdc8ca2af553995e0b2ab5fe7a1d70787259690e0d6cb32d23fc5cea3bb`.

The original and native array remain in ignored research staging. `msk-leeds-spine-source-review/donor1/native-audit.json` and `donor1/native-export-summary.json` retain the evidence. Source anatomical orientation, complete tissue boundaries, segmentation and clinical fidelity remain unapproved; no runtime 3D model has been promoted. The acquisition/export processes completed successfully and must not be restarted merely because their former process handles are gone.

## Native multiplanar coverage review

Nine prespecified quarter/middle/three-quarter sections across all source axes now provide an orientation/coverage review at physical aspect ratio. The original 13.3 GB array hash was rechecked before inspection. All six volume faces were screened at three numerical thresholds; these probes are not validated tissue masks. Source-plane hashes, exact indices, display window and boundary counts are in `donor1/native-plane-review.json`.

The views show detailed osseous architecture, but anatomical level assignment remains unresolved. Two dominant body profiles appear in the selected longitudinal planes; the nominal L4–S1 source title does not independently identify them, and this limited plane selection is not an exhaustive count. Five samples exceed 1000 HU on one side face. Their material identity remains unresolved, so clipping-free complete anatomy is not inferred. See `donor1/coverage-review.json`. No segmentation, closed surface or clinical model has been promoted from this review.

## Side-boundary contact localization

The five >1000 HU boundary samples were reproduced by a sequential inspection that rechecked the complete native-array hash. They form one six-connected five-voxel cluster at column 2007, rows 1474–1476, slices 1497–1498. Full source planes and unmarked local patches were inspected. The cluster lies at the extreme peripheral field, away from visible osseous profiles in those planes; it does not show a recognizable cortical boundary. Its exact material identity is still unproven.

This resolves the location of the numerical contact, not the entire clipping question. No voxel is removed, relabelled or filled, and complete anatomy is not inferred. Exact source indices, LPS coordinates, raw values, source-plane hashes and review figures are retained in `donor1/side-boundary-contacts.json` and `donor1/side-contact-patch-review.json`.
