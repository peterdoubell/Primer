# NextBrain ex vivo source preparation

This review prepares the CC0 NextBrain Data Extension, OpenNeuro ds005422 version 1.0.1, for a separate source-reference reader. It adds source material with fine pontine, deep nuclear and cortical labels. Runtime integration and clinical/reporting-extent reconciliation remain outstanding.

## Provenance and interpretation

The dataset's own `dataset_description.json` declares CC0. The underlying Edlow MRI dataset, ds002179 version 1.1.0, also declares CC0. Both metadata files and source revisions are retained here. All three released files match the publisher's git-annex SHA256 identities. Verified copies are stored at the immutable URLs in `original-mirror-receipt.json`.

The NextBrain authors describe a right-hemisphere reference made from the high-resolution ex vivo scan. Their method uses sparse manual tracing, interpolation and correction, with FreeSurfer cortical subdivision. This 98-label reference is distinct from the 333-region probabilistic histological atlas. See [NextBrain methods](https://www.nature.com/articles/s41586-025-09708-2), the [versioned dataset metadata](https://github.com/OpenNeuroDatasets/ds005422/blob/924a8f3412463457a70e0fb141a88a8b57fc7ba6/dataset_description.json), and the [upstream MRI publication](https://www.nature.com/articles/s41597-019-0254-8).

Two naming issues must remain visible in the reader. Thirty-five present LUT entries use `Left-` or `L_` prefixes, while the dataset description says right hemisphere and 34 cortical labels use `ctx-rh-`. Original names are preserved. A future selector should use side-neutral names with the publisher-declared study scope and expose the original LUT text; these prefixes must not create left-sided clinical bindings. Also, the image filename says `T2w`, while the upstream acquisition is FLASH. The exact derivative contrast lineage has not been established. The proposed display name is “Supplied ex vivo MRI”; no quantitative T2 or specific FLASH input is asserted.

Broad categorical names do not establish complete parent anatomy after subregions have separate labels. Fibre-region masks do not establish tract connectivity. No anatomy is mirrored, repaired, smoothed or invented. Codes 99, 100 and 101 have LUT names but no voxels, and remain unavailable. Clinical approval, normal-population applicability and current-patient registration are not claimed.

## Source-grid evidence

The supplied MRI is UInt8 on an 880×880×640 grid. The UInt8 label grid is 402×870×602. Both have the same nominal 0.2-mm basis and L/A/I index directions. The label grid lies within the MRI grid at offset [124, 10, 23]. The largest world-coordinate residual is 0.0000015944 mm, within the combined Float32 header-origin precision. Integer placement retains every source sample and performs no interpolation. A one-voxel shift in any axis fails the placement check.

The complete MRI is retained. Padding outside the original annotation crop denotes unlabelled coverage, not absent tissue. The native source arrays, header units, qforms/sforms and original LUT remain separate from derived display conventions. Nine native-plane comparisons are included; their display resizing is nearest-neighbour and their horizontal scale bars use the actual displayed width.

## Geometry and transport evidence

All 98 present nonzero labels have exact categorical-cell boundary meshes, retaining every component and cavity. An independent whole-grid face-count oracle verifies all 33,496,568 triangles: every face is unique, source-valid and complete; every corner is a declared cell corner; both triangles cover the face with outward winding; oriented edges balance. Float32 coordinate export has maximum rounding of 0.0000038073 mm. The 185,363 nonmanifold edges are retained source-cell contacts, not silently repaired surfaces.

The package contains 4,800 planes in 39 indexed packs and 294 bounded mesh-array chunks. Independent decoding compares 2,973,696,000 values across the three orientations, including the explicit unlabelled padding. Every original mesh byte reassembles from the chunks. Each mesh chunk decodes to at most 4 MiB, allowing a future reader to upload bounded pieces to GPU buffers without holding a complete large mesh in JavaScript memory.

`transport-manifest.json.gz` preserves the exact numeric manifest; its uncompressed identity is recorded separately. Derived-payload transfer is in progress in the ignored research directory and is not a runtime release. Each object uses an immutable content-hash path and must pass a complete remote byte-hash check. The existing Blob store permits CORS and byte ranges but does not expose Content-Range to browser scripts; a future reader must explicitly enforce status, length and cryptographic member identity, with credentials omitted for public asset requests.

The standalone pontine preview shows source codes 19 and 29 in one coordinate system. Four actual GPU buffers match their source arrays. It is a visual/decoder prototype for those two regions, not evidence of full-reader or all-region GPU testing. Production integration still needs native pixel checks, all-region GPU checks, correctly scoped authentication, zoom/component focus, source-orientation markers, recovery tests and hosted delivery verification.

## Reproduction

The exact research programs are retained as inert `.py.txt` and `.cjs.txt` files. Copy them to an isolated working directory, restore their executable suffixes, obtain the three hash-pinned originals, and run acquisition/header review, boundary generation, independent boundary verification, packaging and independent package verification in that order. Python dependencies are NumPy, nibabel, SciPy and Pillow. The mirroring helper is project-specific and uses the existing Vercel connection; it contains no credentials.

The full radiology, mathematics and physics goal remains active. These source labels do not automatically close the 240 Brain Anatomy structure requirements or their 720 representation obligations.
