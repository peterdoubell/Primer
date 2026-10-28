# Focal cortical dysplasia source candidate — not deployed

OpenNeuro ds004199 version 1.0.6, pinned at commit df7eff349056648098d3e080b7577d6f22fdd67f, explicitly grants CC0. Five files for sub-00004 were acquired and verified against Git blobs or Git-annex SHA256 keys. The source metadata reports left-frontal FCD IIb, while its MRI diagnosis field records suspicion. No diagnosis or histological subtype is inferred from image appearance here.

The source publication says the manual ROI was drawn on FLAIR. The ROI and FLAIR share dimensions, but their original affines differ slightly. An affine corner bound over the complete voxel-cell extent establishes a maximum displacement of about 0.000049 mm and unchanged nearest-grid assignment. Both original affines remain intact. T1 registration to FLAIR is not established and must not be assumed.

The ROI contains 2,580 source voxels in one connected component. A provisional complete source-cell mesh has 4,028 triangles; count and signed-volume checks pass. Independent face-by-face validation, native transport, browser verification, reporting-structure review and integration remain pending. This clinical example must remain separate from the healthy-adult hippocampal annotation case.

Primary publication: https://doi.org/10.1038/s41597-023-02386-7
Data release: https://openneuro.org/datasets/ds004199/versions/1.0.6
