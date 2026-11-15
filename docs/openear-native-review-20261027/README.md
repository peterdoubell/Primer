# OpenEar ZETA native CBCT and independent-mask reference

This addition exposes the two complete supplied registered CBCT volumes, all 13 independent source segmentation channels, and the separate full Bone volume alongside the 13 original author surfaces. It provides source images and source-mask schematics that were previously absent from the runtime volume inventory. It does not approve all temporal-bone or tinnitus reporting requirements.

The intended investigation bindings are `ra.ct-temporal-bone` and `ra.tinnitus`. The reader uses specimen X/Y/Z coordinates. It does not infer patient laterality, normal-population anatomy, image-specific detectability, clinical accuracy or patient registration.

## Source, licence and acquisition

The fixed source is [OpenEar, Zenodo record 1473724](https://zenodo.org/records/1473724), DOI 10.5281/zenodo.1473724, with the publisher's explicit CC BY 4.0 data grant. The complete ZETA archive was previously checked against publisher MD5 and all member CRC/SHA identities; the original acquisition and source-method evidence remains in `../openear-native-source-review/`. No NITRC account or ambiguously licensed substitute is used.

The four original source NRRDs and all 13 original PLY models are retained with their acquired hashes. Both CBCT volumes have source XYZ dimensions 668×587×625, signed little-endian Int16 samples and a supplied isotropic 0.125 mm grid. Reported acquisition voxel size was 0.25 mm before embedding and 0.125 mm after embedding. Equality of voxel spacing does not establish effective spatial resolution; the manifest explicitly leaves effective spatial resolution unestablished. Intensities remain raw source units, with no verified HU calibration.

The original segmentation is a list-axis volume: 13×641×579×475, with separate binary channels. Its original crop offset [20,3,13] reconciles with the CBCT source affine within 3.907985046680551e-14 mm, without fitting or resampling. The separate full Bone volume has the complete CBCT grid; it must not be substituted silently for the cropped Bone channel or vice versa.

Masks combine CBCT and microscopy information. Their overlay does not establish that a structure is resolved in CBCT. Fixation, staining, dehydration and epoxy embedding affect appearance and morphology. The superior-canal opening was created during preparation. Sinus Dura is not a separately resolved venous lumen, wall and dural surface. No hearing, neural function, blood flow or disease finding is inferred. Unsupported reconstructed photographic textures remain withheld.

## Lossless independent-mask transport

The original 13 channels remain independent. Their 773 overlapping foreground positions are retained, with no winner or mutually exclusive relabelling. UInt16 transport uses one bit per original channel and a separate fourteenth bit for the full Bone source. Every original binary value is recoverable exactly. Outside the original cropped segmentation, those 13 bits mean no annotation supplied, not absent tissue. The full Bone bit has separate whole-volume coverage.

The source preparation independently compared all 3,762,218,325 decoded bytes against their original compressed NRRDs. The package oracle checked 2,536,855,825 original channel values, every compressed-member identity, and 2,205,652,500 native plane values through a separate flattened-source-index calculation. There are 5,640 planes in 79 packs.

## Original surfaces and coordinate correspondence

All 7,349,910 original triangles and exact original Float32 positions and face indices remain, including two zero-area Bone triangles. No new smoothing, decimation, repair or component removal is applied. The 56 mesh chunks each decode to at most 4 MiB, allowing bounded CPU memory while uploading the complete selected source geometry to the GPU. All 132,282,312 mesh-array bytes were compared independently with the original PLY records.

Mesh-to-mask pairing follows the publisher's exact source names, not ordinal positions. An exploratory ordinal mapping was rejected after numerical comparison exposed three wrong pairings. The accepted comparison samples every original vertex in its named source mask frame, using the complete Bone volume for the Bone surface. Every vertex lies in the relevant declared source grid and within 0.25 mm of positive source-cell centres; the largest observed distance-field sample is 0.174205 mm. Seven wrong-frame/10 mm displacement controls per mesh distinguish the recorded frame.

This is a source-coordinate consistency measurement. It is not a clinical registration error, Hausdorff distance, tissue-boundary accuracy, or proof of tiny anatomical components. Author surfaces can differ from mask boundaries and small islands. The reader preserves both representations and states that distinction.

## Reader verification

The reader provides both CBCT volumes, selected-mask fill/outline, optional context and overlap marking, 57 component-navigation entries across the independent selections, native magnification, physical scale bars and full original surfaces. Source coordinates remain explicit. Changing display windows affects only display values. The original source samples are unchanged.

Browser evidence covers 84 main CBCT/schematic states at 390 and 1440 pixels, all 14 mask selections, complete actual GPU buffers for the 13 unique meshes, and all 57 component targets at both widths. Additional display variants check both intensity windows, fill/outline, context, and overlaps. The browser decodes all 773 overlap positions at each width. Independent Python pixel oracles compare rendered RGBA values with the pinned native plane members.

Recovery evidence covers ignored range requests, corrupt payloads, failed mesh responses, rapid selections, invalid and empty intensity windows, WebGL context loss during a transfer, and no-WebGL image/schematic use. Public payload requests omit credentials. Range delivery requires 206 status, exact compressed-member length, and both compressed and decoded SHA-256 identities because Blob CORS does not expose Content-Range to browser scripts. Metadata and every payload fetch/body read have a 45-second deadline. Caller cancellation remains distinct from timeout. GPU buffers carry a context epoch, so late decompression cannot delete resources from a restored context; the independently reproduced stale-delete failure and passing repair are retained. Stale planes and models cannot replace a new selection.

Runtime transfer and final integration status are recorded separately. A prepared source, successful local reader, or verified payload does not by itself establish deployment or whole-Primer completion. Clinical and complete-reporting approval remain false.

## Completed remote delivery

All 135 runtime objects and all 17 source originals passed full remote SHA-256 readback. A first Node readback of the large unembedded original failed integrity checking and was not accepted. Subsequent independent HTTP ranges, a complete 281,128,343-byte Python comparison, the matching multipart ETag, and a later complete Node readback all match the pinned original. No persistent stored corruption was reproduced and no object was replaced; the precise cause of the first transient observation was not captured. The failed observation and subsequent evidence remain recorded.

Live browser requests to the public Blob origin passed 32 range/full responses across three source selections. The complete registry and isolated backend helper validate successfully. Root integration and deployment remain separate from these source/reader checks.
