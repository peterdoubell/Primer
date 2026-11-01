# Additional SPL source classes

This adds a single-subject research reference to brain anatomy, MRI sella and adult neck-space modules. It supplies 19 additional brain classes and 75 head/neck classes. It does not establish complete reporting anatomy, biological accuracy, diagnostic suitability, current-patient registration or normal-population ranges. Pediatric neck masses and head/neck malignancy are not bound to this reference.

The source is `mhalle/spl-brain-atlas` at `bec24db25aad5f7600e2df3becfb1f883e61ff56`. The original source LUT names are retained. The source's unnamed raw code 1 is not fabricated or included among these 94 classes. The full source terms, Brigham notice and marked adaptation attribution accompany the viewer.

## Two independent representations

Original publisher positions and every triangle implied by the original strip primitives are preserved, including separate components and coordinate seams. The archived original VTK files retain original normals and strip primitives for independent reconstruction. The legacy Slicer 4.4 source scene uses RAS for these model coordinates without a parent transform. Modern unmarked-VTK LPS assumptions are not applied to this legacy scene.

Categorical-cell boundaries preserve every original label cell, cavity and component. They contain 298,878 vertices and 599,136 triangles across 94 classes. These are discrete source-label boundaries, not a validated biological surface or photorealistic reconstruction. Native T1/T2 arrays and the separate categorical grid reuse the existing SPL reference without resampling or fitted registration.

Original surfaces contain 232,954 vertices and 449,222 triangles. Source class 4084 (`right_anterior_rectus_capitis`) retains an unresolved separate eight-triangle component approximately 34.15 mm from the nearest same-code label-cell centre. It is explicitly disclosed, not removed or fitted. Coincidence analysis found higher geometric edge incidence in 29 source surfaces; no welding or cleanup is applied. Geometric FOV coverage of the source cells does not establish anatomical visibility or complete anatomical extent.

## Validation

Geometry payloads use the existing public source-media static delivery path in hosted deployments, reached through the authenticated viewer’s private redirect. Metadata, viewer scripts and module APIs remain protected. Payloads are excluded from the Python function bundle and hash-checked by the viewer and independent release readbacks.

The protected application routes and module API are tested with isolated synthetic data. The actual browser runs at 390 and 1440 pixels wide, loads both representations of all 94 classes (188 meshes per viewport), compares GPU position/index/world buffers with pinned source-derived bytes, and mounts/reopens inline viewers through all three reporting modules at both widths. Independent NumPy reconstruction compares 1,128 native MRI canvas states (82,202,624 pixels) with original MRI arrays and source-label samples. These are engineering checks; all clinical and anatomical approval flags remain false.

Reproduce the authenticated reader run with the installed requirements and Playwright:

```
python tools/check_spl_additional_context.py
python tools/check_spl_additional_pixels.py
python -m pytest tests/test_spl_additional_reference.py
```

`originals/` contains losslessly compressed pinned VTK originals. The preservation test independently reads each original with `tools/anatomy_sources/spl_additional_vtk.py` and recreates its runtime transport with the existing `pack_mesh` function. `original-surfaces/`, `categorical-cells/` and `MRI-coverage/` retain the acquisition/generation scripts and recorded geometric checks; those historical scripts name their original ignored research staging paths. `prototype/` preserves the earlier fixture-only experiment separately from the authenticated application evidence in `reader/`.

The exact historical runtime inverse covers only the reviewed shared-file edits and descriptor additions. It does not extend prior anatomical approvals or accept descriptor/approval drift. Existing production MRI and source payloads remain unchanged.

The broader whole-Primer task remains incomplete. Sellar cavernous sinuses, carotid encasement, lesion enhancement, skull-base bone and other reporting requirements are not supplied by the pituitary labels; regional hypothalamic classes are not independently validated nuclei. No atlas-source class is presented as a validated disease finding.
