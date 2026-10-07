# Original T01 labyrinth source review

The [original dataset](https://zenodo.org/records/3355272) explicitly grants CC BY 4.0 and describes specimen CT, co-registered micro-CT, labels, surfaces and landmarks. Its source-described registration is not an independently verified raw acquisition or clinical anatomical approval.

The complete original T01.zip (33,768,672 bytes) passed publisher MD5 `d200436a8dd84946817a660c1db6b299`. All seven original file members were read with ZIP CRC checks. CT and micro-CT image/label arrays contain 35,838,696 combined samples; every sample passed separate scalar/axis-order readback and comparison with nibabel. Original source values are preserved without smoothing, resampling, registration fitting or mask repair. Raw DICOM/HU calibration and effective resolution remain unverified.

| Source | Shape xyz | Declared sampling, mm | Label voxels | Image/label maximum corner qform difference, declared mm |
| --- | --- | --- | ---: | ---: |
| CT | 124×96×82 | approximately 0.15625×0.15625×0.2 | 35,226 | 0.0000670894 |
| Micro-CT | 315×226×238 | approximately 0.06070 isotropic | 799,837 | 0.0000123669 |

All four NIfTI files use explicit qforms and no active sform. Image and label shapes agree within each modality, but header qforms are not byte/numerically identical. Independent quaternion interpretation and nibabel agree; the small original image/label differences are measured at the source-volume corners and retained. They are not silently repaired into an identical-grid assertion. Each original binary mask has one six-neighbour component; neither is filtered or repaired. CT and micro-CT differ in sampling and mask voxelization.

The original CT and micro-CT PLY files are byte-identical, including the source micro-CT filename `T1_uCT_SURF.ply`. They are one geometry source duplicated in two folders, not independent source meshes. Both have 87,239 vertices and 174,486 triangles, one connected surface, no boundary/nonmanifold edges and no zero-area triangles. Original ASCII PLY vertices, faces, patch/material declarations and trailing data remain untouched in the research cache. These numeric/topological checks do not validate tissue identity, cortical thickness, native mask-to-surface agreement or complete anatomical extent.

The original descriptor identifies T01 as LEFT and supplies landmark/coordinate values. This is a source statement, not independently linked clinical DICOM laterality or a population reference. The dataset concerns a regional bony labyrinth; it does not supply every ossicular, canal, neural, membranous, vascular, middle-ear, lesion or implant structure required by the temporal-bone module. No source still from another case is registered to this specimen. All anatomy, complete scope and clinical review remain pending; no runtime promotion or structure coverage is granted.

Evidence is saved in `docs/temporal-bone-native-source-review/T01-original-source-review.json`. The original archive and extracted members remain in the ignored `.research/temporal-bone-native-source-review/` cache. Five scientific qform/order/rejection tests pass. Full visual source and mask/surface agreement review remain outstanding.

## Original surface/image visual comparison

All 174,486 original PLY triangles were rendered from two viewpoints without moving vertices, changing faces or smoothing geometry. Illumination is display-only. Original PLY coordinates were mapped into each source image through that image's original qform inverse. All 87,239 vertices lie within both image grids; this is a coordinate-domain check, not proof of tissue identity or exact registration.

Three individual native index planes per modality show the original mask contours beside actual original PLY plane intersections. CT planes are axis 0/index 49, axis 1/index 54 and axis 2/index 48; micro-CT planes are axis 0/index 130, axis 1/index 133 and axis 2/index 134. They are independently selected native planes, not newly registered or resampled cross-modality planes. Original image/label qform discrepancies remain recorded, and same-index mask contours are not presented as a repaired shared affine. Native physical pixel aspect is retained. Recorded percentile windows use original source scalar units; they do not independently establish calibrated HU.

Visual comparison shows CT mask/mesh contour differences, with closer correspondence on the selected micro-CT planes. The original source surface is not assumed to be an exact binary 0.5 label interface. Sampling original labels at every mesh vertex gives median absolute binary-field residuals of about 0.305 (CT) and 0.227 (micro-CT), with maxima near 0.5. These dimensionless field residuals are neither distances nor clinical error measurements; binary interpolation and surface construction affect them. No fitting, repair or new surface replaces the source geometry.

The original source views and mismatch evidence are saved in `T01-source-display-review.json`. The PNGs remain in the ignored source cache and have been visually inspected. Seven scientific qform and triangle-plane tests pass. Complete source identity, mask/surface registration, all anatomical interfaces, tissue thickness, function and independent clinical validation remain unapproved. The original paper is [Robust Cochlear Modiolar Axis Detection in CT](https://arxiv.org/abs/1907.01870); its axis-detection study is not treated as a clinical-completeness certificate for this mesh. No paper graphics were copied.
