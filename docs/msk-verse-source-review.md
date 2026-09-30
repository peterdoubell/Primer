# Paired vertebral CT/segmentation source candidate

27 September 2026. The [author-maintained VerSe repository](https://github.com/anjany/verse)
provides author-linked complete-data archives with CT volumes, vertebral masks,
centroids and preview images. Its data licence is CC BY-SA 4.0; the repository's
MIT code licence is separate and is not applied to medical images or masks.
The inspected complete/restructured release is distinguished from older challenge
formats and historical licence descriptions.

The README was preserved at commit
`02b292b86021a8873043124982f5f58da9ba1cb8`, with a content hash in the
[source record](msk-verse-source-review/source-review.json). The training archive
is approximately 11.5 GB. Only its central directory and six small metadata
members were read using bounded HTTP ranges. HTTP 206, Content-Range, consistent
ETag, member names, uncompressed sizes and ZIP CRC values were checked. No full
cohort download was performed.

Three candidate centroid/CT metadata pairs were inspected. `sub-verse521`
contains centroid labels 7–24 (C7–L5), including every T1–L5 label, without label
25 (L6). Its source acquisition metadata reports about 0.684-mm in-plane spacing
and 1.5-mm slice thickness. The other two inspected candidates include L6 labels.
This is a bounded selection for review, not a finding of normal anatomy or a
judgment that anatomical variants are unsuitable in general.

The CT and segmentation payloads have not yet been inspected. Next checks must
compare actual NIfTI dimensions, voxel spacing, qform/sform and label alignment;
verify the labelled anatomy and field-of-view boundaries against CT; inspect
source annotations/pathology; and retain original data/derivation hashes. No
patient-specific scan, segmentation or model has been placed in runtime.
Published annotation methodology is not independent approval of this case.

The sample represents a route toward image-backed geometry. It does not replace
missing soft tissues, site-specific clinical review or the full MSK scope.
[Preserved README](msk-verse-source-review/README-source.md) includes the authors'
requested dataset and benchmark citations. Reuse must retain data attribution
and ShareAlike obligations for applicable derivatives.

## Selected case payload acquired and geometry checked

The selected CT, mask and author preview were acquired as bounded archive
members, with matching archive ETag, local member names, sizes and ZIP CRCs.
[Acquisition evidence](msk-verse-source-review/case-acquisition.json) records
individual SHA-256 hashes. The CT member is about 139 MB; the full cohort was
not downloaded. Files remain in `/tmp/primer-msk-sources/verse/verse521`.

[Geometry evidence](msk-verse-source-review/case-geometry.json) records matching
512 × 512 × 487 CT/mask grids with 0.68359375 × 0.68359375 × 1.0-mm stored
spacing and matching selected affines. The CT has qform/sform codes 1/1; the
mask has 0/2, so its unused qform is not treated as authoritative. Centroid
orientation matches the L/A/S voxel-axis codes. Every rounded centroid falls
inside its corresponding segmentation label.

Only C7 touches the array boundary. All T1–L5 mask bounding boxes remain within
the volume, but that does not establish segmentation completeness or accuracy.
The source acquisition sidecar reports 1.5-mm slice thickness; this differs
from the 1.0-mm stored slice spacing and must not be relabelled isotropic
resolution. No voxel resampling, segmentation repair or model generation was
performed.

The [author preview](msk-verse-source-review/author-preview.png) was inspected
for readability and preserved unchanged under the dataset's CC BY-SA 4.0 terms
with the author/benchmark citations in the preserved README. It is not an
independent validation of the annotations. CT anatomy, individual pathology,
label boundaries and any eventual derived meshes still require direct review.
No runtime promotion or clinical approval was made.

## Direct T8 CT/mask inspection

The CT payload has now been fully decoded and checked for finite values. A
[nine-plane review](msk-verse-source-review/t8-orthogonal-review.png) compares
original label 15 with native axial, sagittal and coronal CT planes. Plane
indices, crops, spacing, scaling, source hashes and the render hash are recorded
in [review metadata](msk-verse-source-review/t8-review-planes.json). CT voxels and
mask labels were not resampled or edited; display interpolation is nearest.

The overlay uses explicit integer pixel centres matching the displayed pixels,
correcting a half-pixel plotting offset caught during inspection. Orientation
letters come from the selected NIfTI affine. The display range is recorded as
scaled CT values; the plot does not assert an independently calibrated intensity
measurement. Only T8 is outlined; adjacent vertebrae are expected in some planes.

The selected planes demonstrate gross body/posterior-element correspondence.
This is not an exhaustive segmentation review or clinical approval of cortical,
endplate, facet or pedicle boundaries. Voxel-scale differences and partial-volume
uncertainty remain. No mesh was generated or substituted into another atlas.
The derived review image follows the source data's CC BY-SA 4.0 terms; dataset
and benchmark attribution remain in the pinned source README. The reproducible
renderer is `tools/anatomy_sources/render_verse_t8_review.py`.

## Offline T8 surface derived from the original label

A Lewiner marching-cubes surface at label isovalue 0.5 now preserves the original
T8 segmentation grid without smoothing, decimation, filling or component removal.
It contains 19,258 vertices and 38,516 triangles. The mask has one component under
both 6- and 26-connectivity; the surface has one connected component and passes
the basic closed/non-manifold/winding/degeneracy checks. Every surface vertex lies
on the original interpolated mask boundary, and voxel/world round trips agree.
Winding correction is disclosed in the [derivation audit](msk-verse-source-review/t8-surface-audit.json).

The CT declares millimetres; the mask's spatial-unit flag is unknown. World
coordinates are therefore anchored to the CT's selected affine after verifying
numeric CT/mask affine equality. The unknown mask flag is retained, not silently
rewritten. The original source-label and CT hashes accompany the derivation.

[Three-view surface inspection](msk-verse-source-review/t8-surface-review.png)
shows visible voxel stepping. This is an approximation of the source labels,
not an increase in CT or segmentation resolution. It does not certify fine
cortical, facet or endplate detail, nor rule out self-intersections or annotation
errors. No volume or stability measurement is offered for clinical use.

The derived surface is preserved at `output/msk-verse521/t8-surface.npz`, with
CT RAS world coordinates, voxel coordinates, faces and the affine. The renderer
uses explicit anatomical camera directions and no geometry modifications.
Source data and applicable derivatives retain CC BY-SA 4.0 with VerSe attribution.
No runtime promotion, Z-Anatomy registration or clinical approval was made.

## Saved artifact checked independently

A separate checker reloads the preserved NPZ, verifies its hash and both source
NIfTI hashes, solves the world-to-voxel equations independently and samples the
original mask. All 19,258 saved vertices lie on the mask's interpolated 0.5 level,
with zero measured coordinate discrepancy in this case. A separate divergence-
theorem calculation gives mesh volume 26,585.58 mm³ versus mask occupied-voxel
volume 26,645.94 mm³, a −0.2265% difference from the isosurface approximation.

[Saved-surface check](msk-verse-source-review/t8-saved-surface-check.json) and
`tools/anatomy_sources/check_saved_verse_t8.py` preserve the result. This confirms
artifact-to-mask consistency, not biological bone-volume accuracy, every triangle
interior, clinical boundary correctness or overall high fidelity. Nothing was
repaired, promoted or clinically approved.

## All-level component inventory

All T1–L5 labels were checked in the original mask before wider surface
derivation. Sixteen are single components under both 6- and 26-connectivity.
T7 contains a main component of 52,461 voxels and one additional voxel under
face adjacency, but all 52,462 connect under 26-neighbour adjacency. Its exact
voxel/world location is retained in the
[component inventory](msk-verse-source-review/all-level-components.json).

No component was removed or reclassified as noise, fracture or disease. A
single diagonal connection is a source-label property requiring image review,
not a clinical diagnosis. Every T1–L5 label remains inside the volume boundary.
This inventory does not establish full anatomical correctness or waive any
reportable substructure. The reproducible checker is
`tools/anatomy_sources/check_verse_label_components.py`.

## Full T1–L5 set derived offline

All seventeen labels now have separate surfaces in the same CT world frame,
with 798,442 triangles in total. Every foreground voxel count matches the
original component inventory. No smoothing, decimation, filling, source-level
substitution or component removal occurred. The regenerated T8 arrays match
the previously checked T8 artifact exactly.

An initially strict all-vertices-on-isovalue assertion stopped at T1. A
[single-cell reproduction](msk-verse-source-review/t1-isovalue-reproduction.json)
and inspection of the version-pinned implementation established that Lewiner
adds weighted cell-centre helper vertices. In this binary case those centres
can sample 0.625 rather than 0.5. The
[implementation review](msk-verse-source-review/lewiner-helper-review.json)
records the primary source and distinguishes this documented approximation
from registration error. The audit continues to require exact edge-vertex
agreement, rejects unexplained vertex types, and explicitly records helper
counts and deviations. No helper vertex was projected or otherwise edited to
make the metric pass.

All surfaces pass the basic open-edge/non-manifold/degeneracy checks. T12 has
an additional eight-triangle surface component, which is retained and requires
source-image interpretation; component count alone is not a diagnosis or a
reason to remove it. Clinical boundaries and every triangle interior remain
unverified. The full [surface audit](msk-verse-source-review/chain-surface-audit.json)
and [offline package](../output/msk-verse521/t1-l5/manifest.json) retain source
hashes, per-level findings, extraction versions and ShareAlike attribution.
No runtime promotion, normality claim or clinical approval was made.

## Retained T12 and T7 components localized against CT

The small T12 component has six vertices and eight triangles. Its centre is
original voxel `[278, 206, 202]`, whose label is zero; all six face neighbours
are T12. Independent background-component analysis identifies exactly one
fully enclosed background voxel at that position. The component has negative
signed volume (−0.0778834 mm³), consistent with an inward-facing boundary.
It is therefore a source-mask cavity boundary, not a disconnected foreground
bone island. This establishes the segmentation property only: its biological
meaning and whether it reflects a segmentation error remain undetermined.

The previously identified T7 singleton at `[208, 144, 341]` has no face-adjacent
T7 voxel. Its actual diagonal neighbours are recorded explicitly. Both
features have native axial, sagittal and coronal CT comparisons, with original
label contours and affine-derived direction markers. Pixel centres are used
for both image and contour coordinates. No source voxels or surface triangles
were removed or modified.

The reproducible checker is `tools/anatomy_sources/review_verse_source_components.py`.
It verifies the source CT/mask and saved T12 surface hashes before analysis.
See [component evidence](msk-verse-source-review/retained-component-review.json)
and [CT comparisons](msk-verse-source-review/retained-components-ct-review.png).
This resolves an extraction ambiguity, but does not establish clinical boundary
accuracy or authorize runtime promotion of the full vertebral chain.

## Continuous CT review for every T1–L5 label

`output/msk-verse521/review/index.html` is a standalone review artifact with all
17 cropped CT volumes and original target-label arrays embedded. Each crop
retains the label's complete bounding box and surrounding native voxels. Every
stored float32 CT value is checked for exact equality with the decoded source;
no voxel resampling is performed. Source CT/mask hashes are checked first.

The viewer provides all axial, sagittal and coronal slices, adjustable CT
windowing, an original-label toggle, source voxel coordinates, affine-derived
RAS coordinates and pointer-based numerical voxel inspection. Physical voxel
spacing determines the displayed aspect ratio. The source labels are whole
vertebrae; this does not create separate pedicle, facet or endplate labels.
Source attribution, adaptation description and CC BY-SA 4.0 travel with the HTML.

Browser checks covered all 51 level/plane centre samples against independently
extracted source values and all 102 first/last slice positions. Window presets
and overlay controls were exercised without console errors. These are data and
interface checks, not exhaustive rendered-pixel comparisons or anatomical
boundary approval. The dataset remains an offline review candidate; continuous
availability for inspection is not evidence that every boundary has been approved.

Rebuild with `tools/anatomy_sources/build_verse_review_viewer.py` using the staged
source NIfTI files and NumPy/nibabel. The HTML needs no external image server or
JavaScript library: open it in a browser supporting `DecompressionStream`.
[Array/source evidence](msk-verse-source-review/full-volume-review-viewer.json)
and [browser checks](msk-verse-source-review/full-volume-browser-checks.json)
record the source fingerprints, geometry and test scope.

## Browser-ready whole-vertebra package and correspondence bounds

All 17 T1–L5 surfaces are now repacked as gzip-compressed BP3D meshes under
`output/msk-verse521/browser-parts/`. Every saved world-coordinate vertex and
triangle index survives the decode roundtrip exactly: no floating-point
position loss, smoothing, decimation, filling or component removal. Generated
area-weighted unit normals affect lighting only. The package contains 798,442
triangles; original CT RAS coordinates and millimetres are retained.

`standalone.html` embeds the manifest and all compressed geometry and requires
no geometry fetches. `index.html` uses the separate files. Both link to the
matching standalone CT review volume. The latter file-based variant can be
served with `python tools/anatomy_sources/serve_verse_review.py`, which binds
only localhost port 8826 and supplies gzip transport headers. Neither variant
has been promoted into production. The production viewer source is unchanged;
its offline copy adds an atlas registry entry and spine range, and the
standalone variant substitutes embedded-data loading.

Browser review loaded all 17 meshes and exercised selection/isolation for all
17 source objects. The standalone variant also rendered and supported T12
isolation, superior orientation, reset and posterior orientation. The CT link
opened the matching case. No console errors were recorded. The visible
voxel-stepped source surfaces are retained, not cosmetically smoothed into an
unsupported high-resolution appearance. Fine anatomical accuracy remains open.

A separate check sampled every triangle centroid in the trilinearly
interpolated original binary label. Its directional normal-ray search failed
to bracket a crossing within 2 mm for 102 centroids, and some other rays reached
a more distant boundary. These ray distances are **not nearest-surface errors**.
They must not be interpreted as evidence of millimetre-scale anatomical defects.

A second calculation establishes exact source-boundary witnesses. Each witness
is the midpoint of a grid edge with one foreground and one background endpoint,
so its trilinear label value is exactly 0.5. Every triangle contains such a
witness vertex. All world/voxel transformations were checked against the source
affine. Every centroid lies within 0.561163 mm of a known boundary witness,
including the ray-search outliers. Convexity gives a conservative directed
mesh-to-source bound of 1.110699 mm for **all triangle interiors**, using the
best eligible witness vertex for each face. These are upper bounds to the
source segmentation, not measured clinical errors; reverse source-to-mesh
distance and biological boundary correctness remain unproved.

Evidence:

- [Package preservation](msk-verse-source-review/browser-mesh-package.json)
- [Browser checks](msk-verse-source-review/browser-mesh-checks.json)
- [Centroid normal-ray measurements](msk-verse-source-review/triangle-centre-correspondence.json)
- [Exact boundary-witness bounds](msk-verse-source-review/surface-witness-bounds.json)

The source labels remain whole vertebrae. Separate body walls, endplates,
pedicles, laminae, transverse/spinous and articular processes still require
anatomical validation. Discs, ligaments, cartilage and neural structures are
not supplied. No requirement was marked complete or removed on the strength
of these conversion checks.

## Reader integration — 30 September 2026

The thoracolumbar reference now offers the preserved sub-verse521 T1–L5 CT-derived surfaces: 17 separately selectable whole-vertebra objects, 798,442 triangles, without changing their saved positions or topology. The MRI cord/dura reference and reporting orientation guide remain selectable. The CT and MRI cases are independent; no shared registration or combined anatomy is claimed. The 3D pane shows the selected source's accompanying image resources.

A linked CT plane viewer supplies native crops around each vertebral label, with axial/sagittal/coronal slice selection, original-label overlays, window controls and physical voxel aspect ratios. All 17 embedded CT arrays and masks match the saved acquisition-derived crop audit hashes. The embedded data are unchanged; the executable script was separated into `ct-reference.js` to obey the reader's existing Content Security Policy. Hosted delivery uses the established gated redirect to public source media; runtime provenance validation retains the small mesh package and viewer files locally.

Reader checks are recorded in `msk-verse-source-review/reader-browser-checks.json`: all 17 structure selections; independent MRI and guide switching; desktop/mobile layouts; 51 plane centres matching recorded scaled CT values; 102 first/last slice positions matching original crop bounds; window and overlay controls. Source validation does not establish independently calibrated HU, normality, pathology, accurate biological segmentation boundaries or complete reportable substructures. The source data and adaptations retain CC BY-SA 4.0 with attribution.

All anatomical reviews remain pending. No requirement is marked verified because a labelled whole vertebra or matching CT crop is now accessible. The preserved T7 diagonal connection, T12 enclosed background boundary, isosurface helper approximations, unavailable discs/ligaments/neural anatomy, and case-specific limits remain explicit. This integration is local work following PR #58; it is not included in that already deployed release.

### Selected-level source correspondence

Selecting one VerSe vertebra now updates the CT link to its exact source level. The CT viewer accepts only levels present in the embedded source data; unknown values retain the default T1 view. Clearing the selection restores the general CT link. All 17 model/link/initial-CT-level pairs were checked through real browser controls and are recorded in `level-correspondence-browser-checks.json`. The catalog rejects a level map that differs from the registered source manifest. This adds source correspondence, without registering the separate MRI case or approving any anatomical boundary. Earlier browser records remain historical evidence for their recorded fingerprints.

### Acquisition resolution disclosure

An independent artifact-pair review found no changed geometry, wrong case pairing, reflection or crop loss, within the limits recorded in `independent-reader-fidelity-review-2026-09-30.json`. The source acquisition JSON records 1.5 mm slice thickness; the stored CT grid has 1.0 mm slice spacing. The local CT explorer, anatomy notes and evidence ledger now expose that difference without claiming that spacing establishes effective anatomical resolution. The added note was checked on mobile at 390 pixels without horizontal overflow; it does not change stored CT/mask values or source meshes.
