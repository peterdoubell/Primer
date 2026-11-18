# Figures of findings bound to finding requirements (2026-11-18)

## The decision

The earlier passes bound stored figures to structures and left findings and diagnoses alone. On
2026-11-18 the project owner decided that figures of findings are bound to finding requirements.
This pass applies that to the figures already stored.

## What was bound

466 partial bindings on 246 stored figures, covering 237 finding requirements. Bound structures
and parts go from 503 to 739 of 57,985; investigations with none go from 67 to 51. No asset is
anatomically approved and no radiologist has reviewed these.

| How the quoted sentence names the finding | Bindings |
| --- | --- |
| It uses the requirement's own word | 362 |
| It uses a term the requirement lists among its required parts | 71 |
| It names a kind of what the requirement names, or spells out its abbreviation | 33 |

| Side of the requirement | Bindings |
| --- | --- |
| Not sided | 281 |
| Sided; the caption states this side or both | 118 |
| Sided; no side stated; bound on the mirror-image assumption | 51 |
| Sided; the figure record itself states the side | 16 |

## How a pair was accepted

1. A sentence of the figure's published caption, or of its stored source note, names the finding.
   The sentence is stored verbatim in `review.json` and quoted in the coverage basis.
2. Where the figure has selected panels, the sentence is about a selected panel.
3. The fidelity checker finds no modality, state or side conflict for any investigation sharing
   the requirement.
4. The figure was looked at on a contact sheet and is consistent with the sentence.

Spelling variants and word forms count as the same word (haematoma and hematoma, thrombus and
thrombosed), and so do a few exact equivalents (stone and calculus, node and lymphadenopathy).

### Kind-of pairs

These 20 pairs are the only places where the caption's word differs from the requirement's. Each
is true by definition. Removing a pair from `review.json` makes the tool refuse its bindings.

| Caption says | Requirement names | Why |
| --- | --- | --- |
| contusion, laceration | injury | each is an injury |
| arterial bleeding, venous injury | vascular lesion | an injured or bleeding vessel is a vascular lesion |
| ischaemic colitis | injury | ischaemic injury of the colon |
| mass, masses, polyp, haemangioma | lesion | each is a lesion |
| tumor | mass | a tumour is a mass |
| Crohn disease | inflammatory bowel | an inflammatory bowel disease |
| lupus | immune | an autoimmune disease |
| myocarditis | inflammatory | inflammation of the myocardium |
| Anderson–Fabry disease | storage | a lysosomal storage disease |
| Glioblastoma multiforme | high grade glioma | a grade 4 glioma |
| fistulating | penetrating tract | a fistula is a penetrating tract |
| arteriovenous fistula | shunt | an arteriovenous fistula is a shunt |
| Penetrating atherosclerotic ulcer, Dural arteriovenous fistula, Arteriovenous malformation | PAU, DAVF, AVM | the abbreviation spelled out |

## Side handling

Unchanged from the second pass. A stated side binds that side; "both" or "bilateral" binds both.
Where the caption states no side, the figure is bound to each side only where the two sides are
mirror images (breast, temporal bone, neck, cranial sides, parametrium, ureter). The lungs and the
pulmonary arteries are not mirror images, so an unsided lung finding is not bound. Where the side
is stated in a different sentence of the same caption, that sentence is stored as `side_quote`.

## What was not bound

- Catch-all requirements ("every other", "unlisted"), measurements, comparisons and acquisition
  descriptors.
- Unsided lung and pulmonary artery findings, as above.
- Findings named only by an abbreviation the caption does not spell out, or only for a panel that
  is not selected.
- Figures that an existing rule keeps unbound: the reused acute abdomen references, the stroke
  perfusion records and the mixed appendix figure.
- 238 figures have rejected candidates, each with a reason in `review.json`.
- About 770 further caption matches fail the checker because of malformed codes in the figure
  record.
- None of the 116 stored Radiology Assistant figures has a recorded sentence that names a finding
  requirement, so none was bound in this pass.

## Limits of this pass

- Only figures already stored were considered. No new figure was fetched.
- A figure was a candidate only if its description shares a word with a finding requirement or
  one of its listed parts. A figure that describes a finding in other words was not read.
- Bindings are to the requirement, not to its individual parts.

## Files

- `review.json`: accepted pairs (quote, panels, side, evidence), the kind-of pairs, and rejected
  candidates.
- `inverse.json`: exact byte edits and hashes for the evidence file.
- Tool: `tools/anatomy_sources/bind_finding_figures.py`.
- Tests: `tests/test_finding_figure_bindings.py`.
