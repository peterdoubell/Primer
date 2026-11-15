# Hip arthroplasty: lateral Gruen scope omission

Source and repository review, 2026-09-30. This is a proposed scope correction, not an anatomical or clinical approval. The full 22-investigation MSK goal is unchanged.

The effective arthroplasty walkthrough requires femoral Gruen zones 1–7 on the AP view and 8–14 on the lateral view. The anatomical inventory includes only zones 1–7. The seven lateral zones therefore cannot appear as missing targets in the current fidelity audit.

## Current field evidence

- [The authored walkthrough](/Users/peter/Documents/ChatGPT/Primer/data/radiology/reporting-steps/musculoskeletal.json:1293), `investigations["ra.hip-arthroplasty"].steps[1].look`, explicitly includes AP 1–7 and lateral 8–14. The effective `detail(Curriculum(), item)["radiology_reference"]["walkthrough"]["steps"][1]` returned the same wording during this audit. It edits `INTERFACES`, uses measurement `Lucency map`, and offers named-zone finding phrases.
- [The effective reporting override](/Users/peter/Documents/ChatGPT/Primer/data/radiology/investigation-overrides.json:1854), `ra.hip-arthroplasty.reporting.template_sections[1]`, and the matching report-template `INTERFACES` section at line 1897 both require a femoral Gruen zone, maximal lucency and progression. The protocol requires AP pelvis and lateral hip including the whole prosthesis.
- [The anatomy inventory](/Users/peter/Documents/ChatGPT/Primer/data/radiology/msk-structure-requirements.json:12647), structure `hip_arthroplasty.femoral_host_bone`, lists `gruen_zone_1` through `gruen_zone_7`, plus greater trochanter, lesser trochanter and stem-tip adjacent diaphysis. No zone 8–14 identifier occurs anywhere in that file. The parent retains `laterality=examined_side`, `modality_scope=["Radiography"]`, `condition="Within the acquired anatomical coverage."`, and report references to checklist 1, `Interfaces`, and checklist 3, `Bone And Alignment`.
- [Snapshot validation](/Users/peter/Documents/ChatGPT/Primer/tools/check_msk_fidelity.py:40) checks the effective checklist and worksheet bodies, but does not snapshot walkthrough `look` or `findings`. Its successful checklist reconciliation therefore does not prove that every explicit walkthrough target is inventoried.

## Primary source confirmation

Tang and colleagues' original cadaveric study defines fourteen femoral-stem zones on AP and lateral views. Figure 6 directly shows 8, 9, 10 on one side of the lateral stem from proximal to distal, 11 at the distal tip, and 12, 13, 14 ascending the other side. Its experiment excludes zones 4 and 11 from its radiolucent-line statistics; that experimental exclusion does not remove either zone from the module's clinical reporting scope. [Tang et al., QIMS 2020, image assessment and Figure 6](https://qims.amegroups.org/article/view/47101/html#figure6).

Jørgensen and colleagues' original clinical RSA study describes AP and cross-table lateral radiographs, fourteen modified Gruen zones and numbering from anterior to posterior on the lateral projection. Figure 3's caption also specifies that the periprosthetic bone is divided from stem tip to shoulder, with proximal zones ending at the cement mantle. These are projection and implant reference zones, not independent native-bone substructures or universal three-dimensional boundaries. [Jørgensen et al., Bone & Joint Open 2023, radiological evaluation and Figure 3](https://pmc.ncbi.nlm.nih.gov/articles/PMC10322230/).

Combined source interpretation for an explanatory map: 8 anterior proximal, 9 anterior middle, 10 anterior distal, 11 distal to the stem tip, 12 posterior distal, 13 posterior middle, 14 posterior proximal. Exact delineation must identify the source stem, projection and zoning convention. No fixed millimetre extents or diagnostic finding is inferred here.

The Tang figure was viewed directly in the publisher's browser image viewer; no source figure was added to the product. Its article is CC BY-NC-ND 4.0 and is not a commercially cleared asset proposal.

## Existing gallery and models

The effective `key_images` list contains exactly three images: `ra-hip-arthroplasty-detail-1` (cup inclination), `-detail-2` (periprosthetic zone map), and `-detail-3` (liner wear and osteolysis). `structure_atlas` and `source_anatomy_references` are empty for this investigation.

The existing `-detail-2` source image was inspected directly at its original 370×248 dimensions. It shows acetabular I–III and femoral 1–7 on the AP example; it contains no lateral 8–14 map. Its broad caption, “Periprosthetic zone map,” does not establish lateral coverage. [Current image declaration](/Users/peter/Documents/ChatGPT/Primer/data/radiology/investigation-overrides.json:1943) and [published image](https://radiologyassistant.nl/assets/hip-arthroplasty/a5097976d7f36b_Gruen-zones.jpg).

The effective spatial model uses the native `hip` family. BodyParts3D's seven hip entries include native right hip bone, sacrum, femur and muscles; the detailed Z-Anatomy hip inventory has 61 native anatomy/material-surface entries. Neither declares an implanted stem, arthroplasty interface geometry or Gruen zone binding. The ledger contains no explicit `hip_arthroplasty.*` structure binding. Native femur geometry and a `shaft` landmark do not prove an implant-dependent zone.

## Additive correction

Append `hip_arthroplasty.femoral_host_bone.gruen_zone_8` through `.gruen_zone_14` as seven separately reportable parts of the existing parent. Preserve every existing part, report reference, laterality and coverage condition; preserve all three representation types. Distinguish AP and lateral projection in the names or explicit scope metadata. A missing or limited lateral acquisition remains an examination limitation, not permission to erase these targets.

This adds 21 representation obligations: seven parts × image, schematic and model. No existing asset should receive a new complete binding on the strength of this review. The seven zones need acquired-projection exemplars and a source-traceable implant/interface reference before their fidelity can be assessed. A regression check should require the lateral IDs whenever the effective walkthrough explicitly requires lateral 8–14.

Other explicit targets warrant a separate reconciliation: the hip FAI walkthrough names anterior inferior iliac spine/subspine morphology at step 4, while its requirement list has no AIIS target; the ankle MRI walkthrough names peroneus quartus, accessory soleus and flexor digitorum accessorius longus at step 4, without named conditional variant targets. These observations are local scope discrepancies, not new clinical assertions or asset approvals.

Machine-readable additions and the inspected file hashes are recorded in `msk-hip-arthroplasty-gruen-scope-proposal-2026-09-30.json`.

## Applied local correction

All seven missing lateral zones were added without removing existing parts, expanding the total representation obligations from 5,229 to 5,250. Existing zones 1–7 now have explicit AP projection context; zones 8–14 require lateral context. The audit rejects an AP or unspecified projection as compatible evidence for a lateral zone. This compatibility check does not establish completeness or clinical accuracy.

The arthroplasty model retains native hip anatomy for orientation and now states explicitly that no cup, liner, stem, fixation hardware or Gruen-zone geometry is supplied. The reporting-step model no longer inherits an FAI/labrum aim. Existing report fields and the AP/lateral instructions remain intact. Shared pre-existing source bindings were checked unchanged before their container-file fingerprints were refreshed. No implant geometry, image acquisition or approvals were invented.
