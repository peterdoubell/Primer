# Reporting reference taxonomy — 23 September 2026

The reporting-reference index follows the current [Radiology Assistant medical navigation](https://radiologyassistant.nl/), checked on 23 September 2026 and rechecked against the live site on 25 September 2026, which added “Thoracic Aorta - How to Measure” as the CT thoracic aorta measurement reference. It contains **137 investigations or clinical references covering all 189 canonical source articles exactly once**. The 197 navigation links represented in the source catalogue include aliases; the index does not repeat the same canonical article merely because the source links to it from multiple sections.

`data/radiology/reference-investigations.json` is the index. `source-catalog.json` remains the authority for article IDs, URLs, source titles, headings and aliases. Investigation names may put the examination first (for example “MRI shoulder”); the original article names are retained in `source_titles`. This is an original examination index with attributed source coverage, not a claim that all article text has been reproduced locally.

## Organisation

| Radiology Assistant section | Investigations |
| --- | ---: |
| Abdomen | 41 |
| Breast | 6 |
| Cardiovascular | 11 |
| Chest | 11 |
| Head/Neck | 11 |
| Musculoskeletal | 22 |
| Neuroradiology | 17 |
| Pediatrics | 16 |
| More | 2 |

MRI and ultrasound shoulder are separate examinations. Ankle MRI is separate from fracture radiography. Diabetic foot, traumatic muscle injury, non-traumatic muscle disease, hamstring injury and stress fractures have separate entries. Hip arthroplasty and femoroacetabular impingement have distinct radiographic references. Rectal cancer, perianal fistula and dynamic rectal examination likewise remain separate.

Administrative, financial, application-promotion and media-authoring pages are excluded. The source’s medical “More” entries are retained for CT contrast protocols and RECIST. The two cardiovascular chest CT article revisions are grouped under Cardiovascular. The two foot/ankle case archives are grouped into a clinical case reference rather than presented as an invented procedure.

## Important source distinctions

- The source’s [Dynamic Rectal examination](https://radiologyassistant.nl/abdomen/rectum/dynamic-rectal-examination) describes **fluoroscopic barium defecography**. It must not inherit an MRI-only pelvic-floor protocol solely because it uses the existing `rad.5.pelvic-floor` content key.
- The source’s [Femoroacetabular impingement syndrome](https://radiologyassistant.nl/musculoskeletal/hip/femoroacetabular-impingement-syndrome) centres on AP pelvis and Dunn-view radiography. It has its own reference rather than sharing the hip arthroplasty report.
- The local source catalogue calls the [older foot/ankle case archive](https://radiologyassistant.nl/musculoskeletal/wrist/foot-1) “Foot and ankle cases (Wrist archive)”; the live source title is the literal `...`. The local clarified title is preserved as catalogue metadata, not used to create a wrist reporting investigation.
- A shared `module_id` is a backing-content relationship, not permission to display unrelated guide sections, images, classifications or templates. Investigation article IDs define the visible scope.

## Existing modules split into distinct investigations

These backing modules require investigation-specific content selection or overrides. Showing each module’s entire original combined report under every child investigation would reintroduce the broad-topic problem.

| Existing content key | Investigation IDs |
| --- | --- |
| `rad.3.acute-abdomen` | `ra.acute-abdomen`, `ra.transvaginal-nongynaecology`, `ra.ultrasound-acute-abdomen` |
| `rad.5.peritoneum` | `ra.abdominal-wall-hernias`, `ra.ct-peritoneum`, `ra.ct-peritoneal-carcinomatosis` |
| `rad.5.aorta` | `ra.aortic-aneurysm-rupture`, `ra.ct-acute-aortic-syndrome` |
| `rad.5.biliary` | `ra.ultrasound-bile-duct-stones`, `ra.ultrasound-gallbladder`, `ra.biliary-duct-pathology` |
| `rad.5.bowel-ischaemia` | `ra.ct-bowel-ischaemia`, `ra.ct-bowel-wall` |
| `rad.5.ibd` | `ra.mri-crohn`, `ra.ultrasound-ibd` |
| `rad.5.gi-tumours-foreign-bodies` | `ra.ct-small-bowel-tumours`, `ra.gi-foreign-bodies` |
| `rad.5.uterine-mr` | `ra.ultrasound-acute-gynaecology`, `ra.mri-endometriosis`, `ra.mri-cervical-cancer`, `ra.mri-endometrial-cancer`, `ra.mullerian-anomalies` |
| `rad.4.kidney` | `ra.renal-cysts-bosniak`, `ra.solid-renal-masses` |
| `rad.4.liver` | `ra.liver-masses`, `ra.liver-lirads` |
| `rad.5.pancreas-tumour` | `ra.ct-pancreatic-cancer`, `ra.pancreatic-cysts` |
| `rad.5.rectal-mr` | `ra.mri-rectal-cancer`, `ra.mri-perianal-fistula` |
| `rad.5.breast-mri` | `ra.ultrasound-breast`, `ra.breast-cancer-staging`, `ra.mri-breast` |
| `rad.5.breast-implants-male` | `ra.breast-implants`, `ra.male-breast` |
| `rad.5.cardiac-masses-devices` | `ra.cardiovascular-devices`, `ra.cardiac-masses`, `ra.ct-cardiovascular-pearls` |
| `rad.5.peripheral-vascular` | `ra.mra-peripheral-vessels`, `ra.carotid-obstruction` |
| `rad.5.chest-infection` | `ra.ct-covid`, `ra.tuberculosis` |
| `rad.4.hrct` | `ra.hrct-cystic-lung`, `ra.hrct-lung` |
| `rad.5.esophagus-swallowing` | `ra.esophagus`, `ra.swallowing` |
| `rad.5.mediastinum` | `ra.ct-mediastinum`, `ra.thymus` |
| `rad.5.deep-neck-spaces` | `ra.mri-neck-spaces`, `ra.head-neck-malignancy` |
| `rad.5.paeds-masses-neuro` | `ra.paediatric-neck-masses`, `ra.paediatric-cystic-abdominal-masses`, `ra.paediatric-solid-abdominal-masses`, `ra.paediatric-renal-tumours`, `ra.ultrasound-neonatal-brain` |
| `rad.5.ankle-foot` | `ra.ankle-fractures`, `ra.mri-ankle`, `ra.foot-ankle-cases` |
| `rad.5.bone-tumours` | `ra.bone-tumours`, `ra.cartilage-tumours` |
| `rad.5.marrow-muscle` | `ra.mri-diabetic-foot`, `ra.mri-muscle-injury`, `ra.mri-muscle-disease`, `ra.mri-hamstring`, `ra.stress-fractures` |
| `rad.5.paeds-hip-elbow` | `ra.paediatric-elbow-fractures`, `ra.ultrasound-ddh`, `ra.paediatric-hip` |
| `rad.5.hip` | `ra.hip-arthroplasty`, `ra.hip-fai` |
| `rad.5.shoulder` | `ra.mri-shoulder`, `ra.ultrasound-shoulder` |
| `rad.4.spine-imaging` | `ra.thoracolumbar-fractures`, `ra.cervical-spine-injury`, `ra.mri-lumbar-disc`, `ra.mri-myelopathy`, `ra.thoracolumbar-injury` |
| `rad.5.wrist-hand` | `ra.wrist-instability`, `ra.wrist-fractures` |
| `rad.5.intracranial-haemorrhage` | `ra.ct-traumatic-haemorrhage`, `ra.intracranial-haemorrhage` |
| `rad.5.venous-csf` | `ra.venous-sinus-thrombosis`, `ra.intracranial-hypotension` |
| `rad.5.paeds-abdomen` | `ra.neonatal-acute-abdomen`, `ra.necrotising-enterocolitis` |
| `rad.5.paeds-chest` | `ra.neonatal-chest-xray`, `ra.paediatric-mediastinum`, `ra.paediatric-chest-ct` |

## Existing modules with no Radiology Assistant foundation article

These existing curriculum content keys are outside this reporting-reference index; their learning content is not deleted by this taxonomy change.

- `rad.2.modalities`
- `rad.2.radiation-safety`
- `rad.3.ct-image`
- `rad.3.fracture-description`
- `rad.3.mri-sequences`
- `rad.4.head-trauma`
- `rad.4.structured-reporting`
- `rad.5.biopsy-safety`
- `rad.5.msk-mri`
- `rad.5.nuclear-general`
- `rad.5.pet-ct`
- `rad.5.theranostics`
- `rad.5.ultrasound-physics`

## Integrity checks

- All 189 canonical article IDs occur once, with no omission or duplication.
- All 137 investigation IDs are unique.
- Every investigation references at least one source article with its declared backing `module_id`.
- Section and topic values use the source navigation vocabulary; no Genitourinary or general physics category is added.
- All source titles are retained verbatim from the existing catalogue, including intentional legacy-title clarification noted above.
