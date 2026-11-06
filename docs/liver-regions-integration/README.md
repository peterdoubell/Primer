# Source MRI with eight liver regions

The Liver lesson and liver-mass / LI-RADS reporting references open a source MRI study with linked section labels and eight rotatable source-grid models. The source is Zenodo DOI 10.5281/zenodo.20746820, case `a1B8NQX1CHIcaQqs`. Original int32 MRI samples, NIfTI scaling, mask values and affine coordinates are retained. Gzip payloads are served as static assets, while reader entry routes retain authentication.

## Scope and limitations

The record says nine segments, but the archive schema contains background plus eight foreground regions. Segment IV is a single label; IVa and IVb are not inferred. MRI sequence identity and acquisition thickness have not been established from original DICOM. Array spacing is approximately 0.7422 × 0.7422 × 4.4000 mm. Models represent source annotation boundaries, not physical septa or independently validated vascular territories. Clinical/anatomical approval is pending. The record uses CC BY 4.0; archive configuration also contains Apache 2.0 boilerplate. Both are disclosed in the viewer and source metadata.

## Verification

- `tools/check_liver_region_source.py SOURCE_DIRECTORY` compares every published MRI/mask chunk with the original NIfTIs and checks all 256,676 boundary quads against original labels, including exact rounded Float32 corners and absence of duplicate or missing faces.
- `tools/run_liver_region_browser.py` launches an isolated local reader with synthetic credentials and data. It checks all 76 MRI raster planes, nine outline states, eight GPU buffers, invalid window handling, zoom, responsive layouts and reporting return paths. Requires Playwright through NODE_PATH.
- `node tools/check_liver_region_recovery.cjs` verifies rejection of corrupted metadata/pixels, independent 3D selection and retry.
- `tests/test_liver_region_delivery.py` checks asset hashes, static delivery and authenticated routing.

The browser checker refuses non-loopback origins because it creates a synthetic learner profile. Production validation must use a separate read-only checker.

`source-review.json`, `geometry-proof.json` and `expected-raster-hashes.json` preserve source review and independent expected values. `runtime-inverse.json` restricts compatibility normalization to exact reviewed changes in shared files; unknown edits are not normalized.

## Visual orientation review

Desktop/mobile inspection identified missing model direction cues and an absent all-region colour key. The viewer now projects the R/A/S patient axes with the same yaw/pitch convention as the model, identifies the opposite L/P/I directions, and distinguishes near-end-on axes with filled/towards and open/away circles. The verified region inventory supplies the colour key and selected/hidden status.

`node tools/check_liver_region_orientation.cjs` compares 48 rotation/tilt pairs against independently projected unit vectors and the actual GPU uniforms. It checks selected-region keys, narrow layout and loss/restoration of the WebGL context. Source geometry and MRI samples are unchanged.
