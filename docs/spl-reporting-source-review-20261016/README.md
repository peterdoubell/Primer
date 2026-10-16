# SPL brain reporting relationships

The brain-anatomy lesson and reporting reference gain a grouped native-MRI/3D inspector. It contains **217 source classes**, adding **205 distinct classes** to the earlier twelve-structure reference. There are 207 newly generated boundary payload sets, including two previously represented classes, and ten payload sets reused directly from the earlier viewer. Neither payload count nor source-class count is a completeness denominator.

The viewer links each selected class to native axial, coronal and sagittal T1/T2, supplies paired-structure overlays and surfaces, and exposes every retained source component. A projected R/A/S axis display follows the 3D camera. Changing contrast or plane retains a selected minor component. Groups with no categorical classes show MRI only; returning to a populated group restores the prior overlay choice. Source names, conflicting metadata names, combined/residual classes and source hierarchy qualifications remain visible.

The dataset is the [SPL/NAC Brain Atlas](https://www.openanatomy.org/atlas-pages/atlas-spl-nac-brain.html), pinned to commit `bec24db25aad5f7600e2df3becfb1f883e61ff56`. The publisher describes MRI and labels derived from one volunteer. That source description does not establish population norms, clinical accuracy of every parcellation boundary, or a current patient's anatomy.

## Reporting groups and remaining gaps

| Group | Supplied context | Material limits |
|---|---|---|
| Orientation | Native 0.75 mm T1/T2 and separate 1 mm Int16 labels | Separate source affines; no fitted registration or oblique reslicing. |
| Deep grey | 14 classes: caudate, putamen, external/internal pallidal parts, accumbens and adjacent claustral/subthalamic context | Named source labels do not independently validate fine borders or subdivisions. |
| Thalamic parts | 26 named source parts | Includes lamina and geniculate bodies; no demonstrated complete whole-thalamus partition. |
| White matter | Left/right hemispheric white matter | Capsule limbs, corona radiata and other separate tract regions are absent as distinct classes. |
| Commissural/midline | Callosum, septum and anterior commissure | No separate callosal segments or cavum spaces. The remote anterior-commissure component remains inspectable and continuity-unvalidated. |
| Brainstem | 15 source classes including residual pons, partial midbrain, medulla and named nuclear/collicular context | Does not supply complete brainstem nuclei, peduncles or fibre systems. |
| Cerebellum | 70 source classes: parcels, white matter, dentate and combined FaGE | Combined classes stay combined. Zone names come only from recorded source hierarchy, without suffix extrapolation. Distinct peduncles remain absent. |
| Ventricles | Seven current categorical classes | Horn/body/atrial subdivisions are incomplete; source connectivity is not physiological patency. |
| Cortex | 70 parcels | Partial/unsegmented source qualifications remain; these are not complete whole-lobe or sulcal-boundary masks. |
| Sulci | MRI context and explicit source gap | Original model-only sulcal curves are not acquired or represented here. |
| Cisterns/extra-axial spaces | MRI context and explicit source gap | No invented compartment masks. |
| Vascular localisation | MRI context and explicit source gap | No angiographic lumen or vascular-territory validation. |
| Limbic context | The twelve earlier source classes | Separate CA fields/subiculum remain absent. The earlier viewer retains the separate publisher-surface comparison. |

The compressed requirement and inventory records retain the prior audit's source identities and limitations. All 286 components under 26-neighbour connectivity remain present. Components are grid properties, not counts of biological structures. The unnamed source singleton remains in the original full label array; this viewer does not assign it a fabricated identity.

## Geometry and native images

All 2,491,024 displayed triangles follow exposed categorical cell faces, retaining cavities and small components. The new meshes use the same independently checked cell-boundary producer as the earlier reference. No smoothing, component deletion, filling, boundary fitting or cosmetic repair occurs. The voxel stair steps are source sampling, not a claim of a smooth anatomical contour.

The Python function stores the authored manifest as a byte-verified lossless gzip and serves its exact original JSON bytes through the private route. The plain web manifest remains the canonical test/generation artifact; it is excluded from the function bundle.

Native MRI and labels are reused from `spl-nac-limbic`; they are not copied, resampled or transformed to make surfaces agree. The viewer verifies the shared source manifest's exact identity and requires its native descriptors unchanged. Boundary vertices are already source RAS millimetres and receive no additional affine.

`check_spl_reporting_source.py` independently compares every emitted face with an occupancy-grid oracle and every triangle with its exact cell plane, outward normal, half-square-millimetre area and shared diagonal. It checks all source components, sample-contained focus points and original LUT identities. It imports neither the mesh producer nor viewer coordinate helpers.

## Verification

- `current-source-verification.json`: every current mesh/class, exact exposed faces, triangle geometry, original LUT identity and retained components.
- `viewer/standalone-proof.json`: 1,340 actual-canvas cases, **97,572,864 pixels**, both viewport widths, selected-label overlays for all 217 classes in six native contrast/plane combinations, 286 component controls, all 217 actual GPU position/index/world buffers at each width, fitted frusta, projected orientation axes and six load-failure/recovery paths.
- `viewer/reader-proof.json`: eight authenticated synthetic reader cases across Images, 3D anatomy, walkthrough and lesson gallery at 390/1440 px; **3,497,984 native pixels**, actual source delivery, current startup identity, source limits, CSP and layout checks.
- `viewer/preservation-proof.json`: current combined-reader preservation of the earlier twelve-structure source, **874,496 native pixels** and 24 original/categorical GPU meshes at each width. It does not extend the earlier frozen 24-case receipt.
- `integration/runtime-inverse.json`: exact changes to five shared integration/scope files and one added source-inspector item. Historical reconstruction grants no approval to the new anatomy. Current behaviour has its own proofs above.

The authenticated checks use disposable synthetic learner storage and empty Turso credentials. They do not exercise or modify a production learner record. Existing external reference-image URLs are blocked and recorded by these loopback checks; no availability claim is made for those unrelated remote images.

Reproduce source metadata with `python -m tools.anatomy_sources.spl_reporting_prepare`; add `--rebuild-meshes` to reproduce the 207 generated payload sets and compare their transport identities. Run `python tools/check_spl_reporting_source.py`, then `node tools/check_spl_reporting_viewer.cjs` with Playwright available. Run the isolated reader launcher with `python tools/check_spl_reporting_reader.py`, and its earlier-viewer preservation pass with `--preservation-only`. Refresh the registry only after those checks using `python -m tools.anatomy_sources.spl_reporting_registry`.

## Rights and approval boundary

The applicable [full source licence](../../web/anatomy/spl-nac-limbic/LICENSE.txt), [attribution and conversion notices](../../web/anatomy/spl-nac-limbic/ATTRIBUTION.txt), original author/funding notices and research-use qualifications remain attached through the shared source. This is a marked derived representation under the publisher's Slicer Agreement terms, not CC BY. No institutional endorsement, clinical approval, complete reporting-anatomy approval or whole-Primer completion is claimed.
