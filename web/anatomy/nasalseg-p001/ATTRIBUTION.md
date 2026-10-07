# Regional source reference

No MRI tissue characterization, calibrated measurements, physiological drainage or unique diagnosis is supplied. Zhang, Yichi, Wang, Jing, Pan, Tan, Jiang, Quanlin, Ge, Jingjie, Guo, Xin, Jiang, Chen, Lu, Jie, Zhang, Jianning, Liu, Xueling, Tian, Mei, Qi, Yuan, Cheng, Yuan, Zuo, Chuantao. NasalSeg Dataset for Nasal Cavity and Paranasal Sinuses Segmentation from CT Images. DOI 10.5281/zenodo.13893419. CC BY 4.0. Adaptation: original label-interface extraction, float32/gzip transport, display normals and source CT/contour display. Clinical/anatomical review pending.

One regional source CT case (P001); patient age and native DICOM orientation are not independently verified. These are five original region-label interfaces, not a complete sinonasal atlas or the anatomy of the patient being reported.

The source grid is 153×205×52 with declared 0.586×0.586×1.5 mm sampling. This does not establish operative thin-bone effective resolution, raw DICOM/HU lineage or full head coverage.

Both original left nasal-cavity components and 98 open nasal-pharynx edges at the acquired boundary are retained. Viewer rotation or uncropped framing cannot restore anatomy outside the scan.

Frontal/ethmoid/sphenoid cells, full drainage routes, bone/mucosal thickness, optic/carotid/nerve/vessel boundaries and lesion or extrasinus extension are not independently represented.

No extra smoothing, padding, repair, capping, decimation or component removal. Sixteen Lewiner ambiguity-resolution vertices remain; source labels are not independent anatomical validation.

Source LPS coordinates are preserved with float32 transport and display normals. Matching CT planes are from this case; other published figures and models are separate patients without registration.
