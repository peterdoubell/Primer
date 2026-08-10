# The Primer

*A living book that teaches you everything — from your first letters to the frontier of what humankind knows.*

Inspired by the Young Lady's Illustrated Primer in Neal Stephenson's *The Diamond
Age*, this is an interactive, adaptive book that **contains all of Wikipedia** and
is designed to carry a gifted, motivated learner from **preschool to graduate
level over 5–10 years**, depending on the breadth of knowledge they seek.

It runs entirely on your own machine. Once you download the Wikipedia archive, it
works **fully offline** — the whole encyclopedia lives inside the book.

```bash
./run.sh
```

Then open <http://localhost:8747>.

---

## What it is

The Primer is three things woven together:

1. **The whole encyclopedia.** It reads Wikipedia natively from ZIM archives
   (the format used by [Kiwix](https://kiwix.org)). Ships able to download the
   complete English Wikipedia (~110 GB with images, ~60 GB text-only) or the
   Simple English edition for young readers (~1–3 GB). When online, it also
   serves and permanently caches live Wikipedia, so the book grows toward
   completeness as it is used.

2. **A curriculum spine from preschool to the frontier.** A hand-authored graph
   of **343 concepts across 10 domains**, each mapped to real encyclopedia
   articles, arranged in six stages:

   | Stage | Name | Level |
   |------:|------|-------|
   | 0 | Seedling | preschool & kindergarten |
   | 1 | Sprout | primary school |
   | 2 | Sapling | middle school |
   | 3 | Tree | secondary school |
   | 4 | Grove | undergraduate |
   | 5 | Forest | graduate & the frontier |

   Domains: Mathematics · Language & Literature · Physics · Life Sciences ·
   Chemistry · Computer Science · History & Civics · Earth & Space · Arts &
   Music · Mind, Society & Philosophy.

   Concepts unlock as their prerequisites are mastered. The graph is a
   **lattice, not a chain**: 912 prerequisite edges, 98% of concepts resting on
   two or more strands, including **218 cross-domain edges** — so quantum
   mechanics genuinely requires linear algebra *and* differential equations,
   and biochemistry requires organic chemistry.

3. **An adaptive tutor that meets you where you are.** The book learns what you
   know and teaches accordingly.

## What it does

- **Onboards and places you.** Tell it your age, weekly hours, breadth of
  ambition, and favourite fields. It meets you at your level — an eight-year-old
  starts at primary-school lessons, not counting to ten. Placement credit is
  marked *assumed*, not *proven*, and a short server-scored placement check can
  confirm or adjust it per domain.
- **Gives you a daily quest.** Review what's due → learn something new → read
  one article, with visible completion. The day's lessons are stable (they don't
  reshuffle when you reload) and drawn from your chosen domains.
- **Reads any article, in-book.** Every internal link becomes in-book
  navigation; images are proxied and cached so they survive going offline; young
  readers are automatically routed to Simple English.
- **"Ask the Book."** A Socratic tutor panel sits beside every article. It
  grounds itself in what you're reading and matches its register to your age —
  guiding you to answers rather than handing them over. Uses Claude when an
  `ANTHROPIC_API_KEY` is present, and a self-contained rule-based Socratic
  engine when offline.
- **Assesses honestly.** **3,162 expert-authored questions cover every single
  concept**, weighted toward application and transfer, each with an explanation.
  Papers are sampled at random and options shuffled on every serve, and they are
  length- and position-balanced, so no surface strategy ("pick the longest",
  "pick the first", "pick the one echoing the title") beats chance. Grading
  happens **server-side against the book's own copy** of the paper — a forged
  submission scores zero. From secondary school upward each quiz includes a
  **constructed-response** item you answer in your own words; early stages mix
  picture questions with a **tap-to-order** format. Plus 50 procedural generators
  (counting and phonics through calculus, kinematics, stoichiometry and
  complexity theory) for unlimited practice, and filtered auto-generated
  questions for any of Wikipedia's millions of other articles.
- **Teaches the youngest readers directly.** Every preschool and primary concept
  has an authored, child-voiced mini-lesson **and picture/audio questions with
  spoken prompts** — a child who cannot yet read can navigate, learn and be
  assessed by ear and by tapping, never by typing. The interface reads itself
  aloud (with a voice toggle), enlarges its targets, and shows stars rather than
  percentages for ages 3–9.
- **Remembers what you learn.** Mastery requires **two passing attempts at least
  two days apart** — one lucky quiz is not mastery, and placement credit is
  marked *assumed* until proven. What you learn (and every question you miss)
  becomes spaced-repetition cards (SM-2) that resurface just as you're about to
  forget. Mastery **decays**: forgotten foundations re-lock what they unlocked,
  the headline count regresses with them, and the book tells you what to refresh.
- **Tells your story.** A **19-chapter frame story**, personalised to your name,
  runs the whole length of the journey — from *The Book That Knew Her Name* to
  *The Edge of the Map* and a closing epilogue. Each chapter turns only when you
  genuinely earn the lesson it leads to, and the book always tells you what it
  is waiting for.
- **Shows your path.** A pacing engine turns your age, hours and breadth into a
  personal year-by-year roadmap to graduate level, priced against real
  instructional time — and tells you what it will actually cost in hours per
  week, rather than reassuring you. A Journey view records every topic you have
  truly mastered.

## The 5–10 year promise, and what it costs

The **Your Path** view estimates your journey from where you are to graduate
level. The five-to-ten year figure is what it *computes*, not what it assumes:

| breadth | hours/week | estimate |
|---|--:|--:|
| everything, ten fields | 6 | **~25 years** |
| everything, ten fields | 15 | **~10 years** |
| everything, ten fields | 20 | **~7.6 years** |
| a few fields, all the way | 25 | **~3.8 years** |

The whole curriculum prices at **~6,500 hours**. That number is anchored to
instructional time — roughly 13,000 hours for K-12, 4,500 for a bachelor's
degree, thousands more for graduate work — discounted to about a third, which is
what one-to-one adaptive tutoring should buy you: no waiting for the group, no
re-teaching to the median, nothing repeated that you have already shown you
know.

So the promise holds, at **fifteen to thirty hours a week**. That is what an
education costs, and the roadmap says so plainly rather than reassuring you:

> At 6 hours a week this comes to about 25.5 years — the whole plan is 6,496
> hours. Ten years needs 15 hours a week, five needs 31. Fewer fields, or fields
> carried less far, brings both down.

An earlier version of these constants was quietly reverse-engineered from the
marketing claim and priced the whole journey at 2,738 hours, with quantum field
theory at under seventeen. The board caught it. See [BOARD.md](BOARD.md).

---

## Getting the whole of Wikipedia

The book ships with two small demo archives already downloaded:

- **Wikipedia 100** (5,023 core articles, with images, ~48 MB)
- **Simple English Wikipedia** (394,563 articles, text-only, ~937 MB)

To hold the complete encyclopedia, open **The Shelf** in the app and click to
download any archive — it streams in the background and is resumable. Or fetch
one manually into `content/`:

```bash
curl -L -o content/wikipedia_en_all_maxi.zim https://download.kiwix.org/zim/wikipedia/wikipedia_en_all_maxi_2026-04.zim
```

Any `.zim` file dropped into `content/` is picked up automatically (use
**The Shelf → rescan**, or restart). You can also add Wiktionary, Wikibooks,
Wikiversity and more from the same catalogue.

## Optional: a smarter tutor

Set an API key to have Claude voice the Primer's tutor:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

**Privacy note:** with a key set, the reader's tutor chat messages and short
excerpts of the article being read are sent off this machine to
api.anthropic.com to generate replies. Nothing else (no profile, mastery
record, or reading history) is sent, the app discloses the remote engine in
its UI (`tutor_remote`), and the reader can switch the tutor back to fully
local at any time in-app (the `tutor_remote_ok` setting) without touching the
environment variable.

Without a key, the tutor uses a fully offline Socratic engine.

---

## How it's built

Pure-Python backend, no build step for the frontend.

```
primer/
  wiki.py        ZIM reader (libzim) + live Wikipedia + permanent cache + search
  render.py      rewrites AND allowlist-sanitizes article HTML for safe in-book display
  curriculum.py  the concept graph; prerequisite, stage-gate and unlock-requirement logic
  learner.py     SQLite profile, mastery (2 spaced passes + decay), SM-2 deck, XP/streaks, backups
  practice.py    50 procedural exercise generators, counting → calculus, phonics → logic gates
  quiz.py        authored banks, filtered cloze, constructed response, cards from misses
  tutor.py       "Ask the Book" — Claude tutor with rule-based Socratic fallback
  pacing.py      turns age/hours/breadth into a year-by-year roadmap, priced honestly
  library.py     Kiwix archive catalogue + background resumable downloader
  server.py      FastAPI app tying it all together
data/
  curriculum/    10 domain files · 343 concepts · 912 prerequisite edges
                 89 child-voiced lessons · 3,162 authored questions
  story/         the 19-chapter frame story
web/             book-styled single-page app (vanilla JS, no build, WCAG-AA, dark mode)
tests/           219 pytest regression tests (unit + HTTP layer)
content/         ZIM archives, the learner database and its rotating backups
```

Requirements: Python 3.9+ and the pinned packages in `requirements.txt`.
`run.sh` sets up a virtualenv on first launch.

```bash
.venv/bin/python -m pytest tests/ -q
```

## Design notes & honest limits

- The curriculum graph is a **spine, not a cage.** Beyond the 343 authored
  concepts, every one of Wikipedia's millions of articles is reachable by search
  and by following links — and reading any of them logs progress and can feed
  your review deck.
- **Age-based placement** credits stages below the learner's level as *assumed
  known* so lessons start in the right place. It is flagged as unproven, and a
  learner who wants to prove those foundations can quiz them any time.
- **Auto-generated questions never count.** An audit put their defect rate at
  65% — mostly items solvable from grammar alone — so they were retired from
  grading entirely. They survive only as a labelled, unmarked self-check for
  free reading. Every one of the 343 curriculum concepts carries **ten**
  authored items, so nothing that moves mastery is machine-written.
- **Knowing nothing scores like knowing nothing.** Always picking the longest
  option, the first, the second-longest, or mining the served JSON for a leaked
  answer all sit at chance and master zero of the 343 concepts. A test sits real
  papers with each strategy and fails if any of them beats a guess.
- The book has been reviewed by a standing **expert board** (educators, a
  learning scientist, a game designer, a UX designer and an engineer) against
  ten benchmarks — see [BOARD.md](BOARD.md) for the rubric, scores and change log.
- Content and archives come from Wikipedia/Wikimedia and the Kiwix project,
  under their respective licences (article text is CC BY-SA).
