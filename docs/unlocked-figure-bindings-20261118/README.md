# Figures unlocked by the context-code repair, bound (2026-11-18)

## The decision

The context-code repair (`docs/source-context-code-repairs-20261118`) made the records of 250 stored
figures and models readable by the fidelity checker. Before it, the checker refused every binding of
them, so none was bound. On 2026-11-18 the project owner asked for the unlocked figures to be bound.
This pass reviews every caption match on them, for structures and findings alike, under the rules of
the earlier passes.

## What was bound

515 partial bindings on 138 figures, covering 283 requirements: 293 structure bindings and 222 finding
bindings. Bound structures and parts go from 739 to 993 of 57,985. Investigations with none go from 51
to 47: oesophagus, epilepsy MRI, swallowing and cervical lymph nodes now have bindings. No asset is
anatomically approved and no radiologist has reviewed these bindings.

| Investigation | Figures | Bindings | Bound requirements |
| --- | --- | --- | --- |
| `ra.mri-endometrial-cancer` | 33 | 145 | 2 → 60 |
| `ra.mri-cervical-cancer` | 27 | 120 | 2 → 53 |
| `ra.mri-sinuses` | 17 | 61 | 13 → 45 |
| `ra.ct-cardiovascular-pearls` | 21 | 55 | 3 → 29 |
| `ra.mri-endometriosis` | 5 | 41 | 30 → 57 |
| `ra.ct-mri-eye` | 13 | 36 | 4 → 26 |
| `ra.esophagus` | 12 | 26 | 0 → 18 |
| `ra.mri-epilepsy` | 5 | 13 | 0 → 11 |
| `ra.mri-sella` | 2 | 9 | 25 → 26 |
| `ra.swallowing` | 1 | 5 | 0 → 5 |
| `ra.cervical-lymph-nodes` | 1 | 2 | 0 → 2 |
| `ra.head-neck-malignancy` | 1 | 2 | 2 → 3 |

| How the quoted sentence names the requirement | Bindings |
| --- | --- |
| It uses the requirement's own word | 464 |
| It names something that is by definition a kind of what the requirement names | 51 |

| Side of the requirement | Bindings |
| --- | --- |
| Not sided | 300 |
| Sided; the caption states this side or both | 133 |
| Sided; no side stated; bound on the mirror-image assumption | 78 |
| Sided; the figure record itself states the side | 4 |

## How a pair was accepted

1. A sentence of the figure's published caption, or of its stored source note, names the structure or
   finding. The sentence is stored verbatim in `review.json` and quoted in the coverage basis.
2. Where the figure has selected panels, the sentence is about a selected panel. Panels the record
   leaves out (ultrasound, CT, PET or photographs in an MRI figure) are never credited.
3. The fidelity checker finds no modality, state or side conflict for any investigation sharing the
   requirement.
4. The figure was looked at on a contact sheet and is consistent with the sentence.

Names of the requirements of each figure's investigations were matched against the stored
descriptions of the 181 repaired figures that have one. 931 candidate pairs on 156 figures were read,
and 876 of them passed the checker. 283 bindings come from those matches. The other 232 were added
where the same caption names a requirement in other words: a staging figure's "cervical tumour" for
the primary tumour, its "lower uterine segment" for the isthmus.

### Labels

Some figures mark organs with letters that their legend spells out ("B, bladder", "R, rectum",
"UT, uterus", "C, cervix"). Where a selected panel carries the letter, the row quotes the legend entry
and records the letter, and the coverage basis says that the selected panels carry it. 10 bindings
rest on a label. A letter that appears only on panels that are not selected is not used.

### Kind-of pairs

These 28 pairs are the only places where the caption's word differs from the requirement's. Each is
true by definition. Removing a pair from `review.json` makes the tool refuse its bindings.

| Caption says | Requirement names | Why |
| --- | --- | --- |
| carcinoma, adenocarcinoma, carcinosarcoma | tumour | each is a malignant tumour |
| retinoblastoma, choroidal metastasis | intraocular mass | a mass inside the globe |
| myxoma | mass | a myxoma is a mass |
| leiomyoma (oesophagus) | intramural mass | a smooth-muscle mass within the wall |
| haemangioma | vascular lesion | a haemangioma is a vascular lesion |
| bone metastases | skeletal lesion | a metastasis in bone is a skeletal lesion |
| acetabulum | skeletal site | the acetabulum is part of the skeleton |
| coloboma, persistent hyperplastic primary vitreous | congenital | congenital anomalies of the eye |
| vaginal septum, septate uterus, didelphys uterus | variant | developmental variants |
| remaining cervix after previous supravaginal hysterectomy | postoperative anatomical | the cervix left after a hysterectomy |
| hydronephrosis | renal collecting system; renal pelvis and calyces | dilatation of the collecting system |
| hydroureter | ureteric | a dilated ureter |
| sigmoid colon, rectosigmoid | bowel segment | segments of the large bowel |
| sinus of Valsalva aneurysm | aortic wall | an aneurysm of a sinus of the aortic root wall |
| haemopericardium | effusion | a pericardial effusion of blood |
| infarct | injury | ischaemic injury |
| myositis | muscle | inflammation of muscle |
| gas | air | gas outside the lumen |
| main pulmonary artery | pulmonary trunk | another name |
| sphenoethmoidal cell | Onodi cell | another name |

## Side handling

Unchanged from the earlier passes. A stated side binds that side; "both" or "bilateral" binds both.
Where neither the record nor the caption states a side, the figure is bound to each side only where
the two sides are mirror images. In this pass that covers the sinuses, the orbits, the temporal lobes
and hippocampi, the pharyngeal lateral walls, the cervical oesophagus, the parametria, the pelvic
sidewalls and the obturator internus muscles. Where the side is stated in a different sentence of the
same caption, that sentence is stored as `side_quote`.

## Changed after looking at the figures

- **Withdrawn: orbit MRI figure 13 (dacryocystocele, PMC6095049).** The caption states a left lesion,
  but the cyst lies on the patient's right in the article's own display convention (figure 14 is
  marked R on the image left). Neither side is bound.
- **Withdrawn: the oesophageal pouch above the diaphragm (figure 14, PMC5438315).** The caption states
  no side, and the lower thoracic oesophagus is not a mirror-image region: the aorta lies on its left.
- **Added: nine structures that selected panels label.** Bladder, rectum, uterus, cervix and both
  parametria on cervical cancer and endometriosis figures whose legend spells out the letters.
- **Narrowed:** the panels of one endometrial cancer figure, to those that show the ovary and the node.

## What was not bound

- Catch-all requirements ("every other", "each other"), measurements, comparisons and acquisition
  descriptors.
- A structure named only by an abbreviation the caption does not spell out. "USL" is never spelled
  out, so only the sentence that says "uterosacral" is used, and the bilateral cases that say "USLs"
  are not bound.
- 593 checker-clean candidates on 133 figures were rejected, each with a reason in `review.json`.
  Most are word matches inside other words ("intermediate" matched "internal", "endometrial carcinoma"
  matched the endometrium and endometriosis, "para-aortic" matched "parametrial"), structures named
  only for a panel that is not selected, and negations ("no residual", "cannot be identified",
  "without myometrial invasion").
- 55 caption matches still fail the checker: 28 are in a modality outside the requirement's scope
  (for example CT and PET-CT figures matched to MRI investigations), 19 are on context-only figures
  that the repair left refused, 5 are on the other side from the one the record states and 3 are
  normal figures matched to a finding.
- The 69 repaired 3D models are reference-only records without a caption. Binding them needs a
  separate review of each model's source label. (The models were reviewed and bound later on
  2026-11-18: see `docs/model-bindings-20261118`.)

## Limits of this pass

- Only figures that the context-code repair unlocked were considered. No new figure was fetched.
- The figures were compared with their captions at reduced size on contact sheets.
- Bindings are to the requirement, not to its individual parts. Coverage is always partial.

## Files

- `review.json`: accepted pairs (quote, panels, side, evidence, label), the kind-of pairs with
  reasons, rejected candidates and what was not bound.
- `inverse.json`: exact byte edits and hashes for the evidence file.
- Tool: `tools/anatomy_sources/bind_unlocked_figures.py`. It refuses a row whose quote is not in the
  stored description, whose panels are not selected, whose evidence or side does not fit, or that the
  checker refuses.
- Tests: `tests/test_unlocked_figure_bindings.py`.
