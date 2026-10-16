# Independent hippocampal geometry audit

Research only. This directory changes no labels, original marching-cubes meshes,
product files, or clinical readiness flags. The source is the supplied
HippUnfold training label grid for case 101006, named L and R by the source.
Native clinical laterality and registration are not established by this audit.

## Findings about the existing marching-cubes prototype

All 16 original meshes have negative signed world-space volume. The original
builder uses scikit-image's default `gradient_direction='descent'`, then reverses
faces only for a negative affine determinant. The default face convention is
left-handed, so determinant correction alone does not create outward triangle
winding. A one-selected-voxel control independently gives signed volume -1/6
with `descent` and +1/6 with `ascent`; returned scikit-image normals point outward
in both controls, while the parent builder discards them and derives normals
from its faces. The saved parent normals exactly match those face-weighted
inward normals. On the original source meshes, normal probes toward increasing
binary field occur for 475,777 faces and 236,196 saved vertex normals. Small
opposite/tied subsets occur at approximate or singular surface regions; the
probe is not a global proof of biological inside/outside.

The original meshes contain 1,100 vertices outside the exact trilinear 0.5 level
(maximum residual 0.125). Of 479,612 triangle centroids, 388,018 also lie off that
level; maximum centroid residual is 0.2083333333333357. Planar triangles are not
the exact curved trilinear isosurface, even when their vertices lie on it.
The implementation adds some interior vertices using an inverse-value-weighted
center, rather than solving the trilinear level equation. These diagnostics
describe the chosen approximation and cannot be corrected by renaming it an
exact isosurface. [Versioned implementation](https://raw.githubusercontent.com/scikit-image/scikit-image/v0.25.2/skimage/measure/_marching_cubes_lewiner_cy.pyx),
[API convention](https://scikit-image.org/docs/0.25.x/api/skimage.measure.html#skimage.measure.marching_cubes).

The 147 original nonmanifold indexed edges are all covered by 98 sets of exact
duplicate triangles, each appearing twice. Full duplicate coordinates and
orientation dot products are retained in `transport/manifest.json`; sampled
bad-edge midpoint values are 0.625. Every duplicate pair has opposite winding
(normal dot product -1). It would be unjustified to call those edges
faithful anatomical contacts solely from their incidence count. Nothing was
deleted or repaired to make the original meshes manifold.

## Source-preserving alternative actually built

`voxel-boundary/` contains all 16 exact categorical source voxel-cell boundaries.
Integer indices are voxel centers; each selected cell extends +/-0.5 along all
three source index axes. The original affine maps every corner to the supplied
world coordinate system. This follows the documented voxel-center convention,
while the choice of complete categorical cells is an explicit reconstruction
rule. [NIfTI header definition](https://github.com/nipy/nibabel/blob/master/doc/source/external/nifti1.h),
[NiBabel coordinate documentation](https://nipy.org/nibabel/coordinate_systems.html).

Every exposed cell quad is retained and split into exactly two coplanar
triangles. There are 236,196 quads and 472,392 triangles. Independent adjacent-
pair transition scanning reproduces the full face set. Oriented ray-transition
rasterization independently reconstructs every source voxel along all three
axes: 201,326,592 exact comparisons. This proves retention of every source
component and island without using connected-component pruning. Signed mesh
volume matches selected count times absolute affine determinant to within
6.87e-11 mm³; that is supplied-grid cell volume, not native clinical volumetry.

The exact cell boundaries retain 5,401 geometrically welded nonmanifold edges.
Every one has four incident triangles, independently matched to a 2x2 diagonal
checkerboard contact in the source categorical cells. No vertices were split
to disguise those contacts. Corner-only contacts can also exist; an edge-only
manifold check does not exclude them. Flat face normals are required to display
the actual categorical steps without smooth shading suggesting a fitted
biological surface. These retained contacts are source representation facts,
not evidence of normal or abnormal anatomical connections.

The alternative is exact for the declared categorical nearest-cell support.
It is explicitly **not** the trilinear half-level, an acquired 0.3 mm anatomical
surface, or new anatomical ground truth. HippUnfold's publication describes
processed training labels and resampled/registered images, so neither method
establishes native acquisition resolution or clinical validity.
[Source record](https://zenodo.org/records/7007362),
[HippUnfold methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC9831605/).

## Why tetrahedra are not an exact trilinear repair

`interpolation-controls-proof.json` exhaustively tests all 254 nonconstant
binary single-cube configurations with six Freudenthal tetrahedra, and with a
reflected body diagonal. The constructed triangle vertices and centroids lie
on their own piecewise-affine tetrahedral half-level to within 2.23e-16, but
248 configurations differ from the trilinear half-level. Maximum trilinear
residual is 0.375. Changing the tetrahedral diagonal changes center level-side
classification in 160 configurations despite identical source samples.

Tetrahedral interpolation is therefore a legitimate *different* reconstruction
when explicitly chosen, with directional dependence. It does not independently
increase fidelity to the categorical cell support or to the trilinear field.
Choosing it solely because a manifold/residual test becomes green would alter
the target geometry rather than prove the original target correct.

## Reproduce and inspect

Use the specified isolated Python runtime to run, in order:

1. `audit_meshes.py` — original MC audit, exact alternative, independent full
   transition/raster/volume proof in `voxel-boundary-proof.json`.
2. `interpolation_controls.py` — exhaustive tetrahedral controls and original
   winding/normals proof in `interpolation-controls-proof.json` and
   `original-winding-proof.json`.
3. `transport_and_contacts.py` — exact float32 source-index transport, independent
   scalar affine and outward face-normal oracle, source contact proof, full
   original duplicate-triangle diagnostic, and `transport/manifest.json`.

Transport is gzip-compressed little-endian binary: a 16-byte header (`HVX1`,
uint32 vertex count, uint32 triangle count, uint32 zero), followed by float32
XYZ source-index positions and uint32 triangle indices. Every half-integer
position is exactly float32-representable. Ordered indices have outward winding
**after** the original affine, whose determinant is negative. The manifest pins
compressed, decoded, position-buffer and index-buffer SHA-256 values.

The viewer must compare all uploaded geometry buffers against these source
arrays, use the complete source bounding box, retain source contacts and all
classes, and separately verify actual rendered image pixels. This audit has
not verified any viewer, GPU buffer, MRI display, anatomical recognition,
pathology, reportable-structure completeness, or clinical workflow.
