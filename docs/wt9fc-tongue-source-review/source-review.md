# WT9FC partial processed tongue reference

The acquired case is BeLong `sub-007_segID-001`, from [OSF WT9FC](https://osf.io/wt9fc/). Original MRI, label NIfTI, registration affine and demographic spreadsheet bytes retain their publisher MD5 and SHA256 digests. The linked dataset grant is CC0 1.0 Universal. The [separate article](https://www.nature.com/articles/s41597-025-05092-8) uses CC-BY-NC-ND 4.0; no article graphics or captions are repackaged.

The distributed MRI and masks have a 64×320×320 grid with 0.8 mm sampling. They are registered to a study template and mouth-cropped/masked; the publisher also smoothed final masks with a 1 mm Gaussian kernel. They must not be described as an unmodified native acquisition. Independent checks preserve all 6,553,600 stored samples per volume, MRI signal scaling and each distinct original sform. The maximum whole-grid corner difference between the two sforms is 0.000072653 mm; neither is silently replaced.

The original spreadsheet `label_key` identifies label 1 as combined transverse/vertical, 2 as superior longitudinal, **3 as inferior longitudinal and 4 as genioglossus**. All 67,508 source-interface triangles are retained; inferior longitudinal has two components. No extra smoothing, padding, capping, repair, mirroring, decimation, component removal or invented fibre separation is applied. Float32 display transport error is recorded separately from anatomical accuracy.

The source case is female, age 33.12 years. The spreadsheet supplies no individual diagnosis. The source publication describes the released cohort as non-neurodegenerative controls; that description is not independent proof of normal anatomy or swallowing function. Fine extrinsic muscles, fibres, supply, palate, hyoid, pharyngeal wall, larynx and cricopharyngeal interfaces remain outside the four-label reference. No registration with the separate swallowing movies is claimed. Clinical coverage and anatomical approval remain empty/pending.

`source-MRI-label-context.png` displays three source index planes with only zero ROI margins removed and each original pixel repeated three times. Every nonzero MRI sample on those planes is retained; no interpolation or new effective resolution is claimed. `full-source-index-planes.png` retains complete planes and all original zero margins. Both use the declared 1st/99th percentile source-signal window and separately identified publisher masks. No guessed anatomical plane label or physiological interpretation is supplied.

Run the dedicated package builder with the scientific Python runtime and NumPy/Pillow available. Its default creates only dedicated WT9FC package/proof paths. Adding `--apply-registry` registers the partial reference and five pending evidence assets for `ra.swallowing`; atlas/family allowlisting and viewer support must be provided separately by the integrating change.

```sh
python tools/anatomy_sources/package_wt9fc_tongue_reference.py --apply-registry
```

The packaged original NIfTI/affine/spreadsheet and double-precision surface proofs make the command reproducible without the ignored acquisition cache. No rights or fidelity claim relies on generated photographs, inferred normality or an article's licence being applied to a different dataset.
