# MSK investigation scope corrections

Reviewed 26 September 2026. These changes resolve the thoracolumbar reporting-scope defect and the ankle radiographic soft-tissue overclaim recorded in the earlier [structure audit](msk-reporting-structure-audit.md). They do not certify the anatomical assets or complete the clinical/commercial fidelity goal.

| Investigation | Corrected report | Anatomy retained |
|---|---|---|
| `ra.thoracolumbar-fractures` | A dedicated CT/MRI trauma guide replaces the inherited degeneration report. | All 17 structures and 58 required subparts. |
| `ra.ankle-fractures` | Radiographic findings and injury clues are separated from direct findings on an acquired supplemental examination. | All 27 structures and 110 required subparts, including conditional foot and soft-tissue targets. |

The changes are confined to these two keys in [investigation-overrides.json](../data/radiology/investigation-overrides.json), their corresponding [requirements entries](../data/radiology/msk-structure-requirements.json), and focused regression tests. Existing ankle source images and all other investigation keys were preserved.

## Thoracolumbar trauma

The effective report now separates numbering/alignment, vertebral morphology, the posterior tension band, discs and longitudinal ligaments, canal/epidural/neural effects, associated injury, and supplied clinical classification inputs. The editor receives these same fields through the effective catalogue, rather than retaining a generic lumbar-degeneration template.

Posterior-wall and endplate involvement, motion-segment displacement, and tension-band injury are documented independently. A vertical laminar fracture is not treated as sufficient proof of posterior tension-band failure. This follows the [AO Surgery Reference classification](https://surgeryreference.aofoundation.org/spine/trauma/thoracolumbar/further-reading/rationale-for-fracture-classification-a0-a1-a2-a3-a4-b1-b2-b3-c) and the source’s [Radiology Assistant AO review](https://radiologyassistant.nl/musculoskeletal/spine/ao-classification).

The posterior ligamentous complex remains decomposed into supraspinous/interspinous ligaments, ligamenta flava and facet capsules. CT signs, direct MRI findings and indeterminate oedema are distinguished. Clinical neurological status is a separately supplied input: the report cannot infer an intact examination or invent a complete TLICS total from imaging alone. No numerical treatment threshold or automatic treatment recommendation was added. [Source: Radiology Assistant TLICS](https://radiologyassistant.nl/musculoskeletal/spine/tlics-classification-1).

Measurements retain height loss, angulation, retropulsion and displacement, with explicit planes and references. Canal diameter and area methods cannot be silently interchanged. MRI-not-acquired and incomplete-coverage states remain available for neural and ligamentous assessment.

Relevant fracture-age evidence, focal bone lesions, MRI marrow findings and concern for a pathological fracture also remain explicit. Removing the routine degeneration template did not remove these reportable observations.

## Ankle fracture radiography

The report begins with the radiographs actually acquired, their projection/quality and pre-/post-reduction status. It retains malleoli, mortise, syndesmosis, posterior fragment and articular extent. Clear-space or overlap measurements carry view and loading context; a normal value cannot establish intact ligaments. [Source: Ankle Fracture Mechanism and Radiography](https://radiologyassistant.nl/musculoskeletal/ankle/fracture-mechanism-and-radiography).

Weber and Lauge-Hansen labels remain conditional on the observed fracture pattern and do not replace its description or prove stability. Physeal injury remains a separate developmental consideration. Proximal-fibular and foot/hindfoot coverage must be recorded explicitly; an unexamined region is not declared normal. [Sources: Weber/Lauge-Hansen](https://radiologyassistant.nl/musculoskeletal/ankle/weber-and-lauge-hansen-classification), [Special Ankle Fractures](https://radiologyassistant.nl/musculoskeletal/ankle/special-fracture-cases), [AO malleolar fracture anatomy](https://surgeryreference.aofoundation.org/orthopedic-trauma/adult-trauma/malleoli/transsyndesmotic-posterior-lateral-simple-and-medial-fractures/definition).

The retained conditional foot targets have their own [foot/ankle case-discussion source](https://radiologyassistant.nl/musculoskeletal/wrist/foot-1), including tarsometatarsal and hindfoot relationships.

Swelling, avulsion fragments and malalignment are radiographic observations or injury clues. Direct tendon/ligament integrity and cartilage findings are recorded only with an appropriate supplemental examination actually reviewed. The report does not recommend routine MRI or ultrasound for every fracture and no longer asks the reader to grade tendon or ligament discontinuity from radiographs. The retained MRI anatomy is supported by the separate [MRI ankle source](https://radiologyassistant.nl/musculoskeletal/ankle/mri-examination).

Ankle already had an explicit `report_templates` override. That editor template was updated as well as the reporting guide, preventing the old generic technique text from shadowing the correction.

## Wrist scope audit — content retained

`ra.wrist-instability` and `ra.wrist-fractures` were checked against their effective guides, editor templates and anatomical requirements after normal MRI/MR arthrography references became available. **No radiograph-only claim of SL/LT ligament or TFCC fibre integrity was found, so neither override nor its requirements entry was changed.** The instability investigation remains Radiography; the fracture investigation retains its existing Multimodality catalogue value and radiographs/CT report title.

The instability report asks for Gilula arcs, joint intervals, true-lateral alignment, carpal axes and observed dynamic change. It already states that normal neutral views do not exclude dynamic instability and that acquired CT/MRI findings should be described separately. This is consistent with the [Radiology Assistant carpal-instability approach](https://radiologyassistant.nl/musculoskeletal/wrist/carpal-instability) and the distinction between alignment studies and direct soft-tissue assessment in the [original I-WRIST scapholunate imaging consensus](https://link.springer.com/article/10.1007/s00330-021-08073-8).

The fracture report describes morphology, displacement, osseous articular congruity, avulsion clues and swelling; it does not turn an ulnar-styloid fragment or DRUJ alignment into a direct TFCC integrity verdict. [Source: Radiology Assistant wrist fractures](https://radiologyassistant.nl/musculoskeletal/wrist/fractures). The separate [DRUJ/TFCC imaging consensus](https://pubmed.ncbi.nlm.nih.gov/37191922/) distinguishes radiographic/CT assessment of joint relationships from MRI-based soft-tissue assessment. Its primary-study abstract was reviewed for this bounded scope check.

Both editor templates retain generic technique wording for optional sequences or arthrography, but explicitly allow “not performed”; this was not treated as a demonstrated clinical overclaim. All current finding sections match their effective guides. The requirements continue to restrict direct SL/LT/TFCC evidence to MRI/MR arthrography and identify radiographic alignment/avulsion findings as indirect. Adding normal reference images is not grounds to change the investigation modality or imply a patient-specific normal result.

The unchanged wrist entries retain all 48 investigation-specific structures and 149 subparts. Their modality limits remain active; this audit does not validate the new figures or certify complete wrist anatomy.

## Traceability and regression checks

Both requirements entries contain the current checklist/template snapshots, source paths, checklist hashes and remapped structure references. Their previous report content is retained under `resolved_reporting_defects`. Persistent modality and coverage limits remain explicit; no structure or required subpart was deleted, and no asset was promoted to verified coverage.

[test_msk_scope_corrections.py](../tests/test_msk_scope_corrections.py) exercises the effective catalogue and editor templates, preserves the corrected spine/ankle minimum of 44 structures/168 subparts and the unchanged wrist minimum of 48 structures/149 subparts, verifies each source-report link, checks the clinical-input and modality limitations, and ensures the shared broader spine module remains independent. The wrist guards also require any future direct soft-tissue finding field to state an appropriate acquired modality and an unassessed state. Together with the investigation and fidelity suites, 40 tests passed.

Specialist review of the reporting content, complete anatomical representations, and the separate evidence for each image, schematic and model remain outstanding parts of the broader goal.
