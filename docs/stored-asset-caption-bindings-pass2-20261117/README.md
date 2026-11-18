# Side rule relaxed; second pass of stored-figure bindings (2026-11-17)

## The rule change

Until now a figure whose record states no side could not be bound to a left or right requirement.
On 2026-11-17 the project owner relaxed that rule. The change is in `tools/check_msk_fidelity.py`
(`side_unstated`):

- A figure whose record states no side may support a left or a right requirement.
- The side is then an assumption, so that coverage can be partial at most. Claiming `complete`
  gives `requirement_coverage_side_unstated_cannot_be_complete`, and such a figure cannot verify
  the requirement.
- Nothing else changed. A stated side must still match. A bilateral requirement still needs a
  figure that states both sides. A side named in a requirement's `context_requirements` is still
  enforced.

## What was bound

280 bindings on 154 stored figures, covering 191 further required structures. Bound structures
and parts go from 258 to 449 of 57,985; investigations with none go from 88 to 73. All coverage is
partial. No asset is anatomically approved and no radiologist has reviewed these.

| Side of the requirement | Bindings | Depends on the relaxed rule |
| --- | --- | --- |
| Sided; the quoted sentence states this side or both | 116 | yes |
| Sided; no side stated; bound on the mirror-image assumption | 33 | yes |
| Sided; the figure record itself states the side | 9 | no |
| Not sided | 122 | no |

The 131 bindings that do not depend on the rule were found because this pass matches requirement
names more widely than the first (filler words removed, parts of compound names).

## How a pair was accepted

1. A sentence of the figure's published caption, or of its stored source note, names the structure.
   The sentence is stored verbatim in `review.json` and quoted in the coverage basis.
2. Where the figure has selected panels, the sentence is about a selected panel.
3. The fidelity checker finds no modality or side conflict for any investigation sharing the structure.
4. The figure was looked at on a contact sheet and is consistent with the sentence.

Side handling when the record states no side: bound to the side the sentence states (or both when
it says both); not bound when the sentence states only the other side; bound to each side when no
side is stated and the two sides are mirror images. Pairs such as the lung lobes or the venae cavae
are not mirror images, so an unsided sentence does not bind them.

## What was not bound

- Findings and diagnoses (haematoma, fracture, thrombus, stenosis and so on): 133 candidate pairs.
  Whether a figure of a finding should support a finding requirement is a separate decision.
  (Decided on 2026-11-18: see `docs/finding-figure-bindings-20261118`.)
- 126 figures have rejected candidates, each with a reason in `review.json`. Common reasons: the
  sentence is about a panel that is not selected; the caption names a different part or the other
  side; a stored note only says what the figure cannot show.
- About 200 further caption matches still fail the checker for reasons unrelated to side
  (malformed depicted-state, panel-state or extent codes in the figure record).

## First-pass quotes rewritten

The first pass (`docs/stored-asset-caption-bindings-20261117`) dropped the first letter of a quote
that began its description and cut long sentences mid-word. This pass rewrites those 14 quotes
whole-word, and moves one (the clivus on `open-sella-pmc10366012-fig7`) from a sentence about an
unselected CT panel to the sentence about the selected MRI panels. Only wording changed.

## Files

- `review.json`: accepted pairs (quote, panels, side) and rejected candidates.
- `inverse.json`: exact byte edits and hashes for the evidence file.
- Tool: `tools/anatomy_sources/bind_stored_caption_assets_pass2.py`.
- Tests: `tests/test_stored_caption_bindings_pass2.py`, and the side-rule cases in `tests/test_msk_fidelity.py`.
