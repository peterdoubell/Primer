The case IDs are the same that ISPY uses. We used the T1 weighted DCE-MR images, pre contrast scan and first two post contrast scans.


images_bias-corrected_nifti: DICOM images converted to NIfTI and then bias-corrected

images_bias-corrected_resampled_zscored_nifti: images_bias-corrected_nifti, resampled to [1,1,1] and then z-scored across the 3 timepoints

masks_ftv: segmentations for functional tumor volume

masks_stv_manual: manual segmentations of the structural tumor volume

masks_stv_resunet: computationally-generated segmentations for stv


ISPY_DataPaper_features.xlsx: Radiomic features extracted from images_bias-corrected_resampled_zscored_nifti and masks_stv_manual: 