# Native source presentation reconciliation — 2026-10-11

This bounded review covers **20 pending assets and all 40 originally recorded dependency mismatches**: two Liu sub03 cord/dura contour envelopes, 17 VerSe521 T1–T12/L1–L5 source-label meshes, and their native CT-plane helper. It fixes an actual label/readout defect and proposes source-byte-checked presentation amendments. It does not approve fine tissue boundaries, anatomical accuracy, clinical interpretation, source-case normality, current-patient registration or complete reporting coverage.

## Original issues and changes in scope

The original issues remain in `initial-dependency-issues.json`, including each asset ID, dependency path and old expected/current hash. The two old dependencies are `web/app.js` (`911d86e…`) and `source-anatomy-references.json` (`8861959d…`). Their contents were found in Git at the reviewed carotid release. Comparison with the initial branch shows that app changes add source-table caption/context handling, while source associations add unrelated pelvic references. The existing thoracolumbar source entries and native renderer transforms/loader/camera-label functions are unchanged, apart from the subsequently authorized CT-helper correction and its transport registration.

The [proposed amendment contract](proposed-presentation-amendments.json) lists all 20 source files and unchanged hashes, every original issue, current verified dependency hashes, and exact proposed metadata changes. Root owns application to the existing ledgers/registries after independent review. Anatomical status stays `pending`, structure bindings and requirement coverage stay empty, and unrelated holds remain untouched. No historical presentation is retrospectively treated as anatomically certified.

## Concrete presentation defect fixed

The CT helper formerly printed its **binary 0/1 target-membership array as “target label.”** Original VerSe IDs are T1–T12 = 8–19 and L1–L5 = 20–24; label 1 belongs to C1 in the authors' [label specification](https://github.com/anjany/verse#data). The readout now explicitly shows the selected level and original source label ID separately from membership `present`/`absent`. Pointer coordinates outside the image, invalid coordinates or zero-size bounds yield no sampled voxel; leaving the image clears the stale sample instead of presenting a clamped edge voxel.

Independent follow-up review found that a prior-level pointer sample could survive while a new level's arrays were decoding or unavailable. Loading now immediately clears that sample and old source scope. Decode errors clear the unavailable state, and a superseded request's error cannot overwrite a newer load. Controlled real gzip fixtures and the actual desktop/mobile source reader verify these transient states.

Only `web/anatomy/verse521/ct-reference.js` changed existing runtime behaviour. Its reviewed SHA-256 is `30f82f5a0ef534ce44bfbe40961220abc6487fd426f9af914622ef79c0177890`. Every source voxel, mask, affine, mesh position, face, normal and HTML payload remains unchanged. Root updated only the matching source-volume script transport hash to allow strict actual-reader QA.

## Native source, coordinates and geometry

The recorded original temporary masters were unavailable. Minimum licensed source files were freshly reacquired from the pinned author archives, with validated HTTP ranges/archive identity, ZIP CRC, size and recorded SHA-256 checks. No rendered figure or old audit was substituted for a missing native master.

VerSe's CT and segmentation retain the common 512×512×487 grid, selected CT RAS affine and L/A/S index directions. All 17 runtime meshes equal the preserved candidate positions/faces exactly, and those candidates were rechecked against the fresh original labels. Every embedded CT crop equals its corresponding native scaled CT values; every binary mask equals exactly `(original label == selected ID)`. The 798,442 triangles, all label components and original voids are retained. Every edge intersection remains on the 0.5 label-field boundary; retained Lewiner cell-centre helper approximations are explicitly recorded rather than silently repaired. Area-weighted normals remain lighting data.

The native RAS display map is `[R,A,S] → [−R,S,A]`; the native Liu LPS map is `[L,P,S] → [L,S,−P]`. Both preserve distances and handedness. Their numerical coordinates and camera-direction labels were independently checked. These two different source cases are not fitted to one another.

For Liu, the fresh CISS image/sidecar and 146 original Markups JSONs match the recorded source hashes/CRCs. All 3,167 original controls remain inside the native image support and on their supplied planes. Runtime positions/faces equal the preserved reconstruction candidates, and controls remain at their float32 positions. Cord endpoints retain loops of 70/170 vertices; dura endpoints retain 240/180. No caps, thickness, missing tip or roots were fabricated. Reconstruction uses explicit fresh Slicer 5.4 cardinal defaults; the authors' specific unsaved interpolation settings remain unknown. The [primary paper](https://www.nature.com/articles/s41597-024-03919-4) reports a healthy adult volunteer cohort for the released data; that provenance does not independently establish this case's boundary accuracy or normality. The distinct SCI example is not substituted into this open cohort.

Source grants remain VerSe **CC BY-SA 4.0** and Liu **CC BY 4.0**, with their original source and derivative notices. Dataset rights are not converted into anatomical approval.

## Actual reader and source-plane verification

An independently owned app/database was exercised at **1440×1050 and 390×1050**, with only a fictitious local QA profile. The two source references remained independent, initially uncropped, and labelled with their construction/coverage limits.

- All 34 native vertebral selections produced their correct same-level CT link. Both Liu layers, isolation and together views worked; switching to Liu removed the CT link.
- All six anatomical camera labels were checked. Actual WebGL-uploaded positions, lighting normals and index arrays matched all 19 decoded source meshes; source RAS/LPS shader flags matched the appropriate transform.
- All **306 complete CT-frame RGBA buffers** matched independently calculated native crop/window/overlay oracles, across all 17 levels, three planes and lower/centre/upper slices. Native voxel indices, physical RAS coordinates, direction labels, centre values and physical aspect were checked.
- All **204 actual present/absent pointer samples** reported the correct source ID and native voxel/value; **102 outside transitions** reported no sampled voxel. Separate normal-import fixtures cover 408 inside and 85 invalid/outside samples over all 17 source IDs.
- Seven served app/style/native/helper/manifest files matched local SHA-256 values, including the app and stylesheet from the latest-main rebase. No page errors, local HTTP failures or whole-page horizontal overflow occurred. Tall desktop planes were inspected by ordinary vertical scrolling. Desktop/mobile source and mesh screenshots were visually inspected.

Seven focused tests pass, including rejection of stale served hashes and changed native pixel proofs, plus pending, failed and superseded decode lifecycle checks. The complete VerSe/Liu acquisition and coordinate JSONs, complete actual-reader JSON (including its public lesson API), independent native pixel/pointer/GPU oracles, and six already visually inspected desktop/mobile screenshots are portable in this directory. `proposed-presentation-amendments.json` binds all evidence through repository-relative paths and SHA-256 values; `screenshots.json` binds the six image bytes and their [source attribution](screenshots/ATTRIBUTION.md). The source-proof JSONs retain their complete outcomes and original proof hashes, with local raw-master paths explicitly supplemental reproduction locations. Native MRI/CT volumes, original contour arrays and reconstruction candidates remain ignored and are not published by this review. The private capture directory is a nonauthoritative reproduction location. The browser driver uses normal installed Playwright imports; no sliced source execution or arbitrary executable override is used.

## Remaining anatomical work

VerSe provides whole-vertebra source labels, not independently validated cortical/trabecular boundaries, endplate layers, pedicles or facets. Stored spacing 0.68×0.68×1.0 mm differs from the source acquisition thickness of 1.5 mm; neither proves effective fine-tissue resolution. The package supplies no discs, ligaments, epidural tissue, CSF/nerve/cord shapes or fracture/compression model.

Liu's finite open lofts do not supply complete conus tips, grey/white matter, rootlets/cauda equina, a measured dural wall or closed CSF volume. Continuous spline/surface nonintersection and biological boundary accuracy remain unestablished. No current-patient diagnosis, MRI-to-CT registration or complete named reporting structure is inferred from source geometry/presence. These unknown outcomes remain unknown in the contract.

No existing data/evidence ledger was edited by this reviewer, and no commit, deployment, rollback or approval escalation was performed. The owned Playwright browsers closed after capture and the isolated server on port 8903 was stopped; root servers were untouched.

## Applied presentation reconciliation

Root applied the exact independently reviewed contract with `tools/anatomy_sources/apply_native_source_presentation_review.py`. The applied receipt binds 20 unchanged source assets, 41 current dependency entries and preserved-field fingerprints. All 40 historical issues remain recorded. Only additive Liu coordinate metadata and the explicitly qualified cohort unknown were added. Anatomical review remains pending, fine-structure coverage remains empty, and clinical/fine approval remains false. The current MSK queue audit is preserved separately in `current-msk-audit.json`; previous audit snapshots remain historical evidence.

## Fixed source-review CLI paths

The acquisition and verification CLI uses the ignored cache `.research/native-source-presentation-20261011/` in this checkout. `--acquire-verse` is a boolean switch that places only the pinned original VerSe case members in `verse-master/`. Place the previously retained T1–T12/L1–L5 candidate NPZ files in `verse-candidates/`; `--verify-verse` compares those fixed directories and verifies every recorded source/candidate hash before using its arrays. `--write-verse-proof` retains its explicit proof-write switch.

```sh
python tools/anatomy_sources/reconcile_native_source_presentation.py --acquire-verse
python tools/anatomy_sources/reconcile_native_source_presentation.py --verify-verse
```

`--make-proposed-contract` reads the fixed `liu-native-coordinate-proof.json` and `reader-presentation-proof.json` in this review directory. It checks their native oracles, current served hashes and source-preservation scope before writing the proposed contract. The CLI accepts no source, candidate or proof path arguments. Helpers retain path parameters for direct local fixture tests.

GitHub CodeQL found 11 `py/path-injection` paths from the former caller-selected CLI paths to filesystem access. Removing those CLI path inputs bounds each acquisition/read/write location without suppressing the query. Focused regression tests reject every removed path argument before source/proof access and check the fixed native-cache and portable-proof routing. This CLI correction changes no runtime/source files, approval ledger or existing portable proof bytes; the seven contract-bound evidence hashes remain unchanged.
