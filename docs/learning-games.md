# Learning sequences: authoring guide and policy

Every module in Primer opens with a short interactive learning sequence. This
guide explains the teaching loop, the policies the server enforces, and the
plain-text format the sequences are written in. The module-by-module coverage,
with the review status of every sequence, is in
[learning-games-coverage.md](learning-games-coverage.md).

## The teaching loop

Each sequence follows the same order, one small step at a time:

1. **Introduce** the idea in a few sentences, with a picture where it helps.
2. **Demonstrate** it on a worked case.
3. **Ask** the reader to predict, sort, order, match, fill a value, edit,
   reveal clues, compare, explore a parameter, build or explain.
4. **Check** the response on the server.
5. **Explain**: feedback names the specific mistake; a *Why?* gives the
   reasoning; hints are there before the answer.
6. **Transfer**: the last step applies the idea to a fresh situation.

Readers can go back, open the whole activity on one page, leave and resume
where they stopped, and replay. A module may hold several sequences (Number
Theory holds seven); the reader picks between them.

## What the server guarantees

- **Answer keys stay on the server.** The browser receives prompts, options
  (in a per-reader shuffle) and visuals. Correct answers, feedback,
  explanations and anticipated mistakes are sent only after the reader commits
  to a response for that step.
- **Every response is marked by the server** (`primer/learning_games/evaluators.py`).
  Arithmetic is exact; expressions use a small arithmetic-only language
  (`exprs.py`), never `eval`.
- **Retries are honest.** Repeating an identical wrong answer does not count
  as a second attempt. The answer can be shown only after two different tries,
  and a revealed step earns no growth.
- **Clue puzzles reward evidence.** Choosing the right conclusion without
  turning over enough clues is marked as unsupported, not correct.
- **Study is not mastery.** Finishing a sequence for the first time pays a
  small amount of growth (up to 6, scaled by the steps solved without a reveal,
  under a daily cap of 30) and records that the reader studied the module.
  Mastery still comes only from the module quiz, passed on spaced days.
- **Memory aids are marked as study.** A step that took more than one try
  becomes a review card with origin `activity`, which never counts as mastery
  evidence.
- **Locked modules stay locked.** Until a module unlocks, the reader sees only
  its introduction and demonstration; checking a step returns 409, like the quiz.

## Files

| Path | Role |
|---|---|
| `data/learning-games/*.lg` | Authored sequences, one file per field or stage band |
| `primer/learning_games/` | Parser and validator, evaluators, catalog, progress store and API |
| `web/learning-games/play.js`, `visuals.js`, `play.css` | The player, loaded only when a lesson opens |
| `web/module-mission.js` | Adds the *Play* stop and mounts the player on every module page |
| `data/learning-games/reader-links.json` | Stand-alone activities linked from the reader (`tools/learning_games_inventory.py`) |
| `docs/learning-games-coverage.md` | Coverage report (`tools/learning_games_report.py`) |
| `data/learning-observations/` | The lesson observations the Number Theory sequences were built from |

Modules without an authored sequence fall back to one derived from their own
reviewed reporting reference (`primer/learning_games/derived.py`); at present
that is 83 radiology modules.

## Checking your work

```bash
python -m pytest tests/test_learning_games.py -q
python tools/learning_games_report.py
python tools/learning_games_inventory.py
```

The tests load every file and fail on any authoring problem, on a step its own
answer cannot solve, on a step that repeats a quiz question, on an answer key
or explanation leaking into the public payload, and on a stale report or
inventory.

## The format

A file is plain text. Lines starting with `#` are comments. Indentation marks
lines that belong to the beat above them.

```
@ math.2.primes                     module id; starts a module
~ Last-Digit Detective              optional: starts a second or later sequence
from: brilliant-2026-11-05-divisibility   optional provenance
review: radiologist                 optional: specialist review still needed
reviewed: 2026-12-01, consultant radiologist   optional: the reviewer's sign-off
level: 2                            optional stage override
goal: The learning objective (12 to 320 characters).
intro: Introduce the idea.
  show: <visual>
  say: optional spoken version for young readers
demo: Work one case.
  show: <visual>
P: A step prompt (3 to 400 characters)
  + correct option :: feedback
  - distractor :: [error-tag] feedback naming the mistake
  hint: at least one
  why: the explanation
>P: The transfer step is marked with > and comes last.
done: A closing line that points to the next learning step.
```

Every sequence needs one `intro`, one `demo`, at least three checked steps of
at least two kinds, a hint and a `why:` on every step, and exactly one transfer
step, last. Every distractor names the reasoning error in `[brackets]` and says
what went wrong. Prompts are unique within a sequence. Options are kept in the
order written only with `keep`; numeric options are sorted, others shuffled.

### Step types

| Letter | Type | Lines it needs |
|---|---|---|
| `P` | prediction | 2 to 6 options: `+` right, `-` wrong |
| `S` | select all that apply | several `+` and at least one `-` |
| `C` | structural comparison | `left:` and `right:` panels, then options |
| `K` | minimum information | 2 to 5 `clue Label: text`; `need: 1,3 \| 2` lists the minimal sufficient sets; then options |
| `O` | ordering | `items: a \| b \| c` (3 to 7, in the right order); optional `ends: first \| last` |
| `M` | matching | `pairs: a => b \| c => d` (3 to 6) |
| `G` | classification | `bin Name: a \| b` (2 to 4 bins, 4 to 10 items); optional `note item :: reason` |
| `F` | missing value | `frame:` with 1 to 3 `__` blanks; one `answer: v \| alt` per blank; `taps:` choices (required at stages 0 and 1); `x value :: [tag] feedback` |
| `E` | constrained edit | `tokens: a \| b{alt1,alt2}`; `limit:`; `aim:`; `accept: 2=alt1` or `eval: expr.equals value=20` or `eval: nt.repair by=8`; `x 2=alt :: [tag] feedback` |
| `X` | parameter exploration | `param id: min..max /step @start \| Label \| unit`; `out id: expression \| Label \| unit`; `aim:`; `target:` (false at the start, reachable); `view: bars OUT over PARAM`, `plot OUT over PARAM` or `graph EXPR x=a..b` |
| `B` | construction | `bank: a \| b \| c` (3 to 12); one or more `answer: a \| b`; optional `any-order`; `x piece :: [tag] feedback` |
| `R` | reflection | `model:` a model answer |

Any step may add `card: front => back` to set its review card, and `miss:` for
generic feedback on an unanticipated wrong answer.

### Visuals

`show:` (and the `left:`/`right:` panels of a comparison) take one of:
`art` (the module's illustration), `text …`, `emoji …`,
`digits 57236 last=3 hide=2 mark=1,3`, `tree 60(6(2,3),10(2,5))`,
`cycle 3 9 7 1`, `dots 12`, `dots 12 /3`, `dots 3x4`,
`line 0..10 step=1 mark=3,7 hop=3>7`, `bars A=3 B=5 unit=N`,
`table h1 | h2 ;; r1 | r2` (up to 5 columns and 8 rows),
`steps a ;; b`, `chips a | b`, `flow a > b > c`, `time 1066=Hastings | 1215=Magna Carta`,
`frac 3/4 5/8`, `plot 2*x+1 x=0..10`, `balance left | right`, `pair spec || spec`,
`grid 3x3 on=1,5,9`, `clock 3:30`, `shapes circle square`.

## Young readers

At stages 0 and 1 the player enlarges its controls, reads prompts aloud on
request (`say:` overrides the spoken text) and avoids typing: fill steps must
offer `taps:`. Keep sentences short and concrete, and prefer pictures.

## Review

Authored sequences start as *authored, awaiting subject review*. Clinical
content that needs a specialist carries `review: radiologist` (or another
specialist), and the reader is told it has not yet been checked. When a
qualified reviewer has checked a sequence, add `reviewed: YYYY-MM-DD, who` and
regenerate the coverage report.
