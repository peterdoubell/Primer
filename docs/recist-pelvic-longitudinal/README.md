# Case 023 longitudinal RECIST reference

Use the case and publisher target alias as the identity across scans. For each examination, use its own series UID, image filename, and local mask value to select the voxel region. The mask integer is local to each scan. The source CSV gives axial short-axis values for these two nodal targets. It supplies no ruler endpoints.

| Source scan | Target A | Source label, value | Target B | Source label, value | Documented sum |
| --- | ---: | --- | ---: | --- | ---: |
| 2021-07-29, baseline | 16 mm | `n,iliac`, 1 | 16 mm | `n,aortocaval`, 6 | 32 mm |
| 2021-11-03, follow-up 1 | 17 mm | `n,inguinal`, 1 | 13 mm | `n,retroperitoneal`, 9 | 30 mm |
| 2021-12-07, follow-up 2 | 16 mm | `n,pelvis`, 1 | 14 mm | `n,retroperitoneal`, 8 | 30 mm |

Display the source terms with each image and flag their variation for alias A. Both follow-ups tie at the observed minimum of the documented sum. The sum change from baseline is −6.25% on both. An overall response category requires the other RECIST observations, including non-target and new lesions.

Use the existing baseline case for target A label 1. Exported follow-up bands wrap the complete target A mask with a 25 mm sampling margin. Target B is out of these bands and remains in the table. Each scan uses its own native affine, HU transform and in-plane spacing. Label or time selection may move between panels. Keep spatial cursors independent because no cross-examination registration is supplied. The source metadata gives a nominal 5 mm section thickness and 2.5 mm section spacing for each examination.

Read the aligned source volume triplet from the package’s source and mesh manifests. Confirm exact bytes against each delivery manifest. The target is shown from nearest source samples with individually preserved label voxels. A visible voxel boundary model shows the source segmentation. Each source short-axis diameter is a reported value, and drawing a ruler from the mesh would create a different measurement.

Original source, Rojas-Pizarro and colleagues, Universidad de Chile. Primer losslessly extracts samples and builds the exterior boundary of the source-labelled voxels. [Dataset](https://zenodo.org/records/17788162) · [Article](https://doi.org/10.1038/s41597-026-06597-6) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
