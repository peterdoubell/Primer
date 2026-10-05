# Complete original mesh-vertex / native label-boundary comparison

Every original vertex in the five [independent SPL wall candidates](spl-wall-source-review.md) is now compared to the authoritative source annotation, represented explicitly as the union of its native labelled voxel cells. This is a discrete reference-surface choice, not an independently established continuous tissue boundary or clinical acceptance threshold.

The source grid has approximately 0.9375×0.9375×1.5 spacing, with preserved origin and directions. Original RAS model coordinates are converted only to the native LPS/grid basis. Six-neighbour exposed faces of each labelled voxel form rectangular reference faces; internal faces between same-label cells are excluded. No source voxels or mesh values are changed, fitted or resampled. Boundary faces retain their original source voxel I/J/K indices, normal axis, centre and whether they touch the delivered grid exterior.

All 113,650 original position records are retained, including duplicate-index seam records. The comparison finds an initial rectangular-face distance using the nearest face centre, then tests every face centre within that upper bound plus the maximum face half-diagonal. The triangle inequality makes this a conservative candidate bound. Distance to each candidate rectangle uses exact axis-aligned clamping in the native physical-axis frame. An independent all-face brute-force test covers an anisotropic single cell, exact face contact, long-range points and adjacent-cell internal-face exclusion.

| Source label | Vertices compared | Native boundary faces | Maximum vertex distance | Mean vertex distance |
| --- | --- | --- | --- | --- |
| 135, right external oblique | 26,115 | 34,258 | 0.814100 mm | 0.229211 mm |
| 136, right internal oblique | 13,118 | 17,272 | 0.747540 mm | 0.223624 mm |
| 235, left external oblique | 23,002 | 30,368 | 0.912253 mm | 0.249882 mm |
| 236, left internal oblique | 13,228 | 17,472 | 0.927157 mm | 0.252980 mm |
| 32, combined rectus | 38,187 | 50,372 | 0.983550 mm | 0.243964 mm |

Each vertex has lossless evidence containing its original index, exact calculated distance, selected native boundary-face index, closest rectangular-face point and number of conservatively tested candidates. Percentiles and complete reference-face identities are retained. None of the selected labelled-cell boundary faces lies at the delivered grid exterior; this does not prove full acquired coverage, complete muscle course or anatomical annotation correctness.

These results are **not full-surface Hausdorff distances**. Triangle interiors, the reverse distance from the complete label boundary to the mesh, source self/inter-layer intersections, and independent anatomical interpretation remain separate requirements. Voxel discretization, interpolated/smoothed display surfaces, source annotation and sampling can produce differences. No clinical error, tolerance, source HU/phase calibration or replacement readiness is inferred from the submillimetre vertex numbers. The source marks the label map authoritative and the display meshes non-authoritative; that distinction is preserved.

Evidence retains the original [3D Slicer Part B terms](https://www.openanatomy.org/atlas-pages/slicer-license.html), including required prefaced notice, source attribution, modification marking, research/clinical-use qualifications and no endorsement. No clinical/model coverage or runtime promotion is granted. The full radiology objective remains unchanged and incomplete.

Reproduce with `python -m tools.anatomy_sources.compare_spl_wall_label_boundaries --archive .research/wall-independent-sources/spl-abdomen-2016-09.zip --output docs/spl-wall-source-review`. The exact-search, complete original-index, native-face identity and existing source/voxel conservation checks pass. Original archive/volumes/meshes remain in ignored staging; the new comparison evidence is offline and not deployed.
