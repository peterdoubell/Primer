# Stored 3D models bound to the structures their source labels name (2026-11-18)

## The decision

The radiology evidence ledger holds 148 stored 3D models. Until this pass, 142 of them had no binding:
the caption passes could not bind them, because a model has no caption. On 2026-11-18 the project owner
asked for the 3D models to be bound. This pass reviews every one of the 142 against the requirements of
its investigations.

A model shows what its source label says it shows. The label is an HRA ontology label, a BodyParts3D
concept name, a TotalSegmentator, NasalSeg or HVSMR-2.0 class, or an OpenEar, WT9FC or prostate-biopsy
structure name. The ledger record's name carries it.

## What was bound

108 partial bindings on 69 models, covering 94 requirements. All are structure bindings. Bound structures
and parts go from 993 to 1,062 of 57,985. Investigations with none go from 47 to 45: thyroid ultrasound
and prostate MRI get their first bindings. Nothing is anatomically approved, and no radiologist has
reviewed these bindings.

| Investigation | Models | Bindings | Bound requirements |
| --- | --- | --- | --- |
| `ra.mri-endometrial-cancer` | 30 | 31 | 60 → 78 |
| `ra.mri-endometriosis` | 18 | 18 | 57 → 69 |
| `ra.mri-cervical-cancer` | 13 | 13 | 53 → 60 |
| `ra.ct-temporal-bone` | 6 | 12 | 22 → 34 |
| `ra.mri-sella` | 10 | 10 | 26 → 30 |
| `ra.swallowing` | 4 | 8 | 5 → 7 |
| `ra.vascular-anomalies` | 4 | 5 | 31 → 36 |
| `ra.ultrasound-thyroid` | 3 | 3 | 0 → 3 |
| `ra.mri-sinuses` | 3 | 3 | 45 → 46 |
| `ra.carotid-obstruction` | 2 | 2 | 11 → 13 |
| `ra.esophagus` | 1 | 2 | 18 → 20 |
| `ra.mri-prostate` | 1 | 1 | 0 → 1 |

Some models bind requirements that figures already cover (the optic chiasm, the pituitary gland, the
maxillary sinuses), so bound requirements grow by less than the number of bindings.

| Source | Models bound | Bindings |
| --- | --- | --- |
| HRA female pelvis v1.10 | 35 of 54 | 62 |
| OpenEar ZETA temporal bone | 6 of 13 | 12 |
| BodyParts3D 4.3 (sella, carotid) | 11 of 15 | 11 |
| WT9FC tongue muscles | 4 of 4 | 8 |
| TotalSegmentator v3 (neck, thorax) | 5 of 35 | 6 |
| HVSMR-2.0 blood pools | 4 of 8 | 5 |
| NasalSeg | 3 of 5 | 3 |
| Prostate biopsy case 0001 | 1 of 2 | 1 |
| I-SPY1, FedBCa, larynx phonation | 0 of 6 | 0 |

## How a pair was accepted

1. The model's own label names the structure the requirement names, or one of the structures that a
   combined requirement names ("left atrium and venous ostia"). The label is stored verbatim and quoted
   in the coverage basis.
2. The requirement is in an investigation of the model.
3. The fidelity checker finds no conflict for any investigation sharing the requirement.
4. A sided requirement needs a side that the label or the record states and that agrees with where the
   mesh lies. Otherwise the mesh must lie on both sides of the midline, or, for a specimen whose side
   the source does not record, the two sides must be mirror images.

A label that names a whole is never bound to a requirement that names its parts. The TotalSegmentator
aorta is not bound to "aortic arch and descending aorta", and the OpenEar malleus is not bound to its
head, neck or manubrium. A part is never bound to its whole.

### How the label names the requirement

| Evidence | Bindings |
| --- | --- |
| The label and the requirement share the words for the structure (`term`) | 87 |
| The label uses another name, or its source's abbreviation | 13 |
| The label names something that is by definition a kind of what the requirement names | 8 |

These 14 pairs are the only places where the label's word differs from the requirement's. Removing a
pair from `review.json` makes the tool refuse its bindings.

| Label says | Requirement names | Why |
| --- | --- | --- |
| Carotis Interna | internal carotid | Latin name of the internal carotid artery |
| nasal pharynx | nasopharynx | another name |
| RV, LA, RA, SVC | right ventricular, left atrium, right atrium, superior vena cava | the HVSMR-2.0 class list abbreviates the chambers and veins this way |
| ovarian ligament | ovarian uterine attachment | the ligament attaches the ovary to the uterus |
| anterior / posterior wall of uterus | anterior / posterior uterine body | the walls are those parts of the uterine body |
| prostate outline | gland outline | the gland of the prostate investigation is the prostate |
| transverse / vertical, superior longitudinal, inferior longitudinal | intrinsic (tongue components) | intrinsic muscles of the tongue |
| genioglossus | extrinsic (tongue components) | an extrinsic muscle of the tongue |

## Side handling

| Side of the requirement | Bindings |
| --- | --- |
| Not sided | 35 |
| The label states the side, and the mesh lies on that side | 48 |
| The label states no side; the mesh lies on both sides of the midline | 12 |
| Neither label nor record states a side; mirror-image assumption | 12 |
| The model record states the side | 1 |

Where a label states a side, the tool decodes the stored mesh and checks where it lies. It uses the
axes each source declares (`frames` in `review.json`) and a midline taken from the same source: the
vagina, cervix and uterine body for HRA, the pituitary for BodyParts3D, the trachea or the thoracic
vertebrae for TotalSegmentator, the nasopharynx for NasalSeg. Every bound left mesh lies on the body's
left, and every bound right mesh on the body's right. HVSMR-2.0 has no midline structure. Its SVC label
states both sides (the source case has a bilateral SVC), and the mesh has two separate channels 41 mm
apart from left to right.

Three kinds of model rest on a mesh that crosses the midline: the WT9FC tongue muscles, the
TotalSegmentator pulmonary veins and the HRA broad ligament. Each has at least 15% of its vertices on
each side, so it is bound to both sides.

Only the OpenEar ZETA specimen rests on the mirror-image assumption. The source does not record which ear
it is, and its axes are not registered to a patient.

## What the meshes showed about the source

- **The HRA round ligament labels are swapped.** The mesh labelled right round ligament lies on the
  body's left, and the left one on the right. Every other sided mesh of the source (30, including both
  ilia, ovaries, tubes and ureters) lies on its labelled side. Neither round ligament is bound. The
  requirements name only segments of the ligament in any case.
- **The HRA "abdominal ostium" lies at the uterine cornua**, with the same left-right extent as the
  cornua mesh, not at the fimbriated end of a tube. It is not bound.
- **The HRA bladder dome and bladder base share one source label**, "fundus of urinary bladder". Neither
  is bound.

## What was not bound

All 73 other models are listed in `review.json` under `not_bound`, each with its reason:

- 26: no requirement of the model's investigations names the structure. Examples are the thoracic
  vertebrae, the left ventricle, the mesovarium and the internal carotid artery in the sella
  investigation.
- 18: the label names a whole and the requirements name its parts. Examples are the aorta, the
  oesophagus and the trachea of the thorax case, the ossicles, the thyroid gland, and the internal and
  common carotid trunks.
- 14: the requirement names an interface, a tissue or a class, not the labelled structure. Examples are
  the lung lobes and the heart (the requirements name their interfaces with the oesophagus), the
  laryngeal air–tissue surface, the compact and trabecular bone of the ilia, and the sacrum and coccyx.
- 9: the label or the position does not support a binding: the swapped round ligaments, the misplaced
  ostium, the unlabelled cornua and cervicovaginal junction, the two bladder meshes, the uterovesical
  pouch, and the OpenEar "Sinus Dura".
- 6: tumour and target models (I-SPY1, the four FedBCa cases and the prostate biopsy target). Their
  requirements are finding requirements, and their records have no depicted state for the checker to
  read. A suspicious biopsy target is also not an established lesion.

## Not in this pass

- The MSK ledger (`data/radiology/msk-asset-evidence.json`) holds 636 models, of which 12 are bound. It
  is a separate, larger pass. (It was reviewed later on 2026-11-18: see `docs/msk-model-bindings-20261118`.)
- No model record, mesh, source context or reader file changed. The app does not read ledger bindings.

## Limits of this pass

- This is a check of source labels and mesh positions, not a radiologist review. The meshes were not
  compared with patient images.
- Bindings are to the requirement, not to its individual parts. Coverage is always partial.

## Files

- `review.json`: accepted rows (label, evidence, side), the side frames, the pairs in other words with
  reasons, the source findings, and every model that was not bound, with its reason.
- `inverse.json`: exact byte edits and hashes for the evidence file.
- Tool: `tools/anatomy_sources/bind_models.py`. It refuses a row whose label is not in the model record,
  that does not name the requirement as recorded, whose side the label or record does not state, whose
  mesh lies on the other side, or that the checker refuses.
- Tests: `tests/test_model_bindings.py`.
