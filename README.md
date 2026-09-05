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
   of **348 concepts across 10 domains**, each mapped to real encyclopedia
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
   **lattice, not a chain**: 926 prerequisite edges, 98% of post-Seedling
   concepts resting on two or more strands, including **221 cross-domain
   edges** — so quantum
   mechanics genuinely requires linear algebra *and* differential equations,
   and biochemistry requires organic chemistry.

3. **An adaptive tutor that meets you where you are.** The book learns what you
   know and teaches accordingly.

## What it does

- **Onboards and places you.** Tell it your age, weekly hours, breadth of
  ambition, and favourite fields. Every new reader starts at Stage 0 with no
  assumed knowledge. A short server-scored placement check can then credit what
  you demonstrate per domain; placement credit is *assumed*, not *proven*.
- **Gives you a daily quest.** Review what's due → learn something new → read
  one article, with visible completion. The day's lessons are stable (they don't
  reshuffle when you reload) and drawn from your chosen domains.
- **Reads any article, in-book.** Every internal link becomes in-book
  navigation; images are proxied and cached so they survive going offline; young
  readers are automatically routed to Simple English.
- **"Ask the Book."** A Socratic tutor panel sits beside every article. It
  grounds itself in what you're reading and matches its register to your age —
  guiding you to answers rather than handing them over. It answers locally by
  default; Claude voices it only once remote answering is explicitly switched
  on (see *Optional: a smarter tutor*).
- **Assesses honestly.** **3,212 expert-authored questions cover every single
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
- **Tells your story.** A **19-chapter frame story**, personalised to your name
  *and your pronouns*, runs the whole length of the journey — from *The Book
  That Knew Their Name* to *The Edge of the Map* and a closing epilogue. The
  source text names and genders nobody: it carries `{NAME}` and pronoun tokens
  which are rendered per reader, so the protagonist is you rather than a girl
  called Nell with your name pasted over hers. The book offers she/her and
  he/him, asks rather than guessing when the choice is unknown, and lets you
  change it afterwards. Each chapter turns only when you
  genuinely earn the lesson it leads to, and the book always tells you what it
  is waiting for.
- **Shows your path.** A pacing engine turns your age, hours and breadth into a
  personal year-by-year roadmap to graduate level, priced against real
  instructional time — and tells you what it will actually cost in hours per
  week, rather than reassuring you. A Journey view records every topic you have
  truly mastered.
- **Keeps more than one reader, and lets you set the level per subject.**
  Optional Google sign-in (see *Google sign-in*, below) gives each person their
  own profile under one hosted copy. The Account screen also carries a slider
  per subject you've chosen, so a reader far ahead in one field and just
  starting another isn't held to one number across both.

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

Claude can voice the Primer's tutor. This takes **two** deliberate steps, and
**remote answering is off until both are done**:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

...and then switching it on in the app (the `tutor_remote_ok` setting, `POST
/api/profile/settings {"tutor_remote_ok": true}`). A key on its own changes
nothing: it says the installation *could* answer remotely, which is not a
child's consent to send their questions to a third party. Until the switch is
turned on, the offline engine answers and nothing leaves this machine.

**Privacy note:** once it *is* on, the reader's tutor chat messages and short
excerpts of the article being read are sent off this machine to
api.anthropic.com to generate replies. Nothing else (no profile, mastery
record, or reading history) is sent, the app discloses the remote engine in its
UI and on `/api/state` (`tutor_remote`), every reply carries a `remote` flag,
and the switch works in both directions at any time without touching the
environment variable.

With the switch off, or with no key at all, the tutor uses a fully offline
Socratic engine.

---

## How it's built

Pure-Python backend, no build step for the frontend.

```
primer/
  wiki.py        ZIM reader (libzim) + live Wikipedia + permanent cache + search
  render.py      rewrites AND allowlist-sanitizes article HTML for safe in-book display
  curriculum.py  the concept graph; prerequisite, stage-gate and unlock-requirement logic
  learner.py     SQLite profile, mastery (2 spaced passes + decay), SM-2 deck, XP/streaks, backups
  store.py       the one connection factory: local SQLite files, or Turso (libSQL) in the cloud
  practice.py    50 procedural exercise generators, counting → calculus, phonics → logic gates
  quiz.py        authored banks, filtered cloze, constructed response, cards from misses
  tutor.py       "Ask the Book" — Claude tutor with rule-based Socratic fallback
  pacing.py      turns age/hours/breadth into a year-by-year roadmap, priced honestly
  library.py     Kiwix archive catalogue + background resumable downloader
  server.py      FastAPI app tying it all together
data/
  curriculum/    10 domain files · 348 concepts · 926 prerequisite edges
                 89 child-voiced lessons · 3,212 authored questions
  story/         the 19-chapter frame story
web/             book-styled single-page app (vanilla JS, no build, WCAG-AA, dark mode)
tests/           pytest regression suite (unit + HTTP layer)
content/         ZIM archives, the learner database and its rotating backups
```

Requirements: Python 3.9+ and the pinned packages in `requirements.txt`.
CI exercises Python 3.9 and the Vercel runtime pinned to Python 3.12.
`run.sh` sets up a virtualenv on first launch.

```bash
.venv/bin/python -m pytest tests/ -q
```

## Where the record lives

**Locally: nothing to configure.** The reader's whole record is a SQLite file
under `content/`, and the article cache is another one. One file, no server,
copyable to a USB stick, readable in twenty years. This is the default and the
recommended way to run the book; set no environment variables and nothing about
it has changed.

**In the cloud, that stopped working.** On a serverless host such as Vercel the
filesystem is read-only apart from `/tmp`, and `/tmp` belongs to one warm
instance for a few minutes. The hosted demo therefore **forgot its reader
between requests**: you would answer a placement quiz, the next request would
land on a different instance with an empty database, and the book would greet
you as a stranger. Nothing was corrupted — there was simply nowhere durable to
write.

**The fix is Turso** ([libSQL](https://turso.tech)), which is SQLite over the
wire: same dialect, same `?` placeholders, same `ON CONFLICT`. Set two
environment variables and every store — profile, mastery, review deck, served
papers, article cache — persists in one managed database instead of a
disposable file:

```bash
export TURSO_DATABASE_URL="libsql://your-database.turso.io"
export TURSO_AUTH_TOKEN="..."
```

On Vercel, adding the `tursocloud/database` Marketplace integration injects
both. Unset them and the book is local again, immediately: the backend is
chosen per connection, from the environment as it stands at that moment.

**Preview deployments never use the remote database.** The integration
provisions one database across Production, Preview and Development, which means
a preview built from any open pull request would otherwise boot, run
`_init_db()`, and apply *that branch's* migrations to the production reader's
record — how production once came to be running pre-migration code against a
post-migration schema. `primer/store.py` refuses the remote database whenever
`VERCEL_ENV=preview`, falling back to the ephemeral per-instance SQLite that is
the right shape for a preview anyway: empty, disposable, harmless. Set
`PRIMER_ALLOW_PREVIEW_REMOTE=1` only if the preview genuinely has a database of
its own.

**Hosted access.** A Vercel deployment requires `PRIMER_ACCESS_PASSWORD` and
accepts an optional `PRIMER_ACCESS_USERNAME` (default: `primer`). Every route
except public `/healthz` is then closed to strangers. If the password is
missing on Vercel, protected routes fail closed instead of exposing the book.

A reader who is not signed in is sent to `/sign-in` — the book's own page, in
its own paper and gold — and the credentials they give there set a signed,
HttpOnly cookie good for a month (`POST /sign-out` ends it early). The cookie
is an HMAC of the username keyed by the password, so rotating
`PRIMER_ACCESS_PASSWORD` revokes every session that was ever issued. Nothing
sends `WWW-Authenticate`: that header is what makes the browser draw its own
grey credential dialog, which is unstyleable and was the first thing a reader
met. Basic credentials are still *accepted* on every route, unadvertised, so
`curl -u` and CI need no cookie jar.

**A second reader, no Google account needed.** `PRIMER_ACCESS_USERNAME2` /
`PRIMER_ACCESS_PASSWORD2` (then `...3`, `...4`, ...) add more named
accounts to the same gate above — each is checked the same way, and each
gets its **own separate profile** (mastery, deck, streak, story) the first
time anyone signs in with it, exactly as Google sign-in does, without any
Google Cloud Console setup. The original, unsuffixed pair always resolves
to `reader_id=1`, the profile every deployment already had, so nothing
about a single-account install changes by adding this. Two people sharing
one hosted copy need nothing more than a second username and password; a
household that later wants real per-person accounts across devices can
layer Google sign-in on top (see *Google sign-in*, below) without
disturbing either static account.

All of this lives in `primer/store.py`. It is a single seam — the learner, wiki
and sittings stores each call one `connect()` — and it is deliberately
asymmetric. With no variables set it hands back a genuine `sqlite3.Connection`
with exactly the PRAGMAs the three call sites used to set for themselves; the
remote path is an adapter that presents the same interface on top of the libSQL
client, papering over the places where that client is not a DB-API driver
(no `executescript`, no `sqlite3.Row`, no cursor, no implicit transaction, its
own exception classes). Three honest caveats:

- `PRAGMA journal_mode=WAL` and `busy_timeout` are answered locally and never
  sent. Both describe a local file and a local lock; a managed database over
  HTTP has neither, and handles concurrency server-side.
- The HTTP client autocommits individual statements. Critical shared writes
  (single-use papers, mastery updates and daily effort XP) therefore use
  atomic claims or compare-and-swap retries, but a process or network failure
  can still interrupt a larger multi-statement operation between its writes.
- `PRIMER_BACKUP_DIR` and the daily rotating backups in `content/backups/` are
  page-copies of a local file and do not apply to Turso. Turso is
  provider-managed, so hosted deployments rely on its point-in-time backups.

## Google sign-in (optional, multi-reader)

Every deployment starts single-tenant: one profile, `reader_id=1`, no account
needed. Google sign-in is an inner layer *inside* the password gate above, not
a replacement for it — it lets more than one person keep a separate profile
(their own mastery, deck, streak, story) safe across devices and browsers,
under the same hosted copy. A reader who never signs in sees no difference at
all.

**To turn it on:**

1. **Google Cloud Console** — create a project, configure the OAuth consent
   screen, and create an OAuth client (type: Web application). Add both
   redirect URIs it will ever need: the production one
   (`https://yourdomain.example/auth/google/callback`) and the local one
   (`http://localhost:PORT/auth/google/callback`).
   For yourself and your family, leave the consent screen's publishing status
   as **Testing** and add each Google account to the **Test Users** list —
   Google shows no "unverified app" warning to a listed tester and no review
   is required. Moving to **Production** instead opens sign-in to any Google
   account, but shows that warning until you complete Google's full
   app-review process, which needs a live privacy policy; that process is
   deliberately out of scope here.
2. **Set the two client credentials** the Cloud Console just gave you:
   ```bash
   export GOOGLE_CLIENT_ID="....apps.googleusercontent.com"
   export GOOGLE_CLIENT_SECRET="..."
   ```
   On Vercel, add them as project environment variables. Unset,
   `/auth/google/start` answers 503 rather than a broken redirect, and the
   app is exactly as it was before this feature existed.
3. **Back up first.** The migration that adds reader accounts is additive and
   lossless — every existing row lands under `reader_id=1` — but it is still
   a schema change against a real database's history. Confirm a recent backup
   exists (`content/backups/` locally, or Turso's own point-in-time recovery
   in the cloud) before the first deploy that carries this code runs against
   production data.
4. **Claiming the original profile.** After the migration, `reader_id=1` is
   *not* auto-claimed by whoever signs in first — every fresh Google identity
   gets its own new, empty profile by default. Sign in, then use the
   **Claim this profile** action on the Account screen (re-entering
   `PRIMER_ACCESS_PASSWORD` as one-way proof of possession) to move onto the
   history the book already had. It only works once.

**Not the same thing:** verifying *site ownership* with Google Search
Console — proving to Google's crawler that you control the domain — is
unrelated to any of the above and isn't wired in yet. It needs a
verification code or HTML file that only exists after you create the
property in Search Console yourself; once you have it, adding it is a small
change (exempting the file's path from the access gate, or a meta tag on
`web/sign-in.html`, whichever method you pick).

## Design notes & honest limits

- The curriculum graph is a **spine, not a cage.** Beyond the 348 authored
  concepts, every one of Wikipedia's millions of articles is reachable by search
  and by following links — and reading any of them logs progress and can feed
  your review deck.
- **Age never grants placement credit.** Every reader starts at Stage 0. The
  server-scored placement check credits demonstrated standing as *assumed*, not
  *proven*, and those foundations can be quizzed at any time.
- **Auto-generated questions never count.** An audit put their defect rate at
  65% — mostly items solvable from grammar alone — so they were retired from
  grading entirely. A second hand audit, this time *after* the filters and on
  real article text, put the current rate at **72.5% (29 of 40, 95% CI
  57–84%)**: better than the generator was, still bad, and the reason these
  items stay unmarked. Method, sheet and limits are in
  [tools/hand-audit-cloze-2026-08.md](tools/hand-audit-cloze-2026-08.md); rerun
  it with `python3 tools/audit_cloze.py`. A third pass in 2026-08 measured 55%
  (22 of 40) after a precision round — better again, still a coin flip — and on
  that evidence the last place they appeared, the unmarked self-check for free
  reading, was **retired** rather than shipped behind a warning label. The
  generator survives only as the audit's measurement apparatus; nothing in the
  app calls it. Every one of the 348 curriculum concepts carries its own
  authored item bank, so nothing that moves mastery is machine-written.
- **Backups are same-disk until you say otherwise.** The learner record is
  copied daily into `content/backups/` on a tiered schedule (~5 daily, 4
  weekly, 12 monthly). That protects against mistakes, not against a dead
  drive: both copies are on the same disk. Set **`PRIMER_BACKUP_DIR`** to a
  path on removable or synced storage and the copies land off-disk. The server
  logs the backup location and this warning at startup, and reports it on
  `/api/state` as `backup.off_disk` — decided by comparing filesystem device
  ids, so pointing the variable at another folder on the same drive is
  correctly reported as still same-disk.
- **Knowing nothing scores like knowing nothing.** Always picking the longest
  option, the first, the second-longest, or mining the served JSON for a leaked
  answer all sit at chance and master zero of the 348 concepts. A test sits real
  papers with each strategy and fails if any of them beats a guess.
- The book has been reviewed by a standing **expert board** (educators, a
  learning scientist, a game designer, a UX designer and an engineer) against
  ten benchmarks — see [BOARD.md](BOARD.md) for the rubric, scores and change log.
- Content and archives come from Wikipedia/Wikimedia and the Kiwix project,
  under their respective licences (article text is CC BY-SA).
