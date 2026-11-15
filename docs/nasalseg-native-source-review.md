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

## Serialized surface and CT alignment display

The five actual compressed OBJ files were hash checked, read back and rendered with all 134,496 extracted triangles. Declared LPS axes and physical aspect are retained. Display illumination uses triangle normals only; it does not alter source geometry or imply new tissue texture. The 98 original open nasal-pharynx edges are shown in red. Original disconnected regions remain present. Camera occlusion and selected views cannot prove anatomical completeness.

A separate review figure compares the original mask contours on CT with intersections of the serialized LPS triangles on those same original source planes: zyx axis 0/index 24, axis 1/index 87 and axis 2/index 79. Mesh coordinates are transformed back with the inverse of the original declared affine; no fitted registration, resampling, snapping or anatomical repair is applied. The two displays visually align on these three planes. This is a source consistency check, not a quantitative claim that every triangle exactly matches an independently validated anatomical wall. In particular, the retained Lewiner ambiguity vertices and piecewise planar triangulation remain extractor approximations.

Plane intersection checks distinguish crossing triangles from wholly off-plane and plane-coincident triangles. They do not project nearby geometry onto the CT plane. Rendering evidence and hashes are saved in `source-surface-display-review.json`; the full PNGs remain in the ignored research cache. Ten scientific checks pass, including grid order, component/boundary preservation and triangle-plane intersection behavior. Independent raw acquisition/HU lineage, source anatomical validation, complete reportable structures and runtime model integration remain pending.

## Partial reader source reference

The reader now offers a regional CT source reference containing all five original label-interface surfaces and the same-case CT/contour figure. All 134,496 triangles and original components/open edges remain. Display transport converts positions to float32 with recorded maximum error ≤0.00004 declared mm; exact face bytes survive readback. Double precision source positions and faces are retained as compressed review evidence. Display normals do not change geometry. Dataset attribution and the original CC BY 4.0 record are preserved independently of the differently licensed article.

The model starts with its entire acquired source extent, explicitly labelled “Acquired source extent · scan-truncated.” Rotation, selection and isolation cannot recover missing anatomy. Patient age is not inferred. The model is not registered to the unrelated published CT/MRI lesion figures. Missing sinuses, operative bone, mucosa, nerves, vessels, physiological drainage and lesion/extension anatomy remain explicit. Clinical and anatomical approval stay false, and all five model assets plus the source CT display retain empty structure coverage with pending anatomical review.
