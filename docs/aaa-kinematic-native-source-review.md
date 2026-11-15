# Native AAA CT and original external-surface review

Reviewed 6 October 2026. The previous goal turn made progress by packaging all thirteen original rupture figures and expanding the full effective AAA reporting scope. This review obtains original volumetric and geometric sources needed for further fidelity work, without substituting external contours for every reported structure.

The original [Zenodo dataset](https://zenodo.org/records/15477710), DOI **10.5281/zenodo.15477710**, provides cropped ECG-gated contrast-enhanced CT and processed external aneurysm surfaces from ten patients. The original dataset metadata grants **CC BY 4.0** and is preserved with author attribution. The reviewed [primary paper, version 2](https://arxiv.org/abs/2505.17647v2), DOI 10.1016/j.dib.2025.111797, explains the processing and synthetic-method controls. The entire original archive is retained in ignored research storage, and original STL files are preserved byte-for-byte under lossless gzip in this review packet. No original voxel, geometry, normal or attribute is altered.

- Archive: 81,782,778 bytes; publisher MD5 `7caf0624939e8482e7d960cd14317d8e` verified, SHA-256 `036ddd6e13b89e001a8e3d96b06ffb71860eaa80a1a4477e9d5cad1ac94e51c5`; all 99 regular member CRCs verified.
- Original data: **10 external STL surfaces, 199,468 facets, 78 acquired cropped CT frames and 51,743,358 delivered signed-int16 voxels**. Every frame's complete header, file hash, original voxel-byte hash, dimensions and stored value range is recorded.
- Original binary STL fields are independently compared using scalar `struct` and NumPy record layouts, including signed zero and attribute words. Exact-position deduplication is used only for topology analysis; no source vertices are welded, capped, smoothed or fitted.
- The source CT headers explicitly use **LPS**, whereas the paper describes STL coordinates as **RAS**. Numerical comparison changes only the signs of the first two world axes. Source basis correspondence is not independently verified anatomical registration.

| Patient | Original facets | Open boundary edges | Original corners outside selected CT cell extent |
| --- | ---: | ---: | ---: |
| P1 | 20,037 | 367 | 0 |
| P2 | 20,046 | 342 | 0 |
| P3 | 19,893 | 273 | 904 |
| P4 | 20,045 | 501 | 0 |
| P5 | 19,873 | 439 | 0 |
| P6 | 19,895 | 317 | 0 |
| P7 | 20,030 | 310 | 0 |
| P8 | 19,897 | 431 | 0 |
| P9 | 19,863 | 315 | 0 |
| P10 | 19,889 | 333 | 1,386 |

All ten exact-position analysis meshes have one connected component and no nonmanifold edges. Each has open boundaries, consistent with an external cut surface rather than a complete tissue volume. Those observations do not prove absence of self-intersections, correct wall boundaries, clinical measurement accuracy or complete anatomy. P3/P10 crop exceedance is retained without applying an alignment shift or repairing geometry; the available frames and model phase require further source review.

The native headers do not explicitly declare physical space units, HU calibration or contrast-bolus timing, and STL does not declare units. Native coordinate values remain unscaled; no independent millimetre/HU calibration is invented from plausible CT spacing or intensity values. Percentage filenames describe **cardiac-cycle frames**, not arterial/venous contrast phases. The 2025 paper's systolic paragraph includes P2 in its 30% list and omits P3, then states P2/P4 use 40%; actual delivered P2/P4 files are 40%/80%. The discrepancy is explicit, and independently verified model/phase registration remains false for every case.

## Anatomical and processing limits

The source paper describes automated PRAEVAorta segmentation, cropping, label merging, removal of branches/artifacts, isotropic resampling, smoothing, hole filling and ACVD remeshing. It exports only the processed external surface in this ten-case dataset. The source masks for lumen, thrombus/wall and calcification are not supplied. No faithful separate inner wall, wall thickness, thrombus, lumen, calcification, visceral/renal/access branches, rupture site, haemorrhage compartment, fistula or repair component is granted by the external surface label. Source algorithm suitability claims do not substitute for independent review of these delivered models.

The archive also contains eleven `Ground Truth/` method-verification files. The warped systolic image and finite-element outputs are synthetic, not independent acquired anatomy or clinical systolic ground truth. They are indexed separately and never counted among the 78 acquired patient frames. Assumed-thickness inner walls and biomechanical outputs are not silently adopted as measured wall anatomy or rupture prediction.

A newer [twenty-patient publication](https://pmc.ncbi.nlm.nih.gov/articles/PMC13247696/), DOI 10.1016/j.dib.2026.112865, and its [dataset record](https://zenodo.org/records/19182978) were inspected as a potential further source. Original XML matched its publisher MD5. That paper explicitly describes a **1.5 mm assumed wall thickness**, automated/AI-assisted segmentation and modelling assumptions. Its dataset record grants CC BY 4.0, while its article metadata reports CC BY-NC; dataset and article rights are separate. The 1.86 GB twenty-case archive was not acquired or cross-registered in this packet, and no identities, geometry or biomechanical maps were borrowed across records.

## Review artifacts and checks

[Native proof](aaa-kinematic-native-source-review/native-source-review.json) preserves every original file/voxel/facet identity and the full actual phase inventory. [Render bindings](aaa-kinematic-native-source-review/render-review.json) link ten inspected context sheets to the exact source frames/surfaces. Thirty native axial slices use nearest-neighbour display with a declared stored-value window; overlays are mathematical intersections of unchanged facets with the native planes, not independently annotated wall truth. Source CT is not resampled. The sheets retain the open surfaces and original placements, with review-only camera and uniform surface colour. A footer overlap noticed in P6 was corrected and all ten final artifacts were inspected.

The P10 lower/middle review slices visibly show two separately enhanced, calcified lumen-like regions within one smooth external envelope. Their actual vascular identities and connection cannot be established from these selected views or the merged surface. This is a source-review hold, not a new diagnosis or permission to split a model by guessed anatomy.

Reproduce with:

```sh
python -m tools.anatomy_sources.acquire_aaa_kinematic_source --source-root .research/aaa-native-source-review
python -m tools.anatomy_sources.review_aaa_kinematic_source --source-root .research/aaa-native-source-review
python -m tools.anatomy_sources.render_aaa_kinematic_source --source-root .research/aaa-native-source-review
```

The downloader preserves the checked-in reviewed metadata snapshot; it does not claim a fresh rights/retraction check from volatile repository metrics. Tests cover every preserved surface, all 78 original voxel grids, phase/coordinate/crop holds, synthetic-data separation, signed-zero/normal/attribute preservation, corruption/nonfinite rejection, source-transform tests, native plane-edge/coplanar cases and exact render bindings. Python 3.9: three pass with four scientific dependency skips; scientific Python 3.12: seven pass.

No clinical approval, complete structure coverage or runtime promotion is granted. The full radiology objective remains active: 33,246 known-floor obligations, 84 unexpanded investigations, 106 unreconciled curriculum surfaces and unknown total. Runtime rights counts remain 687 unique images / 244 cleared / 443 unverified. Source integrity checks are preparation for clinical fidelity review, not a substitute for it.
