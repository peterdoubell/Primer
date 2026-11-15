# SPL-PNL/NAC native coordinate source review

This package preserves the original native T1/T2 MRI, the full categorical label volume and 12 original publisher surfaces. It also provides separate exact voxel-cell boundary surfaces for the 12 selected label classes. The exact boundaries are the default; original surfaces remain comparisons. No clinical or whole-module approval is asserted.

The source is the [SPL/NAC atlas](https://www.openanatomy.org/atlas-pages/atlas-spl-nac-brain.html), pinned to [commit bec24db25aad5f7600e2df3becfb1f883e61ff56](https://github.com/mhalle/spl-brain-atlas/tree/bec24db25aad5f7600e2df3becfb1f883e61ff56). It is one normal volunteer and combines automatic parcellation with manual segmentation. Original Git blobs, lengths and SHA256 values are recorded.

## Coordinate convention

Original model vertices are **legacy Slicer RAS millimetres**. The main MRML scene is Slicer4.4.0 and contains no selected model or volume parent transform. The contemporaneous VTK reader passes original polydata through unchanged. Modern Slicer unmarked-VTK defaults must not be applied retrospectively. The NRRD volumes explicitly declare LPS; multiplying their declared affines by diag(-1,-1,1,1) yields matrices exactly matching the main MRML scene. There is no fitted alignment.

Native T1 and T2 contain 288 × 320 × 208 Float32 samples at 0.75 mm. Labels contain 256³ Int16 samples at 1 mm. All 55,115,776 source samples remain bit-exact. Axis 0 is fastest; storage offset is i + nx × (j + ny × k). Each grid has its own affine. The unused 1 mm MRI resample starts at (-127.5,-127.5,127.5) LPS while labels start at (-128,-128,128), a half-voxel offset; equal array dimensions would not justify index alignment.

## Surfaces and measured limits

The derived surfaces expose every original categorical cell face whose neighbor has a different code, including every cavity and tiny component. RAS cell corners are exact half-integers. Each face becomes two outward triangles; independent full-grid face-set checks and signed enclosed volume equal to every source voxel count pass for all classes. Corner/edge contacts that are nonmanifold in the categorical source remain present. These boundaries are exact to the source segmentation, not an independent anatomical validation.

Original VTK surfaces are separately retained without deleting, welding, smoothing, repairing or rounding vertices, normals, strips or implied triangles. They differ from the labels, especially the fornix. Distances below are sampled in both directions: every original vertex to the nearest exposed label-cell quad, and every exposed label-cell face center to the nearest original triangle. They are **not continuous Hausdorff bounds**.

| Code | Source label | Voxels | Exact faces | Original vertex → label boundary max (mm) | Label face center → original surface max (mm) |
|---|---|---:|---:|---:|---:|
| 17 | left hippocampus | 4641 | 3686 | 1.8493 | 1.9603 |
| 53 | right hippocampus | 4378 | 3312 | 2.4845 | 4.2241 |
| 18 | left amygdala | 1733 | 1412 | 1.3708 | 1.7593 |
| 54 | right amygdala | 2166 | 1604 | 2.3628 | 3.2943 |
| 3007 | left fornix of forebrain | 741 | 1440 | 5.4833 | 12.2374 |
| 3005 | right fornix of forebrain | 760 | 1486 | 7.1654 | 2.5972 |
| 3003 | left mammillary body | 67 | 116 | 0.8488 | 1.2137 |
| 3002 | right mammillary body | 76 | 130 | 0.8208 | 1.3081 |
| 1016 | left parahippocampal gyrus | 1989 | 2844 | 2.3664 | 2.2372 |
| 2016 | right parahippocampal gyrus | 1900 | 2724 | 0.7943 | 1.3899 |
| 100 | left mammillothalamic tract | 30 | 96 | 0.4848 | 1.1859 |
| 200 | right mammillothalamic tract | 33 | 96 | 0.8274 | 1.1604 |

The left fornix 12.2374 mm outlier is an isolated one-voxel label component; the 739-voxel main component reaches 3.4536 mm. It is preserved. The original left/right fornix vertices reach 5.4833/7.1654 mm from their categorical boundaries. These discrepancies are disclosed instead of altering either source to force agreement.

## Transport and independent checks

The 16-byte HVX1 header is magic, vertex count, triangle count, reserved0. Float32LE RAS positions and Uint32LE triangles follow. Original normal and length-prefixed strip arrays have separate lossless sidecars, and exact original VTK files are retained as gzip archives. Native MRI/label gzip bodies are unchanged; retained NRRD headers reconstruct the exact original files. The package adds 37,892 categorical boundary triangles alongside all 29,130 original strip-derived triangles.

Independent Python/NumPy source-array checks agree with the JavaScript coordinate core on 34 complete native planes (2,439,168 source pixels and label overlays), 18,514 source-label-derived MRI probes per contrast, all 16,369 original mesh vertices through coordinate round trips, and 36 half-voxel field-boundary cases. This verifies coordinate/data behavior, not clinical correctness or browser visual quality.

## License and remaining limits

The publisher expressly applies the **3D Slicer Agreement v1.0, Part B** to this atlas. Full terms, the required Brigham notice, original source notices and marked-conversion details accompany both data and this review. Part B permits proprietary incorporation subject to its terms; it retains research-use and clinical-application restrictions/disclaimers, third-party obligations and no-endorsement conditions. This is not a Creative Commons license.

The broad hippocampus and parahippocampal labels do not establish separately labelled subiculum or CA fields. No disease, histology, population variation, patient registration, whole-module clinical approval or complete reporting coverage follows from this package.

Publisher HTML and historical source-code evidence are archived losslessly as gzip, with raw and stored hashes in archive-storage.json. The proof files and complete manifest are listed in source-review.json.

Manifest SHA256: `204f87b6d88a9570eb34664497a1462a5d8bba1afa0c2f7abe1cdf11082de2e6`.
