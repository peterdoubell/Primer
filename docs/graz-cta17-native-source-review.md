# Graz cta17: original paired lumen annotations and separate native surfaces

Reviewed 6 October 2026. The previous goal turn added acute-aortic clinical references and the full reporting scope. This packet obtains actual type B dissection CT with separate true/false annotations rather than borrowing channels from a combined model or flat rendering.

Source: [Mayer et al. dataset](https://figshare.com/articles/dataset/Aortic_Dissection_Dataset_and_Segmentations/22269091), DOI 10.6084/m9.figshare.22269091, **CC BY 4.0**; [primary publication](https://pmc.ncbi.nlm.nih.gov/articles/PMC11156948/), DOI 10.1038/s41597-024-03284-2. Original publication XML matches its publisher MD5. The article reports final expert checks by Christian Mayer, Johannes Schmid and Heinrich Mächler. Case 17 is not marked as student-segmented in the source tables; exact individual annotator identity is not assigned.

Five original selected members from the raw-CT and segmentation archives are verified by range identity, full member length/CRC/SHA and consistent per-archive ETag. Entire multi-gigabyte archives were not downloaded; full publisher archive MD5s remain unverified. Original CT remains in ignored research storage, while original masks and losslessly compressed delivered STL are retained here.

The raw/staged CT have exactly equal **120,586,240 signed-int16 voxels**, despite different file/header bytes. The original grid is 512×512×460, with native directions −0.69140625, −0.69140625 and 1.5. Published reconstructed slice thickness is 2.0 mm; that is not substituted for the delivered 1.5 slice increment. Source reports arterial contrast and no ECG gating; original DICOM calibration/bolus metadata is unavailable.

| Annotation | Source label | Original voxels | Six-connected components | Derived positions / triangles |
| --- | ---: | ---: | ---: | ---: |
| True Lumen | 1 | 356,048 | 7: 356,024 / 9 / 1 / 1 / 8 / 4 / 1 | 101,441 / 202,870 |
| False Lumen | 2 | 496,428 | 1 | 89,884 / 179,764 |

Masks have **zero overlapping voxels** and numerically matching native CT grids. Their source status tags are completed for true lumen and inprogress for false lumen; workflow tags and published expert review remain separate evidence. Small components are not deleted. Separate binary-level-0.5 surfaces retain original anisotropy and source offsets/affines, converted numerically from LPS to RAS without fitting. No merging, smoothing, decimation, invented padding or flap/wall model is introduced. Closed label boundaries are not assumed to be complete vascular walls or physiological surfaces.

[Paired source proof](graz-cta17-native-source-review/paired-lumen-source-review.json) binds all original files, samples, matrices, labels and derived array hashes. The delivered source STL is also preserved unchanged, but its positive coordinate ranges are not assigned to the native patient frame by guessing a scale/translation. [Published conversion code](https://github.com/apepe91/AD_NRRD_TO_STL), inspected at commit 7700c2a15c707ff292e7275d14558914c24817be, resamples and combines channels before remeshing, and explicitly loops over cases 25–40. It is not executed, redistributed or asserted to be the exact generator for case 17.

Voxel-derived volumes under source mm units are **255.309 / 355.971 mL**, compared with published **254.1 / 358.2 mL**. Mean/SD stored CT values are **279.009/26.852** and **118.288/79.832**, compared with reported **281±24 / 118±80 HU**. Those differences remain explicit; no source samples/masks are edited to force agreement, and table statistics do not independently establish DICOM HU calibration.

The source excludes clearly thrombosed sections and attributes some ambiguous dark regions to delayed filling before labelling them as lumen. Entry/re-entry localization was not performed. It excludes type A, markedly thrombosed and poorly distinguishable cases. Thus the masks do not provide every false-lumen/thrombus boundary, flap layer/thickness, tear, branch, perfusion territory or complication needed by the full acute-aortic reference.

[Render proof](graz-cta17-native-source-review/render-review.json) binds six inspected native CT/label planes and separate/combined same-frame surface views. Source-label colours are illustrative, not biological tissue signals. Crowded coordinate ticks were reduced and the final figure re-inspected without changing geometry. These are review artifacts, not approved clinical atlas models.

Reproduce acquisition, source review and rendering with the acquire_graz_cta17_source, review_graz_cta17_source and render_graz_cta17_source modules, using .research/graz-dissection-source-review as source-root. NumPy/SciPy/scikit-image/matplotlib are required for review/rendering. Tests preserve label values/components, raw/staged CT equality, original and derivative identities, half-grid coordinate correspondence, source-table discrepancies, source frame uncertainty and retained clinical holds. Python 3.9: three pass/two scientific skips; scientific Python 3.12: five pass.

No local independent clinical approval, complete structure coverage or runtime promotion is granted. Full goal remains active: **35,496 known-floor obligations, 83 unexpanded investigations, 106 unreconciled curriculum surfaces and unknown total**. Runtime rights remain 697 unique images / 254 cleared / 443 unverified. Full acquisition/annotation/source reconciliation remains required for missing structures; this packet does not redefine completion around two channels.
