# Original AVT R6 CT/mask and full-resolution source-mask geometry

**Source update, 6 October 2026:** [Complete original-DICOM comparison](avt-r6-dicom-linkage-review.md) now identifies every R6 pixel in RIDER Lung PET-CT, verifies original mm/HU calibration and resolves this specific pair's upstream CC BY 3.0 attribution. The original unresolved findings below describe the initial review; these source/calibration claims are superseded by the linked complete evidence. Historical export release, mask anatomy, bolus timing and clinical approval remain unresolved.

Reviewed 6 October 2026. Following the ten external-surface review, this packet obtains a source with a delivered aortic-tree mask, rather than borrowing branches from another patient or inventing structures in an external envelope. It improves the available CT/label evidence while leaving clinical fidelity unapproved.

The [AVT dataset](https://figshare.com/articles/dataset/Aortic_Vessel_Tree_AVT_CTA_Datasets_and_Segmentations/14806362) and [primary publication](https://pmc.ncbi.nlm.nih.gov/articles/PMC8760499/), DOI 10.1016/j.dib.2022.107801, identify the aneurysm case as `Rider/R6 (AAA)/`. That is a source directory label, not an independently confirmed diagnosis. The publication describes semi-automatic thresholding, manual corrections and morphological processing; some cases omit branches, and no case-specific independent clinical reader is identified for R6.

Original ZIP members were fetched through exact public HTTP ranges, with full member length, CRC32 and SHA-256 checks and one consistent source ETag. This verifies the selected members; **the 3.90 GB archive was not downloaded and its full publisher MD5 was not verified**. Original member hashes:

- `R6.nrrd`: 296,153,333 bytes; SHA-256 `2931246e0eab752244389d502dd798dd3414a25b54eb1b2f625f43d3f28f5ccd`.
- `R6.seg.nrrd`: 418,228 bytes; SHA-256 `2d5609646c808646dab10343ae56046c9613e35b5c98b2917ec88682415f335f`. The original mask is preserved byte-for-byte in this review packet; CT is retained in ignored research storage.

Both original grids contain **512×512×1064 voxels** in LPS. Their direction/origin differences are below 10⁻¹² native units, recorded without rounding, resampling or fitting. The CT contains 278,921,216 signed-int16 samples, with stored values −2000 to 4095. Neither apparent CT values nor plausible spacing is treated as independently verified HU/physical calibration or bolus timing.

The original binary mask contains **1,275,074 labelled voxels**, with four six-connected components of **1,274,179 / 18 / 762 / 115 voxels**. All are retained. Its only named segment is `aorta`; its original Slicer metadata retains `Segmentation.Status:inprogress`. That status may be a workflow default, so it is not a diagnosis of a bad mask. It also cannot be relabelled as independent finished clinical QA merely because the publication calls the dataset benchmark ground truth.

## Source-mask surface and inspected CT contexts

An explicitly derived binary-level-0.5 full-resolution marching-cubes surface contains **272,202 positions and 544,138 triangles**. Source-mask bbox offset, actual LPS matrix and RAS basis signs are preserved in [native proof](avt-r6-native-source-review/native-source-review.json). Positions are retained as little-endian float64 and triangles as uint32, under lossless gzip with uncompressed-array hashes. No padding, caps, smoothing, decimation, component removal, branch splitting, label edit, fitting or cross-patient geometry is introduced. It has 270 boundary edges and zero nonmanifold edges; these numerical controls are not anatomical approval or proof against self-intersections.

This surface is not original delivered STL geometry. It is a reconstruction of the actual supplied binary mask, and carries that mask's segmentation limits. A single combined label does not independently resolve every branch identity, lumen, wall layer/thickness, thrombus, calcium, rupture site, haematoma compartment, fistula or repair component required by the reporting contract. Root/ascending, arch, descending and abdominal/iliac source extents remain in the candidate instead of shrinking to one smooth aneurysm contour, but separately reportable boundaries still require source review.

[Render proof](avt-r6-native-source-review/render-review.json) binds twelve inspected original axial planes and the complete mask-derived 3D view to the exact source files/arrays. The initial −200..600 stored-value window saturated most soft tissues in this dataset; it was corrected to 800..1600 after checking source distributions. The display choice does not rescale or alter voxels and does not assume an HU offset. The final CT overlays are readable, the entire surface fits the view after camera-limit padding, and annotations retain all clinical/measurement holds. These are review artifacts, not clinical atlas assets.

## Per-source commercial rights remain separate

The Figshare record's CC BY 4.0 badge is accompanied by an explicit statement that original collection licences apply. The primary publication says adapted public collections retain CC BY-NC-SA/EULA terms. Consequently the mixed AVT collection is not blanket-cleared for commercial use.

The actual [TCIA RIDER Lung CT page](https://www.cancerimagingarchive.net/collection/rider-lung-ct/) was retrieved directly, with the current image row granting CC BY 4.0 and a historical image row granting CC BY 3.0. The older official wiki also shows CC BY 3.0. [Preserved row evidence](avt-r6-native-source-review/tcia-license-row-review.json) binds the retrieved HTML hash and exact licence URLs. These are commercial-compatible grants, but exact R6-to-original-TCIA case/version and source-attribution linkage remain unverified. No noncommercial KiTS terms are silently removed or inherited as RIDER rights. Clinical-runtime rights clearance remains pending that case-specific reconciliation; no product asset or commercial approval is granted here.

Attribution for source review: Lukas Radl, Yuan Jin, Antonio Pepe, Jianning Li, Christina Gsaxner, Fen-hua Zhao and Jan Egger, *Aortic Vessel Tree (AVT) CTA Datasets and Segmentations*, DOI 10.6084/m9.figshare.14806362; original RIDER Lung CT collection, The Cancer Imaging Archive, cited in the AVT publication. Original applicable attribution/version reconciliation remains explicit. No endorsement is implied.

Reproduce with:

```sh
python -m tools.anatomy_sources.acquire_avt_r6_source --source-root .research/avt-native-source-review
python -m tools.anatomy_sources.review_avt_r6_source --source-root .research/avt-native-source-review
python -m tools.anatomy_sources.render_avt_r6_source --source-root .research/avt-native-source-review
```

The downloader retains the pinned original metadata/range/licence snapshots; new requests or cached-file checks are recorded separately and are not a fresh rights review. Tests verify original bytes, all mask/CT samples, source grid conversion, half-integer isosurface correspondence, component/status preservation, corruption rejection, exact derived/render hashes and retained rights/clinical holds. Python 3.9: three pass/two NumPy skips; scientific Python 3.12: five pass.

No clinical approval, complete anatomical coverage or runtime promotion is granted. The full goal remains active: 33,246 known-floor obligations, 84 unexpanded investigations, 106 unreconciled curriculum surfaces and unknown total. Runtime image-rights counts remain 687 / 244 cleared / 443 unverified.
