# Tibial-cartilage source-variant review

This review compares original public Open Knee(s) oks003 masks and mesh variants.
It does not approve clinical accuracy or establish an undocumented revision history.
All source coordinates, voxels and surfaces remain unchanged.

The unversioned `oks003_TBC-L_AGS.nii` and `oks003_TBC-M_AGS.nii` masks were
downloaded through their published repository links. Their original byte counts,
SHA-256 values, modification dates and ETags are in `acquisition.json`. Four
additional original meshes (raw and earlier processed versions) and the public
MRML scene were acquired; see `comparison-source-acquisition.json`. The scene
does not establish the selected `_02` cartilage meshes' ancestry.

## Measured comparison

| Side | Candidate mask volume (mm³) | Raw mesh difference | Earlier processed difference | Currently selected `_02` difference |
|---|---:|---:|---:|---:|
| Lateral | 1814.607 | −0.36% | −1.62% | −8.69% |
| Medial | 1786.575 | −0.47% | −4.01% | −11.66% |

These differences compare an enclosed surface volume with the volume of occupied
author-label voxels. They are **not estimates of biological error**. The raw
surfaces match the candidate label in all six sampled native MRI sections;
earlier processed surfaces have section Dice 0.992–0.998, and selected surfaces
0.959–0.970. Exact values and source hashes are in [variant-audit.json](variant-audit.json).

- [Lateral comparison](tbc-l-variants.png)
- [Medial comparison](tbc-m-variants.png)

Only declared NIfTI coordinates are used; there is no fitted registration.
Images show unchanged source MRI samples, cyan candidate-label contours and gold
mesh contours. Higher agreement with the author's label does not independently
prove a more accurate tissue boundary. The source processing specification
requires checking for lost features/volume, but does not provide an exact log
explaining these individual `_02` revisions.

## Audit correction

The previous intersection routine omitted contours when a plane ran exactly
along raw mesh edges or faces, yielding false zero overlaps. The routine now
retains on-plane edges, removes internal coplanar triangulation edges and
deduplicates shared boundaries without geometric rounding. Seven analytic box,
coplanar-face and tangent-vertex tests pass in the scientific Python runtime.

Re-running all existing 14-structure/84-section comparisons reproduced the
previous JSON byte for byte: SHA-256
`5bd53e668563dbbd23b8a511caba9c0c6d1f0029658221d5e08b5caf0ea89fa0`.
No existing viewer geometry, registration evidence or clinical approval changed.

Reproduce with `tools/anatomy_sources/audit_openknee_tibial_variants.py` and
`tests/test_mesh_plane_sections.py`. The script uses the same scientific runtime
as the paired-source audit (NumPy, SciPy and Matplotlib).

## Decision

Retain the selected assembly and its two explicit unresolved revision mappings.
The masks are now quantitatively evaluated candidates, not merely rejected
filenames. Before choosing a replacement, review the actual MRI tissue boundaries
and obtain a defensible explanation of the processed revisions. Do not substitute
a raw or earlier surface solely to obtain a higher label-overlap score.
