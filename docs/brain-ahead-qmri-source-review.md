# AHEAD quantitative MRI source context

Pinned source: [AHEAD quantitative MRI templates (MNI2009b), version 3](https://doi.org/10.21942/uva.19646364.v3), by P.L.E.A. Bazin, B.U. Forstmann, J.M. Alkemade, S. Miletić and S.J.S. Isherwood. The publisher [versioned metadata](https://api.figshare.com/v2/articles/19646364/versions/3) grants CC BY 4.0 and describes population median and interquartile-range maps. File names identify 105 subjects. These group templates are distinct from an individual clinical examination and from the 97-subject MASSP source atlas.

Six original files were acquired: median and interquartile-range maps for R1, R2* and quantitative susceptibility. `r2map` is the publisher's filename code; the publisher description identifies the contrast as R2*. Intensity units and quantitative calibration have not been independently reconciled, so source values are retained without clinical numerical interpretation. Derived myelin, iron and proton-density maps are outside this acquisition; they are not counted as absent requirements or waived from any relevant future investigation.

All six files match publisher byte lengths and MD5 checksums, with independent SHA-256 records. The compressed total is 397,892,250 bytes. Raw volumes remain offline in `.research/ahead-templates`; `brain-ahead-qmri-source-review/acquisition.json` preserves the acquisition and rights evidence.

Every file has a 394 × 466 × 378 float32 array and exactly the same declared affine as the MASSP best-label volume, with RPS storage orientation. All original voxel values are finite. Their common 0.5 mm sampling grid must not be interpreted as proof of original acquisition resolution or anatomical precision. Shape and affine equality support an unresampled overlay, but do not independently validate the source registrations, cohort correspondence or boundaries.

Three native sections were reviewed in all three contrasts: axial RAS Z = −3 mm, coronal Y = 0 mm and left sagittal X = −20 mm. The fixed regional crop includes the selected pallidal/putamen contours and surrounding MRI context. Plot axes and plane indices preserve original world coordinates. Display-only flips place RAS axes in increasing order; nearest-neighbour display and per-plane 2nd–98th percentile windows are disclosed in `native-qmri-review.json`. No source voxel was resampled, smoothed, recoloured in storage or modified.

The median views include the original MASSP best-label contours for GPi, GPe and putamen; an unmarked median version is also retained so contours cannot conceal underlying contrast. Interquartile-range views retain population variability separately. The regions have visible, contrast-dependent internal and surrounding signal patterns. The illustrations do not independently delineate every clinical boundary or validate fine laminae, diseased anatomy or routine CT/MRI appearances.

Artifacts:

- `native-qmri-med-review.png`: native median sections with source contours.
- `native-qmri-med-unmarked-review.png`: the same native median sections without annotations.
- `native-qmri-iqr-review.png`: native population variability, without atlas contours.
- `native-qmri-review.json`: source hashes, geometry, intensity ranges, finite-voxel checks, plane indices, crops and display windows.

All records and illustrations are in `docs/brain-ahead-qmri-source-review/`. Rights attribution accompanies these derived views; their changes are limited to stated section/crop selection, grayscale display windows, axis presentation and explicit overlays. No clinical approval, reader-atlas registration, runtime asset or complete anatomical coverage binding has been added.

Reproduction uses `python -m tools.anatomy_sources.acquire_ahead_qmri_templates` and `python -m tools.anatomy_sources.review_ahead_qmri_templates`, with the separate scientific dependencies. Complete structure extent, patient-specific correspondence, original source-method validation and specialist anatomical review remain required.

## Direct joint-model MRI comparison

The new joint-interface model is now sectioned directly against the native MRI templates. These overlays are intersections of the exported triangles with the actual RAS image plane, not re-drawn label-mask contours. Each model file hash and its atlas/source selection are checked before plotting. Neither an alignment transform nor source resampling is fitted.

The comparison includes axial Z = −3 mm, coronal Y = 0 mm and sagittal X = −20/+20 mm, in each of the three median contrasts. Twelve annotated panels therefore include bilateral sagittal context as well as bilateral axial/coronal context. The corresponding twelve unmarked median panels and twelve IQR panels remain available. Twenty-four distinct source sections (six volumes × four planes) are recorded with native indices, display windows and exact direct-section segment counts.

New artifacts are prefixed `native-qmri-joint`: `native-qmri-joint-med-review.png`, `native-qmri-joint-med-unmarked-review.png`, `native-qmri-joint-iqr-review.png` and `native-qmri-joint-review.json`. Earlier source-label contour comparisons remain preserved separately. Direct triangle sections have consistent coordinates across all three contrasts; apparent tissue signal and boundary visibility still vary by contrast.

This supplies review evidence for the actual exported geometry. Selected planes do not establish every continuous boundary, fine medullary lamina extent, whole-surface MRI accuracy or clinical approval. The 105-subject template versus 97-subject atlas context, derived subvoxel interpolation and unverified quantitative intensity units remain explicit. No runtime representation or clinical fidelity credit was added.

Reproduction adds `--mesh-source .research/massp-brain/joint-interface-surfaces` to `python -m tools.anatomy_sources.review_ahead_qmri_templates`. All six source grids/hashes and all six exported mesh hashes passed, and the annotated/unmarked views were visually inspected. No stored voxel or mesh coordinates changed.
