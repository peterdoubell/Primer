# Complete bounded bidirectional mesh / native-cell surface comparison

The reverse comparison now covers every exposed rectangular face of the five authoritative source label-cell unions against the complete original display meshes. Combined with the [continuous forward certificates](spl-wall-triangle-bound-review.md), this produces bounded bidirectional Hausdorff intervals between those two explicitly defined geometric representations. It does **not** establish continuous anatomical truth, clinical accuracy or an acceptance threshold.

Each native rectangle is partitioned into two coplanar triangles without changing its covered area. Original source voxel identities, normal axes and face centres are retained. The distance oracle finds exact nearest points on original mesh triangle interiors, edges or vertices. A nearest-centre triangle supplies an upper bound, then every triangle centre within that bound plus the greatest source-triangle centroid radius is tested. This is conservative by the triangle inequality; a brute-force all-triangle test independently checks the search. Analytic plane, edge, vertex and anisotropic rectangle cases verify the point-to-surface calculations.

The same 1-Lipschitz centroid/radius analysis used for the forward direction recursively covers all unsampled reverse cell interiors. Terminal paths form a complete nonoverlapping binary partition of every original boundary-face triangle. No source voxel, mesh vertex, normal, connectivity, transform or source label is edited. Numerical interval width is 0.05 mm; it is not claimed to be native acquired resolution or biological precision.

| Source label | Native boundary rectangles | Reverse lower bound | Reverse upper bound | Terminal cells |
| --- | --- | --- | --- | --- |
| 135, right external oblique | 34,258 | 1.719193 mm | 1.759351 mm | 85,007 |
| 136, right internal oblique | 17,272 | 1.712424 mm | 1.753233 mm | 42,240 |
| 235, left external oblique | 30,368 | 1.837758 mm | 1.878604 mm | 76,769 |
| 236, left internal oblique | 17,472 | 1.851014 mm | 1.892296 mm | 47,201 |
| 32, combined rectus | 50,372 | 2.234738 mm | 2.282021 mm | 103,204 |

Every reverse interval exceeds its matching forward interval, so these reverse intervals also bound the full bidirectional maxima for this source pair. A forward-only check would understate the complete difference, most noticeably for combined rectus. Smoothing, display simplification, annotation and discrete-cell geometry can contribute; the numbers do not identify anatomical error or prove an omitted clinical structure.

Complete lossless evidence retains each terminal cell’s original rectangle-triangle ID, refinement path, centroid, sampled distance, cover radius and upper bound. Rectangle index is recoverable as `original_triangle_index // 2`, linked to its source voxel I/J/K and normal axis. Forward-source hashes are pinned before combining intervals. Tests verify every reverse cell’s exact dyadic coverage, no overlapping terminal paths, numerical bound widths, conservative nearest-surface search and correct bidirectional aggregation.

Source self/inter-layer crossings, authoritative annotation reliability, fine-layer/course completeness, full acquired field of view, patient axes and independent anatomical review remain unresolved. The combined rectus label is not guessed into sides, and absent sheath/transversus/fascial structures are not reconstructed. Model promotion and clinical coverage remain unapproved.

The original [3D Slicer Part B notice](https://www.openanatomy.org/atlas-pages/slicer-license.html), research/clinical-use qualifications and attribution apply to the evidence. Reproduce with `python -m tools.anatomy_sources.bound_spl_wall_reverse_distance --archive .research/wall-independent-sources/spl-abdomen-2016-09.zip --output docs/spl-wall-source-review --error-mm 0.05`. Runtime and rights/coverage counts are unchanged. The full all-radiology objective remains active and incomplete; new evidence is offline and not deployed.
