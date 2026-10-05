# Bounded continuous forward wall-mesh comparison

All 224,612 original triangles expanded from the five source VTK strip meshes now have continuous forward distance bounds against the explicit authoritative-label voxel-cell boundary representation. This extends the [vertex comparison](spl-wall-label-boundary-review.md); it does not complete the reverse comparison or establish continuous anatomical ground truth.

For each analysis triangle cell, the distance from its centroid to the complete native rectangular-face union is computed with the conservative exact-face search. Distance to a closed set is 1-Lipschitz. The maximum centroid-to-corner radius covers the entire convex triangle cell, so centroid distance plus that radius bounds every unsampled interior point. The original source triangles are recursively partitioned along their longest edge only for analysis. Terminal cells form a complete nonoverlapping binary cover of every original triangle. No vertices, source faces, labels, source transforms or voxels are changed.

The greatest sampled distance gives a valid lower bound, initialized also by the full original-vertex maximum. Cells whose upper bounds could exceed that global witness by more than 0.05 mm are refined. The remaining terminal cells certify a global interval no wider than 0.05 mm, with a small numerical padding explicitly retained in the bound. Numerical interval width is not source acquisition resolution or a clinical acceptance threshold.

| Source label | Forward lower bound | Forward upper bound | Terminal analysis cells |
| --- | --- | --- | --- |
| 135, right external oblique | 1.090564 mm | 1.140196 mm | 90,230 |
| 136, right internal oblique | 1.105503 mm | 1.154661 mm | 44,207 |
| 235, left external oblique | 1.166097 mm | 1.214670 mm | 84,637 |
| 236, left internal oblique | 1.096957 mm | 1.145342 mm | 53,216 |
| 32, combined rectus | 1.213789 mm | 1.263728 mm | 112,933 |

All lower bounds exceed their respective original-vertex maximum. Triangle interiors therefore contain larger reference-boundary distances than a vertex-only check revealed. Complete compressed evidence retains each terminal cell’s original triangle ID, binary refinement path, centroid, sampled distance, cover radius and upper bound, together with the global witness and original source hashes.

Tests independently check a triangular example whose vertices all have zero distance while its interior has a known positive maximum. They verify the numerical interval contains the analytic maximum, every original triangle’s terminal cover has exact dyadic mass one, no terminal path overlaps another, and all original source identities remain pinned. Original native CT/label/model conservation and the exact rectangular-face search remain covered by their separate checks.

These are **continuous mesh-to-discrete-cell-union forward bounds**. They are not full bidirectional Hausdorff distances or clinical accuracy scores. The complete reverse distance from the label surface to the mesh, source self/inter-layer crossings, authoritative annotation reliability, tissue-course completeness and independent anatomical review remain pending. No smoothing, fitting, repair, missing-layer reconstruction, guessed rectus-side split or clinical promotion is introduced.

Evidence retains the source [3D Slicer Part B terms](https://www.openanatomy.org/atlas-pages/slicer-license.html), required prefaced notice and research/clinical-use qualifications. Runtime and rights/coverage counts are unchanged. Reproduce with `python -m tools.anatomy_sources.bound_spl_wall_triangle_interiors --archive .research/wall-independent-sources/spl-abdomen-2016-09.zip --output docs/spl-wall-source-review --error-mm 0.05`. Full radiology fidelity remains incomplete; this new evidence is offline and not deployed.
