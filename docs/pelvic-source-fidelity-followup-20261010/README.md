# Pelvic source fidelity follow-up

The original Human Reference Atlas female assembly provides a concrete route to replace the MRI endometriosis module's procedural pelvic orientation with preserved source atlas geometry. The inspected subset has 54 original mesh occurrences and 293,490 triangles. All original packed attributes and indices occupy 5,558,012 bytes; simplification is unnecessary for this intake. This review makes no runtime change or whole-reporting coverage claim.

## West Bohemia: stronger units/frame evidence, limited anatomical provenance

The [original visualiser](https://doi.org/10.5281/zenodo.17423100) manual, printed page 25, declares the displayed distances in millimetres. Page 40/Figure 37 declares six source view directions. Static inspection of the original packaged Python module recovers 24 explicit reference landmarks, direct `PolyData(vertices, faces)` construction, and an unscaled coordinate-distance calculation labelled `millimeter`. The producer software was never executed.

Every landmark was compared with every original bone triangle. Nearest surface distances range from 0.065032 to 2.994381 declared millimetres; an independent nearest-vertex bound and four analytic triangle-distance cases check the calculation. All eight paired left landmarks have positive left-minus-right X displacement and correspond to left bone surfaces. PSA/PSP and PSI/L5 ordering support authored +Y posterior and +Z superior, with +X left. This establishes the intended source frame, not DICOM acquisition axes, acquired spacing or current-patient registration. Example target landmarks are distinct from the embedded reference landmarks.

The [2026 evaluation coauthored by the producers](https://csma2026.sciencesconf.org/688347/document) distinguishes its fresh-cadaver MRI/CT reference from the generic FPFV template. Those acquisition facts therefore cannot be assigned to the shipped JSON. Its single morphed case has reported bony mean error 0.9 mm and standard deviation 3.98 mm over 50,000 points. Perineal-body anterior-posterior displacement is reported; quantitative soft-tissue surface comparison was not possible because muscle/thickness representations differ. This supports a useful generic biomechanical template while limiting patient-specific soft-tissue claims. It does not establish original subject, segmentation or fine-layer provenance for the exact Zenodo meshes.

The five unpaired organ objects remain exact, single index-connected components, with no separate named uterine or bowel-wall layers. Ovaries and tubes are absent. Component counts and byte preservation are not anatomical validation.

## HRA: original native geometry, rights and correspondence

[Browne and Schlehlein's female v1.10 assembly](https://doi.org/10.48539/HBM637.DWBM.744) has an explicit CC BY 4.0 raw-data grant and Visible Human Dataset provenance in the retained original metadata. [NLM](https://www.nlm.nih.gov/research/visible/visible_human.html) separately describes the original male/female cadaver images as public-domain data. The HRA atlas grant and authoring are retained as their own evidence; cadaver acquisition does not automatically validate every authored subdivision.

The original GLB is 374,505,632 bytes, SHA-256 `95f0c3d2f918582608692ca1139e8bdb18c147a16470e9ee9af8b276bd77c422`, containing 1,160 nodes and 956 meshes. The selected 54 occurrences include vagina/junction, both ovaries, bilateral tubal parts, uterine regions/walls/cervix, 16 ligament/fold objects, bladder regions/orifices, bilateral source ureters, rectum/sigmoid and six pelvic bone presentations. Every selected ancestor transform is identity. [glTF](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#coordinate-system-and-units) declares metre units and +Y up. Separate published HRA graph placements are retained in research staging and were not silently applied to the native GLB.

An independent Three.js 0.180.0 `GLTFLoader` matches every selected POSITION, NORMAL, COLOR_0, texture-coordinate and index bit, plus scene placement. Twenty native meshes in the five older standalone uterus/ovary/tube originals also match the full assembly exactly. The standalone uterus v1.1 metadata says **Visible Human Male**, while [NIH 3D's original uterus entry](https://3d.nih.gov/entries/20996) identifies the female reference. This conflict is preserved; the older wording does not overwrite the full-scene provenance.

The original front/side renders show actual source regional, wall and bone presentations. Uterine wall objects 483/484 share 234 exact coordinate triangles. Their source names and surface classifications do not establish endometrium, myometrium, junctional zone or independent tissue layers. No opening, duplicate, overlap or cutaway-like presentation is repaired.

This is a viable source atlas reference with reliable native transport and an ordinary redistribution grant. Fine uterine/bowel layers, torus/rectovaginal/parametrial boundaries, nerves, endometriosis lesions, surgical margins and current-patient registration remain pending. Existing CVH5 decoder/clinical holds are unchanged.

## Evidence and reproduction

- `primary-evidence-review.json`: exact manual/publication identities and source-specific claims.
- `native-correspondence-review.json` and `producer-code-evidence.json`: source landmarks, original bone correspondence and static producer instructions.
- `hra-original-geometry-review.json`: every selected source node, mesh, primitive, accessor, original byte span/hash, material and transform.
- `independent-gltf-decoder-review.json`: complete independent standard-decoder readback.
- `independent-package-correspondence-review.json` and `independent-packaged-gltf-decoder-review.json`: direct original-to-packaged-excerpt comparison and a second standard decode of that exact excerpt; all 54 original geometries, materials and placements agree.
- `standalone-to-united-correspondence.json` and `source-uterus-morphology-review.json`: original reproductive correspondence and exact shared triangles.
- `original-hra-united-female-v1.10-metadata.json`: unchanged producer metadata and raw-data grant.
- `original-hra-uterus-female-v1.1-metadata.json`: unchanged older standalone metadata, including its conflicting Male wording.

Original GLBs, graph/crosswalk, standalone metadata and the privately inspected conference PDF remain in ignored `.research/hra-female-pelvic-source-20261010`. The conference PDF is not redistributed here because its reproduction grant was not established. Figures retain source meshes/materials; review cameras, lighting and visibility choices are display controls, not MRI signals.

Reproduce the tracked correspondence inventory with Python 3.12 and NumPy:

```sh
python tools/anatomy_sources/review_pelvic_source_fidelity_followup.py \
  --source ../west-bohemia-pelvic-source \
  --preserved docs/west-bohemia-pelvic-source-review \
  --output docs/pelvic-source-fidelity-followup-20261010 \
  --hra-source ../hra-female-pelvic-source-20261010
```
