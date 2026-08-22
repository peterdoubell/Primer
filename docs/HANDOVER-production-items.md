# Handover — Commission: rebalance the item banks toward production

**For:** Opus, executing.
**Branch:** `engagement-round-1` (PR #14, open, mergeable). Base `main`.
**Repo:** `/Users/peter/Code/Primer`

---

## 1. What is already done — do not redo it

Two board seats and two benchmarks the user asked for **already exist and are
committed** (`69d0674`):

- **Neal Stephenson** — benchmark **#11 The Book as Artifact (Design Fidelity)**.
  Lens: is this the Young Lady's Illustrated Primer — a book with a voice, a bond
  with one reader, a story that *is* the curriculum — or courseware wearing its
  cover? He judges register, ritual, the book-as-character, and the seams where
  the metaphor breaks.
- **Tim Ferriss** — benchmark **#12 Interactive Learning Loops (Meta-Learning)**.
  Lens: DiSSS, minimum effective dose, time-to-first-win, whether practice is
  *doing the thing* or reading about it, and whether a busy or discouraged
  learner is re-engaged or quietly lost.

Their loops have also been run — **Rounds 22–27**, taking both benchmarks
**6 → 9**, then a skeptics' pass (Round 27) that refuted nothing but found four
real defects and fixed them. `BOARD.md` is the full record; read its last ~200
lines before touching anything.

**Neither benchmark reaches 10, and both are blocked on the same thing.**

---

## 2. The commission

> "the authored banks are still 75% recognition — 2446 `choice` against 612
> `numeric` and 204 `short`, with zero authored `order` or `tally` items despite
> both being fully implemented in `runQuestions`. That is 3,262 items to
> re-author or extend across eleven curriculum files… It is a real gap, it is a
> body of authoring work, and it should be commissioned rather than improvised."
> — BOARD.md, Round 26

Exact composition today (`data/curriculum/*.json`):

| file | choice | numeric | short | order | tally |
|---|--:|--:|--:|--:|--:|
| 01-mathematics | 369 | 153 | 29 | 0 | 0 |
| 02-language | 301 | 11 | 48 | 0 | 0 |
| 03-physics | 256 | 96 | 8 | 0 | 0 |
| 04-life-sciences | 259 | 56 | 22 | 0 | 0 |
| 05-chemistry | 186 | 85 | 1 | 0 | 0 |
| 06-computer-science | 259 | 52 | 8 | 0 | 0 |
| 07-history | 205 | 30 | 34 | 0 | 0 |
| 08-earth-space | 183 | 62 | 4 | 0 | 0 |
| 09-arts | 185 | 28 | 13 | 0 | 0 |
| 10-mind-society | 204 | 34 | 31 | 0 | 0 |
| 11-radiology | 39 | 5 | 6 | 0 | 0 |
| **total** | **2446** | **612** | **204** | **0** | **0** |

**75.0% recognition.** Both renderers already exist and are tested:
`web/app.js:2135` (`order`) and `:2187` (`tally`).

### The goal
Move the balance toward **retrieval and production** without lowering item
quality. This serves Ferriss's #12 (*practice that is production, not
recognition*) and Webb's **#2 Assessment Validity** simultaneously. It is
authoring work — judgement per item — not a transform to run over a corpus.

---

## 3. The trap that has already bitten this project twice

**Machine-generated items have twice produced defective items that had to be
withdrawn.** The measured auto-cloze defect rate was **90% → 55%** after a
tightening pass (`tools/hand-audit-cloze-2026-08.md`), still short of the ≤10%
bar, and the self-check feature was **retired** on that evidence rather than
shipped. Do not batch-convert items with a script and declare victory.

**A blocking gap you must close first:** `tools/check_banks.py` has **no rules
for `order` or `tally`**. Authored production items would ship unvalidated by
the one tool that guards this corpus. Extend the checker *before* authoring at
scale — at minimum: every `order` has ≥3 steps with exactly one defensible
sequence; every `tally` has `len(items) == int(answer)`; no item is answerable
from the stem alone.

Existing checker rules that must keep passing: pick-by-length edge
(`MAX_LENGTH_EDGE = 0.08`, warn at `0.045`), the stage 0–1 two-option share cap,
and the absolute-language skew check. Run `python3 tools/check_banks.py` — it
must report **0 problems across 11 files**.

---

## 4. Suggested approach (judgement required, not a recipe)

1. **Extend the checker first** (above). Nothing else is safe without it.
2. **Pick one domain as a pilot** — mathematics and chemistry have the highest
   `numeric` share already and convert most naturally to `order` (derivations,
   procedures, reaction steps). Do one file end to end, measure, then decide.
3. **Convert where the shape genuinely fits.** A `choice` item testing *sequence*
   ("what happens first?") is an `order` item wearing the wrong clothes. One
   testing *recall of a name* usually should stay `choice` — converting it to
   `short` just makes it a spelling test. Prefer rewriting the *task* over
   re-labelling the *format*.
4. **Stage 0–1 gets `tally`.** Those readers cannot read: `tally` is the only
   shape they can operate unaided (see the generator at `primer/practice.py`,
   `g_count_tally`, and its item contract below).
5. **Hand-audit a sample and record the number**, following the precedent in
   `tools/hand-audit-2026-08.md` — method, n, Wilson CI, honest limitations.
   Append a dated section; never overwrite the series.

### `tally` item contract (fixed — the renderer codes against it)
```json
{ "kind": "tally", "prompt": "Touch each flower, then press the button.",
  "items": ["🌸","🌸","🌸"], "answer": "3",
  "say": "How many flowers? Touch each one.", "explain": "…" }
```
`len(items)` **is** the answer; there is no separate count field. Grades through
the existing `_numeric_equal` path — `primer/quiz.py` needs no change.

---

## 5. Hard invariants — this codebase has been broken by each of these

- **Verify UI on the sandbox only.** `preview_start {name:"primer-design"}`,
  port **8748**. Port 8747 is the reader's **real** database and browser sessions
  against it have corrupted real learning history repeatedly.
  Assets are content-hash cache-busted at startup: JS/CSS edits need a full
  `preview_stop` + `preview_start`, not a reload.
- **Two dark blocks.** Any new themed custom property goes in the light `:root`,
  a `--dk-*` source, **and both** `@media (prefers-color-scheme: dark)` and
  `:root[data-theme="dark"]` — which must declare an **identical** property set.
  Verify with a regex diff (currently **56 / 56**).
- `--accent` means **wrong-answer/error only**. `var(--on-fill)` on coloured
  fills, never `#fff`. Every `var(--x)` must be defined (sole exception
  `--range-fill`).
- **Every animation needs a `prefers-reduced-motion` path.**
- **Live regions are mounted empty, then filled** (~30ms). A region inserted with
  its text already inside is announced unreliably or not at all. This file has
  fixed that bug four separate times.
- **Full keyboard operation**, focus never dropped to `<body>`, dialogs trap and
  restore focus.
- **Never touch `content/primer.db`.** Tests must use temp DBs. To check it is
  unharmed, do **not** use `profile.stage` as the canary (stage 0 is correct
  since `ad8c196`) — compare row counts and max timestamps in `events`,
  `reading_log`, `mastery`, `sittings` against `content/backups/*.db`.
- **Branch protection:** no direct pushes to `main`, **no merge commits**, PRs
  only. Rebase to linearise. CI runs CodeQL + Python 3.9 and 3.12.

---

## 6. Verification ritual (run before every commit)

```
python3 -m pytest -q -p no:cacheprovider     # 568 passed, 1 skipped
python3 tools/check_banks.py                 # 0 problems across 11 files
node --check web/app.js
```
Plus the dark-parity regex diff and an undefined-token grep if you touched CSS.
Verify reader-facing changes **live in the sandbox browser** — static checks
cannot tell you whether a tally is operable by a five-year-old.

---

## 7. Definition of done

- Recognition share materially reduced, with the **measured** figure stated —
  not estimated. Say the number even if it disappoints.
- `check_banks.py` extended to validate `order` and `tally`, and reporting 0
  problems.
- A hand-audit sheet appended with method, n, Wilson CI and limitations.
- Suite green; `BOARD.md` updated with a new round in the file's established
  voice, including what was **not** done and why.
- Re-score #11 and #12 honestly. **If the work does not earn a 10, say so.**
  This file's own history shows unearned scores get refuted in the next pass.

## 8. What not to do

- Do not batch-convert with a script and skip the hand audit.
- Do not re-open the visual design work — the palette, typography and drawn-glyph
  system are settled across 25 iterations.
- Do not add a build step, a framework, or anything that breaks offline-first.
- Do not lower a checker threshold to make a bank pass.
