# Manually annotated cervical dorsal-rootlet source

27 September 2026. This acquisition supplies voxel labels and paired MRI as a
candidate alternative to fixed-radius nerve tubes. It does not replace the
lumbar case or establish complete nerve anatomy.

## Pinned source, scope and rights

The primary source is [Spine Generic data-multi-subject](https://github.com/spine-generic/data-multi-subject),
release `r20250314`, resolved identifier
`a0738046538232df8e09eba8d98899eada9c11d5`. The source metadata was inspected
through the public GitHub API. The selected raw T2w image and seven label maps
were retrieved through the public mirror advertised in the repository's
annex configuration, with exact sizes and SHA-256 values checked against the
published annex keys. The whole 26 GB dataset was not downloaded.

The repository's legal licence file contains **CC BY 4.0**, while
`dataset_description.json` says **CC0**. Both original files are preserved.
Attribution and the CC BY 4.0 notice are retained; the data are not represented
as unambiguously public domain. Data rights are kept separate from the rootlet
prediction code's MIT licence.

The selected subject, `sub-amu02`, has four manual-rater rootlet masks and one
STAPLE consensus. The snapshot sidecars retain C2–C8 wording, but the authors'
[annotation protocol](https://github.com/ivadomed/model-spinal-rootlets/issues/17)
explicitly specifies **dorsal C2–T1**, starting with numeric value 2 for C2 and
subsequent levels sequentially. The arrays contain class 9, retained as T1 with
that source evidence. This does not provide ventral-rootlet labels. A newer
prediction model's broader scope is not retroactively assigned to this dataset.

[Scope and licence evidence](msk-rootlet-source-review/source-scope-and-rights.json)
and [acquisition records](msk-rootlet-source-review/acquisition.json) preserve
these distinctions. The actual image/label files remain in local staging.

## Grid and annotation audit

The MRI and all five rootlet maps share shape **64 × 320 × 320**, approximately
**0.8 mm isotropic stored spacing**, millimetre spatial units, and compatible
selected affines. Label conversion from float64 to uint8 was lossless because
every stored label was a finite integer in the expected class set. No
registration, resampling, smoothing or component removal was applied.

| Source level | Consensus voxels | Pairwise manual Dice range |
|---|---:|---:|
| C2 | 237 | 0.720–0.830 |
| C3 | 224 | 0.626–0.687 |
| C4 | 54 | 0.331–0.578 |
| C5 | 87 | 0.396–0.695 |
| C6 | 102 | 0.419–0.633 |
| C7 | 101 | 0.456–0.651 |
| C8 | 160 | 0.449–0.729 |
| T1 | 164 | 0.000–0.671 |

The consensus contains 1,129 labelled voxels. None of its class bounds touches
the image-array edge. Rater 3 supplies no T1 voxels; this is retained as an
annotation difference, not interpreted as absence of the anatomical structure.
The consensus is derived from raters, not an independent fifth manual observer.
Dice measures overlap, not biological truth, and no acceptance threshold was
invented to mark these structures complete.

Connected-component inventories are preserved under both face and full-neighbour
connectivity. They are not converted into named individual rootlets or sides.
Small components are not removed or joined merely to make cleaner-looking models.

The supplied spinal-cord context mask is algorithm-generated according to its
sidecar, not accepted as a manual anatomical reference. The manual disc dlabels
contain exactly one voxel for each of eleven label values: they are landmarks,
not disc volumes, annulus/nucleus segmentations or endplate surfaces.

## Review artifact and remaining work

The [paired MRI comparison](msk-rootlet-source-review/manual-rater-mri-comparison.png)
shows the same native coronal-oriented plane and display window for the four
raters and consensus, beside the MRI alone. Only labels intersecting that plane
are visible. The [case audit](msk-rootlet-source-review/case-and-rater-audit.json)
records the plane/crop/window, per-rater counts, agreement, grid checks and
component sizes. These are source-review results, not clinical approval.

Reproduce acquisition with `tools/anatomy_sources/acquire_rootlet_case.py` and
the numerical/image review with `tools/anatomy_sources/audit_rootlet_case.py`.
No published prediction model was run, no fixed diameter was imposed, and no
runtime asset or completed MSK requirement was added. This is a cervical dorsal
rootlet candidate; ventral roots, lumbar roots, complete exiting nerves,
fascicular detail and the remaining MSK structures stay in scope.

## Observer comparison and boundary interpretation — 30 September 2026

The comparison package now contains 39 separate source-label surfaces for the
four raters and STAPLE consensus. Rater 3's missing T1 annotation remains an
explicit empty state. All five annotations use the original MRI coordinates
and the same full-set viewing frame and initial camera; isolating a label permits
closer inspection. The viewer exposes both boundary interpretations described below.

For this case, each consensus label equals the voxels selected by at least two
of the four raters. There are 390 unanimous voxels among 1,129 consensus voxels,
and no overlapping voxel receives conflicting nonzero level labels from the
raters. These are empirical properties of this case, not a general definition
of STAPLE or a probability of anatomical correctness.

The 0.5 interpolated display surfaces enclose 76.7–91.9% of the occupied label
voxel volume. The difference is substantial for these small labels, although
float32 positional transport error is below 0.000004 mm. It is representation
sensitivity, not measured error relative to real nerve tissue. Polygon density
cannot recover detail absent from the approximately 0.8 mm MRI grid.

A second reference uses the exposed faces of the occupied voxel-cell union.
Double-precision volume matches the annotated occupancy for all 39 nonempty
labels. The largest relative volume change after browser-format transport is
below 7e-7. However, 35 of the 39 voxel-boundary surfaces have non-manifold edges
because source cells touch along edges or corners. Those contacts are retained
and documented. Neither a smooth appearance nor exact computational occupancy
is taken as evidence of complete anatomical fidelity.

`output/msk-rootlet-sub-amu02/comparison.html` now lets a reviewer switch between
four raters/consensus and the interpolated surface/voxel reference. All ten
combinations passed browser checks: source mesh counts, explicit T1 absence in
the annotation, shared framing/camera and error-free rendering. The viewer was
tested over localhost in an isolated agent-browser session. It is an offline
review artifact; no production model or completion claim was added.

Evidence:

- [Separate annotation surfaces and agreement](msk-rootlet-source-review/annotation-surface-comparison.json)
- [Occupied-voxel boundary comparison](msk-rootlet-source-review/voxel-cell-boundary-comparison.json)
- [Current comparison viewer](msk-rootlet-source-review/comparison-viewer.json)
- [Ten browser combinations](msk-rootlet-source-review/boundary-choice-browser-checks.json)

The interrupted temporary cache had been cleared. The pinned source files were
recovered with all original hashes intact into `.research/anatomy-sources/rootlets`,
which is excluded from Git history and deployment. [Recovery evidence](msk-rootlet-source-review/source-cache-recovery.json)
records the path change without replacing the original acquisition snapshot.
Research dependencies are also local to `.research/`; production dependencies
are unaffected. `build_rootlet_cell_boundaries.py` and the existing comparison
builders reproduce the artifacts. Full biological boundaries, complete nerve
courses and the remaining MSK reporting structures still need adequate evidence.
