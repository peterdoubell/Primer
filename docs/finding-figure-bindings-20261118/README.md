# Figures of findings bound to finding requirements (2026-11-18)

## The decision

The earlier passes bound stored figures to structures and left findings and diagnoses alone. On
2026-11-18 the project owner decided that figures of findings are bound to finding requirements.
This pass applies that to the figures already stored.

## What was bound

462 partial bindings on 245 stored figures, covering 237 finding requirements. Bound structures
and parts go from 503 to 739 of 57,985; investigations with none go from 67 to 51. No asset is
anatomically approved and no radiologist has reviewed these.

| How the quoted sentence names the finding | Bindings |
| --- | --- |
| It uses the requirement's own word | 362 |
| It uses a term the requirement lists among its required parts | 66 |
| It names a kind of what the requirement names, or spells out its abbreviation | 34 |

| Side of the requirement | Bindings |
| --- | --- |
| Not sided | 277 |
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
thrombosed), and so do a few exact equivalents (stone and calculus, node and lymphadenopathy,
intussusception and invagination, vasospasm and spasm).

A source's own diagnosis is accepted as the source's statement, even where the description adds
that the image alone does not prove it. The basis quotes the whole sentence, limit included.

### Listed terms

Some requirements have a general name, such as "distinct lesion examples", and list the specific
findings among their required parts. Where the sentence uses one of those terms, the row names
the parts that list it (`listed_parts`) and the coverage basis repeats them. Where a term fits
several parts, only the parts the caption's term stands for are named: "gas in the SMV" counts
as mesenteric venous gas, not as intramural gas. Where the caption does not say which of two
parts it is (a cyst that may be simple or complex), both are named.

### Kind-of pairs

These 21 pairs are the only places where the caption's word differs from the requirement's. Each
is true by definition. Removing a pair from `review.json` makes the tool refuse its bindings.

| Caption says | Requirement names | Why |
| --- | --- | --- |
| contusion | injury | a contusion is an injury |
| arterial bleeding, venous injury | vascular lesion | an injured or bleeding vessel is a vascular lesion |
| ischaemic colitis | injury | ischaemic injury of the colon |
| mass, masses, polyp, haemangioma, haemorrhage | lesion | each is a lesion; the haemorrhage is into the adrenal gland |
| hepatic metastases | spread site | a hepatic metastasis is a site of spread |
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
- A finding that the description mentions only to say that the source's suggestion, attribution
  or description of it is unconfirmed. Examples: the laceration of renal trauma figure 11, the
  colitis of bowel wall figure 14 and the adhesion of bowel obstruction figure 10.
- Figures that an existing rule keeps unbound: the reused acute abdomen references, the stroke
  perfusion records and the mixed appendix figure.
- 240 figures have rejected candidates, each with a reason in `review.json`.
- 740 further caption matches fail the checker. 336 are genuine conflicts (a modality outside the
  requirement's scope, or a side or depicted state that does not match), which the checker is right
  to refuse. The other 404 involve a malformed context code in the figure record, such as an extent
  of `source_local_views` or a depicted state with capital letters. Such a code makes the checker
  refuse every binding of its figure; 256 stored figures and models carry one, and repairing them is
  a separate pass.
- None of the 116 stored Radiology Assistant figures has a recorded sentence that names a finding
  requirement, so none was bound in this pass.

## Limits of this pass

- Only figures already stored were considered. No new figure was fetched.
- A figure was a candidate only if its description shares a word with a finding requirement or
  one of its listed parts. A figure that describes a finding in other words was not read.
- Bindings are to the requirement, not to its individual parts.

## Files

- `review.json`: accepted pairs (quote, panels, side, evidence, listed parts), the kind-of pairs,
  and rejected candidates.
- `inverse.json`: exact byte edits and hashes for the evidence file.
- Tool: `tools/anatomy_sources/bind_finding_figures.py`.
- Tests: `tests/test_finding_figure_bindings.py`.
