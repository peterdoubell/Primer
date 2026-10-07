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
