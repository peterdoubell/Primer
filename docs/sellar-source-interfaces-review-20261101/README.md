# Sellar source interfaces and native-grid schematics

This evidence packet supplies 36 exact categorical-cell interface meshes and 108 section schematics for 21 selected SPL source classes. It retains all 652 shared unit-square faces, represented by 1,304 triangles. These are representations of the published source labels, not independently validated biological walls, nerve continuity or complete sellar reporting anatomy.

The source is the SPL-PNL/NAC atlas at commit `bec24db25aad5f7600e2df3becfb1f883e61ff56`. Its original native T1/T2 and separate categorical grid remain unchanged. Model positions are exact half-cell RAS coordinates derived from the pinned label affine. No smoothing, gap bridging, fitting, component deletion or model transformation is applied.

The 21 classes include the five optic-pathway labels; three pituitary source parts; ten hypothalamic regional labels; paired mammillary-body classes; and the third-ventricular lumen class. The 210 possible class pairs are all retained in the audit, including the 174 without shared faces. A nearest source-cell-centre distance is not anatomical tissue separation.

Four opposite-side-named pairs share 23 cell faces: left/right optic tracts (7), left/right inferior tuberal hypothalamic regions (6), left/right posterior superior hypothalamic regions (2), and the paired mammillary-body classes (8). These are retained source observations, with no automatic fusion, physiological interpretation or pathology classification.

Each mesh includes original cell/axis/direction/code provenance. The independent verifier enumerates every selected cell's six neighbours, then checks all mesh corners, face areas, triangle winding, SVG cell values and SVG contact sections through the original affine. The SVGs show cropped source ROIs containing each pair's source extent, with three native categorical sections. They do not synthesize MRI signal or resolve unacquired microscopic layers.

The controlled preview combines the source contact mesh, original T1/T2 samples, paired label overlays and the SVG sections. Browser checks cover 390/1440-pixel viewports, all 36 pairs, both source sides, both contrasts, every schematic and GPU geometry bytes. Independent reconstruction compares 125,927,424 actual MRI canvas pixels across 864 native-plane states (1,728 plain/marked canvases); 1,728 crosshair locations are checked. All 360 captured GPU camera states preserve a rigid basis within Float32 precision and keep selected geometry inside the frustum. This is fixture-only evidence, not authenticated application or production verification.

The preview now places each selected contact inside the two complete provided source-label boundaries, preserving all components. Blue/orange identify the same source classes in MRI, schematics and 3D; magenta marks shared-cell faces. Whole-context and contact-only framing are explicit options. Context fetch failure preserves the original MRI/contact view and supports retry; rapid selection and WebGL restoration retain the current pair. All 21 context meshes are read back from GPU buffers at both widths, and the context/interface shaders use identical GPU camera uniforms. The reader is now integrated locally into authenticated brain-anatomy and MRI-sella module pages; deployment verification remains pending. The original controlled-fixture evidence remains separate from the authenticated synthetic application evidence in `reader/`. That application run covers four module/viewport mounts and reopen cycles, 576 MRI states, 251,854,848 actual canvas pixels, 3,456 crosshair locations and 720 GPU camera states. Existing external lesson images were blocked during this isolated run and their delivery is not claimed. The 131-group, 840-part sellar reporting inventory is preserved in `requirement-source-granularity.json`: eight named-class candidate groups, five partial/regional context groups, and explicitly limited contact candidates. None of the 2,520 image/schematic/model obligations is granted anatomical or clinical approval by this packet.

Re-run the independent geometry/SVG verifier:

```
python tools/anatomy_sources/check_sellar_source_interfaces.py --output /tmp/sellar-interface-proof.json
```

With Playwright and Chromium installed, re-run the controlled browser preview:

```
node tools/check_sellar_interfaces_preview.cjs
```

The browser tool writes new results under `.research/sellar-interfaces-preview-rerun` by default; an optional first argument selects a different output directory. Historical generation scripts are retained in `generators/`; create `.research/sellar-source-interfaces-20261101` and run them from the repository root to reproduce their original `.research/sellar-source-interfaces-20261101` staging directory.

Full source terms and a marked adaptation notice accompany the packet. The whole radiology/math/physics goal remains incomplete.

Run `python tools/check_sellar_context_cameras.py` to independently check the shared layer cameras and source extents. `node tools/check_sellar_context_lifecycle.cjs` exercises failed context fetch/retry, rapid pair changes and WebGL context loss/recovery. The viewer makes user zoom cropping explicit. `integration-readiness.json` records a separate hosted-bundle prerequisite; it does not itself change deployment settings or data approval.
