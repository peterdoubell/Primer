# R6: complete original DICOM linkage and calibration

Reviewed 6 October 2026. All **1,064 original DICOM instances and 278,921,216 stored pixels** match AVT R6 exactly, without resampling, fitted alignment, HU-offset guessing or source edits. This resolves acquisition identity/calibration, not complete anatomical fidelity.

The [AVT publication](https://pmc.ncbi.nlm.nih.gov/articles/PMC8760499/) cites RIDER Lung CT, DOI 10.7937/K9/TCIA.2015.U1X8A5NR. Its current public query returned 561 CT series with at most 407 instances. That alone could not exclude a historical/resampled derivative. The checksum-verified [IDC index 24.2.2](https://github.com/ImagingDataCommons/idc-index-data/releases/tag/24.2.2) identified two 1,064-instance RIDER Lung PET-CT candidates. One had different spacing/origin and mismatched pixels; the other matched a sample, then every original slice/pixel.

The matched source is [RIDER Lung PET-CT](https://www.cancerimagingarchive.net/collection/rider-lung-pet-ct/), DOI **10.7937/k9/tcia.2015.ofip7tvm**, series UID `1.3.6.1.4.1.9328.50.17.321375527633491919048584720362415649934`. [Complete evidence](avt-r6-dicom-linkage-review/complete-dicom-linkage-review.json) retains every object/SOP/pixel identity and allowlisted geometry/calibration field. The original publication citation remains alongside this case-specific correction; other AVT cases are not silently reassigned.

Each original slice declares 512×512 signed-int16 samples, PixelSpacing **0.724609×0.724609 mm**, axial orientation `[1,0,0,0,1,0]`, and LPS position `[-185.5,-185.5,-655.375+k×0.625]`, k=0…1063. Every instance has **RescaleSlope=1, RescaleIntercept=−1024, RescaleType=HU**. PixelPaddingValue −2000 accounts for 57,590,033 source padding voxels. Padding is a sentinel, not tissue HU; numeric nonpadding extrema include reconstruction/edge values and do not establish tissue identity. No values are clamped or removed.

The original mask and derived geometry hashes remain unchanged. The native packet now inherits verified millimetre/HU calibration and exact current series linkage. Bolus/arterial-phase interpretation, highest acquired-master resolution, historical AVT export release, diagnosis, semantic branch/wall/lumen boundaries and clinical mask QA remain unverified. Source identity/calibration cannot substitute for those reviews.

The direct official collection image row, IDC record and original DOI metadata identify **CC BY 3.0** for this CT. The AVT producer grants CC BY 4.0 for the mask with inherited upstream terms. Attribution-compatible reuse grants are now verified for this specific pair; no blanket clearance of other cases or KiTS noncommercial terms follows. [Official licence rows](avt-r6-dicom-linkage-review/original-collection-license-rows.json) and [DOI metadata](avt-r6-dicom-linkage-review/original-source-doi-metadata.json) retain the original grants and attribution.

Publisher-recorded creators are preserved without inferred name corrections: Muzi, Peter; Wanner, Michelle; Kinahan, Paul; *Data From RIDER Lung PET-CT*, DOI 10.7937/k9/tcia.2015.ofip7tvm. Mask attribution remains Radl et al., DOI 10.6084/m9.figshare.14806362. Derivations/overlays are identified; no endorsement is implied. Original DICOM/index files remain in ignored research storage; patient names/demographics are not copied into the proof.

Reproduce with NumPy/pydicom:

```sh
python -m tools.anatomy_sources.acquire_avt_r6_source --source-root .research/avt-native-source-review
python -m tools.anatomy_sources.acquire_avt_r6_original_dicom --source-root .research/avt-native-source-review
python -m tools.anatomy_sources.verify_avt_r6_dicom_linkage --source-root .research/avt-native-source-review
python -m tools.anatomy_sources.review_avt_r6_source --source-root .research/avt-native-source-review
python -m tools.anatomy_sources.render_avt_r6_source --source-root .research/avt-native-source-review
```

The interrupted acquisition was confirmed stopped with 663 cached instances before resuming; no live process was restarted after a mere observation timeout. All original pixels, geometry/calibration, immutable derived arrays and retained clinical/version holds pass checks. Whole-module clinical-grade anatomy remains unproven; the full goal stays active.
