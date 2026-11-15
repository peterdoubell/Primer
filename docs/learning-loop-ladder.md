# Learning loop and ladder handover

Branch: `codex/learning-loop-ladder`, based on `origin/board-round-22` at
`e2cfd2247b240c6bfe03ca8dcc44ca971e0fbe9f` (Round 30).

## What changed

Practice now has its own priced Today step. Completing an issued sitting counts
attendance once, including an explicitly unscored sitting; only a real passing
result counts Learn. The youngest stages need ten countable correct items and
three individually spaced passes. The node and story surfaces show the same
three-pass requirement. Closing practice refreshes the lesson immediately.

All 75 young knowledge banks now have authored pair/order teaching notes. The
independent semantic audit found incorrect and ambiguous ordering keys; these
were corrected or withdrawn, leaving 251 sequences. Sequence-specific criteria
also drive the spoken prompt. The fixes include family age direction, instrument
pitch direction, water's phase changes, specified programming tasks, cycle starting
points and experiment conditions. Two differently worded synonyms are no longer
competing answers in the magnet bank. Living versus formerly living is separated
explicitly in the classification prompt.

Mistake cards preserve teaching outside selectable order/pair keys. Ordering
review alternatives use complete members in a different order, even on a one-card
deck, with a deterministic fallback. Failed review exposure restarts the evidence cooling
off window. A normalized durable-front identity covers legacy cards whose display
backs include explanations, abbreviate the answer or show short-answer keywords.
Correct recall adds no new exposure, matching the quiz policy. Burning successful
reviews was rejected after the expanded simulation delayed honest mastery to days
20–27. Review quality remains self-reported; this does not defeat forged grades.
The front identity supplements the original prompt/key identity; first commitments remain evidence
when they precede exposure. Later cold retrieval becomes countable again.

The general stage still settles by median and falls at most one rung per sitting.
Any general field measured at stage 4 or above keeps the global interface at least
at stage 2. Specialist fields are excluded. Assumed prerequisite access is labelled
on the map and lesson, including the existing specialist-entry exception.

Observed reading visits adjust only the assigned reading allowance, never the
entire instructional programme. Today uses the same rate. Individual reading
records cap at 90 minutes, with the existing 30-minute per-title rate cap retained.
The copy says these are longest visits, not completed articles, and discloses that
returning to finish an article can make the estimate too short. Tutor focus/hover,
pictures, papers and hidden tabs pause the clock independently.

The full-suite run also exposed an existing maintenance shutdown spin: after a
stop during backup, the worker skipped its wait and immediately backed up again.
Each lifespan now owns its stop event and closes its worker; the loop checks that
event before starting another pass. The independent mastery auditor verified the
regression plus overlapping lifespans and exceptional exits.

## Evidence and limits

Independent reports are preserved in `docs/audits/learning-ladder-{loops,mastery}.md`.
Both independently scored the repaired implementation **8.0/10**. Final implementation:
commit `b3e1533`, tree `a97009117654ddff83725e14bf330a9eced22944`.
Both independent audits are pinned to that exact tree. Earlier failed claims, lower scores and differing intermediate measurements
remain visible in the reports.

- Full regression suite: **1,629 passed, 3 skipped**, 344.09 seconds. The skipped
  tests remain visible in pytest output; no failed test is excluded.
- Final focused material/fairness suite: 751 passed in 29.18 seconds, before the
  final living-category wording refinement. That refinement is checked separately.
- Stage policy: all 23,328 three-field transitions checked. This is exhaustive for
  that enumerated function domain, not every HTTP history. Actual HTTP placement,
  genuine-time earned promotion/recovery and graduate-gate agreement also pass.
- Six mutation checks were killed by their corresponding regressions: remove the
  advanced-stage floor, remove individual spacing, scale the whole lesson by reading
  rate, omit legacy review exposure, stop logging completed practice, or burn an already-correct review answer. Reproduce
  with `python tools/check_loop_mutations.py`; it copies source directories only.
- Expanded 45-day simulation: honest learners reached proof on days **13, 11**
  (plants), **13, 9** (living things), and **7, 8** (water states). Final combined
  runs gave **no mastery in all six guesser and all six fixed-half-knower runs**
  (540 nonlearning daily sittings). All 18 runs continued through day 45. Three representative nodes, two seeds per
  mode, pure guesses/fixed half knowledge/learning after two feedback encounters.
  The learning model forgets knowledge not successfully retrieved for ten days.
  These are simulated outcomes, not measurements of human retention or transfer.
- Adaptive ablation: independent candidate run had **1/23 vs 18/23 errors** on
  the same graded held-out paper three days after equal-budget practice, enabled
  versus disabled. Final material recheck: **1/23 versus 22/23 errors** (4.3% versus 95.7%)
  across eight seeds. The earlier candidate and final control draws differ; both
  measured results are retained. The retention model is stipulated;
  the causal result establishes a scheduling effect under that model, not that the
  wording of explanations has a proven educational effect.
- Fairness checks cover all 126 generators at levels 0, 1, 2 and 4, both directions
  of article/word-overlap cues, and length/number ranks. Final tool run: exactly three known findings across 126 generators; the final
  living wording refinement also passes its targeted audit.
  The three pre-existing findings (complex numbers, fractions, integrals) remain
  disclosed. A marginal magnet rank finding in the audited candidate was repaired
  through meaningful distractors/response categories, not a wider whitelist.

## Browser verification

All browser work used port **8748** and new scratch SQLite files. No live learner
record was read, copied or changed. The final walkthrough used `/tmp/primer-preview-final.db`:

1. Set up Ada, age 5, three hours/week, Life Sciences.
2. A wrong food answer received the authored explanation; 9/10 created one card.
3. Same-day retry re-encountered food first and scored 10/10, visibly unscored.
   Today showed Practice 1/1, Learn 0/1, and reduced the remaining evening from
   24 to 15 minutes. No mastery was awarded.
4. Advance the scratch wall clock one day. The food card was due and reviewed.
5. After the cooling-off period, complete 10/10 sittings on days 4, 5 and 6.
   The missed food item reappeared and was answered correctly. Results and lesson
   showed 1/3, 2/3, then “Mastered”/“You have proved this one”.
6. Scratch store corroborates five practice events, four scored attempts, one
   review, one card and three passes with a mastery timestamp.

A separate scratch reading fixture verified real tutor focus and picture controls:
the reading record stayed at 65 seconds through both holds, then advanced to 136
seconds after returning to reading and navigating away. The deterministic test
`node tools/check_reading_clock.cjs` executes the actual client clock and verifies
60 active seconds through overlapping tutor/picture/paper/visibility holds.
The browser fixture used a local placeholder picture, not a downloaded article.
`node tools/check_review_choices.cjs` also executes the actual review-choice
function with a stalled shuffle, multiword members, a single card and an internal
colon in the prompt; each result is a different complete ordering.

## Dashboard delivery

The requested Claude dashboard URL returns “Page not found” in the available
browser. An editable link or publication route has been requested. No same-URL
update is claimed. `docs/dashboard-learning-loop-update.md` holds the reviewable
update for publication when access is available.

## Reproduce

From this branch with the project Python dependencies installed:

```sh
primer_verify_dir=$(mktemp -d)
PRIMER_DB="$primer_verify_dir/import.db" PRIMER_BACKUP_DIR="$primer_verify_dir/backups" python -m pytest -q
python tools/check_loop_mutations.py
node tools/check_reading_clock.cjs
node tools/check_review_choices.cjs
python tools/check_generators.py
```

The generator tool deliberately reports the three disclosed existing findings;
`test_generator_fairness.py` verifies the exact allowed set has not expanded.
Never point these checks at a live learner database.
