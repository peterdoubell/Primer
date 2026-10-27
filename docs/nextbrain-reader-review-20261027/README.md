# NextBrain ex vivo reference reader

Brain Anatomy gains a study-specific reference for all 98 present source labels: matched supplied MRI, native segmentation schematics, and complete categorical-cell boundary meshes. The reader retains 4,800 native planes, 33,496,568 triangles and 3,721 connected source components. Source fidelity does not establish clinical extent equivalence, patient registration or whole-Primer completion.

The dataset, licence evidence, original hashes, independent source-grid checks and complete numeric reproduction are in `../nextbrain-source-review-20261027/`. NextBrain Data Extension (OpenNeuro ds005422 v1.0.1, revision `924a8f3412463457a70e0fb141a88a8b57fc7ba6`) and its upstream MRI are CC0. All 333 derived transport objects were uploaded to the existing source Blob store and independently read back with matching hashes. Original files are also mirrored with verified hashes. No NITRC account or ambiguously licensed mirror is used.

## Interpretation

The publisher declares a right-hemisphere reference, while 35 raw names use `Left-` or `L_`. The selector removes side prefixes; the exact original label name remains visible. No left-side reporting requirement is inferred. The supplied filename says T2w, but the cited upstream acquisition used FLASH and the exact derivative lineage is unresolved. The reader says “Supplied ex vivo MRI” and claims only the supplied 0.2 mm grid. It does not claim quantitative T2 or a 100 µm derivative.

Broad source categories can exclude separately labelled subregions. Fibre regions are not tractography. The 98-region MRI reference is distinct from the 333-region probabilistic histology atlas. Codes 99–101 are absent, and zero outside the original annotation crop means no annotation supplied. Source-cell contacts, small islands and nonmanifold edges are preserved. Clinical, normal-population, complete-reporting and patient-registration approval flags remain false.

## Reader and transport

All source geometry is retained. Compressed parts decode to at most 4 MiB and stream into the selected model's GPU buffers. A selection is displayed only when its parts have been verified. Superseded requests are aborted, and stale results cannot replace the selected region. The MRI and annotation planes retain the original sampling; their crop alignment uses the independently checked integer offset `[124,10,23]`, without interpolation. Orientation comes from the supplied affine. Scale bars span 50 source cells (nominally 10 mm).

Public Blob requests omit credentials. Blob CORS does not expose Content-Range, so plane transport requires status 206, exact member length and both compressed and decoded SHA-256 identities. Responses with ignored ranges, incorrect bytes, excess lengths or wrong hashes fail closed. Only the reader route receives an added connect-src for the exact source Blob hostname. App authentication remains required for every authored reader file.

## Evidence

- `browser-proof.json`: 98 actual GPU models, all 294 decoded chunks compared to expected hashes, visible rendered pixels for every region, 196 MRI/schematic states and 588 native plane canvases. Runtime file hashes bind the observations to the exact reader.
- `pixel-proof.json`: independent Python comparison of 372,556,800 rendered pixels against source plane members and their orientation transforms.
- `recovery-proof.json`: ignored-range, corrupt-body, mesh HTTP failure, stale-selection, invalid-window and WebGL-loss recovery, plus disconnected-component navigation.
- `remote-browser-proof.json`: 30 real cross-origin responses with expected range/full statuses and three regions loaded successfully.
- `lesson/proof.json`: authenticated synthetic loopback Brain Anatomy lesson at 390 and 1440 pixels, real remote payloads, selection and open/close. Fixture credentials are attached only to the loopback app origin. No production learner records were changed.
- `runtime-inverse.json`: an exact four-file integration delta for frozen historical evidence; it grants no approval to the new reference. New route, source-scope and independent reader checks verify the addition separately.

The source-preparation programs are preserved beside their original source evidence. The reader verification programs are archived here as inert text; the authenticated lesson check is executable via `tools/check_nextbrain_lesson.py` with Playwright available. The offline browser checker expects the exact prepared `package/` directory and validates every requested immutable object before serving it. The pixel checker consumes that browser proof and the same pinned native plane members. Verification outputs are evidence, not a replacement for clinical anatomical review.
