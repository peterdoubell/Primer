# Bilateral hippocampal source and rater comparison — work in progress

This source candidate extends the epilepsy anatomy work with original high-resolution T2 MRI and two manual source annotation sets. It is not complete epilepsy reporting coverage or clinical approval.

Publisher: Clark and Maguire, Dryad DOI 10.5061/dryad.2v6wwpzt3, version 7 (version ID 288011). The publisher API explicitly grants CC0. Its authenticated download API was unavailable without credentials. A public mirror at revision c6f92135179823a6d1ba4ac2f0cd0e4e547bdc28 advertises the identical archive size and SHA-256; label and README bytes independently match publisher fingerprints. Full archive streaming verification is running separately and must pass before publication. Acquired members have CRC verification and fixed SHA-256 fingerprints.

Case 10 was selected because both Main Sample and DICE annotations are supplied for the same MRI. All six original NIfTI files remain intact. The operative sforms agree; inactive qforms in the raw repetitions do not override them. The prepared mean requires its nonunit intensity scale. The separately named 0009 and 0010 raw files are byte-identical and must not be counted as independent image contents. The paper's general 104-partition description differs from this supplied 112-plane grid; no reconciliation is inferred.

Two annotations disagree: per-label Dice for the six subfield categories ranges from 0.6807 to 0.8286. The source Cyst label appears only in the DICE mask. Combined source categories remain combined, including CA2/3 and pre/parasubiculum. These are manual delineations, not histological ground truth or independent clinical diagnoses.

The local package contains 4,944 native planes in 21 packs and 13 meshes (six Main Sample, seven DICE). An independent decoder compared 253,919,232 original samples, including raw signedness and scaling. Independent geometry reconstruction verifies every exposed source face, its two triangles, outward orientation and signed source-cell volume. No source resampling, smoothing or component deletion is performed. The meshes total 167,796 triangles; 13 meshes do not mean 13 distinct validated anatomical structures.

The local reader now provides MRI, selected annotations, schematic and disagreement views, all source components, calibrated image magnification, pixel picking and component-focused 3D framing. Source-header directions are explicit. At the crosshair it reports both source labels and scaled MRI intensity. Other components remain in the 3D buffers when the view focuses one component.

The original-array browser oracle passed 204 states at 390 and 1440 pixels, comparing all displayed plane pixels and actual GPU buffer bytes. It also checks source-header orientation, screen millimetre scales, camera framing, keyboard zoom scrolling, context recovery, failed-transfer recovery, no-WebGL image fallback and a forced-pending manifest at a non-loopback origin. The first unsigned-image oracle wrapped subtraction; its deterministic reproducer and correction are retained. One desktop readiness timeout was not fully diagnosed; the revised harness records failure state and waits beyond the transport deadline. Subsequent full runs passed.

The first full archive stream ended prematurely at 4.90 GB. The second attempt used bounded ranges but stopped after connection timeouts at 6.68 GB. A third attempt now persists SHA256 state and a small chunk cache, allowing continuation after process or network failure. Its save/restore logic passed 271 independent hashlib comparisons. The prior prefixes must be reread once because those attempts did not persist hash state. No claim of full publisher-archive authentication is made yet.

The transport harness passed 10 cases, including corruption, ignored ranges, oversize responses, caller aborts and deterministic deadlines. Ten adverse browser snapshots verify late decoded data cannot replace a newer selection, restored context, newer slice or a raw image; corrupted geometry is rejected and retry recovers.

The source methods identify the prepared mean as the annotation reference. Overlays and annotation navigation are now restricted to that image. All raw repetitions remain available as images, without assuming anatomical registration from matching file grids. A direct archive-member comparison also confirms the Main Sample and DICE folders contain byte-identical reference images.

Remaining: complete archive authentication, authenticated lesson integration, whole reporting-structure coverage review, then CI and staged deployment verification. This is a local development reader, not a deployed clinical product.

Primary publication: https://doi.org/10.1038/s41597-023-02449-9
Publisher data: https://doi.org/10.5061/dryad.2v6wwpzt3
