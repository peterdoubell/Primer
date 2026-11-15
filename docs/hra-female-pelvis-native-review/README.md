# Exact native HRA female pelvic source excerpt

This package retains 54 complete original mesh occurrences and 293,490 triangles from the HRA united-female v1.10 GLB. It is a curated source reference. Clinical, every-structure, fine-layer and complete reporting anatomy approval remain false or pending.

| Original selected group | Complete occurrences |
| --- | ---: |
| Vagina and original cervicovaginal junction | 2 |
| Fallopian tubes | 8 |
| Ligaments of uterus and ovaries, including source pouch/broad ligament/mesenteric regions | 16 |
| Ovaries | 2 |
| Uterus and cervical source surfaces/walls | 10 |
| Rectum and sigmoid colon | 2 |
| Ureters and bladder source regions | 8 |
| Selected pelvis source meshes | 6 |
| Total | 54 |

The selected original accessor/index storage occupies 5,558,012 packed bytes. Viewer BP3D files preserve original Float32 positions and normals and widen unchanged ordered index values to uint32. Every selected primitive and occurrence remains distinct. Extra source attributes are retained in `selected-original-native.glb.gz`; the original uterus wall `COLOR_0` arrays are included. Original material objects are retained in both native evidence and the runtime manifest. Viewer colors and shading are display aids and are not biological tissue identity or MRI signal.

The native excerpt preserves all 1,160 original source node slots, children, source extras, scenes, local metadata and transforms, and all 151 original material objects. Unselected mesh attachments are omitted explicitly. Selected mesh/accessor addresses are changed to reference only retained storage. Vertex IDs, values and triangle order are unchanged. Selected nodes and every source ancestor have identity local/global transforms. No crop, weld, smooth, repair, fill, merge, geometric remap or fitting occurs. The full original glTF JSON chunk is also retained byte-for-byte in compressed form.

glTF declares metre units and a right-handed Y-up coordinate system. Source acquisition calibration, patient anatomical axes and MRI registration remain unverified. Source camera labels carry no patient direction claims.

The original anterior/posterior uterus wall labels are preserved. Those meshes share 234 exact coordinate triangles; they do not constitute independently verified endometrium, myometrium, junctional zone or histological layers. Source cutaway-like presentations and open surfaces are retained. Parametrial and nerve boundaries, torus uterinus, rectovaginal septum, bowel-wall layers, lesions, surgical margins and complete module anatomy remain pending.

The full female assembly metadata describes a “Female-united set” derived from the “Visible Human Dataset.” The older standalone uterus v1.1 metadata literally says “Visible Human Male.” The standalone ovary/tube metadata explicitly says “Visible Human Female.” Original documents are retained separately; no wording is silently corrected and donor equivalence is not inferred.

`original-united-female-v1.10-metadata.json` retains the original raw-data CC BY 4.0 grant, creators Kristen Browne and Heidi Schlehlein, citation, DOI and source download distribution. The attribution notice is also shipped beside the runtime manifest.

Independent evidence includes the source reviewer inventory with raw accessor offsets/hashes, Three.js 0.180.0 GLTFLoader readback of both the full source and packaged native excerpt, direct raw full-GLB-to-excerpt comparison, standalone-to-full-scene correspondence, and exact triangle duplication analysis. The committed tests independently decode raw accessor storage with NumPy, compare every retained attribute and ordered index, verify BP3D byte transport, and preserve source provenance and approval holds. The 374,505,632-byte original GLB stays in ignored acquisition storage.

Reproduce from the repository root:

```sh
python3 tools/anatomy_sources/package_hra_female_pelvis.py \
  --source-root /Users/peter/Documents/ChatGPT/Primer/.research/hra-female-pelvic-source-20261010 \
  --output web/anatomy \
  --review-output docs/hra-female-pelvis-native-review \
  --source-review docs/pelvic-source-fidelity-followup-20261010/hra-original-geometry-review.json

/Users/peter/Documents/ChatGPT/Primer/.research/runtime-grade-py312-20261008/bin/python \
  -m pytest tests/test_hra_female_pelvis_source.py -q
```

Runtime reference contract:

```json
{
  "atlas": "hra-female-pelvis-v1.10",
  "family": "female-pelvis-source",
  "manifest_url": "/app/anatomy/hra-female-pelvis-v1.10/manifest.json",
  "manifest_sha256": "ca947cc1bf39e165708d2a634e1acbe847629b90d14a89b6f38a4f6ccfbcc776",
  "initial_layer": "source-surfaces",
  "initial_cropped": false,
  "source_coordinate_system": "native-gltf-y-up"
}
```

`transport-review.json` records hashes, counts, storage sizes and exact source-to-excerpt mappings. Runtime/source-reference registration is integrated separately; this package does not approve complete module fidelity.
