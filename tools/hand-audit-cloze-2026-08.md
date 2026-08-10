# Hand audit — auto-generated cloze quality, 2026-08

`primer/quiz.py` carried a comment recording a **65% hand-audited defect rate**
for auto-generated cloze items *before* the sentence filters that comment
introduced, and no number after them. So the shipping defect rate was unknown,
and had been unknown for as long as the filters had existed. This file is the
after number. It follows `tools/hand-audit-2026-08.md`: a reproducible sampler,
a sheet classified by hand, a Wilson interval, and the limits stated plainly.

## Method

`python3 tools/audit_cloze.py 40 2026-08` draws a seeded sheet. The seed fixes
both the article draw and `quiz.R`, so the sheet reproduces exactly. Source
text is the local article cache (`content/primer.db`, opened `mode=ro`) — real
Wikipedia prose the reader is actually quizzed on, not a curated corpus. Twenty
articles, up to three items each, first forty items taken.

Each item was marked OK or given a defect, reading the stem and options only:

- **UNANSWERABLE** — the stem does not determine the key.
- **AMBIGUOUS** — another option is also defensible.
- **LEAK** — the stem or the option list gives the key away (only one option is
  grammatical, only one is a possessive, and so on).
- **NONSENSE** — at least one distractor cannot occupy the blank at all.

An item with any of these is defective. That is a strict bar: NONSENSE alone
still leaves an item the learner answers correctly, just more easily than
intended. The breakdown below separates the harms so the headline number is not
read as worse than it is.

## Result

**29 of 40 items defective — 72.5%.** Wilson 95% CI, n=40: **57%–84%**.

Measured on the shipped generator (commit adding `_tag_classes`). The same
sampler and seed run against the generator *before* that change scored **36 of
40 defective — 90%** (Wilson 95% CI 77%–96%). So the fix moved the rate, and
the intervals barely overlap; but the honest headline is that **the current
cloze defect rate is 72.5%, which is bad.** An auto-generated cloze item is
more likely to be flawed than sound.

Breakdown of the 29 defective items by worst harm:

| Harm | Count | Share of sheet |
|---|---:|---:|
| Would mislead or stump a learner (UNANSWERABLE / AMBIGUOUS) | 6 | 15% |
| Free mark — answerable without knowing the subject (LEAK) | 2 | 5% |
| Answerable, but at least one impossible distractor (NONSENSE) | 21 | 53% |
| Sound | 11 | 28% |

## What was fixed, and what was not

The dominant cause on the pre-fix sheet was distractors drawn from anywhere in
the article and matched only on surface shape — case, length, suffix. A noun
blank was routinely offered `since`, `although`, `became`, `roughly`. Those are
not wrong answers; they are impossible ones, and the item collapses into a
grammar puzzle. `quiz.py` now tags every word with a coarse, corpus-local class
(noun / proper noun / adjective / verb / other) from the slots it occupies in
that article, requires the key to be a noun, name, or adjective, and requires
every distractor to carry the key's class. Two smaller gaps closed alongside:
sentences carrying leftover single-letter maths variables or Greek glyphs are
rejected as no longer prose, and quantifiers (`less`, `dozens`, `thousands`)
joined the weak-key list.

The 53% residual is the same failure one level down: options are now the right
*class* but still the wrong *kind* — `Babylonia mechanism`, `Solla counting
house`, `see your inverses`. Fixing that needs to know what a word means, not
what slot it sits in, and no regex over one article's text will get there. The
same applies to the 15% that are genuinely ambiguous: `Early ______ were not
necessarily precise` is a fine sentence with either `inferences` or `writers`.

One design choice was made against yield on this evidence. A variant that
walked down the keyword ranking instead of taking the top-ranked key produced
about half again as many items and hand-audited at 29/40 rather than 23/40 on
its sheet. It was reverted. That comparison was not controlled — the distractor
pool widened in the same step — so it is reported as a direction, not a
measurement. Yield on short paragraphs fell enough that
`tools/audit_cloze_defects.py`'s corpus had to grow from 17 paragraphs to 84 to
stay above the measurability floor its test asserts.

## Reading this honestly

Forty items is a small sheet: the true rate could sit anywhere in 57–84%, and
the interval is wide enough that a re-run on a different month's seed could
plausibly land ten points either side. The draw covers twenty articles, so a
domain whose prose defeats the generator in a particular way — heavy maths,
dense list sentences — could be over- or under-represented by chance. The
classification is one person's, on one pass, against the definitions above;
the NONSENSE and AMBIGUOUS calls in particular are judgement, and a second
reader would not agree on every line. Nothing here measures whether a *sound*
item is worth asking, only whether a generated item is broken.

The sheet was not adjusted after the fact, and no item was reclassified to move
the number.

## What follows from it

These items are already excluded from grading — they run as a labelled,
unmarked self-check, and mastery moves only on authored bank items. This audit
does not change that; it supplies the number that was missing behind it. At
72.5% the exclusion is clearly still the right call, and the case for ever
promoting auto-generated cloze into graded use is not close.

## Cadence

Re-run on a new month seed whenever `quiz.py`'s generation path changes, and
append the new sheet below rather than replacing this one, so the series stays
visible.

---

# Second sheet — 2026-08-10, after the precision pass

## What changed in between

The generator was rebuilt around one rule: refuse anything it cannot build
well. Concretely —

- **Word-class evidence is now taken from the whole article**, not from the
  handful of sentences that survived the quality filters. The tagger was
  previously asked how a word behaves on the strength of one or two sightings
  and answered "no idea" for most of the vocabulary.
- **Morphology vetoes the tagger.** A word may only be an option if its shape
  agrees with the class its context suggested, and participles (`-ed`, `-ing`)
  are refused outright. This is what stops *fluid*, *orbital* and *denser*
  being offered for a noun blank because the article happened to use them after
  a determiner.
- **Recurrence bar.** A key or an option must appear at least twice in the
  article. Words the article uses once were the arbitrary ones (*Solla*,
  *Nuzi*, *inward*, *salt*).
- **Name blanks are not built at all.** Every proper-noun item on the first
  sheet was broken, because a credible wrong name must be the same *kind* of
  thing as the right one and nothing here knows that: "Babylonia mechanism",
  "Solla counting house". Against the intuition that a name is the most
  concrete thing on the page, and on the evidence.
- **Adjective blanks are not built either.** They were the ambiguity engine:
  "implemented in ______ form" is answered as well by *conditional* as by
  *functional*.
- **Container nouns joined the weak-key list** (*type*, *system*, *method*,
  *value*, *process*, *condition*, …): grammatically perfect keys that name no
  fact, and every near-synonym in the article is a defensible answer.
- **Number agreement** between key and options; **years** must share a digit
  count, sit within 120 years of the key, and never already appear in the stem
  (the first sheet offered *1675* for "James Gregory (______–1675)").
- **Truncated final sentences are rejected** — the article text arrives cut at
  a character budget, so the last "sentence" was routinely a fragment.
- **A three-item floor per article.** Fewer than three survivors and the
  article returns none, so the UI shows its honest "not enough prose" state
  rather than a thin bad paper.

## Method

Identical to the first sheet and deliberately so: `python3 tools/audit_cloze.py
40 2026-08`, same seed, same read-only article cache, forty items, classified
by hand against the same four defect definitions. One mechanical change: the
sampler now walks a larger pool of articles until the sheet is full, because
the generator refuses most articles outright and a pool sized to the sheet
would have returned three items instead of forty. The draw is still uniform
over the cache.

## Result

**22 of 40 items defective — 55%.** Wilson 95% CI, n=40: **40%–69%**.

The comparison number had to be re-measured, because the classifier changed.
The same seed's *pre-change* sheet — the very sheet the section above scores at
29/40 — classified **36 of 40 defective, 90%** (Wilson 77%–96%) by the reader
who classified this one. That is a stricter hand than the first record's, not a
different generator: this reader counts a semantically absurd but grammatical
option (*characteristic water*, *adjectival rings*) as NONSENSE. **Only the
90% → 55% pair is a controlled comparison.** Against the first record's own
scale the improvement is real but the two headline numbers, 72.5% and 55%, are
not strictly comparable.

| Harm | Count | Share of sheet |
|---|---:|---:|
| Would mislead or stump a learner (UNANSWERABLE / AMBIGUOUS) | 11 | 27.5% |
| Free mark — answerable without knowing the subject (LEAK) | 0 | 0% |
| Answerable, but at least one impossible distractor (NONSENSE) | 11 | 27.5% |
| Sound | 18 | 45% |

The shape of the failure has changed as much as its size. Impossible
distractors fell from 53% of the sheet to 27.5%; ambiguity *rose*, from 15% to
27.5%. That is not a regression, it is the cost of the cure: distractors are
now drawn from the article's actual recurring subject vocabulary, and a word
that is plausible in the blank is very often also defensible in it. *"The
curvature of a differentiable ______"* offering *surface* against *curve*, or
*"the ______ of the structure of DNA"* offering *study* against *discovery*,
are not tagger failures. They are two right answers.

## The bar was missed, and by a lot

The target for this pass was ≤10% defective, with instructions to stop and say
so if ~20% could not be reached. 55% is nowhere near either. Halving the rate
took every mechanical signal available in one article's own text; what remains
needs to know what words mean. No lexical resource is installed (`nltk`,
`spacy` are both absent) and no regex over a single article will separate
"plausible but wrong" from "also correct".

So the fallback shipped instead: `/api/selfcheck` now returns
`provisional: true` on any paper that has questions, and the generator refuses
articles that cannot supply three items.

## Yield: the price paid

Measured across the 753 curriculum article slots, at the 6000 characters
`/api/selfcheck` actually passes:

| | Articles yielding ≥1 item | Total items |
|---|---:|---:|
| Before | 586 of 753 | 1,960 |
| After (filters only) | 156 of 753 | 376 |
| After (filters + 3-item floor) | 69 of 753 | 248 |

Nine articles in ten now produce no self-check at all, against roughly one in
five before. That is the intended trade and it is a severe one: for most
articles the feature is now the empty state. The two regression tests that
gated on corpus size were re-based accordingly (from ">1000 items" to ">150"),
and `tools/audit_cloze_defects.py`'s frozen 84-paragraph corpus was retired
outright — after this pass it produced *zero* items, because five-sentence
paragraphs cannot supply the recurrence and class evidence the generator now
demands. It reads the real article cache instead.

## Limitations

Everything the first record says about a forty-item sheet still applies, and
one thing more. The 90% before-number and the 55% after-number were classified
by the same reader against the same definitions, which is what makes them
comparable to each other — but that reader had already read the after-sheet
while developing the changes, and knew which items the new filters were
supposed to have saved. That is a real bias toward the after-number, in the
direction of leniency, and it is not correctable after the fact. A clean
re-measurement would use a fresh month seed and a classifier who has not seen
the code. The AMBIGUOUS calls in particular are judgement: several items scored
defective here (25, 26, 29) are ones a second reader might well pass.

## What follows from it

Unchanged, and now with a second number behind it: these items stay out of
grading. At 55% the reader must additionally be *told*, which is what
`provisional` is for. The remaining case for the feature is that it prompts a
re-read, and a re-read is worth something even when the question that provoked
it was flawed — but that is an argument, not a measurement, and it should not
be allowed to stand in for one.

## Outcome (2026-08-10): the feature was retired on this evidence

The argument at the end of the section above did not survive its own caveat.
`/api/selfcheck` and the self-check path in the client are removed. 55%
defective is a coin flip dressed as a question, `provisional` is a disclaimer
rather than a fix, and "it prompts a re-read" is exactly the argument this file
warned should not stand in for a measurement.

The generator (`quiz.cloze_from_text`) stays in the tree as measurement
apparatus only — nothing in the app calls it — so that this audit remains
reproducible and so the regression tests can hold the 5% bar the feature would
have to clear to come back. It comes back on a number, from a fresh seed and a
classifier who has not seen the code, or not at all.
