# Fatade acquired pelvic MRI source review

The source README grants CC BY 4.0 and the data deposit describes participant consent and anonymisation. The reviewed archive matched the published MD5 and passed ZIP CRC checks. SHA-256 and DICOM series geometry are recorded in the audit. [Dataset](https://doi.org/10.5281/zenodo.21445496)

The archive contains 302 slices in eight distinct study and series groups. Patient ID is uniformly blank. The deposit describes the archive as T2-weighted with 320 × 320 pixels. The numerical DICOM audit records three image dimensions different from that summary and finds differing acquisition parameters. For example, the gradient-echo series has a 4.76 ms TR and a 2.39 ms TE. Each study should be interpreted from its own header. The archive provides no case diagnoses or segmentations.

The packaged sagittal study contains 25 acquired 320 × 320 spin-echo planes with 0.71875 mm pixel spacing. The slice thickness is 4 mm and centre spacing is 4.8 mm. TR is 4050 ms and TE is 79 ms. Each slice retains its exact source orientation and position, and all 2,560,000 stored samples round-trip byte for byte. The packed data contain only image samples plus the separately stored geometry and source digests. DICOM private metadata remain in the local source archive. The contact sheet shows all 25 planes and supports visual inspection of the delivered pixels.

The study provides pelvic anatomy and acquisition geometry. Endometriosis findings, lesion labels, paired T1 sequences and specialist classification require separate evidence. The UT-EndoMRI Zenodo record displays CC BY metadata and separately limits use to non-commercial scientific research in its user agreement. [UT-EndoMRI user agreement](https://zenodo.org/records/15750762)

The 3D stack places every source plane at its original image centre. It constructs plane corners from each source LPS origin, the DICOM direction cosines and pixel spacing. The selected plane displays its exact unsigned source samples through the current window. The remaining outlines indicate acquired centre positions. The reader leaves unsampled space empty.
