# Original adrenal gland and vessel source candidates

Eight original BodyParts3D version-manifest 4.3 objects were acquired through the upstream download service: separate left/right adrenal glands, inferior/middle suprarenal arteries and suprarenal veins. Original ZIP CRC, both actual representation-mapping trees and every OBJ file/representation/concept/version header were checked. Full metadata snapshots and original OBJ bytes remain under the ignored source root; selected manifest/mapping excerpts and fingerprints are preserved in this review packet.

The upstream grant is [CC BY-SA 2.1 Japan](https://lifesciencedb.jp/bp3d/info_en/license/index.html), with BodyParts3D © 2008 DBCLS attribution. The archived 4.0 dataset's separate CC BY 4.0 grant was not reused for these upstream objects. Review figures retain ShareAlike attribution. No runtime licence clearance or clinical anatomy approval follows from public availability alone.

| Original object | Source label | Triangles | Exact-position components |
| --- | --- | ---: | ---: |
| FJ3129 | Left adrenal gland | 3,996 | 1 |
| FJ3130 | Right adrenal gland | 2,294 | 1 |
| FJ3467 | Left inferior suprarenal artery | 954 | 2 |
| FJ3584 | Right inferior suprarenal artery | 754 | 1 |
| FJ3472 | Left middle suprarenal artery | 552 | 1 |
| FJ3586 | Right middle suprarenal artery | 654 | 1 |
| FJ3480 | Left suprarenal vein | 674 | 1 |
| FJ3580 | Right suprarenal vein | 608 | 1 |

Every one of the 10,486 original triangles is retained. Positions, normals and face/normal indices are fingerprinted in the [full geometry inventory](bodyparts-adrenal-source-review/original-obj-geometry-review.json). Exact-position indexing is analysis only; it does not weld or modify the original objects. All eight have no exact-position boundary or nonmanifold edges and no zero-area triangles. These checks do not prove anatomical solidity or biological correctness. Source-declared versus actual bounds differ by at most approximately 0.0001 mm; neither values nor coordinates were corrected or fitted.

The left inferior artery contains a 952-face component and a separate two-face component. Original faces 462/463 have identical three positions with opposite order; none of those positions occurs in the remaining source faces. [Independent source-face readback](bodyparts-adrenal-source-review/coincident-source-component.json) preserves the original indices and positions. This coincident sheet is not assigned a biological branch, removed as presumed noise or used to support vessel-wall/lumen claims.

The complete continuous-contact audit tests all 10,486 triangles in native source millimetres. Its 96,505 conservative candidate pairs comprise 80,779 explicit tests and 15,726 noncoplanar shared-edge pairs resolved geometrically. It preserves 724 contacts beyond ordinary adjacency: one within the coincident source component and 723 between original gland/vessel objects. The tolerance is 1e-9 mm, not native acquired resolution. Source contacts do not prove vascular entry anatomy, tissue interfaces, invasion or a reason to delete tissue. Original source position relationships have not been independently anatomically approved.

[Contact summary](bodyparts-adrenal-source-review/complete-contact-summary.json) fingerprints the [complete lossless contact evidence](bodyparts-adrenal-source-review/complete-source-contacts.json.gz), including every contact point and original source face identity. [Contact location views](bodyparts-adrenal-source-review/adrenal-source-contact-locations.png) preserve all eight source meshes as context, every affected face and every numerical contact, with separate detail of the coincident sheet. [Location provenance](bodyparts-adrenal-source-review/contact-location-review.json) records complete face coverage. Projection overlap is not a biological classification.

Both [azimuth-35](bodyparts-adrenal-source-review/original-source-azimuth35.png) and [azimuth-215](bodyparts-adrenal-source-review/original-source-azimuth215.png) views render every original triangle separately in native source coordinates. Panel scales and review lighting are display choices. The azimuth-35 and contact-location figures were directly inspected for source identities, complete presentation, axes, component context and attribution. This presentation inspection is not independent clinical validation.

The objects do not separately label gland body/limbs, capsule, cortex/medulla, every superior/accessory arterial branch, parent vessel origins, vessel-wall layers, a calibrated lumen, pathological lesions or tumour thrombus. Their original acquisition resolution, reduction history, anatomical accuracy, patient-coordinate orientation and complete extent remain unresolved. No original mesh is fused, smoothed, repaired, capped, registered to the published image cases or promoted into runtime; existing erroneous kidney/artery selections remain cleared. All 672 adrenal representation obligations remain required and unverified/missing.

Verification: 26 scientific source/selector/geometry/contact regressions passed, including preserved pancreatic/peritoneal behaviour and complete original adrenal source identities, components, contacts and rendered faces. Fifteen local adrenal/source/image checks also passed. These tests confirm evidence integrity and scope limits; they cannot supply specialist clinical approval. The full all-radiology goal remains incomplete.
