# Native FCD package status

The local package contains 2,192 native FLAIR, T1 and lesion-mask planes and the complete source-cell lesion boundary. The plane checker compares 126,812,160 stored samples against the original NIfTI files. The mesh delivery checker decodes HVX1 bytes and compares every triangle index and correctly rounded vertex with the separately audited source boundary.

The mesh retains all 4,028 triangles and 2,006 vertices without smoothing or decimation. Maximum float32 coordinate error is 0.000003811 mm. This is source-cell geometry, not evidence of an anatomically smooth lesion border or independent diagnostic confirmation.

Both current verification receipts bind manifest SHA256 `17c57029b09ab6eddfb9648dfdc4df3d570a04d778a90fa37aedec42e39fde6b`. Builder pending flags are conservative build-time defaults; verification is recorded separately in the receipts rather than rewriting the manifest after checks.

Remaining work: reader implementation, native display orientation and pixel checks, FLAIR/ROI coordinate handling, interactive 3D rendering verification, hosted delivery, authenticated lesson integration and release. T1-to-FLAIR anatomical registration is unverified: T1 must remain image-only unless separately established. This package does not complete epilepsy reporting coverage or the whole-Primer objective.

## Reader progress

The local reader now shows upright native oblique planes using an exact display-axis permutation, with no interpolation. Header-based direction labels and source-scaled pixels are checked against nibabel. It supports FLAIR lesion overlays, source-labelled voxel navigation, separate crosshairs, and the complete 3D lesion surface. GPU buffers are checked against the verified mesh bytes. Desktop and 390-pixel mobile browser checks cover metadata retry, context recovery and invalid-window recovery. These are local checks, not production verification. Hosted delivery, authenticated lesson integration, broader adverse transport checks and release remain outstanding.

## Hosted payload delivery

All ten runtime objects (79,020,140 bytes) and all five original source files have been uploaded to the existing public Blob store. Complete remote readback matched each SHA256 and byte length. `runtime-delivery.json` records the immutable content-addressed URLs. The reader still uses loopback delivery: hosted reader checks and authenticated lesson binding remain pending. The archived upload script records the executed workflow and expects its original research-directory inputs; it is not a standalone deployment command.

## Hosted reader verification

The reader now defaults to the verified immutable Blob prefix. Only a loopback-only test option permits local payload fixtures. Desktop and mobile browser receipts record real hosted responses, exact GPU buffer checks and recovery checks, bound to current reader source hashes. Independent original-NIfTI comparison passes for all 147,456 displayed FLAIR lesion-overlay pixels at each width. Authenticated lesson integration and production deployment are still pending.
