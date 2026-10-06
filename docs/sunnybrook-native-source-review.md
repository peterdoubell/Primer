# Sunnybrook native cine and original LV model evidence

The [primary Sunnybrook dataset](https://www.cardiacatlas.org/sunnybrook-cardiac-data/) supplies 45 mixed-pathology cases, original manual contours and fitted left-ventricular finite-element models. Its dataset and derivatives are CC0 1.0 Universal. The original archive licence and README are retained here; CAP software licensing is a separate question. Attribution: Radau P, Lu Y, Connelly K, Paul G, Dick AJ, Wright GA, “Evaluation Framework for Algorithms Segmenting Short Axis Cardiac MRI”, MIDAS 2009, <http://hdl.handle.net/10380/3070>.

This packet selects the original mapped case **SCD0000101 / SC-HF-I-1**, source category heart failure with infarct, male, age 53. The contour folder spells the original identifier `SC-HF-I-01`. Category and historical inclusion thresholds are source metadata, not a new diagnosis, a current universal threshold, independently measured EF, or independently demonstrated LGE.

## Actual source evidence

- Complete first-party DICOM batch 1 archive acquired: 433,585,535 bytes; SHA-256 `708ce04db1ac33948a00b9052d44e9548c6807121a4841f4c35080d6db127b72`. This is a local acquisition hash, not a publisher-supplied checksum. ZIP CRCs checked for extracted members.
- All **360** original model image references match exact native SOP and series UIDs among **1,047** case DICOM members. Each referenced 256×256 signed 16-bit pixel buffer agrees with independent little-endian scalar decoding. No source pixels or UIDs were repaired.
- **18** original planes (6 long-axis, 12 short-axis) each supply **20** distinct pixel buffers with increasing original trigger times and unchanged per-plane orientation/position. Nominal intervals differ between planes; these are not simultaneous 4D acquisitions of one heartbeat.
- All **20** original `.exnode` phases, their XML mapping, original `.exelem` and **33** manual contour files are retained byte-identically. XML frame 0 maps to source phase file 1. All 40 prolate nodes per phase retain λ value/three derivatives, μ and θ; focal length 35.8171. The XML interval `0.05` is retained without reinterpreting it as milliseconds.
- All **16** original volume elements retain eight source node IDs and 40 scale factors each. λ uses cubic Hermite × cubic Hermite × linear Lagrange; μ/θ use trilinear Lagrange, with **decreasing-in-xi1** angular modification for θ. No ordinary polygon interpolation or new surface has been substituted.

`native-cine-linkage-review.json` includes the allowlisted geometry, source pixel/file hashes and exact image references. Original DICOM UIDs contain leading-zero components, and one series UID spans SAX, LAX, perfusion and other folders. The source defect is explicit: series UID alone is not a grouping key. Pixel spacing and geometry are declared source metadata, not independent scanner/phantom calibration.

`native-sa6-20-frame-context.png` and `native-plane-phase-context.png` show matched original pixels with a recorded display window and nearest-neighbour display. They are contact sheets, not raw volumetric/cine viewers or quantitative validation. Additional perfusion/tissue acquisitions remain outside the current decoder review. The initial parameter report's `native_image_linkage_verified=false` records the earlier stage; the separate native linkage report supplies the subsequent exact UID/pixel evidence. Neither validates model geometry.

## Model and contour work still required

The pinned [original CAP reader](https://github.com/ABI-Software/capclient/tree/a4a8fa5a4200a5c6da372d42f6e2961bef14f1d3) loads finite-element files, converts prolate coordinates through Cmgui and applies a projection. Its matrix reader/transpose convention and xi3_0 epicardial / xi3_1 endocardial graphic selection are recorded with source-file hashes in `cap-model-reader-code-review.json`. That code was inspected, not executed, and is not proven identical to the 2012 conversion revision. Independent Zinc/Cmgui evaluation, native-plane registration, angular seam/apical/basal checks, original contour pixel/index/phase conventions and comparisons remain required. No mesh, smoothed/closed surface, contour loft, replacement myocardium, function measurement or clinical approval has been generated.

The fitted LV model and sparse manual contours cannot fill complete RV, valves, chordae, vessels, pericardium, scar/maps, all myocardial layers or disease-specific anatomy. Full reporting structure requirements remain active. Nothing in this packet is promoted into runtime or credited as verified leaf coverage.

## Reproduce

Use `tools/anatomy_sources/acquire_sunnybrook_source.py --source-root .research/native-cine-source-review --include-cine` to acquire/recheck pinned first-party source bytes. Public dataset download tokens are published resource links, not account credentials. The first cine archive is 433 MB; cached files are hash-checked. The initial source-page snapshot was independently acquired from the primary page and its hash is in the original report; retain/reacquire `sunnybrook-primary-page.html` to rerun that initial report.

Run `review_sunnybrook_source_parameters.py`, then `verify_sunnybrook_native_cine.py`, then `render_sunnybrook_native_cine.py`, each with the same `--source-root`. Native decoding requires pydicom/numpy; scientific display also requires matplotlib. The large original DICOM archive stays in ignored research storage, not the hosted application bundle. The checked-in exact model, contours, reports and contact sheets preserve the review evidence without source edits.
