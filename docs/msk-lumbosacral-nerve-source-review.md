# Image-backed lumbosacral nerve-source review

27 September 2026. This source pass addresses neural anatomy missing from the
bone-only VerSe candidate. It does not join two subjects into a synthetic atlas
or waive the remaining MSK structures.

## Source and rights

Liu, Zhang, Zhou, Xu, Chu and Jia provide [MRI data, annotations and generated
models](https://doi.org/10.6084/m9.figshare.c.7372564). The selected Figshare
records explicitly use **CC BY 4.0** for both original MRI and marker/model
files. This is distinct from the accompanying
[Scientific Data article](https://www.nature.com/articles/s41597-024-03919-4)'s
CC BY-NC-ND licence. No article figure was adapted. The new review image derives
from the separately licensed dataset and retains attribution and change disclosure.

[Preserved source records](msk-lumbosacral-nerve-source-review/source-records.json)
identify the article versions, record hashes and licence URLs. The generator's
public code was inspected in staging only: no licence file was visible in its
tree, so it was not copied into this project or used to generate assets.

## Acquired data and numerical correspondence

The original 4.5 MB marker archive was checked against the publisher's MD5 and
its member CRCs. It contains **47,384 defined control points** in 2,316 annotation
files across 14 subjects, all explicitly in LPS millimetres. The subject-14 dura
filenames use an underscore in the subject prefix; the audit records this
variant and preserves the source filenames and data.

Only the selected subject-03 CISS, DESS and T2-TSE volumes and sidecars were
acquired from the 1.21 GB MRI archive. Bounded HTTP ranges preserve the archive
ETag, declared byte ranges and per-member ZIP CRC; each extracted file also has
a SHA-256. The whole-archive MD5 is recorded as advertised, **not claimed as
verified**. Raw MRI stays in local staging and is not deployed.

The selected NIfTI headers show:

| Series | Array shape | Stored voxel spacing, mm | Sidecar slice thickness, mm |
|---|---|---|---|
| CISS | 960 × 960 × 80 | 0.30 × 0.30 × 2.00 | 2.00 |
| DESS | 192 × 48 × 192 | approximately 1.266 × 1.270 × 1.266 | 1.27 |
| T2-TSE | 407 × 1325 × 30 | 0.625 × 0.625 × 3.30 | 3.30 |

The README and paper report differing generic acquisition values. The case
headers/sidecars above are retained rather than replacing them with a generic
protocol. Stored voxel spacing is not a claim of isotropic resolving power.

All 536 subject-03 nerve-root points, 1,097 cord-contour points and 2,070
dura-contour points lie within the CISS voxel support after the explicit
LPS-to-RAS coordinate change and inversion of its original affine. This is
coordinate inclusion, not proof of anatomical correctness or registration.
Only 4 of 14 ganglion markers lie within CISS, 12 within DESS, and all 14 within
T2-TSE. Both S2 ganglion markers lie outside DESS. No extrapolation or fitting
was performed to force them inside a volume.

A [native CISS review image](msk-lumbosacral-nerve-source-review/sub03-ciss-marker-review.png)
shows the unchanged source plane beside projected original markers for bilateral
L1–S2 labels. Slice selection, crop, window and point coordinates are recorded
in the [audit](msk-lumbosacral-nerve-source-review/annotation-and-image-audit.json).
Markers within half a native slice are shown. They identify annotations, not
segmented nerve boundaries or measured diameters. The directions follow the
native near-axial grid; pixels are enlarged with nearest-neighbour display.

## Generated-model limitation

The authors describe manual trajectories and contour annotations, spline-based
model construction and later intersection corrections. Their inspected example
sets every nerve radius parameter to 0.5 with metric scene scale 0.001, adds
entry points relative to the cord mesh, and fits 100-point smoothed paths. These
are modelling choices, not evidence of measured individual nerve calibre.
The native 602 MB generated-model archive has not been acquired, so exact
correspondence of every published model to that example remains unestablished.
The [method screen](msk-lumbosacral-nerve-source-review/generator-method-screen.json)
records immutable code-blob identities and the inspected limitations.

Original trajectories may support explicitly labelled course diagrams after
review. They cannot be counted as complete high-fidelity nerve-surface models.
Cord and dura contours are a separate candidate for image-backed surface work;
no surface quality is inferred merely from the availability of those points.

## Remaining scope

There is no verified disc, annulus/nucleus, spinal ligament, facet capsule or
complete rootlet segmentation here. Named L1–S2 marker trajectories alone do
not establish traversing/exiting relationships at every reportable vertebral
level, full cauda-equina coverage, conus extent or pathological compression
interfaces. No runtime asset, clinical approval or completed requirement was
added by this acquisition. The current source decision is to retain the MRI
and original annotations for further review, without accepting the generated
nerve tubes as measured anatomical surfaces.

## Cord/dura contour continuity and endpoint review

A direct audit of all selected original markup JSON files finds 66 cord
contours on native CISS slices 14–79 and 80 dura contours on slices 0–79.
Neither sequence has missing integer slices or duplicate slice indices within
its range. The maximum within-contour spread is below 1e-9 native slices;
maximum displacement from the nearest slice centre is about 0.000113 slices.
The original affine was used throughout, without fitting the contours to MRI.

All control positions are finite, with no duplicate control points or zero-length
closing edges. No strict crossing between nonadjacent control-polygon segments
was detected. On all 66 paired slices, every cord control point is inside the
dura control polygon. These tests concern control polygons: collinear overlaps,
tangencies, the complete interpolated curves and between-slice containment are
not established by these results.

The markup files do not explicitly record a `curveType`. Straight segments
therefore serve only as review aids and are not claimed to reconstruct the
original Slicer interpolation. The lowest cord control polygon (slice 14) has
area about 1.105 mm²; the highest (slice 79) about 42.313 mm². Dura endpoint
control-polygon areas are about 180.170 and 133.167 mm². These are polygon
measurements, not validated tissue cross-sectional areas. All endpoints remain
finite: there is no evidence here for a zero-area anatomical tip or a closed
volume, and the highest contours reach the final native image plane.

[Native MRI comparisons](msk-lumbosacral-nerve-source-review/cord-dura-native-plane-review.png)
show source pixels separately from original points and straight control polygons
at slices 14, 40 and 79. The paired figure preserves the source directions,
recorded window and original point coordinates. No loft, cap, smooth surface or
clinical completeness assertion was created to conceal the endpoint limits.

Evidence: [all-contour audit](msk-lumbosacral-nerve-source-review/cord-dura-contour-audit.json)
and [review-plane coordinates](msk-lumbosacral-nerve-source-review/cord-dura-review-planes.json).
This confirms an orderly image-backed contour sequence worth further surface
assessment. It does not verify conus-tip completeness, gray/white matter anatomy,
rootlet attachments or the full neural reporting scope.

## Versioned interpretation of the saved curves

The [Slicer 5.4 curve-node constructor](https://github.com/Slicer/Slicer/blob/v5.4.0/Modules/Loadable/Markups/MRML/vtkMRMLMarkupsCurveNode.cxx)
selects cardinal splines and ten subdivisions per control-point segment. The
closed-curve subclass closes the curve; the version-pinned vtkAddon generator
parameterizes by control-point index, not chord length. The
[generic JSON storage implementation](https://github.com/Slicer/Slicer/blob/v5.4.0/Modules/Loadable/Markups/MRML/vtkMRMLMarkupsJsonStorageNode.cxx)
saves basic properties, control points, measurements and display properties,
but not curve type or sampling settings. Those settings do appear in scene XML
serialization. Consequently, a fresh default interpretation is reproducible;
an original nondefault author setting cannot be inferred from these files.

The [version/source record](msk-lumbosacral-nerve-source-review/slicer-default-interpretation.json)
pins Slicer, vtkAddon and the VTK fork. The relevant CardinalSpline and
ParametricSpline implementations in the installed VTK 9.2.6 comparison engine
differ from Slicer's pinned versions only by ABI namespace wrappers. Original
control data are retained separately; the float32 input/output point behavior
of this interpretation is explicit, with maximum input roundoff about
0.00001535 mm in this case.

All 146 contours were reconstructed under these **stated defaults**, without
claiming recovery of unrecorded author settings. Every original control point
is passed through at its float32 representation. No strict crossing was detected
among sampled curve segments, and every sampled cord point lies inside the
corresponding sampled dura polygon. These finite checks do not prove continuous
spline nonintersection or containment between slices.

Maximum deviation from the corresponding straight control segment is about
0.22662 mm. That quantifies sensitivity to interpolation, not anatomical error
or MRI resolving power. The [paired review](msk-lumbosacral-nerve-source-review/cord-dura-default-curve-review.png)
shows the default curves, original controls and native MRI separately. Original
endpoints remain finite and unchanged; no tissue surface, cap or anatomical tip
was fabricated.

[Reconstruction evidence](msk-lumbosacral-nerve-source-review/default-curve-reconstruction.json)
records all 146 source hashes and derived NPZ hashes. Arrays are saved under
`output/msk-lumbosacral-sub03/default-curves/`. Reproduction uses the isolated
VTK 9.2.6/NumPy 1.26.4 Python 3.9 installation in local staging; those packages
were not added to production dependencies. The code is
`tools/anatomy_sources/reconstruct_lumbosacral_default_curves.py`; the image
renderer accepts `--default-curves`. Clinical boundary accuracy and full neural
coverage remain unverified.

## Open cord and dural contour-envelope candidates

Two new surface candidates connect adjacent interpreted source contours:
**21,700 triangles / 10,970 vertices for cord**, and **40,980 triangles /
20,700 vertices for dura**. Every sampled default-curve position is retained
exactly; only the repeated closure endpoint is deduplicated. The newly derived
triangles use an order-preserving dynamic-programming strip with fixed seam
quads. No smoothing, end cap, tip extension or cross-subject fitting is applied.
These are contour envelopes, not complete verified tissue volumes; in particular,
the dural surface has no measured wall thickness.

Both meshes have one edge-connected component, no non-manifold edges, no
inconsistent paired-edge winding and no degenerate triangles. Their boundary
edges match **only** the first and last source rings: 240 for cord and 420 for
dura. No closed-volume measurement is reported. The endpoints remain visibly
and mathematically open at the source limits.

Across 432 sampled cross-sections (quarter, half and three-quarter positions
between adjacent image planes), each surface yields one closed intersection
polygon with no strict nonadjacent segment crossing. On all 195 paired sampled
sections, the cord section points remain inside the corresponding dural section.
These sampled checks do not prove absence of every continuous self-intersection,
inter-surface contact or biological boundary error.

The candidate package is `output/msk-lumbosacral-sub03/surface-candidates/`.
Its `standalone.html` embeds both meshes and supports separate envelope layers,
combined views, structure isolation and reset. Browser testing over localhost
loaded both meshes, exercised those controls and recorded no console errors.
The production viewer and deployed application are unchanged. Direct file
launch was not tested because the browser tool restricts that protocol.

Evidence: [loft audit](msk-lumbosacral-nerve-source-review/open-envelope-loft-audit.json),
[viewer provenance](msk-lumbosacral-nerve-source-review/open-envelope-viewer.json),
and [browser checks](msk-lumbosacral-nerve-source-review/open-envelope-browser-checks.json).
Reproduce with `tools/anatomy_sources/loft_lumbosacral_contours.py`, followed by
`tools/anatomy_sources/build_lumbosacral_surface_viewer.py`.

This establishes inspectable image-backed candidates under explicit interpolation
assumptions. It does not resolve missing nerve rootlets, gray/white matter,
conus-tip completeness, full dural/CSF volumes, compression interfaces or the
remaining MSK anatomy. No requirement has been marked complete from these checks.

## Independent full-mesh intersection screens

The saved browser-mesh bytes were checked with PyMeshLab 2025.7.post1's
[self-intersecting-face filter](https://pymeshlab.readthedocs.io/en/latest/filter_list.html#compute-selection-by-self-intersections-per-face),
individually and as a combined cord/dura mesh. No faces were selected. Positive
and negative synthetic controls are retained: the filter detects transverse
crossings, including a crossing beyond a shared vertex, and accepts a valid
shared edge. However, it misses both a coplanar overlap and a coplanar fold over
a shared edge. Its zero result is therefore not accepted alone as clearance.

A separate screen supplements that demonstrated blind spot. VTK 9.2.6's static
cell locator supplies bounding-box candidate pairs. Plane-distance tests and
translated, projected convex-polygon clipping test positive-area overlaps.
Controls recover the known 0.08 mm² coplanar overlap and 0.125 mm² folded-edge
overlap, and return zero for separated triangles and a valid shared edge. The
bounds-query controls also check that intersecting candidates are returned in
both directions, including a triangle contained inside another one's bounds.

At a 1e-8 mm plane tolerance, 3,461,714 broad-phase pairs contain no numerically
coplanar candidates. At the wider 1e-4 mm tolerance, 3,462,164 broad-phase pairs
include 246 near-planar candidates (85 cord/cord and 161 dura/dura), with no
positive-area overlap above 1e-10 mm². The wider pass is conservative: a projected
overlap there would be a near-planar warning, not automatically a true 3D
intersection. Isolated tangencies are not classified as positive-area overlap.

The combined result is **no intersections detected by these complementary
numerical screens**, not an exact-arithmetic proof or clinical validation.
Original vertices and faces remain unchanged; no geometry was repaired or
removed to obtain the result. Open source boundaries remain intentional.
The additional PyMeshLab installation is confined to local research staging
and is not a production dependency.

Evidence: [independent filter and controls](msk-lumbosacral-nerve-source-review/independent-intersection-screen.json),
[coplanar screen](msk-lumbosacral-nerve-source-review/coplanar-overlap-screen.json),
and [near-planar screen](msk-lumbosacral-nerve-source-review/near-planar-overlap-screen.json).
Reproduce with `tools/anatomy_sources/check_neural_mesh_intersections.py` and
`tools/anatomy_sources/check_neural_coplanar_overlaps.py` (optional tolerance
argument `0.0001` for the wider screen). No coverage requirement or clinical
approval was changed.

## Reader integration — 30 September 2026

The thoracolumbar-fracture reporting module now offers the preserved MRI-derived
cord/dural contour envelopes as a partial source reference in its 3D anatomy tab.
The original reporting orientation guide remains selectable, and its walkthrough
landmarks and report fields are retained. A matching native MRI/contour review
figure is available both in the Images tab and alongside the model.

Runtime assets are under `web/anatomy/liu-lumbosacral-sub03/` and
`web/reference-media/liu-lumbosacral-sub03/`. The source-reference registry validates
manifest and asset fingerprints, geometry headers, local paths, available tissue
layers and image dimensions before exposing the reference. The model uses its
own registered family, so unrelated spine modules retain their existing renderers.
Both open source endpoints, the interpolation assumptions and missing neural
compartments remain explicit in the reader. Midline source cameras now name
right and left lateral views directly.

Desktop/mobile browser checks verified the actual reporting page: both meshes,
cord/dura switching, isolation, guide fallback and return, the matching source
image at 2240 × 1440 in the lightbox, and no horizontal overflow at 390 px.
The 241 relevant Python tests and eight orientation tests passed. The local
startup stall on generated recovery-copy WebPs was fixed by excluding those
copies from illustration discovery; original recovery files are preserved.

[Reader browser evidence](msk-lumbosacral-nerve-source-review/reader-browser-checks.json)
records the source configuration and rendering hashes. The runtime rights
inventory includes the new MRI figure. The model/image evidence entries retain
pending anatomical review and no inferred full-structure bindings. Consequently,
the 5,229 representation requirements remain 0 verified, 161 unverified and 5,068
missing. This is an actual reader improvement, not completion of the clinical/
commercial-quality goal. Changes are in the local workspace; no new deployment
was performed in this step.
