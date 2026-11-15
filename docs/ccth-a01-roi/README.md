# CCTH-A01 sampled ROI surfaces

The paired case is CCTH-A01, MR1, from Mayr and colleagues. The original T2 pixels, 30 acquired sections and RTSTRUCT outlines are available in the linked reader. [TCIA collection](https://www.cancerimagingarchive.net/collection/cc-tumor-heterogeneity/)

The source review matches every RTSTRUCT contour to the referenced acquired DICOM frame. It projects the closed planar outline into that frame's row and column coordinates. Two independent point-in-polygon calculations agree for centres away from the contour. The display includes centres on the outline. The few same-ROI multi-loop planes have disjoint occupied pixels.

Each occupied centre represents its cuboidal sampling cell. The two surfaces follow the boundaries of those cells on the sagittal MRI lattice. The largest deviation between a regular 4 mm lattice centre and its original source centre is 0.000122 mm. The original outlines retain their exact published coordinates in the MRI reader. The voxel model keeps its stepped sampling boundaries. Edge-only contacts cause five and twelve non-manifold edges in ROI 1 and ROI 2 respectively. No open coordinate edges were observed.

The masks contain 20,234 and 7,657 occupied cells. Their derived surfaces have 18,992 and 11,600 triangles, and share 6,129 occupied cells while retaining independent labels. The original dataset assigns the same source name to both ROIs and leaves their interpreted types blank. Measurements describe this display discretization. Patient-specific tissue identities, staging and adjacent-organ interfaces require the clinical source examination and specialist review.
