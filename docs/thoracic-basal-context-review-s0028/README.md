# Same-case basal lung, liver and spleen correspondence

This review companion preserves the complete original s0028 CT and seven original TotalSegmentator v3.0.0 labels. The liver and spleen provide spatial context for basal lung assessment. Their labels do not establish ultrasound acoustic paths, breathing-linked motion, a diaphragm or pleural tissue layer, or a current-patient finding.

The source is [TotalSegmentator v3.0.0](https://zenodo.org/records/22688904), Jakob Wasserthal, CC BY 4.0. Original archive member CRCs and publisher archive identity before/after acquisition are verified. The whole 37.4 GB archive checksum is not independently verified. Acquisition ranges and individual source SHA-256 identities are recorded in `basal-context-acquisition.json` and `source-review.json`.

Every original sample, affine and label component is retained. Two independent NIfTI readers agree. Interfaces use the complete binary labels at level 0.5, without smoothing, padding, decimation, capping, fitting or deletion. There are 486,984 retained triangles, including 118,304 liver and 16,896 spleen triangles. Centred display buffers have zero measured positional error for this source. No extracted interface has boundary or nonmanifold edges.

The liver has components of 398,757 and two voxels under face connectivity. The spleen has components of 28,223 and one voxel. The small fragments remain present and are not interpreted as accessory anatomical organs. The source-plane image marks their coordinates so their CT correspondence can be reviewed. A binary label interface does not identify a tissue capsule.

Open `index.html` through a local HTTP server to inspect every source-index CT plane, select the corresponding label, window source values and rotate all seven interfaces. The viewer defaults to the liver. `basal-source-correspondence.png` shows six complete source planes with label boundaries at native pitch; the white rings identify the small fragment coordinates.

Verification: 126 display cases, all seven source arrays at two viewport widths, affine plane corners, load-failure recovery and 14 actual GPU-buffer/draw-count cases. Browser proofs include implementation hashes. Automated tests independently reconstruct every interface and display buffer.

Clinical anatomy, HU calibration, independent patient orientation and normal-atlas approval remain unverified. This companion is not yet bound into the production module. Existing production lung and curated anatomy viewers remain in place.
