# Hand audit — application vs recall, 2026-08

`tools/check_banks.py` reports a *naming share* and says plainly that the
figure is a lower bound on recall-only items: it counts stems that ask for a
name, and cannot see an item that asks you to restate a definition in longer
words. The tool's own comment calls the hand audit "the only measurement that
counts". This file is that measurement, so the claim stops resting on a
process with no evidence it was ever run.

**Method.** `python3 tools/check_banks.py --sample 24` draws a month-seeded,
reproducible sheet from the 1180 stage 4–5 items. Each stem is marked **R**
(asks the reader to recall or name something) or **A** (asks them to apply a
principle to a situation they have not been handed the answer to). Marked by
reading the stem only, before looking at the options.

**Result: 24 A, 0 R.** 95% CI on the application share, Wilson, n=24:
**86%–100%**.

| # | Node | Mark | Why |
|---|------|:----:|-----|
| 1 | hist.5.political-theory | A | Ranks three concrete distributions under maximin |
| 2 | lang.4.comp-lit | A | Judges two renderings of "terroir" in context |
| 3 | math.5.diffgeo | A | Applies Gauss–Bonnet to a given surface |
| 4 | phys.5.quantum-info | A | Infers Bob's qubit state after Alice measures |
| 5 | phys.4.particles | A | Computes proton charge from quark content |
| 6 | math.4.numtheory | A | Predicts 5^12 mod 13 *and* the reason |
| 7 | phys.4.particles | A | Reasons from range formula to mediator mass |
| 8 | cs.4.networks | A | Diagnoses a bandwidth-delay-product stall |
| 9 | math.4.discrete | A | Computes edges from the degree sum |
| 10 | cs.4.systems | A | Predicts the consequence of a leak |
| 11 | earth.4.planetary | A | Computes radius ratio from transit depth |
| 12 | lang.4.linguistics | A | Predicts aspiration in an unseen environment |
| 13 | chem.4.organic | A | Predicts a reaction outcome |
| 14 | bio.4.genetics | A | Works a cross to a ratio |
| 15 | chem.4.physical | A | Explains a yield drop via Le Chatelier |
| 16 | earth.4.climatology | A | Reasons about grid resolution trade-offs |
| 17 | phys.4.relativity | A | Applies gravitational time dilation, with reason |
| 18 | arts.4.art-theory | A | Explains two readings of one picture |
| 19 | math.5.diffgeo | A | Applies Gauss–Bonnet to a torus |
| 20 | earth.4.planetary | A | Reasons from nebula theory to composition |
| 21 | cs.4.os | A | Diagnoses I/O saturation from symptoms |
| 22 | math.5.frontier | A | Reasons about what a result would settle |
| 23 | mind.4.economics-behav | A | Explains pricing behaviour from a principle |
| 24 | cs.4.ml | A | Chooses a fix for underfitting from symptoms |

**Reading this honestly.** 24 items is a small sample: the true application
share could sit anywhere in 86–100%, and this sheet cannot detect a pocket of
recall items concentrated in a domain the draw happened to miss. It also
measures *stems*, not whether the distractors make the item winnable by
elimination — that is the length/position work `check_banks.py` does. What it
does establish is that the stage 4–5 banks are not a naming quiz, which is the
specific doubt the lower-bound figure could not settle.

**Cadence.** Re-run on a new month seed whenever the banks change materially,
and append the sheet here rather than replacing it, so the series is visible.
