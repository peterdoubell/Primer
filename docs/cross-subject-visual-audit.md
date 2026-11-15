# Cross-subject visual audit

## Follow-up corrections, 2026-09-05

`hist.1.maps` was inspected and found to contain only text describing map
symbols. It now has one invented worked map: school south of park, river east
of both, north arrow, matched key and a graphical distance scale. Its straight
route is exactly three scale-bar lengths, or six kilometres. The illustration
and caption explicitly avoid measuring physical screen centimetres. Both
resolutions were visually inspected; four focused cohort tests pass, including
deterministic rendering and distance invariance at four resize factors. The
83-lesson humanities asset checker passes. No interaction is claimed for this
static plate.

Introductory history follow-up: `hist.0.community` now draws a stethoscope,
protective helmet/radio and inspected book, linking tools to listening,
coordination and source checking rather than leaving three text-only panels.
`hist.0.longago` now compares one concrete postal example (Britain, 1840) with
a present-day phone message, plus a surviving-evidence panel. The message is
invented and the stamp schematic; this is not a reproduction of an artifact or
a claim that all places changed tools together. The date and prepaid-postage
context were checked against the Smithsonian National Postal Museum:
[The World's First Postage Stamps](https://postalmuseum.si.edu/exhibition/the-queen%E2%80%99s-own-postal-reforms-that-transformed-the-mail/the-worlds-first-postage-stamps).
Both 800/1600-pixel versions were visually inspected. Three focused cohort
tests pass, including deterministic rerendering of both replacements; the
83-lesson humanities checker and 432-lesson illustration checker pass.

The historical findings below now have three additional corrections:
`mind.0.fair` uses clothed figures instead of stick markers, with unchanged eye
levels, support heights and barrier comparison. `mind.0.feelings` now draws
the shared school setting and each child, retaining self-reported feelings
rather than inferring an emotion from appearance. `arts.4.composition` now
shows two original four-note voices on a semitone grid: C4/D4/E4/D4 above
A3/B3/C4/B3, with one-beat durations and exact 3/3/4/3-semitone intervals.
The separate A/B/A-prime form example is explicitly not a description of those
four notes or certification of strict counterpoint. Both responsive resolutions
were visually inspected; deterministic render tests and all humanities asset
checks pass. These changes do not certify the uninspected backlog below.

Snapshot: 2026-09-05. This is a bounded review of the current working tree, covering Language & Literature, Computer Science, History & Civics (including economics), Arts & Music, and Mind, Society & Philosophy. The first five model proposals and four corrections below are implemented locally; remaining proposals are not complete.

## Coverage and evidence

The current curriculum inventory contains 432 lessons, 432 illustrations, 864 responsive WebPs and 87 interactive model entries (519 gallery items). Fourteen entries use `spatial-3d`, including perspective and the Bloch sphere; three use `concept-lab` for economics, linguistics and modal logic.

| Domain | Lessons / illustrations | Models | Lesson counts by stage 0, 1, 2, 3, 4, 5 |
| --- | ---: | ---: | --- |
| Language & Literature | 40 / 40 | 3 | 5, 8, 8, 8, 6, 5 |
| Computer Science | 34 / 34 | 6 | 3, 4, 6, 7, 8, 6 |
| History & Civics | 29 / 29 | 3 | 3, 4, 5, 6, 6, 5 |
| Arts & Music | 25 / 25 | 3 | 4, 4, 5, 5, 4, 3 |
| Mind, Society & Philosophy | 29 / 29 | 3 | 3, 4, 5, 6, 6, 5 |
| Reviewed domain totals | 157 / 157 | 18 | All six stages represented |

Evidence: a direct inventory of `nodes[].lesson_media` in the five curriculum JSON files and a successful run of `python3 tools/check_curriculum_illustrations.py` on this date. The checker establishes asset coverage and integrity, not teaching quality, visual legibility, or numerical correctness of every interactive model.

Current models in these domains are:

- Language: alphabet explorer and early reading path.
- Computer science: sequence runner, algorithm tracer, stack/queue lab, TCP packet tracer, complexity/certificate lab.
- History: family timeline and chronological ordering.
- Arts: classroom paint mixer and art-elements composer.
- Mind/philosophy: counterexample lab and truth-table lab.

The new models add supply/demand, syntactic attachment, modal accessibility, perspective projection and single-qubit phase/measurement to that existing inventory. Advanced history methods and musical composition remain model opportunities. These are coverage observations, not a requirement to add a model to every lesson.

## Concrete corrections to prioritize

Four defects were verified by opening actual WebP files. These are corrections to current content, separate from requests for new models.

| Priority | Lesson | Observed defect | Proposed correction and acceptance evidence |
| --- | --- | --- | --- |
| Corrected 2026-09-05 | `cs.1.binary` | The plate shows four place values 8, 4, 2, 1 and **1101 = 13**. Curriculum and generator metadata previously described three places and **101 = 5**. | Both alt text and caption now describe 1101, decimal 13 and all four places. `python3 tools/generate_language_cs_illustrations.py --check` verified all 74 lesson illustration pairs. SHA-256 checks before and after confirm both binary WebPs are unchanged. |
| First | `lang.4.linguistics` | The syntax terminals “Those”, “dogs” and “bark” sit directly on the bottom panel border. | Raise the tree terminals or enlarge/reflow the panel, keeping clearance below their descenders. Verify at 800 and 1600 pixels. |
| First | `cs.5.distributed` | “follower F2 OFFLINE” runs behind the first log cell, obscuring the end of the label. The vertical replication arrow also crosses the word “replicate”. | Wrap the follower label into two lines and move the arrow label beside its shaft. Verify labels do not intersect boxes or arrows at either resolution. |
| First | `arts.2.color-theory` | The perspective rays and foreground rectangle overlap the lower explanatory text. The balance fulcrum also extends into its caption. | Reserve a dedicated caption band below each drawing and shorten/raise the geometry. Preserve the actual geometric comparison. Verify full separation at both resolutions. |

Exact rendered evidence:

- `/Users/peter/Documents/ChatGPT/Primer/web/illustrations/sprout/computer-science/cs-1-binary-800.webp`
- `/Users/peter/Documents/ChatGPT/Primer/web/illustrations/grove/language/lang-4-linguistics-800.webp` and `lang-4-linguistics-1600.webp` in the same directory.
- `/Users/peter/Documents/ChatGPT/Primer/web/illustrations/forest/computer-science/cs-5-distributed-800.webp` and `cs-5-distributed-1600.webp` in the same directory.
- `/Users/peter/Documents/ChatGPT/Primer/web/illustrations/sapling/arts/arts-2-color-theory-800.webp` and `arts-2-color-theory-1600.webp` in the same directory.

The binary mismatch also appears in `/Users/peter/Documents/ChatGPT/Primer/data/curriculum/06-computer-science.json` and `/Users/peter/Documents/ChatGPT/Primer/tools/language_cs_illustrations/computer_science.py`. Rendering ownership for the two language/CS layout fixes is in `language_advanced_detail.py` and `cs_advanced_detail.py` within that generator package. The arts layout belongs to `/Users/peter/Documents/ChatGPT/Primer/tools/humanities_illustrations/arts.py`.

## Further rendered review

Correction status: all three layout defects above were repaired in their native generators and both 800/1600 WebPs regenerated. Visual inspection at both resolutions confirmed syntax terminals clear the border, distributed-system labels clear cells/arrows, and perspective/balance drawings clear their captions. Language/CS and humanities generator checks passed. The table preserves the original findings as an audit trail.

Twenty-eight lesson plates were opened at their 800-pixel size; three layout findings above were also inspected at 1600 pixels before and after correction. The following are actual visual observations, not inferences from the generators. All paths in the table are relative to `/Users/peter/Documents/ChatGPT/Primer/web/illustrations/`.

| Inspected asset | Finding / disposition |
| --- | --- |
| `seedling/language/lang-0-phonics-800.webp` | Clear letter-to-sound mapping, ordered blending and accent caveat. Preserve; audible blending or a 2D stepper would add more than 3D. |
| `sapling/language/lang-2-grammar-800.webp` | Clear hierarchy connecting sentence, phrases, roles and words. Preserve as a static reference. |
| `grove/language/lang-4-linguistics-800.webp` | Four coordinated representations are useful; fix the border collision above. |
| `forest/language/lang-5-philology-800.webp` | Stemma uses dashed inferred witnesses, solid surviving witnesses, a legend, actual variant readings and explicit uncertainty. Preserve. |
| `sprout/computer-science/cs-1-binary-800.webp` | Legible switches and a correct four-bit worked sum. Metadata corrected on 2026-09-05; raster files preserved. |
| `tree/computer-science/cs-3-algorithms-800.webp` | Concrete merge-sort split, comparisons, result and per-level work. Preserve; an incremental merge trace is an optional 2D extension. |
| `grove/computer-science/cs-4-ml-800.webp` | Distinct train/held-out panels, distinct point shapes, visible errors and held-out warning. Preserve. |
| `forest/computer-science/cs-5-distributed-800.webp` | Specific log entries and quorum example explain a mechanism; repair label collisions. |
| `forest/computer-science/cs-5-quantum-800.webp` | Concrete H-then-H amplitude cancellation and probability result. Preserve as a companion to a possible phase/Bloch model. |
| `sprout/history/hist-1-ancient-800.webp` | Readable causal sequence and a warning against a single-cause account. Mainly prose in cards; a future material-evidence example would deepen it, but 3D alone would not. |
| `tree/history/hist-3-economics-intro-800.webp` | Correctly labelled qualitative axes and surplus/shortage comparison. Preserve and add a quantitative 2D model. |
| `grove/history/hist-4-historiography-800.webp` | Source types converge through a named criticism method to a qualified claim. Preserve; an evidence-reveal interaction is appropriate. |
| `forest/history/hist-5-economic-theory-800.webp` | Worked payoff matrix, confounding graph and matched-value gains/losses. Dense but readable with distinct questions and limitations. Preserve. |
| `forest/history/hist-5-anthropology-800.webp` | A flat stratigraphic stack plus evidence procedure; position/context is a real spatial relationship that a sectionable 3D trench could improve. |
| `sprout/arts/arts-1-crafts-800.webp` | Upgraded 2026-09-05: before/after drawings show clay coils becoming a hollow pot, a soap block rounded by removal, and identical paper pieces arranged into a house. Material changes now carry the explanation instead of text-only columns. |
| `sapling/arts/arts-2-color-theory-800.webp` | Useful comparisons; repair drawing/caption collisions. Perspective is a strong 3D candidate. |
| `tree/arts/arts-3-design-800.webp` | Clear design/test/revise process. Preserve; the lesson needs an applied constraint example more than a freely rotating object. |
| `grove/arts/arts-4-composition-800.webp` | Two coloured contours show simultaneous events, but have no pitch scale, note values, staff, or measured intervals. Add actual musical information before treating it as a rigorous worked counterpoint example. |
| `seedling/mind-society/mind-0-feelings-800.webp` | Two contrasting experiences of the same school event avoid claiming a universal response. Entirely text cards; simple scene/body-clue drawings would help early readers. Avoid using facial appearance as a diagnostic label. |
| `tree/mind-society/mind-3-ethics-800.webp` | One shared dilemma and three reason frameworks make a readable comparison. Preserve; do not turn contested moral conclusions into an automatic score. |
| `grove/mind-society/mind-4-economics-behav-800.webp` | Clear equal-expected-value example and distinction between benchmark and observed choice. Preserve; probabilities and outcomes are suitable 2D controls. |
| `forest/mind-society/mind-5-logic-advanced-800.webp` | Directed accessible-world graph makes necessity/possibility concrete, alongside a qualified paraconsistency contrast. Preserve and add an exact modal-graph evaluator. |
| `seedling/arts/arts-0-drawing-800.webp` | Upgraded 2026-09-05: a cup, too-narrow outline and revised outline demonstrate one observable change. Height stays fixed; width guides make the correction explicit. Replaces the text-only cycle. |
| `seedling/arts/arts-0-singing-800.webp` | Four syllables align to evenly spaced beats while the contour rises/falls. Preserve the age-appropriate contrast; optional user-initiated audio would make the pitch relationship audible. |
| `seedling/history/hist-0-community-800.webp` | Entirely text cards about helpers. Add specific tools/actions showing how each helper responds to a need, without stereotyped character designs. |
| `seedling/history/hist-0-longago-800.webp` | Text-only comparisons lack concrete time/place context and pictures of the changed tools. Add a bounded example with dated/contextualised objects; avoid suggesting old methods disappeared everywhere. |
| `seedling/language/lang-0-stories-800.webp` | Character, garden, missing key, search and found key make a specific causal chain visible. Preserve the sequence; the bottom abstract vocabulary is a supporting adult/reader explanation. |
| `seedling/mind-society/mind-0-fair-800.webp` | Equal boxes versus varied support convey the mechanism, but people are stick markers. Retain the exact height/barrier comparison while upgrading figures to the richer visual standard; the turn-taking diagram remains useful. |

No visual approval is implied for the 129 uninspected plates in these five domains. Uniform palette, framing and typography in this sample already match the mathematics family; replacing good explanatory graphics merely for stylistic novelty would add little. Early text-only and stick-marker plates remain explicit upgrade work, not accepted completion.

The introductory drawing and crafts replacements were inspected at both 800 and
1600 pixels. Alt text was updated in the generator and curriculum, and the
humanities checker verified all 83 lesson illustration pairs. The focused cohort
tests include deterministic rerendering of these two concrete examples. The full
suite before these static edits passed 894 tests with two skips; this does not
substitute for the remaining visual audit. No deployment is implied.

## Highest-value model proposals

Proposals 1–5 are now implemented, giving each reviewed subject area a substantive interaction without forcing spatial controls onto non-spatial ideas. Proposals 6–8 remain pending. Verification: 32 focused Python tests passed; the five-model checker exercised 1,117 deterministic builds and 13 meaningful controls. Browser checks passed all 14 spatial scenes and the three concept scenes, including all 64 modal configurations, keyboard controls, exact reset, desktop/mobile bounds and current-source hashes. Screenshot review is separate from those numerical checks.

| Order | Lesson / proposed model | Why this representation | Meaningful controls and verification |
| --- | --- | --- | --- |
| 1 | `hist.3.economics-intro`: supply, demand and a posted price | **2D.** Price and quantity already form the relevant plane. | Move posted price and a demand-shift parameter. Show planned quantities, numerical shortage/surplus and the new crossing. Explicitly distinguish a movement along a curve from a shift. Use named linear toy assumptions, not claims about a real market. |
| 2 | `lang.4.linguistics`: two parses of one sentence | **2D tree.** Hierarchy and attachment, not depth, create ambiguity. | Switch the prepositional-phrase attachment in an original sentence such as “I saw the person with the telescope”. Highlight the changed branch and corresponding interpretation. Include an accessible bracketed/text parse, with no external parsing service needed. |
| 3 | `mind.5.logic-advanced`: accessible worlds | **2D directed graph.** Accessibility need not be spatial distance. | Toggle truth of P at accessible worlds and toggle named accessibility edges. Compute □P and ◇P from exactly the displayed relation. Include the empty-successor case: universal truth versus existential falsehood, while stating which frame is being shown. |
| 4 | `arts.2.color-theory`: perspective projection | **3D with a 2D image-plane companion.** Depth changes the projected size and convergence. | Move a cube in depth, change viewing position/focal distance and show rays to the image plane. Preserve physical cube size while projected size changes. Separate orbiting the explanatory scene from the camera that defines the projection. |
| 5 | `cs.5.quantum`: single-qubit phase and measurement | **3D Bloch sphere plus explicit probabilities.** Phase and basis are hidden by the current real-amplitude H/H example. | Polar/azimuth controls or named X/H/Z gates; display Z- and X-basis probabilities. Show that changing relative phase can preserve Z probabilities but change X probabilities. Limit the model to one qubit; identify pure states and do not imply the sphere represents a general entangled register. |
| 6 | `hist.5.anthropology`: excavated context and cross-sections | **3D.** Horizontal position and vertical context both matter. | Reveal layers or a cutaway; select one synthetic find and report its recorded context. Include a later cut/fill so depth alone does not automatically determine age. Label all dates/materials as a teaching scenario, not an archaeological reconstruction. |
| 7 | `arts.4.composition`: two musical lines | **2D notation/time plus optional user-initiated sound.** Pitch and duration need explicit encoding. | Step simultaneous notes, adjust a specified note and show its interval with the other voice. Use a short original phrase; identify the musical convention. A pitch-labelled static upgrade is worthwhile even before adding controls. |
| 8 | `hist.4.historiography`: revise a claim with evidence | **2D evidence cards and argument links.** Provenance, corroboration and silence are relationships between claims and sources. | Reveal fictional diary/payroll/newspaper excerpts and compare justified claim revisions. Preserve uncertainty, conflicting perspectives and the distinction between absence of evidence and evidence of absence. No single “truth score”. |

Additional suitable later 2D extensions are a four-bit toggle for `cs.1.binary`, a stepwise merge trace for `cs.3.algorithms`, and a probability/outcome comparison for `mind.4.economics-behav`. The existing plates already supply the exact examples these interactions should explain.

Acceptance for every implemented model should include keyboard controls, visible and spoken state, meaningful reset, labelled assumptions, deterministic numerical expectations, responsive layout and a lesson-specific explanatory gain. A rotating shape with unchanged interpretation is not sufficient evidence of that gain.
