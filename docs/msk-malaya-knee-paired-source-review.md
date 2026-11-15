# Malaya knee paired-source review — 26 September 2026

**Disposition:** retain the scans offline for research/source-correspondence review. The actual MRML reference provides useful gross anatomical context, but this audit does not justify a diagnostic or fine-anatomy paired viewer. The separate T2-labelled sequence is not established as a validated pair. No anatomical or clinical approval was granted.

## Correct source image

The final MRML segmentation references `vtkMRMLScalarVolumeNode25`, named `108: T1 SAG VIBE DIXON_W L-LIMB`, through `referenceImageGeometryRef`. It does **not** reference volume12 (`19: RT T2 FS spc_SAG_iso (KNEE)`). The newly acquired exact volume25 NRRD is 27,645,476 bytes, retrieved through the unrestricted source archive’s normal HTTP-range support; its ZIP CRC32 is `fb5ca3ce` and SHA-256 is `bad8067951cd601dd1c9397e2f64a5aef902d55dfbe898036cdd50bdcb376852`. The full archive checksum was not claimed.

The reference grid is 420×923×176 with spacing 1.153846×1.153846×1.2mm. Its origin corresponds to segmentation IJK `[0,1,0]`: the segmentation has one extra superior padding row. This is explained by metadata, not a fitted correction. All 10 target label volumes lie within both inspected image fields of view. The separate nominal T2-FS grid is 306×448×176 at 1.071429×1.071429×1.1mm. These are exported sampling grids, not established effective acquisition resolution.

## Methods and quantitative limits

Original source files and voxel grids were preserved. Each MRI view uses original voxel values in a native sagittal, coronal or axial plane; no image interpolation or anatomical fit was used for the review panels. Author labels were nearest-neighbour sampled at the MRI voxel centres. Mesh outlines come from direct triangle/plane intersections. Plane coordinates and indices are recorded. Display windows use local 0.5/99.5 percentiles; intensity values are not calibrated HU. Trilinear sampling was used only for the separately recorded descriptive intensity statistics.

Medial/lateral author-label voxels were selected on their respective sides of the established component X-gap midpoint for audit only. No source label volume or mesh was rewritten. Each structure has three planes for each of the two sequences, giving 60 inspected sections in 10 review sheets with raw and overlay panels.

**Dice below compares mesh sections with the author’s labels on the reference grid. It does not compare either with independently labelled MRI ground truth.** Lower Dice on the different T2 grid cannot be interpreted as measured inter-sequence misregistration: sampling and plane differences alone affect it. Likewise, nearest boundary-voxel-centre distance is a point-sampling proxy, not exact anatomical boundary error.

| Structure | Author-label voxels | Mesh volume vs label volume | Reference-grid section Dice range | Vertex-to-boundary-voxel-centre p95, mm |
| --- | ---: | ---: | ---: | ---: |
| Distal femoral cartilage | 8180 | -4.12% | 0.968–0.979 | 1.004 |
| Patellar cartilage | 1869 | -5.22% | 0.941–0.990 | 1.027 |
| Lateral tibial plateau cartilage | 1149 | -6.74% | 0.954–0.959 | 1.106 |
| Medial tibial plateau cartilage | 1373 | -6.75% | 0.930–0.963 | 1.047 |
| Anterior cruciate ligament | 963 | -9.69% | 0.908–0.936 | 1.111 |
| Patellar ligament | 2994 | -5.79% | 0.859–0.904 | 1.095 |
| Posterior cruciate ligament | 1222 | -5.38% | 0.916–0.951 | 1.124 |
| Lateral meniscus | 725 | -10.59% | 0.902–0.967 | 1.047 |
| Medial meniscus | 799 | -16.84% | 0.860–0.946 | 1.067 |
| Quadriceps tendon | 6124 | -3.04% | 0.946–0.981 | 1.125 |

The meshes are 3.04–16.84% smaller in volume than their selected label-voxel representations. This demonstrates smoothing/discretisation disagreement; it does not establish biological tissue-volume error. Bounding-box correspondence alone would not reveal it.

## Per-structure visual findings

- **Distal femoral cartilage:** Contours follow the broad bright articular band in the reference image. Thin interfaces and local thickness cannot be independently resolved at this grid.
- **Patellar cartilage:** Posterior patellar band is visible in sagittal/axial reference planes. Superior/inferior ends and depth span few pixels; no fissure or sublayer assessment is supported.
- **Lateral tibial plateau cartilage:** Gross plateau position is supported. The layer is only a few voxels thick and adjacent meniscal/cartilage interfaces blend.
- **Medial tibial plateau cartilage:** Gross plateau position is supported, with pixel-scale contour differences. The separate T2-labelled sequence gives weak thin-layer boundary contrast.
- **Anterior cruciate ligament:** Source contour occupies the intercondylar course, but reference contrast does not delineate independent bundles or attachment footprints. Do not infer continuity/tear status.
- **Patellar ligament:** Long extensor band corresponds broadly to the source image. Thin axial width and end/enthesis boundaries show partial-volume sensitivity; retinacula are not represented separately.
- **Posterior cruciate ligament:** Gross course is distinguishable in sagittal/coronal context. Exact capsular margins, insertion boundaries and bundles remain unresolved.
- **Lateral meniscus:** Compartment and gross curved body are recognisable. Only 725 source voxels underlie the component; free edge, horns, roots and peripheral attachments lack independent detail.
- **Medial meniscus:** Gross body follows the joint margin, but the largest mesh/mask volume difference occurs here. Fine roots, horn attachments and free-edge morphology are not established.
- **Quadriceps tendon:** Broad tendon/aponeurotic region and patellar approach are visible. Individual laminae and the tendon-muscle transition are not independently delineated.

Across the reference panels, broad compartment/course relationships are coherent, but boundaries are often blurred over a few source voxels. The overlays largely reflect the author’s already-smoothed labels. The raw images must be considered separately; close yellow/cyan contour agreement cannot validate a structure merely because both came from the same segmentation workflow. The separate source-labelled T2 series is retained as comparison material with unproven cross-sequence alignment, not as a validation target.

## Modality and contrast caveat

The representative source DICOM has CT Image Storage SOP Class, `Modality=CT`, `ImageType=ORIGINAL/PRIMARY/AXIAL`, `RescaleType=HU` and `Manufacturer=3D Slicer`, despite its T1 VIBE DIXON series description. TR, TE, inversion time, flip angle and magnetic field strength are absent. It is a reconstructed/mislabelled derivative, not reliable original MR acquisition metadata; its values must not be treated as calibrated CT attenuation. No attempt was made to invent a calibration.

The authors describe Siemens Prisma 3T MRI and seven sequences, but the acquired NRRDs do not preserve the parameters needed to independently certify contrast weighting or achieved fat suppression. Therefore both sequences remain **source-labelled**. The explicit MRML geometry reference identifies which exported image grid the labels use; it does not establish what tissue borders an expert would draw.

## Metadata corrections

The staged and published knee manifests now set `clinical_image_pair.available=false`. They separately record volume25 as the MRML segmentation-reference image and volume19 as an unvalidated comparison sequence. The old `paired_T2_FS_exported_grid_mm` field is replaced by accurately named reference/comparison exported-grid fields. The old bounding check is explicitly scoped to STL-to-author-segmentation names, LPS metadata and extents.

Only nonidentifying technical evidence is copied to `/app/anatomy/msk-mri-knee/registration-evidence.json`, with a pinned SHA-256. It contains no pixels, patient identity fields or private filesystem paths. Exact before/after checks prove all staged/public part records, geometry hashes, coordinate transforms and approval statuses remained unchanged. The MRI files and generated review images remain under `/tmp/primer-msk-sources/high-fidelity/um-knee-image-audit/`.

## Reproduction and evidence

- `tools/anatomy_sources/acquire_malaya_reference_volume.py` follows the MRML reference to the exact public ZIP member and verifies CRC and SHA-256.
- `tools/anatomy_sources/audit_malaya_knee_images.py` produces the coordinate-preserving review sheets and quantitative JSON.
- `tools/anatomy_sources/verify_malaya_registration.py` retains source-only extent checks and writes the corrected image/provenance distinctions.

Use the existing Python 3.12 runtime with staged NumPy/Matplotlib/pydicom and SciPy dependencies. Audit outputs: `reference-volume-acquisition.json`, `paired-source-audit.json`, ten `*-source-planes.png` sheets, `registration-evidence.json` and `metadata-correction-check.json`. The focused knee/ankle source tests pass (9 tests). The correspondence metrics do not satisfy clinical-fidelity approval.

The ten inspected review sheets and quantitative JSON are also preserved with
checksums in [the offline review folder](msk-knee-source-review/README.md).
They are outside `web/`; neither they nor the raw volumes are offered as
diagnostic examples. A separate clean packaging run reproduced all current
part records and corrected public provenance exactly, without private paths.
