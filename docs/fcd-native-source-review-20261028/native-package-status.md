# Native FCD package status

The local package contains 2,192 native FLAIR, T1 and lesion-mask planes and the complete source-cell lesion boundary. The plane checker compares 126,812,160 stored samples against the original NIfTI files. The mesh delivery checker decodes HVX1 bytes and compares every triangle index and correctly rounded vertex with the separately audited source boundary.

The mesh retains all 4,028 triangles and 2,006 vertices without smoothing or decimation. Maximum float32 coordinate error is 0.000003811 mm. This is source-cell geometry, not evidence of an anatomically smooth lesion border or independent diagnostic confirmation.

Both current verification receipts bind manifest SHA256 `17c57029b09ab6eddfb9648dfdc4df3d570a04d778a90fa37aedec42e39fde6b`. Builder pending flags are conservative build-time defaults; verification is recorded separately in the receipts rather than rewriting the manifest after checks.

Remaining work: reader implementation, native display orientation and pixel checks, FLAIR/ROI coordinate handling, interactive 3D rendering verification, hosted delivery, authenticated lesson integration and release. T1-to-FLAIR anatomical registration is unverified: T1 must remain image-only unless separately established. This package does not complete epilepsy reporting coverage or the whole-Primer objective.
