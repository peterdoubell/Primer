# Complete native lentiform MRI inspection

The existing brain reader supplies six complete MASSP joint-interface models but only four static MRI planes. Those planes cannot inspect every source-selected boundary. The new regional inspector makes every native axial, coronal and sagittal section through the six selections available in all three AHEAD contrasts, both median and interquartile range. It also intersects the actual complete exported model triangles with each selected RAS plane and retains an unmarked MRI view.

The current `ra.brain-anatomy` contract explicitly requires bilateral putamen, external globus pallidus and internal globus pallidus under its deep-grey checklist and lentiform requirement groups. The existing full-source labels 38/39, 11/12 and 9/10 match these six named structures. The new artifact improves their whole-extent boundary inspectability. It does not delineate fine medullary laminae or convert the broad neighbouring caudate, thalamus or capsule labels into their separately required segments, nuclei or limbs. The other brain requirements and clinical context obligations retain their missing/unverified state.

## Sources and source meaning

- [MASSP 2.0 lifespan probabilistic atlas v2](https://doi.org/10.21942/uva.27291579.v2), Bazin, Forstmann, Alkemade and Miletic. The pinned publisher source describes 97 adults, ages 18–80, in MNI2009b space, with RPS storage axes.
- [AHEAD quantitative MRI templates v3](https://doi.org/10.21942/uva.19646364.v3), Bazin, Forstmann, Alkemade, Miletić and Isherwood. File names identify 105 subjects. The publisher describes R1, R2* and quantitative susceptibility population median and interquartile-range maps. `r2map` remains the original file code; the display names the publisher's R2* contrast.
- Both pinned datasets grant [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Original acquisition, source checksums and prior rights evidence remain in `docs/brain-massp-source-review/` and `docs/brain-ahead-qmri-source-review/`. The official versioned metadata endpoints were re-read successfully on 2026-10-11; the web reader could not access those endpoints, so the direct official responses were checked against the acquired source records.

The declared source shapes and sform affines match exactly. The comparison therefore uses unchanged corresponding array indices without a fitted transform or voxel resampling. That equality proves sampling correspondence, not independent source registration precision, patient-specific correspondence or clinical boundary accuracy. The 97-subject label atlas and 105-subject quantitative template remain distinct cohorts. Source MRI units have not been independently calibrated for clinical numerical interpretation.

MRI IQR expresses population intensity spread. The seven separately displayed probability maps express source population membership for the six labelled regions and background. Neither quantity is a patient's diagnostic certainty. Original source float32 bits are preserved; no normalization, confidence threshold, mirroring or probability-tail edit is performed.

## Complete selected extent and unchanged neighbouring IDs

The crop is **149 × 96 × 68**, starting at original source indices **[122, 150, 111]** and ending exclusively at **[271, 246, 179]**. It contains all **160,498** original best-label voxels selected for the six structures, plus four native voxels/2 mm of context around their complete source bounds. Every one of the **972,672** crop voxels remains available in each of the 14 transported arrays.

The original regional best-label array retains **all** source IDs, including neighbouring structures. It is not a binary target mask or relabelled six-class array. The inspector reads the original label ID and publisher structure name at the crosshair. Neighbouring structures and nonzero probability tails may continue outside the crop; no complete neighbouring extent is claimed. The original full six meshes remain intact and are reused by compressed and decoded hashes, with all **329,192** triangles retained.

The MRI arrays use reversible row-wise uint32 XOR, byte shuffle and gzip. Probability arrays use an exact dictionary of original float32 bit patterns with uint8 dictionary indices and gzip. Both are transport encodings, not numerical quantization. All six MRI arrays and all seven probability arrays decode byte-for-byte to the original float32 native crops. The original best-label NIfTI stores integer IDs as float32; its transport changes storage dtype to uint8 while preserving every label ID. Its decoded SHA-256 covers uint8 ID bytes. Converting those decoded IDs back to float32 reconstructs every original crop bit, including the sign of zero; this dataset's crop contains no negative-zero labels. The original float32 crop hash is recorded separately.

The 14 compressed payloads total **17,434,638 bytes**. `delivery-inventory.json` gives each file's compressed/encoded/decoded SHA-256, bytes, codec and dictionary size. Deployment storage is a separate integration concern; all source contrasts and uncertainty data remain present.

## Verification

`runtime-source-comparison.json` records a comparison of the actual browser JavaScript decoder against the original NIfTI files: **12,644,736 float32 bit comparisons** across 13 MRI/probability fields and **972,672 lossless label-ID comparisons**, plus exact reconstruction of the original float32 label crop. It independently checks all six complete target extents, all projected native pixel/world mappings, and 90 sections of the complete exported meshes against the existing Python geometric section routine within **1e-12 mm**. Synthetic cube fixtures check exact coplanar boundaries, removal of internal triangulation edges and outside planes. These checks establish source transport and geometric consistency, not independent anatomy.

`browser-proof.json` records standalone artifact QA at 1440 × 1000 and 390 × 844. All six median/IQR choices, six structures, four overlays, all three planes at their start/end/middle, pointer selection and keyboard controls were exercised. Raw displayed values and source indices were compared with independently decoded source bytes. There was no horizontal page overflow or JavaScript error. The accompanying desktop/mobile mesh and unmarked IQR screenshots were visually inspected.

The inspector also rejects failed or hash-mismatched original arrays and clears stale images, sample values and slice identifiers. Superseded MRI responses cannot replace the current choice. Invalid display limits clear the presentation until reset. Those cases are included in the browser proof after the final scoped UI changes.

The standalone QA server serves only this checkout's web files on loopback; it does not access a user's database, browser profile or credentials. Actual authenticated reader integration and production delivery remain root integration checks. The generator's `runtime_binding_added: false` records that this output proposal did not itself modify curriculum or shared registry bindings.

## Browser model transport amendment

Actual authenticated integration exposed a difference from the standalone server: the established MASSP model route sends `Content-Encoding: gzip`, so browsers deliver an already inflated BP3D response to `fetch`. The original standalone receipt exercised gzip file bodies without that header and cannot prove this integrated route worked.

The amended source-model loader accepts two explicit transports. A gzip body must match the original compressed SHA-256 before decompression, then the original decoded SHA-256 and exact BP3D header, length and counts. An already inflated body must begin with BP3D magic, match the original decoded SHA-256 and pass the same exact header/length/count checks. Other raw bodies and corrupt hashes or counts fail. This dual transport applies only to the six existing source meshes; all fourteen native array payloads retain their compressed-hash/decompression/decoded-hash checks.

The actual shared loader is exercised with all six complete meshes in both forms, plus 24 corrupt compressed/decoded/magic/header negative fixtures. Original arrays, manifest coordinates, geometry and probability semantics are unchanged. The revised source comparison binds the amended runtime script hash; actual integrated browser verification is recorded separately from the earlier standalone receipts.

Reproduction:

```sh
python -m tools.anatomy_sources.brain_fine_native
node tools/anatomy_sources/brain_fine_check.cjs
python -m tools.anatomy_sources.brain_fine_verify
```

Generation and independent original-source verification require the existing scientific runtime and cached original MASSP/AHEAD NIfTI files. The Node checker uses only the packaged assets and actual runtime module. No dependency is added to the application.

## Remaining fidelity limits

This is a complete native reference inspector for the six source selections. Their clinical anatomical fidelity remains unverified. Fine pallidal laminae, source registration precision, individual/pathological/developmental anatomy, routine clinical contrast appearances and all remaining reporting structures still need suitable source evidence and anatomical review. No clinical/commercial readiness, certification expectation, fine anatomical coverage approval or new requirement credit is asserted.
