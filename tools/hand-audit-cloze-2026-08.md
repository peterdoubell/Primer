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
