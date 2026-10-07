# Original sinonasal source-grid and label-interface review

The [NasalSeg dataset record](https://zenodo.org/records/13893419) explicitly grants CC BY 4.0. The associated article has a separate CC BY-NC-ND 4.0 grant; no article figures are reused. Dataset attribution: Yichi Zhang and the NasalSeg dataset authors, record 13893419. Preserve original attribution and the dataset grant when distributing derivatives. The [HaN-Seg paired CT/MRI dataset](https://zenodo.org/records/7442914) has a noncommercial, no-derivatives grant and is excluded as a commercial geometry source. Its volumes were not acquired.

The complete 224,005,800-byte NasalSeg archive passed its publisher MD5. Original case P001 CT and mask members passed ZIP CRC and independent scalar readback of all 3,261,960 combined samples. Both declare the same 153×205×52 xyz grid, LPS affine and 0.5859375×0.5859375×1.5 mm sample pitch. This is a regional volume, not proof of an uncropped native head, calibrated scanner HU, effective resolution or operative thin-bone detail. Matching raw DICOM acquisition and preprocessing lineage remain unverified.

The original source label mapping is retained: 1 right maxillary sinus, 2 left maxillary sinus, 3 right nasal cavity, 4 left nasal cavity, 5 nasal pharynx. Label names are source attribution; independent anatomical and laterality validation remains pending. The original left nasal-cavity mask has two six-neighbour components. Nasal pharynx touches the lower z boundary. Neither finding is filtered, filled, joined or capped.

Unsmoothed, undecimated Lewiner marching-cubes interfaces are extracted at binary level 0.5 on the original samples, transformed through the declared affine and saved as compressed OBJ files in the ignored research cache. These are interfaces of the supplied region labels. They do not independently delineate bone, mucosa, nerves, vessels or their thickness. No padding, boundary closure, geometric repair, smoothing or removal of small components is applied.

| Original label | Triangles | Surface components | Boundary edges | Interior ambiguity vertices |
| --- | ---: | ---: | ---: | ---: |
| Right maxillary sinus | 17,204 | 1 | 0 | 0 |
| Left maxillary sinus | 15,580 | 1 | 0 | 0 |
| Right nasal cavity | 42,672 | 1 | 0 | 4 |
| Left nasal cavity | 42,062 | 2 | 0 | 11 |
| Nasal pharynx | 16,978 | 1 | 98 | 1 |

Every edge-interface vertex is checked against opposite original binary samples. The 16 additional ambiguity-resolution vertices are retained; their maximum trilinear binary-field residual is 0.125. This residual describes the extractor's cell triangulation, not an anatomical distance or accuracy claim. No nonmanifold edges or zero-area triangles were found. All serialized vertices and faces passed readback against the extracted arrays. Affine inverse checks preserve source indices. Original components and acquisition-boundary truncation remain explicit.

The same-case CT/contour display uses the declared physical sample aspect and original in-plane indices. A −1000..1500 source-unit display window does not establish calibrated HU. Three displayed planes do not prove every surface or label anatomically correct. The reviewed PNG and all five OBJ files remain in `.research/sinonasal-native-source-review/`; hashes and scientific review results are saved in `docs/nasalseg-native-source-review/`.

Frontal, ethmoid and sphenoid sinuses, detailed drainage pathways, operative bone interfaces, skull base, optic nerves, carotids, perineural routes and pathological extension are not established by these five masks. MRI tissue characterization cannot be borrowed from this CT case. No runtime promotion, anatomical leaf coverage or clinical approval is granted. Complete sinonasal requirements and independent anatomy review remain necessary before this source can support the requested clinical/commercial standard.
