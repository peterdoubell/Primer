# Original prostate source reference

Source case Prostate-MRI-US-Biopsy-0001,source64-year-old male. These are operator source references,not a normal whole-prostate atlas or the current patient.

All1,198 original prostate faces and4,280 suspicious-target faces remain. The prostate was outlined semi-automatically in Profuse with user-adjustable contours/vertices; accuracy is user-dependent. A suspicious MRI biopsy-target ROI is not proven complete tumour or histological extent.

The delivered model/MRI/SEG frame identifiers and independent all-voxel comparison support the source DICOM LPS association. No fitting,axis flip,resampling,smoothing,capping or component deletion was applied. Original mesh and producer-derived mask differ at480 gland and5 ROI voxel centres; every original value remains. This numeric correspondence is not independent anatomical accuracy.

The source encapsulated models omit the required measurement-units code. Display millimetre scale is inferred from the matching producer MRI/SEG grids and numeric correspondence; full DICOM model conformance and independent clinical registration are not claimed.

The source supplies complete T2,producer ADC and calculated-DWI grids. ADC and calculated DWI use their own coarser source grid. They have no supplied rescale/physical ADC calibration,original native high-b series or DCE. Source study description and private diffusion metadata do not supply missing acquisitions or current assessment.

Only the original T2 grid has the two producer-derived masks. They were rasterized from source STL and are not independent native manual voxel annotations. No mask is fitted or resampled onto ADC/DWI.

The41 idealized PI-RADS regions,zones,outer fibromuscular boundary,pseudocapsule,ducts,nerves,vessels,seminal vesicles,sphincter,nodes,bone and actual extension/treatment interfaces still require faithful source coverage and independent review. The whole-gland outline and one suspicious ROI do not meet full reporting coverage.

Source ultrasound has different private voxel-size tags and lacks standard patient orientation/position. Publisher nonrigid MRI-to-US target mapping is not this viewer's native registration. Source Likert-like scores do not assign current PI-RADS2.1. Source clinical/pathology/biopsy results are not inferred.

Natarajan,S.,Priester,A.,Margolis,D.,Huang,J.,and Marks,L.(2020). Prostate MRI and Ultrasound With Pathology and Coordinates of Tracked Biopsy,version2. TCIA DOI10.7937/TCIA.2020.A61IOC1A. CC BY4.0. Adaptation: complete source arrays/face transport,illustrative lighting and overlays; no endorsement implied.
