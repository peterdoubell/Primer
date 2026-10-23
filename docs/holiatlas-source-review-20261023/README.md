# holiAtlas source-template reference

This adds a separate population-template source to the brain-anatomy reference. It does not register holiAtlas to SPL, HippUnfold or a patient. Existing reporting contracts and original source viewers remain intact.

The original dataset is Manjón and collaborators' holiAtlas v1.0, Zenodo DOI 10.5281/zenodo.15690524, published under CC BY 4.0 in the captured record. Full creators, source links and marked Primer derivations accompany the reader. The supplied processed grid is 0.5 mm; that is not acquisition resolution. T1/T2 are processed population templates and WMn-like contrast is source-author synthesized. Sulcal labels represent assigned CSF territories, not traced sulcal centre-lines or independently verified gyral banks.

The protocol has 350 named anatomical classes, plus background and a reserved empty code. The supplied substructure volume contains 332 named classes; 18 named classes are absent. They remain unavailable. The 53 source structure groups preserve the authors' hierarchy rather than introducing new clinical groupings.

## Preserved source data and geometry

- Original 185,807,931-byte archive matches its published MD5; SHA256 and member CRC evidence are retained in `holiatlas-acquisition.json`.
- Supplied label and three contrast grids, sforms and qforms agree. All full contrast arrays are finite, and NIfTI intensity scaling is identity. The original Float32 label samples round-trip bit-for-bit through UInt16 code storage.
- All 332 present classes retain every categorical-cell face, cavity and component. The 868 components at 26-connectivity have source-valid focus voxels.
- An independent global label-transition oracle checks 5,825,138 faces and 11,650,276 triangles against the source volume. It checks world-space corners, square diagonals, outward winding, signed cell volumes and closed oriented edge balance. Nonmanifold source contacts remain unrepaired.
- All 4,632 native planes are stored as independent gzip members in 15 indexed packs (438,062,629 bytes). Actual pack ranges independently reassemble every original sample bit in all three axes. The client requests one bounded member per plane and limits its plane cache to 16 MiB.

## Current application evidence

`reader/proof.json` records eight authenticated application paths: Images, 3D anatomy, reporting walkthrough and lesson gallery at 390 and 1440 pixels. The current reader startup and source assets are pinned. It checks 10,686,240 native canvas pixels against independent source-volume oracles, actual GPU buffers for all 332 classes, every source group, missing-label controls, CSP and overflow. All learner writes use isolated synthetic storage. This is not a production-delivery or clinical-approval claim.

`preserved-old-spl/preservation-proof.json` separately checks the prior SPL viewer in the current combined app: 874,496 pixels and 24 GPU meshes per viewport. Original frozen source-review artifacts are not rewritten.

`reader-current-recovery-proof.json` repeats five recovery tests through the authenticated application: malformed ranges, ignored ranges, corrupted bytes, missing payloads and delayed earlier selections. Exact native pixels are checked after recovery. Run `tools/check_holiatlas_recovery.py` to reproduce. Production range delivery still needs its own staged check. Lossless compressed metadata keeps the large static assets and plain metadata outside the Python function bundle.

`runtime-inverse.json` restores only five exact pre-integration files for historical byte assertions. Earlier source and clinical approvals do not extend to this reader. Descriptor mutations, duplicates and unrelated bytes are rejected.

## Reporting correspondence and remaining work

`reporting-correspondence.json` indexes all 210 explicitly named required parts for brain anatomy. Its exact-name candidates are a conservative starting point, not an anatomical synonym map or a coverage score. No requirement is marked complete. Parent masks do not automatically establish separately reportable child anatomy, and this source does not establish missing cistern, capsule, vascular-territory or complete sulcal representations. Image/model context also does not establish every required schematic.

The full clinical/commercial radiology objective and all math/physics fidelity requirements remain open. This reference must not be presented as certification or independent clinical truth.

## Reproduction

The captured record identifies the original archive, checksum and public download. Source preparation and independent checks are retained here as the exact research scripts, with their original relative input names. To reproduce, copy them and the verified archive into an isolated research directory along with the captured protocol/header review files. The actual application reader check is `tools/check_holiatlas_reader.py`; run with the scientific Python environment and Playwright available on `NODE_PATH`. It provisions only temporary synthetic storage. Registry and lossless runtime metadata generation use `python tools/anatomy_sources/build_holiatlas_registry.py`; changing a registry still requires explicit review and updating the pinned registry SHA in `primer/holiatlas_reference.py`. Current assets and proof inputs are pinned separately.
