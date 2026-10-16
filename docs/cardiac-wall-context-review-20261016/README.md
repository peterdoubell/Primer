# Supplementary cardiac walls and published CT comparisons

Review date: 2026-10-16. This addition improves inspectable cardiac anatomy context; it does not establish complete reporting anatomy or clinical/commercial readiness for the whole Primer.

Two independent sources are appended to thoracic ultrasound, MRI cardiomyopathy, coronary CT and cardiac-mass references and their shared lessons. Existing CT sources, images, reporting guides and clinical data remain separate. Neither source is fitted, registered or relabelled as the current patient's study.

## Original curated geometry

Fourteen original BodyParts3D 4.3 objects retain all 72,572 triangles, source coordinates, face order and authored normals. They include separately labelled left/right atrial walls, one combined ventricular-wall object, six semilunar cusps and five papillary-labelled objects. Original OBJ files, representation/FMA headers, CRC-verified ZIP acquisition and original mapping/license evidence are retained. Upstream license: **CC BY-SA 2.1 Japan**, with DBCLS attribution; the different 4.0 archive grant is not reused.

The combined ventricular-wall object has eight exact-position diagnostic components, seven nonmanifold edges and three zero-area triangles. The anterolateral LV papillary-head and right anterior pulmonary-cusp objects each retain two components. None are deleted, smoothed, welded, capped, fitted or declared independently normal anatomy. Source object closure does not prove physiological boundary accuracy. The ventricular object is not split into separate clinically verified LV/RV wall models. Annuli, chordae, pericardial layers, fine interfaces and functional measurements remain absent or unverified.

Display transports preserve every ordered face and original normal association with quantified float32 coordinate error. The aspect-aware camera reset uses a source bounding-sphere fit; independent projection checks verify every original vertex remains within the viewport at desktop/phone sizes. Original geometry is not cropped to make it fit. Research browser evidence covers 36 cases, including 28 exact actual-GPU position/normal/index comparisons. `curated-prototype-browser-proof.json` records the pre-integration source viewer evidence; current authenticated reader evidence is separate.

## Published image comparisons

The complete original 425,386,105-byte archive was acquired from [Zenodo record 3863028](https://zenodo.org/records/3863028), the official mirror of Dryad DOI 10.5061/dryad.9s4mw6mc9. Its publisher MD5 and original Dryad SHA-256 both match. The source data are CC0 1.0. No original PNG is repainted, cropped, relabelled or re-encoded.

The reader includes all **6,061 original PNGs in the eight methods-defined categories**: coronary sinus, descending aorta, IVC, left atrial wall, proximal ascending aorta, pulmonary artery, right ventricular wall and SVC. Each original file remains byte-identical under its content-addressed filename; the inventory retains its original archive member and source case identifier. Case identifiers are displayed as consistent source-case pseudonyms. The original 512 × 256 comparison images contain two 256-pixel panels; no raw CT volume, physical slice spacing, scanner intensity calibration or 3D mask is inferred from them.

[Baskaran and colleagues' methods and figure captions](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0232573) identify green as manual annotation and red as model prediction. These roles are displayed explicitly. Prediction/annotation disagreement is preserved; neither side is treated as a current-patient result or independently perfect boundary. Three additional archive categories (LAA, LV papillary muscle and posterior mitral leaflet) remain excluded from the teaching reader because their separate definitions/validation and per-panel interpretation are not established by the eight-class methods. All 7,749 original archive PNGs were inventoried and CRC-checked in research; exclusion is based on source-role evidence, not on model agreement.

## Reader, delivery and verification

`data/radiology/cardiac-wall-context.json` binds the two source contexts, exact file sets and hashes. Curated geometry has 31 resources; the comparison viewer has 6,064 resources including every methods-defined PNG. Authored viewers are authenticated, private and not cached. Registered payloads use fixed static paths in production. Unknown/encoded resource aliases, symlinks, nonregular files and present corrupt bytes cannot fall back to a different source.

The comparison script is an external same-origin asset under the existing script CSP; only its own HTML permits hash-verified Blob images. No global script or external-host permission is broadened. Existing cardiac orientation/anatomy modes remain available alongside the new supplementary contexts.

`integration/local-reader-proof.json` covers sixteen real authenticated reader cases: four references and their shared lessons, at 1440 and 390 pixels. All fourteen source objects remain available. Each of the eight comparison categories passes full decoded-RGBA equality against independently decoded source PNGs in every reader case. Forty-two representative authored/source resource responses match originals or explicitly decoded HTTP representations. All 6,095 resource identities are independently checked by the source tests. Source images and geometry supply no automatic current-patient report findings.

`integration/runtime-inverse.json` pins exact literal reversals of six shared files for older frozen evidence. The bounded lesson view restores only the known supplementary instructions and exact new source objects; unrelated changes remain visible/rejected. Prior source reviews, guarded native decoders, registration limits and clinical flags are unchanged. The new viewers are new source-specific code, not approval extensions to older decoders.

Focused source/history checks passed 153 tests; reporting, UI and scope checks passed another selected suite of 96 tests. Full CI and staged/canonical delivery verification remain release gates. The goal inventory still has 136 investigations, 106 curriculum nodes and 40 unexpanded investigations. No whole-goal, fine-anatomical, normal-atlas or clinical-completeness approval is granted by these counts.

The runtime registry and comparison inventory use deterministic, byte-verified gzip storage to stay within the function-size limit. Every decoded JSON byte and all source records are preserved. The original registry remains offline, and the original inventory is retained in `comparison-manifest.json`. A thin-production fixture verifies that only packed metadata and authored resources are required in the function; static source payloads retain their original bytes. The authenticated inventory response uses JSON MIME with gzip content encoding.
