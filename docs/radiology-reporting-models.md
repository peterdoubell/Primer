# Radiology reporting anatomy companions

Every one of the 96 radiology modules has a local, interactive 3D landmark companion. They use 35 shared anatomical/acquisition families with a module-specific initial focus and reporting prompt. These are original schematic meshes and curves, not patient scans, photorealistic anatomy, diagnostic simulators, or 96 independently segmented specimens.

The mapping is in `data/radiology/reporting-models.json`. Geometry and the browser adapter are in `web/radiology-reference-models.js`. Each model registers a separate `radiology-reference:<node-id>` scene, preserving the three existing radiology lesson scenes. `PrimerRadiologyReferenceModels.render(reference.spatial_model)` delegates to the existing accessible SVG 3D renderer.

## Anatomy families

Acquisition planes; procedural access; thorax; cardiac chambers; coronary arteries; aorta; brain; spine; sella; neck spaces/thyroid; orbit; paranasal sinuses; temporal bone; swallowing; trigeminal pathway; liver segments; pancreas/biliary tree; bowel; abdominal compartments; renal/adrenal; rectum/pelvic floor; prostate zones; bladder; female pelvis; scrotum; breast; knee; shoulder; hip; ankle; hand; elbow; long bone; infant skull sutures; whole-body nuclear localisation.

## Interaction and orientation

Each scene supports selection of a reporting landmark, axial/coronal/sagittal guide planes, guide-plane position, faded surrounding anatomy, and selected/all/hidden labels. The shared renderer provides mouse/touch dragging, arrow-key rotation, keyboard zoom, buttons and separate view/model reset controls. All geometry is calculated locally; these models do not need external image hosts or WebGL.

The world convention is +X patient left, +Y superior, +Z anterior. A freely rotated perspective is not the usual radiological image display. A plane is a positional guide; it does not generate a diagnostic cross-sectional image or hide everything on one side. Distances are schematic units without clinical calibration. Colours identify structures and selection, never pathology or tracer uptake.

Coronary geometry uses usual origins and right dominance. The prostate PZ is a posterolateral shell, TZ surrounds the urethral axis, CZ is posterior at the base, and anterior fibromuscular stroma is anterior. Liver segments retain left/right, superior/inferior and anterior/posterior relationships, with the caudate posterior. Each scene carries more specific limitations in its rendered note.

## Anatomy references checked

The models are original illustrations based on anatomical relationships, not traced copies of source figures. Relevant authored references checked during the update on 2026-09-23:

- [Coronary anatomy and anomalies](https://radiologyassistant.nl/cardiovascular/anatomy/coronary-anatomy-and-anomalies)
- [Prostate anatomy](https://radiologyassistant.nl/abdomen/prostate/prostate-cancer-pi-rads-v2-1-1)
- [Liver segmental anatomy](https://radiologyassistant.nl/abdomen/liver/segmental-anatomy)
- [Lung segments and bronchi](https://radiologyassistant.nl/chest/lung-anatomy/lung-segments)
- [Shoulder anatomy and variants on MRI](https://radiologyassistant.nl/musculoskeletal/shoulder/mri-anatomy)
- [Neonatal brain ultrasound](https://radiologyassistant.nl/pediatrics/spine/neonatal-brain-us)

These model notes deliberately avoid diagnosis, staging, CAD-RADS/PI-RADS/VI-RADS assignment, dose computation, therapy eligibility, procedural safety or patient-specific measurements.

## Verification

Run `node tools/check_radiology_reference_models.js`. This independently validates all 96 bindings, 35 distinct family geometries, 480 meaningful controls and 2,701 deterministic builds (including parameter extremes, combined plane extremes, invalid numeric input, label hiding and malformed wrapper input). The maximum scene budget is 1,350 primitives. Explicit assertions protect the prostate and Couinaud spatial relationships described above. Browser interaction and visual verification are separate from these geometry assertions.

All 35 family views were rendered in the browser and visually reviewed. The integrated prostate and CCTA reporting routes were checked on desktop and at a 390-pixel mobile width. Landmark and plane selection, context fading, camera buttons, keyboard rotation and reset behaved correctly; the checked mobile views had no horizontal page overflow and the browser reported no JavaScript errors. Screenshots are working verification artefacts under `/tmp/primer-radiology-family-models` and `/tmp/primer-radiology-live-*-viewport.png`, not application assets.
