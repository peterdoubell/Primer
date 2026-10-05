# Complete independent SPL wall contact review

All five [independent source models](spl-wall-source-review.md) were compared in their unchanged native RAS coordinates, preserving original position/normal/triangle-strip identity. The analysis covers all 224,612 expanded strip triangles, with zero invalid analysis triangles. Native strips are expanded in their defined alternating orientation; no source mesh is smoothed, welded, repaired, pruned, thickened or fitted.

The conservative AABB sweep produced 1,617,564 candidate pairs: 1,280,646 explicitly tested and 336,918 nonparallel shared-edge pairs resolved analytically. Ordinary adjacency is allowed only within the same original model. Contacts between labels remain recorded, including exact shared-coordinate edge/point contacts. Numerical tolerance is 10⁻⁹ mm, which is not acquired source resolution or clinical accuracy.

The complete evidence retains **19,748 contacts**: 24 within original models and 19,724 between models. Each contact keeps original label value, expanded triangle index, native strip index, triangle ordinal within the strip and all calculated contact points. Compressed/uncompressed hashes and the complete candidate-array identity are recorded. All ten between-model pairs have explicit counts, including zero-count pairs.

| Original model | Within-model findings |
| --- | --- |
| Right external oblique, label 135 | 6 |
| Right internal oblique, label 136 | 3 |
| Left external oblique, label 235 | 12 |
| Left internal oblique, label 236 | 0 |
| Combined rectus, label 32 | 3 |

Between-model findings are 10,248 for right external/internal oblique, 9,265 for left external/internal oblique, 123 for right external oblique/combined rectus, and 88 for left external oblique/combined rectus. The other six pairs have zero retained contacts under this numerical procedure. Zero counts do not establish biological separation, correct tissue boundaries, full coverage or source annotation accuracy. The 24 within-model findings remain nonordinary numerical contacts requiring original-face interpretation; they are not automatically called tissue injury or a validated reason to alter anatomy.

The inspected location sheet shows all retained contacts, within-model findings and between-model findings in XY/XZ/YZ source projections. Every panel keeps all original strip triangles in context, marks the affected source faces and displays every retained contact point. Projection overlap is a display limit; original coordinates and strip identities remain available in the lossless evidence.

These source-quality findings mean the independent models are not yet verified clean replacements for the held artist surfaces. Their source metadata still marks the label map authoritative and the display meshes non-authoritative. The [bidirectional label-cell comparison](spl-wall-bidirectional-distance-review.md) remains an explicit discrete reference comparison, not clinical acceptance. Original-face classification, inter-layer tissue interpretation, annotation reliability, missing-layer/course completeness and independent clinical accuracy remain pending. No model promotion or coverage credit is granted.

The original [3D Slicer Part B terms](https://www.openanatomy.org/atlas-pages/slicer-license.html), required prefaced notice, source attribution, research/clinical-use qualifications and no endorsement apply. Reproduce with `python -m tools.anatomy_sources.audit_spl_wall_contacts --archive .research/wall-independent-sources/spl-abdomen-2016-09.zip --output docs/spl-wall-source-review`, then `python -m tools.anatomy_sources.render_spl_wall_contacts --archive .research/wall-independent-sources/spl-abdomen-2016-09.zip --output docs/spl-wall-source-review`. Tests verify every original strip/triangle identity, all-model/pair/contact accounting, hashes and source conservation. Runtime and rights/coverage counts are unchanged; the full radiology objective remains active and incomplete. New evidence is offline and not deployed.
