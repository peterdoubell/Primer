"""The learner model: who is reading the book, and what do they know.

SQLite-backed. Tracks the reader profile, per-node mastery of the curriculum
graph, an SM-2 spaced-repetition deck built from what they learn, a reading
log of every article opened, and lightweight motivation state (XP, streaks).

Design commitments (from the review board):
- **Mastery is durable, not a snapshot.** A node is only "mastered" after two
  passing attempts at least ~2 days apart — one lucky quiz right after reading
  is not mastery. Assumed-known credit from placement is marked separately.
- **The deck feeds back into mastery.** A lapsed review lowers a node's
  strength and flags it for refresh; the SRS is the memory, not the quiz.
- **XP cannot be farmed.** Every point is tied to a graded success or a genuine
  first read, stored per-event, so reopening an article pays nothing.
- **Streaks forgive.** Local-day boundaries and a couple of auto-applied
  "freezes" mean one busy day doesn't erase months of habit.
"""

import bisect
import datetime
import functools
import json
import math
import logging
import os
import secrets
import shutil
import sqlite3
import threading
import time
from typing import Dict, List, Optional

from . import store

log = logging.getLogger("primer.learner")

_lock = threading.Lock()

DAY = 86400.0
PASS = 0.8                       # score that counts as a passing attempt
MASTERY_MIN_INTERVAL = 2 * DAY   # min gap between 1st and 2nd pass to master (12+)
# Strength is "fresh enough to count" above this. It is not a free parameter:
# 0.35 is one and a half half-lives of silence (0.5 ** 1.51 = 0.351), i.e. the
# reader has gone about 45 days without touching a newly-learned node before it
# stops opening gates — and it is the same number MAX_INTERVAL_DAYS shows its
# arithmetic against below (365 * log(0.35, 0.5) ≈ 553 days, so the longest
# schedulable interval, 500 days, still lands above the gate). Picking the gate
# and the interval cap independently is what previously let a card be correct,
# on time, and still read its node as faded; they are two views of one number.
#
# Honest limitation: both this gate and the linear half-life growth in
# _strength_now are tuned by in-house simulation against SM-2's own interval
# ladder — the criterion is internal consistency (a card reviewed on schedule
# never reads faded; a node drilled in one sitting never becomes permanent),
# not goodness-of-fit to observed recall. They are NOT fitted to an empirical
# retention dataset the way half-life regression (Settles & Meeder 2016) or an
# ACT-R activation model would be, and we do not claim the 45-day figure is a
# measured forgetting curve for any real population. Fitting one needs
# per-review recall logs at a scale this book does not yet have; until then the
# number is a defensible engineering choice, not a finding.
FRESH_GATE = 0.35
# Mastery strength decays with this half-life the *first* time something is
# learned. Each later reinforcement — another passing attempt, or a successful
# review of a card the book minted — doubles it, up to a ceiling.
#
# A flat 30 days meant a concept stopped counting about six weeks after it was
# last touched, no matter how well established it was. But SM-2 intervals grow
# past three months, so a node the reader knew *cold* decayed out between its
# own scheduled reviews, re-locking everything built on top of it. Simulated
# over six years, a strong learner's proven set never rose above twenty.
#
# Growth per reinforcement is the spacing effect, the same principle the review
# scheduler already runs on: the better you know something, the longer it lasts.
#
# It grows with the SQUARE ROOT of reinforcements and caps at a year.
#
# Two earlier shapes were both wrong in the same direction. Doubling saturated
# after about seven reviews. Linear growth at step 2.2 was supposed to fix that
# and did not: the ladder it actually produced was
#
#     r=1..7 -> 30, 96, 162, 228, 294, 360, 365 days
#
# so the ceiling still arrived at the seventh reinforcement — one week of daily
# spaced practice — which is the exact failure the paragraph above rejects.
# Fixing "everything evaporates" by making nothing evaporate is not a fix, and
# a linear law with a hard ceiling is only a slower version of doing that.
#
# Sub-linear growth is the right shape on its own merits: each additional
# spaced retrieval should buy less than the one before (diminishing returns are
# what the spacing literature actually reports), and sqrt is the cheapest law
# with that property that still rises without bound. STRENGTH_HALF_LIFE_STEP is
# now the sqrt coefficient, and the ladder it produces is
#
#     r    =  1     2     3     4     5     6     8    10    20    30    42
#     days =  30    82   104   121   135   147   169   188   259   313   365
#
# — the ceiling needs 42 spaced reinforcements, not 7, and the last few are
# worth a fortnight each rather than two months each.
#
# The coefficient is not free: it is bounded below by SM-2's own ladder. A card
# reviewed exactly on schedule must never let its node read as faded, i.e. the
# scheduled interval must stay under half_life * log(FRESH_GATE, 0.5) = 1.515
# half-lives at every rung. That is what ties MAX_INTERVAL_DAYS to this law —
# see the comment there. 1.75 clears every rung with margin, verified by
# simulation and by an end-to-end on-schedule review test.
#
# A reinforcement also has to be *spaced* to count. Massed repetition does not
# build durable memory, and letting it do so here meant a node could be made
# permanent in a single sitting.
# Placement credit is not a memory, so decaying it like one was a category
# error with a user-visible cost. `seed_assumed` writes strength 0.8 at one
# reinforcement, which crosses the 0.35 gate at day 36: five weeks after a
# placement interview, every node it had credited silently re-locked, the
# roadmap re-inflated, and `mastery_detail` reported mastered/proven/assumed/
# faded ALL false — a credited node became indistinguishable from one the
# reader had never touched, with no message to the reader at any point.
#
# The credit says "we believe you already know this, and we have not tested
# you". Nothing about the passage of time makes that belief *less* true; only
# a test can. So the credit holds the gate open at exactly the gate for this
# long, and then becomes explicitly STALE rather than quietly vanishing: gates
# close, but `mastery_detail` names the state (`assumed_stale`) so the book can
# say "your placement credit has expired — sit the interview again" instead of
# showing a lesson the reader passed months ago as if it were new.
#
# Six months is one school term either side of a holiday: long enough that a
# reader who steps away over a summer comes back to the level they were placed
# at, short enough that a two-year-old placement is not still opening doors.
ASSUMED_CREDIT_LIFE = 180 * DAY
RELEARN_DELAY = 10 * 60          # a new card waits before it can be cashed
STRENGTH_HALF_LIFE = 30 * DAY
STRENGTH_HALF_LIFE_MAX = 365 * DAY
STRENGTH_HALF_LIFE_STEP = 1.75   # coefficient on sqrt(reinforcements - 1)
REINFORCE_MIN_GAP = DAY
# Distributed-practice research (e.g. Toppino 1991; Vlach & Sandhofer 2012)
# finds young children benefit from spacing measured in hours, not days —
# their natural practice cycle is several short sessions across one day, and
# requiring a full day between reinforcements under-counts genuine spaced
# repetition for a 4-year-old the way it would not for a teenager. A single
# DAY-wide gap was applied to every reader regardless of age; this scales the
# minimum gap down for younger readers while keeping it long enough that
# massed same-sitting repetition still can't buy a reinforcement.
REINFORCE_MIN_GAP_BY_AGE = [
    (7, 3 * 3600),    # under 7: three hours
    (12, 8 * 3600),   # 7-11: eight hours
    (99, DAY),        # 12+: a full day
]


def _half_life(reinforcements: "float | None") -> float:
    """Decay half-life in seconds for a node with this many reinforcements.

    One function so the law lives in one place: `_strength_now` decides with
    it, and the tests that assert the ladder read it rather than re-deriving
    an algebraic copy that can silently drift from the real one.

    `reinforcements` may be fractional — a self-graded success from a reader
    whose calibration is poor pays a partial reinforcement (see
    `review_card`), and a partial payment must buy a partial half-life.
    """
    r = max(0.0, float(reinforcements if reinforcements else 1) - 1.0)
    return min(STRENGTH_HALF_LIFE * (1 + STRENGTH_HALF_LIFE_STEP * math.sqrt(r)),
               STRENGTH_HALF_LIFE_MAX)


# The clock the reader is timed by is the reader's own browser, which makes it
# untrusted input twice over: a hostile client can post anything, and an honest
# one records the twenty minutes a reader spent answering the door mid-quiz.
# Both are handled the same way — a per-item reading outside this band is not a
# measurement of anything and is discarded rather than clamped, because
# clamping a forty-minute interruption to five minutes would still poison the
# median with a number nobody spent.
PACE_ITEM_MIN_SECONDS = 2.0
PACE_ITEM_MAX_SECONDS = 300.0


def _per_item_seconds(seconds: Optional[float], items: int) -> Optional[float]:
    """Seconds per item, or None if the reading is not usable."""
    try:
        total = float(seconds)
    except (TypeError, ValueError):
        return None
    n = int(items or 0)
    if n <= 0 or not math.isfinite(total):
        return None
    per = total / n
    if per < PACE_ITEM_MIN_SECONDS or per > PACE_ITEM_MAX_SECONDS:
        return None
    return round(per, 2)


def _reinforce_min_gap(age: Optional[float]) -> float:
    if age is None:
        return REINFORCE_MIN_GAP
    for ceiling, gap in REINFORCE_MIN_GAP_BY_AGE:
        if age < ceiling:
            return gap
    return REINFORCE_MIN_GAP


# The same distributed-practice argument, applied to the other two places that
# hard-code a spacing in days. It was inconsistent to shorten the reinforcement
# gap for a 5-year-old (above) while still making them wait two full days to
# prove a node and a full day for their first review step: if a young child's
# natural practice cycle is several short sessions across a day, then a day is
# a *long* gap for them, and both the proving window and the SM-2 learning
# steps were quietly demanding adult-scale spacing from readers the gap fix had
# already agreed shouldn't be held to it.
#
# Rather than invent a second age table that could drift out of step with the
# first, this is expressed as the ratio of that table's gap to the adult gap:
# under-7s get 1/8 of the adult spacing, 7-11s get 1/3, 12+ are unscaled. One
# table, one literature, three consumers.
def _age_spacing_scale(age: Optional[float]) -> float:
    return _reinforce_min_gap(age) / DAY


def _mastery_min_interval(age: Optional[float]) -> float:
    """Minimum gap between a node's two proving passes, age-scaled.

    2 days for 12+, 16 hours for 7-11, 6 hours for under-7s — still long
    enough that two attempts in one sitting can never prove a node, which is
    the property MASTERY_MIN_INTERVAL exists to guarantee.
    """
    return MASTERY_MIN_INTERVAL * _age_spacing_scale(age)


# SM-2's first two intervals (1 day, then 6 days) are the ladder's learning
# steps, and they carry the same age assumption. Scaled by the same factor a
# young reader gets 3 hours then 18 hours — sub-day learning steps, which is
# what every modern SRS actually does for new material anyway. Later intervals
# are not scaled: once a card is on the multiplicative ladder its spacing is
# set by demonstrated ease, not by the reader's age.
SM2_FIRST_INTERVAL = 1.0
SM2_SECOND_INTERVAL = 6.0


def _sm2_first_steps(age: Optional[float]) -> "tuple":
    scale = _age_spacing_scale(age)
    return SM2_FIRST_INTERVAL * scale, SM2_SECOND_INTERVAL * scale
# SM-2's interval is unbounded — a well-remembered card reaches 1,225 days at
# its 7th review and 12,934 at its 9th. Strength decay is capped at a 365-day
# half-life, so a card scheduled that far out left its node reading unproven
# for the whole gap between reviews: correct, on time, and still faded. This is
# the largest gap a card may go, chosen so a fresh strength of 1.0 cannot decay
# below the 0.35 gate before the next review.
#
# The binding constraint is not the ceiling half-life but the half-life the
# reader has actually *reached* by the time SM-2 first schedules this far out.
# Under the old linear growth law the two happened to coincide, so the cap was
# set against the 365-day ceiling (365 * log(0.35, 0.5) ≈ 553 days) and 500 was
# comfortable. Sub-linear growth breaks that coincidence: a card reaches its
# 6th review around the 7th reinforcement, where the half-life is 159 days and
# only 240 days of gap survive above the gate. 200 days clears that rung — and
# every later one, since the cap holds the interval flat while reinforcements
# keep lengthening the half-life. Verified by simulation and by the end-to-end
# on-schedule review test.
MAX_INTERVAL_DAYS = 200
STREAK_FREEZES = 2               # single-day gaps auto-bridged in a streak
# A spent freeze is forgiven this many days later — the budget renews, it is
# not a lifetime debt. Without this, a reader with a genuinely excellent
# eleven-month run and two sick days near its start showed "0 rest days left"
# every day since (nothing ever earns it back), and a single fresh missed day
# eleven months later then truncated their CURRENT streak by over a month —
# not because that new miss was expensive on its own, but because paying for
# it left no budget to also afford the two sick days' worth of debt still on
# the books from a year prior. best_streak_days(), which is not anchored to
# "today", could simply choose a window that started after the old debt and
# was unaffected — so the same connected history read as ~360 days one way
# and ~325 the other, and the gap between the two only widens with a longer
# history. A month is long enough that "getting sick for a day" and "having a
# rough day eleven months later" are treated as what they are: two unrelated
# events, not one that permanently taxes the other.
STREAK_FREEZE_RENEW_DAYS = 30

STAGE_NAMES = ["Seedling", "Sprout", "Sapling", "Tree", "Grove", "Forest"]
STAGE_SPAN = [
    "ages 3–5 · preschool & kindergarten",
    "ages 6–9 · primary school",
    "ages 10–13 · middle school",
    "ages 14–17 · secondary school",
    "undergraduate level",
    "graduate level & the frontier",
]
STAGE_TITLES = [
    "Curious Seedling", "Bright Sprout", "Growing Sapling",
    "Standing Tree", "Sheltering Grove", "Whole Forest",
]


class LearnerStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _conn(self):
        # Local files by default, Turso when TURSO_DATABASE_URL is set. The
        # PRAGMAs and the by-name row access moved into store.connect() rather
        # than being dropped — see primer/store.py.
        return store.connect(self.db_path, named_rows=True)

    def _init_db(self):
        with _lock, self._conn() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS profile (
                    reader_id INTEGER PRIMARY KEY,
                    name TEXT, age REAL, hours_per_week REAL,
                    breadth TEXT, stage INTEGER, domains TEXT,
                    created_at REAL, settings TEXT DEFAULT '{}'
                );
                CREATE TABLE IF NOT EXISTS mastery (
                    reader_id INTEGER NOT NULL DEFAULT 1,
                    node_id TEXT,
                    level REAL DEFAULT 0,          -- 0..1 exponential moving avg
                    attempts INTEGER DEFAULT 0,
                    passes INTEGER DEFAULT 0,      -- attempts scoring >= PASS
                    first_pass_at REAL,
                    last_pass_at REAL,
                    strength REAL DEFAULT 0,       -- decays; refreshed by review
                    last_seen REAL,
                    assumed INTEGER DEFAULT 0,     -- credited by placement, untested
                    mastered_at REAL,
                    reinforcements INTEGER DEFAULT 1,
                    reinforced_at REAL,
                    first_mastered_at REAL,
                    PRIMARY KEY (reader_id, node_id)
                );
                CREATE TABLE IF NOT EXISTS srs_cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reader_id INTEGER NOT NULL DEFAULT 1,
                    front TEXT, back TEXT, node_id TEXT, article TEXT,
                    ef REAL DEFAULT 2.5, interval REAL DEFAULT 0,
                    reps INTEGER DEFAULT 0, lapses INTEGER DEFAULT 0,
                    -- Cumulative graded reviews. `reps` is SM-2's ladder
                    -- position and is reset to 0 on every lapse, so it cannot
                    -- serve as a count of how much reviewing has happened.
                    reviews INTEGER DEFAULT 0,
                    due REAL, created_at REAL, origin TEXT DEFAULT 'book',
                    UNIQUE(reader_id, front, node_id)
                );
                CREATE TABLE IF NOT EXISTS reading_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT, opened_at REAL, seconds REAL DEFAULT 0,
                    reader_id INTEGER DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT, payload TEXT, at REAL, xp INTEGER DEFAULT 0,
                    reader_id INTEGER DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS attempt_effort_claims (
                    reader_id INTEGER NOT NULL DEFAULT 1,
                    node_id TEXT NOT NULL,
                    local_day TEXT NOT NULL,
                    claimed_at REAL NOT NULL,
                    PRIMARY KEY (reader_id, node_id, local_day)
                );
                CREATE TABLE IF NOT EXISTS placement (
                    reader_id INTEGER NOT NULL DEFAULT 1,
                    domain TEXT NOT NULL,
                    stage INTEGER, asked TEXT DEFAULT '[]', done INTEGER DEFAULT 0,
                    settled_at REAL,
                    PRIMARY KEY (reader_id, domain)
                );
                CREATE INDEX IF NOT EXISTS idx_events_at ON events(at);
                CREATE TABLE IF NOT EXISTS burned(
                    reader_id INTEGER NOT NULL DEFAULT 1,
                    node_id TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    at REAL NOT NULL,
                    PRIMARY KEY (reader_id, node_id, fingerprint)
                );
                CREATE INDEX IF NOT EXISTS idx_burned_node ON burned(node_id, at);
                CREATE INDEX IF NOT EXISTS idx_cards_due ON srs_cards(due);
                CREATE INDEX IF NOT EXISTS idx_reading_title ON reading_log(title);
                CREATE TABLE IF NOT EXISTS readers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    google_sub TEXT UNIQUE,
                    email TEXT, name TEXT, created_at REAL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    reader_id INTEGER, created_at REAL, expires_at REAL
                );
                CREATE INDEX IF NOT EXISTS idx_sessions_reader ON sessions(reader_id);
                """
            )
            # Lightweight migrations for databases created before these columns.
            # One-time backfills for rows written before a column existed. A
            # migration that adds a column is only half the job when live code
            # reads it: `strength` and `last_seen` defaulted to 0/NULL, and once
            # `proven_set` and `gate_map` became decay-aware, every node a
            # pre-decay reader had genuinely proven silently re-locked.
            cols = {r[1] for r in c.execute("PRAGMA table_info(mastery)")}
            event_cols = {r[1] for r in c.execute("PRAGMA table_info(events)")}
            card_cols = {r[1] for r in c.execute("PRAGMA table_info(srs_cards)")}
            for col, ddl in [
                ("passes", "ALTER TABLE mastery ADD COLUMN passes INTEGER DEFAULT 0"),
                ("first_pass_at", "ALTER TABLE mastery ADD COLUMN first_pass_at REAL"),
                ("last_pass_at", "ALTER TABLE mastery ADD COLUMN last_pass_at REAL"),
                ("strength", "ALTER TABLE mastery ADD COLUMN strength REAL DEFAULT 0"),
                ("last_seen", "ALTER TABLE mastery ADD COLUMN last_seen REAL"),
                ("assumed", "ALTER TABLE mastery ADD COLUMN assumed INTEGER DEFAULT 0"),
                ("lapses", "ALTER TABLE srs_cards ADD COLUMN lapses INTEGER DEFAULT 0"),
                ("origin", "ALTER TABLE srs_cards ADD COLUMN origin TEXT DEFAULT 'book'"),
                ("reviews", "ALTER TABLE srs_cards ADD COLUMN reviews INTEGER DEFAULT 0"),
                ("reinforcements", "ALTER TABLE mastery ADD COLUMN reinforcements INTEGER DEFAULT 1"),
                ("reinforced_at", "ALTER TABLE mastery ADD COLUMN reinforced_at REAL"),
                ("first_mastered_at", "ALTER TABLE mastery ADD COLUMN first_mastered_at REAL"),
                ("xp", "ALTER TABLE events ADD COLUMN xp INTEGER DEFAULT 0"),
            ]:
                present = cols | card_cols | event_cols
                if col not in present:
                    try:
                        c.execute(ddl)
                    except sqlite3.OperationalError:
                        pass
            # When a placement was settled — needed so a settled domain can be
            # re-opened for re-measurement after a cooling period rather than
            # one noisy sitting fixing the reader's level forever.
            pl_cols = {r[1] for r in c.execute("PRAGMA table_info(placement)")}
            for col, ddl in [
                ("settled_at", "ALTER TABLE placement ADD COLUMN settled_at REAL"),
            ]:
                if col not in pl_cols:
                    try:
                        c.execute(ddl)
                    except sqlite3.OperationalError:
                        pass
            # Re-read after the migrations above so the backfills can rely on them.
            cols = {r[1] for r in c.execute("PRAGMA table_info(mastery)")}
            for ddl in [
                # A node with `mastered_at` set was proven under the old rules;
                # give it full strength as of its last pass rather than letting
                # decay read it as forgotten the moment the reader upgrades.
                """UPDATE mastery SET strength = 1.0
                     WHERE mastered_at IS NOT NULL AND COALESCE(strength, 0) = 0""",
                """UPDATE mastery SET last_seen = COALESCE(last_pass_at, mastered_at)
                     WHERE last_seen IS NULL AND mastered_at IS NOT NULL""",
                """UPDATE mastery SET reinforcements = MAX(1, COALESCE(passes, 1))
                     WHERE reinforcements IS NULL""",
                # Best-effort backfill: a row currently mastered was earned at
                # some point, so its history should not start blank. A row that
                # had already lost mastery before this migration ran has no
                # trace of when it was first earned — that record was already
                # gone before the fix, and cannot be recovered.
                """UPDATE mastery SET first_mastered_at = mastered_at
                     WHERE first_mastered_at IS NULL AND mastered_at IS NOT NULL
                       AND assumed = 0""",
                # `reviews` is new; every existing card has a history that
                # predates it. reps+lapses is the best lower bound available
                # (it undercounts a card that lapsed and then climbed again,
                # because the lapse zeroed reps) — but a lower bound on the
                # denominator of a *rate* is the safe direction only if it is
                # applied once, at migration, rather than left to compound.
                """UPDATE srs_cards SET reviews = COALESCE(reps, 0) + COALESCE(lapses, 0)
                     WHERE COALESCE(reviews, 0) = 0""",
            ]:
                try:
                    c.execute(ddl)
                except sqlite3.OperationalError:
                    pass
            # The reservation table replaces a read-then-insert query over
            # events.  Preserve today's already-spent slots when an existing
            # installation first opens this schema, or the first attempt after
            # an upgrade would be paid twice. Older days can never be claimed
            # again and need no migration.
            c.execute(
                """INSERT OR IGNORE INTO attempt_effort_claims(
                       node_id, local_day, claimed_at)
                   SELECT json_extract(payload, '$.node'),
                          date(at, 'unixepoch', 'localtime'), MIN(at)
                     FROM events
                    WHERE kind='attempt' AND at>=?
                      AND json_extract(payload, '$.node') IS NOT NULL
                      AND json_extract(payload, '$.score') >= 0.5
                    GROUP BY json_extract(payload, '$.node'),
                             date(at, 'unixepoch', 'localtime')""",
                (_local_midnight(time.time()),))

            # ---- multi-tenant: fold reader_id into every table's identity ----
            #
            # `profile`, `mastery`, `srs_cards`, `attempt_effort_claims`,
            # `placement` and `burned` each have a PRIMARY KEY or UNIQUE
            # constraint that predates readers existing at all — `node_id TEXT
            # PRIMARY KEY` on `mastery`, for instance, meant only one row could
            # ever exist per node, globally.  SQLite cannot ALTER a PRIMARY
            # KEY or UNIQUE constraint in place; widening one means rebuilding
            # the table.  `reading_log` and `events` use a plain autoincrement
            # id with no such constraint, so a bare ADD COLUMN is enough for
            # them — see below.
            self._widen_table_to_reader(
                c, "profile",
                """CREATE TABLE IF NOT EXISTS profile (
                    reader_id INTEGER PRIMARY KEY,
                    name TEXT, age REAL, hours_per_week REAL,
                    breadth TEXT, stage INTEGER, domains TEXT,
                    created_at REAL, settings TEXT DEFAULT '{}'
                )""",
                ["name", "age", "hours_per_week", "breadth", "stage",
                 "domains", "created_at", "settings"])
            self._widen_table_to_reader(
                c, "mastery",
                """CREATE TABLE IF NOT EXISTS mastery (
                    reader_id INTEGER NOT NULL DEFAULT 1,
                    node_id TEXT,
                    level REAL DEFAULT 0, attempts INTEGER DEFAULT 0,
                    passes INTEGER DEFAULT 0,
                    first_pass_at REAL, last_pass_at REAL,
                    strength REAL DEFAULT 0, last_seen REAL,
                    assumed INTEGER DEFAULT 0, mastered_at REAL,
                    reinforcements INTEGER DEFAULT 1, reinforced_at REAL,
                    first_mastered_at REAL,
                    PRIMARY KEY (reader_id, node_id)
                )""",
                ["node_id", "level", "attempts", "passes", "first_pass_at",
                 "last_pass_at", "strength", "last_seen", "assumed",
                 "mastered_at", "reinforcements", "reinforced_at",
                 "first_mastered_at"])
            self._widen_table_to_reader(
                c, "attempt_effort_claims",
                """CREATE TABLE IF NOT EXISTS attempt_effort_claims (
                    reader_id INTEGER NOT NULL DEFAULT 1,
                    node_id TEXT NOT NULL, local_day TEXT NOT NULL,
                    claimed_at REAL NOT NULL,
                    PRIMARY KEY (reader_id, node_id, local_day)
                )""",
                ["node_id", "local_day", "claimed_at"])
            self._widen_table_to_reader(
                c, "placement",
                """CREATE TABLE IF NOT EXISTS placement (
                    reader_id INTEGER NOT NULL DEFAULT 1,
                    domain TEXT NOT NULL,
                    stage INTEGER, asked TEXT DEFAULT '[]',
                    done INTEGER DEFAULT 0, settled_at REAL,
                    PRIMARY KEY (reader_id, domain)
                )""",
                ["domain", "stage", "asked", "done", "settled_at"])
            self._widen_table_to_reader(
                c, "burned",
                """CREATE TABLE IF NOT EXISTS burned (
                    reader_id INTEGER NOT NULL DEFAULT 1,
                    node_id TEXT NOT NULL, fingerprint TEXT NOT NULL,
                    at REAL NOT NULL,
                    PRIMARY KEY (reader_id, node_id, fingerprint)
                )""",
                ["node_id", "fingerprint", "at"])
            # srs_cards keeps its own autoincrement `id` — that value is a real
            # identifier (review_card looks cards up by it), not a throwaway,
            # so it has to survive the rebuild unchanged rather than being
            # reassigned. Only the UNIQUE constraint widens.
            srs_cols = {r[1] for r in c.execute("PRAGMA table_info(srs_cards)")}
            srs_exists = bool(c.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                ("srs_cards",)).fetchone())
            if srs_exists and "reader_id" not in srs_cols:
                c.execute("ALTER TABLE srs_cards RENAME TO srs_cards_legacy")
            c.execute(
                """CREATE TABLE IF NOT EXISTS srs_cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reader_id INTEGER NOT NULL DEFAULT 1,
                    front TEXT, back TEXT, node_id TEXT, article TEXT,
                    ef REAL DEFAULT 2.5, interval REAL DEFAULT 0,
                    reps INTEGER DEFAULT 0, lapses INTEGER DEFAULT 0,
                    reviews INTEGER DEFAULT 0,
                    due REAL, created_at REAL, origin TEXT DEFAULT 'book',
                    UNIQUE(reader_id, front, node_id)
                )""")
            if c.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                    ("srs_cards_legacy",)).fetchone():
                c.execute(
                    """INSERT OR IGNORE INTO srs_cards
                           (id, reader_id, front, back, node_id, article, ef,
                            interval, reps, lapses, reviews, due, created_at,
                            origin)
                       SELECT id, 1, front, back, node_id, article, ef,
                              interval, reps, lapses, reviews, due,
                              created_at, origin
                         FROM srs_cards_legacy""")

            # reading_log/events keep their autoincrement id and never had a
            # natural-key collision risk, so a plain column is enough.
            rl_cols = {r[1] for r in c.execute("PRAGMA table_info(reading_log)")}
            if "reader_id" not in rl_cols:
                try:
                    c.execute(
                        "ALTER TABLE reading_log ADD COLUMN reader_id "
                        "INTEGER DEFAULT 1")
                except sqlite3.OperationalError:
                    pass
            ev_cols2 = {r[1] for r in c.execute("PRAGMA table_info(events)")}
            if "reader_id" not in ev_cols2:
                try:
                    c.execute(
                        "ALTER TABLE events ADD COLUMN reader_id "
                        "INTEGER DEFAULT 1")
                except sqlite3.OperationalError:
                    pass
            # Deferred to here rather than the top-of-file script: on an
            # existing (pre-migration) database, events/reading_log still
            # lack reader_id at the point that script runs, so an index on it
            # there would fail before the ADD COLUMN above ever had a chance
            # to run.
            c.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_reader "
                "ON events(reader_id)")
            c.execute(
                "CREATE INDEX IF NOT EXISTS idx_reading_reader "
                "ON reading_log(reader_id)")

            # The one reader this database has ever had is not auto-claimed by
            # whoever signs in first — see the Account screen's claim flow.
            # Creating the row here (id=1, unclaimed) just gives every other
            # reader_id=1 row backfilled above a place to belong; it grants no
            # access on its own, since `readers.google_sub IS NULL` matches no
            # Google sign-in.
            c.execute(
                "INSERT OR IGNORE INTO readers(id, google_sub, email, name, "
                "created_at) VALUES (1, NULL, NULL, NULL, ?)",
                (time.time(),))

    def _widen_table_to_reader(self, c, table, create_sql, legacy_cols):
        """Fold `reader_id` into a table whose PRIMARY KEY/UNIQUE constraint
        cannot include it without a rebuild — see the migration block above
        for which tables need this and why.

        Rebuilt as a rename-forward, not a drop-and-recreate: over Turso's
        HTTP transport every statement autocommits on its own — there is no
        multi-statement transaction to hold one open across (see
        store.py `_LibsqlConnection._target`) — so a CREATE/INSERT/DROP/RENAME
        sequence that a cold-started serverless instance can be killed in the
        middle of would risk losing the table outright if DROP ran before
        RENAME finished. Renaming the OLD table out of the way first instead
        means every step here is independently safe to retry: the old data is
        never destroyed, only ever copied, and an interrupted attempt is
        simply resumed by the next process's own `_init_db()` — there is no
        cross-run state to track beyond what `sqlite_master`/`PRAGMA
        table_info` already show. The `_legacy` table is never dropped
        automatically; keeping it costs nothing and undoing a mistake here
        without it would cost everything.
        """
        legacy = table + "_legacy"
        cols = {r[1] for r in c.execute("PRAGMA table_info(%s)" % table)}
        exists = bool(c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,)).fetchone())
        if exists and "reader_id" not in cols:
            c.execute("ALTER TABLE %s RENAME TO %s" % (table, legacy))
        c.execute(create_sql)
        legacy_exists = bool(c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (legacy,)).fetchone())
        if legacy_exists:
            col_list = ", ".join(legacy_cols)
            c.execute(
                "INSERT OR IGNORE INTO %s (reader_id, %s) "
                "SELECT 1, %s FROM %s"
                % (table, col_list, col_list, legacy))

    # ---------- profile ----------

    def get_profile(self, reader_id: int = 1) -> Optional[Dict]:
        """The reader, with the two numbers that always ride along.

        All three reads share one connection. They used to be three: the row,
        then `total_xp()`, then `streak_days()`, each opening and closing its
        own. That is nearly free against a local file and emphatically not
        free against Turso, where a connection is an HTTPS client and every
        statement is a round trip — and get_profile() is on the path of almost
        every route the reader touches. Same queries, same order, same
        answers; one connection instead of three.
        """
        with _lock, self._conn() as c:
            row = c.execute("SELECT * FROM profile WHERE reader_id=?",
                            (reader_id,)).fetchone()
            if not row:
                return None
            xp = self._total_xp(c, reader_id)
            day_rows = self._streak_day_rows(c, reader_id)
        p = dict(row)
        p["domains"] = json.loads(p["domains"] or "[]")
        p["settings"] = json.loads(p["settings"] or "{}")
        s = min(int(p["stage"] or 0), 5)
        p["stage_name"] = STAGE_NAMES[s]
        p["stage_span"] = STAGE_SPAN[s]
        p["title"] = STAGE_TITLES[s]
        p["xp"] = xp
        p["streak"] = _streak_walk_from_rows(day_rows, _local_day(time.time()))[0]
        return p

    def save_profile(self, name: str, age: float, hours_per_week: float,
                     breadth: str, stage: int, domains: List[str],
                     settings: Optional[Dict] = None,
                     reader_id: int = 1) -> Dict:
        # The COALESCE below exists so a caller who only means to change
        # name/age/domains — POST /api/profile, which never passes settings
        # at all — leaves story_chapter_id, theme, and every other reader
        # preference untouched. It only works if a real SQL NULL reaches
        # `excluded.settings` when the caller omitted settings; serializing
        # `settings or {}` before binding turned every omission into the
        # JSON string "{}", which is never NULL to SQL, so COALESCE always
        # picked the new (empty) value and silently wiped every existing
        # setting on every single profile save — including story_chapter_id,
        # which meant any domain change rewound the reader's story position
        # and, since nothing capped re-earning an already-earned chapter,
        # opened a wipe-then-replay path to unlimited chapter XP. Bind an
        # actual NULL when the caller means "leave settings alone"; bind the
        # JSON only when the caller passed an explicit dict (even `{}`,
        # which now correctly means "clear settings", not "I forgot to
        # pass any").
        payload = None if settings is None else json.dumps(settings)
        with _lock, self._conn() as c:
            c.execute(
                """INSERT INTO profile(reader_id, name, age, hours_per_week, breadth, stage, domains, created_at, settings)
                   VALUES(?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(reader_id) DO UPDATE SET name=excluded.name, age=excluded.age,
                     hours_per_week=excluded.hours_per_week, breadth=excluded.breadth,
                     stage=excluded.stage, domains=excluded.domains,
                     settings=COALESCE(excluded.settings, profile.settings)""",
                (reader_id, name, age, hours_per_week, breadth, stage, json.dumps(domains),
                 time.time(), payload),
            )
        return self.get_profile(reader_id)

    @staticmethod
    def stage_for_age(age: float) -> int:
        if age < 6:
            return 0
        if age < 10:
            return 1
        if age < 14:
            return 2
        if age < 18:
            return 3
        return 4

    # ---------- mastery ----------

    @staticmethod
    def _strength_now(strength: float, last_seen: Optional[float], now: float,
                      reinforcements: int = 1) -> float:
        if not last_seen or strength <= 0:
            return strength
        half_life = _half_life(reinforcements)
        return strength * (0.5 ** ((now - last_seen) / half_life))

    @classmethod
    def _standing_strength(cls, r, now: float) -> float:
        """Decay-aware strength, with untested placement credit held at the gate.

        Every view that *decides* something reads this rather than
        `_strength_now` directly, so "is this node still standing?" has one
        answer. The row must carry `assumed`; see ASSUMED_CREDIT_LIFE for why
        placement credit is held rather than decayed, and `_assumed_stale` for
        what happens when the holding period runs out.
        """
        s = cls._strength_now(r["strength"] or 0, r["last_seen"], now, r["reinforcements"])
        if cls._on_credit(r) and not cls._assumed_stale(r, now):
            return max(s, FRESH_GATE)
        return s

    @staticmethod
    def _on_credit(r) -> bool:
        """True for a node standing on placement credit and nothing else.

        `assumed` alone is not enough: a node credited by placement and since
        passed once (but not yet twice-and-spaced) still carries the flag, and
        that node has real evidence behind it which must be allowed to fade
        normally. The hold is for nodes the book has never actually tested.
        """
        keys = r.keys()
        passes = (r["passes"] if "passes" in keys else 0) or 0
        return bool(r["assumed"]) and passes == 0

    @classmethod
    def _assumed_stale(cls, r, now: float) -> bool:
        """True when placement credit has outlived its holding period."""
        if not cls._on_credit(r):
            return False
        seen = r["last_seen"]
        return bool(seen) and (now - seen) >= ASSUMED_CREDIT_LIFE

    def mastery_map(self, reader_id: int = 1) -> Dict[str, float]:
        """Raw EMA level per node — a soft *display* signal, and only that.

        `level` never fades by design: the asymmetric EMA in `_apply_attempt`
        (0.4 gain / 0.25 loss, plus max() on passes) makes it a ratchet-ish
        record of the best performance the reader has demonstrated, which is
        the right thing for a progress bar to remember. But it is therefore
        NOT a statement of current retention — a node can show level 0.9 here
        years after its strength decayed to nothing. Anything that *decides*
        (gates, pacing, headlines, "is this still known?") must read the
        decay-aware views instead: `gate_map` for unlock logic, `proven_set`/
        `mastered_set` for standing mastery, `_strength_now` for freshness.
        Display code that shows this number next to a decayed strength should
        label it as "best level reached", not "current mastery" — the two
        diverge on purpose, and presenting the ratchet as current state is
        exactly the misuse the gates were rebuilt to prevent.
        """
        with _lock, self._conn() as c:
            rows = c.execute("SELECT node_id, level FROM mastery WHERE reader_id=?",
                            (reader_id,)).fetchall()
        return {r["node_id"]: r["level"] for r in rows}

    def mastered_set(self, reader_id: int = 1) -> set:
        """Nodes currently standing as mastered — earned or assumed, not faded.

        Decay applies here for the same reason it applies to `proven_set` and
        `gate_map`: three functions answering one question three different ways
        put `proven: false`, `mastered: true` and `mastery_detail.proven: true`
        in a single response body.
        """
        now = time.time()
        with _lock, self._conn() as c:
            rows = c.execute(
                """SELECT node_id, strength, last_seen, reinforcements, assumed, passes
                   FROM mastery WHERE reader_id=? AND mastered_at IS NOT NULL""",
                (reader_id,)).fetchall()
        return {r["node_id"] for r in rows
                if self._standing_strength(r, now) >= FRESH_GATE}

    def gate_map(self, reader_id: int = 1) -> Dict[str, float]:
        """Map for the curriculum's unlock/gate logic: 1.0 for genuinely
        mastered nodes, otherwise the raw level capped below the 0.8 gate so a
        not-yet-mastered node can never open the next one.

        Mastery that has decayed below half strength no longer counts as open —
        forgotten foundations re-lock what they used to unlock, until refreshed.
        Untested placement credit is held open for ASSUMED_CREDIT_LIFE and then
        closes as *stale*, which the book reports rather than merely enacting.
        """
        now = time.time()
        with _lock, self._conn() as c:
            rows = c.execute(
                "SELECT node_id, level, mastered_at, strength, last_seen, reinforcements, "
                "assumed, passes FROM mastery WHERE reader_id=?", (reader_id,)).fetchall()
        out = {}
        for r in rows:
            if r["mastered_at"] is not None:
                s = self._standing_strength(r, now)
                out[r["node_id"]] = 1.0 if s >= FRESH_GATE else min(r["level"], 0.79)
            else:
                out[r["node_id"]] = min(r["level"], 0.79)
        return out

    def passed_set(self, reader_id: int = 1) -> set:
        """Nodes with at least one genuine passing attempt (not placement).

        Decay applies here for the same reason it applies to `proven_set` and
        `gate_map` — and it is easy to miss that it must, because this set is
        the *looser* of the two the story gate consults ("a lesson the reader
        was placed past needs one honest pass, not two"). Looser is not the
        same as permanent. `passes` alone never regresses for a node that was
        never mastered: `_apply_attempt` clamps it back only inside its
        `mastered_at is not None` branch, so a node passed once and then
        failed outright keeps `passes = 1` forever. Without the freshness
        check, a reader who passed a lesson once and has since failed it —
        with `gate_map` re-locking its successors and `mastery_detail`
        reporting `proven: false` — could still turn the page on it, and
        collect the chapter's XP, repeatably at any depth of forgetting.
        """
        now = time.time()
        with _lock, self._conn() as c:
            rows = c.execute(
                """SELECT node_id, strength, last_seen, reinforcements
                   FROM mastery WHERE reader_id=? AND passes >= 1""",
                (reader_id,)).fetchall()
        return {r["node_id"] for r in rows
                if self._strength_now(r["strength"] or 0, r["last_seen"], now,
                                      r["reinforcements"]) >= FRESH_GATE}

    def mastery_detail(self, node_id: str, reader_id: int = 1) -> Dict:
        """What this node still needs, in terms the book can explain."""
        with _lock, self._conn() as c:
            r = c.execute(
                """SELECT level, passes, first_pass_at, mastered_at, assumed,
                          strength, last_seen, reinforcements, first_mastered_at
                   FROM mastery WHERE reader_id=? AND node_id=?""",
                (reader_id, node_id)).fetchone()
            prof_row = c.execute("SELECT age FROM profile WHERE reader_id=?",
                                 (reader_id,)).fetchone()
        # Same age-scaled window `_apply_attempt` will actually apply — if the
        # book tells a 5-year-old "come back in two days" while the check says
        # six hours, the explanation is wrong in the direction that costs the
        # reader a day and a half of credit they had already earned.
        prove_gap = _mastery_min_interval(prof_row["age"] if prof_row else None)
        if not r:
            return {"passes": 0, "passes_needed": 2, "ready_at": None,
                    "mastered": False, "proven": False, "assumed": False,
                    "assumed_stale": False, "ever_proven": False, "faded": False}
        ready_at = None
        if r["first_pass_at"]:
            ready = r["first_pass_at"] + prove_gap
            ready_at = ready if ready > time.time() else None
        now = time.time()
        fresh = self._standing_strength(r, now) >= FRESH_GATE
        stale_credit = self._assumed_stale(r, now)
        # Four words, four distinct states, and every route must use them the
        # same way: `proven` is earned and current, `ever_proven` is earned at
        # some point, `faded` is earned but gone quiet, `assumed` is credited by
        # age or placement and never earned at all.
        #
        # These four lines are deliberately the same expressions /api/curriculum
        # computes over proven_set()/ever_proven_set()/gate_map(), in the same
        # order, because every time this dict has re-derived one of them its own
        # way the two routes have ended up telling different stories about one
        # node in a single response body. Twice already: `assumed` read the raw
        # column (credit given, not credit standing), and `ever_proven`/`faded`
        # hung off `mastered_at` — which is CLEARED the moment a mastered node is
        # failed on a re-sitting. So a reader who earned a node, let it fade, and
        # then failed a refresh had the top level of the very same body say
        # `ever_proven: true, faded: true` while this dict said false to both,
        # erasing work they had genuinely done. `first_mastered_at` is written
        # once and never cleared, for exactly this reason — forgetting does not
        # un-happen having once known something — and ever_proven_set() already
        # reads it. This is that same fix, in the sibling that never got it.
        mastered = r["mastered_at"] is not None and fresh
        proven = r["mastered_at"] is not None and not r["assumed"] and fresh
        ever_proven = r["first_mastered_at"] is not None
        return {
            "level": round(r["level"] or 0, 2),
            "passes": r["passes"] or 0,
            "passes_needed": 2,
            "ready_at": ready_at,
            "mastered": mastered,
            "proven": proven,
            "ever_proven": ever_proven,
            "faded": ever_proven and not proven,
            # `assumed` is now about the credit EXISTING, not about it still
            # standing. It used to be gated on `mastered`, which is freshness-
            # gated — so once placement credit decayed past the gate, all four
            # of these words went false at once and the dict said nothing at
            # all about a node the placement interview had explicitly credited.
            # A state that expires needs a name for having expired, or the book
            # cannot tell the reader why a lesson it had skipped came back.
            "assumed": (r["mastered_at"] is not None and not proven
                        and not ever_proven),
            "assumed_stale": stale_credit,
        }

    def pending_proofs(self, reader_id: int = 1) -> List[Dict]:
        """Every node standing one earned pass short of mastery, with the
        moment its second pass becomes possible.

        The book already makes this appointment — `_apply_attempt` refuses to
        master a node until `now - first_pass_at >= prove_gap` — and until now
        it never told the reader when. This is that appointment, in one query.
        Deliberately not a loop over `mastery_detail`: that opens a connection
        per node (see `_conn`), and this list is read on every Today.

        Three filters, each of which the book is wrong without:

        - `mastered_at IS NULL` — a node already proven has no appointment
          left to keep.
        - `assumed = 0` — placement credit is not a pass. A credited node
          carries `mastered_at` from the moment `seed_assumed` writes it, so
          the clause above already covers today's data; it is stated anyway
          because the cost of it ever not covering it is the book promising
          the reader a ceremony for work they never did.
        - the same freshness gate `passed_set()` applies, for the same
          reason. `passes` never regresses for a node that was never
          mastered: `_apply_attempt` clamps it back only inside its
          `mastered_at is not None` branch, so a node passed once and then
          failed outright keeps `passes = 1` forever. Without this check the
          book offers a dated appointment for a gate that has re-shut — the
          exact trap `story.needs()` guards against by zeroing a faded
          node's pass count (story.py:230-233). `_strength_now` rather than
          `_standing_strength` because with `assumed = 0` the two agree, and
          this is the expression `passed_set()` reads.

        Unlike `mastery_detail`, `ready_at` is NOT nulled once it falls into
        the past: this list is sorted by it, and a caller needs "ready now"
        to sort ahead of "ready tomorrow" rather than collapsing into a null
        that cannot be compared to a float. An elapsed `ready_at` means ready
        now, and must be rendered as an invitation — never as a date in the
        past the reader appears to have missed.
        """
        now = time.time()
        with _lock, self._conn() as c:
            rows = c.execute(
                """SELECT node_id, passes, first_pass_at, strength, last_seen,
                          reinforcements
                     FROM mastery
                    WHERE reader_id=? AND passes >= 1 AND mastered_at IS NULL
                      AND assumed = 0 AND first_pass_at IS NOT NULL""",
                (reader_id,)).fetchall()
            prof_row = c.execute("SELECT age FROM profile WHERE reader_id=?",
                                 (reader_id,)).fetchone()
        # The age-scaled window `_apply_attempt` will actually apply, read the
        # same way `mastery_detail` reads it. Telling a 5-year-old "tomorrow"
        # when the check opens in six hours costs them a day of credit they
        # have already earned; the two must never be computed differently.
        prove_gap = _mastery_min_interval(prof_row["age"] if prof_row else None)
        out = [{"node_id": r["node_id"], "passes": r["passes"] or 0,
                "ready_at": r["first_pass_at"] + prove_gap}
               for r in rows
               if self._strength_now(r["strength"] or 0, r["last_seen"], now,
                                     r["reinforcements"]) >= FRESH_GATE]
        out.sort(key=lambda p: p["ready_at"])
        return out

    def proven_count_current(self, reader_id: int = 1) -> int:
        """Proven nodes whose memory has not decayed away — the honest headline
        number, matching what the gates actually treat as open."""
        now = time.time()
        with _lock, self._conn() as c:
            rows = c.execute(
                """SELECT strength, last_seen, reinforcements FROM mastery
                   WHERE reader_id=? AND mastered_at IS NOT NULL AND assumed=0""",
                (reader_id,)).fetchall()
        return sum(1 for r in rows
                   if self._strength_now(r["strength"] or 0, r["last_seen"], now,
                                         r["reinforcements"]) >= FRESH_GATE)

    def proven_set(self, reader_id: int = 1) -> set:
        """Nodes mastered by genuine, spaced performance — not placement credit.

        Decay applies here exactly as it does in `gate_map`. It did not, which
        left the book telling three different stories about one node: the
        curriculum called it unmastered, the node page called it mastered, and
        today's list counted neither. What has faded is not currently proven.
        """
        now = time.time()
        with _lock, self._conn() as c:
            rows = c.execute(
                """SELECT node_id, strength, last_seen, reinforcements FROM mastery
                   WHERE reader_id=? AND mastered_at IS NOT NULL AND assumed=0""",
                (reader_id,)
            ).fetchall()
        return {r["node_id"] for r in rows
                if self._strength_now(r["strength"] or 0, r["last_seen"], now,
                                      r["reinforcements"]) >= FRESH_GATE}

    def credited_set(self, reader_id: int = 1) -> set:
        """Nodes the book has ever credited as mastered, freshness aside.

        Deliberately NOT decay-aware, and the one such set that is. It exists
        so `assumed` can mean "credited and never earned" in both routes at
        once: `mastered_set` is freshness-gated, so deriving `assumed` from it
        made placement credit vanish entirely the moment it stopped standing,
        rather than becoming stale credit the reader can be told about.
        """
        with _lock, self._conn() as c:
            rows = c.execute(
                "SELECT node_id FROM mastery WHERE reader_id=? AND mastered_at IS NOT NULL",
                (reader_id,)).fetchall()
        return {r["node_id"] for r in rows}

    def assumed_stale_set(self, reader_id: int = 1) -> set:
        """Nodes whose placement credit has expired — see ASSUMED_CREDIT_LIFE."""
        now = time.time()
        with _lock, self._conn() as c:
            rows = c.execute(
                """SELECT node_id, last_seen, assumed, passes FROM mastery
                   WHERE reader_id=? AND mastered_at IS NOT NULL AND assumed=1""",
                (reader_id,)).fetchall()
        return {r["node_id"] for r in rows if self._assumed_stale(r, now)}

    def ever_proven_set(self, reader_id: int = 1) -> set:
        """Nodes proven at some point, faded or not — for history and journals,
        where 'you did this' stays true even after the memory dims.

        Reads `first_mastered_at`, not `mastered_at`. The latter is cleared to
        NULL the moment a mastered node is failed on a re-sitting — so a reader
        who earned a node, let it fade, and then failed a refresh check on it
        saw the Journey view and the journal lose that entry entirely, dropping
        straight from one record to zero. `first_mastered_at` is set once, the
        first time a node is genuinely earned, and a later failure never
        touches it — forgetting does not un-happen having once known something.
        """
        with _lock, self._conn() as c:
            rows = c.execute(
                "SELECT node_id FROM mastery WHERE reader_id=? AND first_mastered_at IS NOT NULL",
                (reader_id,)
            ).fetchall()
        return {r["node_id"] for r in rows}

    _MASTERY_STATE_COLUMNS = (
        "level", "attempts", "passes", "first_pass_at", "last_pass_at",
        "strength", "last_seen", "assumed", "mastered_at", "reinforcements",
        "reinforced_at", "first_mastered_at",
    )

    def _cas_mastery(self, c, reader_id: int, node_id: str, previous, state) -> bool:
        """Replace a mastery row iff every field still matches `previous`.

        Both quiz attempts and card reviews use this one compare shape. A
        partial token such as `attempts` is insufficient because reviews alter
        strength and durability without incrementing it.
        """
        before = tuple(previous[name] for name in self._MASTERY_STATE_COLUMNS)
        changed = c.execute(
            """UPDATE mastery SET level=?, attempts=?, passes=?, first_pass_at=?,
                      last_pass_at=?, strength=?, last_seen=?, assumed=?,
                      mastered_at=?, reinforcements=?, reinforced_at=?,
                      first_mastered_at=?
                 WHERE reader_id=? AND node_id=?
                   AND level IS ? AND attempts IS ? AND passes IS ?
                   AND first_pass_at IS ? AND last_pass_at IS ?
                   AND strength IS ? AND last_seen IS ? AND assumed IS ?
                   AND mastered_at IS ? AND reinforcements IS ?
                   AND reinforced_at IS ? AND first_mastered_at IS ?""",
            tuple(state) + (reader_id, node_id) + before).rowcount
        return changed == 1

    def _apply_attempt(self, c, reader_id: int, node_id: str, score: float,
                       assumed: bool, now: float):
        """Apply one attempt, retrying if another instance changed its row.

        Turso's HTTP transport autocommits each statement, so the process-local
        lock cannot make the SELECT/calculation/write sequence atomic across
        serverless instances.  `_apply_attempt_once` uses the row it read as an
        optimistic compare value; a lost comparison retries from the winner's
        state instead of overwriting it.
        """
        while True:
            applied = self._apply_attempt_once(c, reader_id, node_id, score, assumed, now)
            if applied is not None:
                return applied

    def _apply_attempt_once(self, c, reader_id: int, node_id: str, score: float,
                            assumed: bool, now: float):
        prof_row = c.execute("SELECT age FROM profile WHERE reader_id=?",
                             (reader_id,)).fetchone()
        age = prof_row["age"] if prof_row else None
        min_gap = _reinforce_min_gap(age)
        # Age-scaled proving window — see _mastery_min_interval.
        prove_gap = _mastery_min_interval(age)
        row = c.execute("SELECT * FROM mastery WHERE reader_id=? AND node_id=?",
                        (reader_id, node_id)).fetchone()
        if row:
            level = row["level"]
            # Documented deviation from a symmetric EMA: gains move at 0.4,
            # losses at 0.25. A passing score is fairly clean evidence of
            # knowledge, so the level should respond to it quickly; a poor
            # score is noisier (a bad day, a misread question, guessing costs
            # on a short paper), so a single one is damped rather than allowed
            # to erase several sittings' worth of standing. Mastery loss has
            # its own dedicated, sharper mechanism (the failure branch below
            # clears mastered_at outright), so the EMA does not need to be the
            # thing that punishes — it only needs to drift honestly.
            level = (max(level, 0.6 * level + 0.4 * score) if score >= level
                     else 0.75 * level + 0.25 * score)
            attempts = row["attempts"] + 1
            passes = row["passes"] or 0
            reinforcements = row["reinforcements"] or 1
            reinforced_at_write = row["reinforced_at"] if "reinforced_at" in row.keys() else None
            first_pass = row["first_pass_at"]
            last_pass = row["last_pass_at"]
            mastered_at = row["mastered_at"]
            was_assumed = row["assumed"]
            first_mastered_at = (row["first_mastered_at"]
                                 if "first_mastered_at" in row.keys() else None)
        else:
            level, attempts, passes, reinforcements = score, 1, 0, 1
            first_pass = last_pass = mastered_at = reinforced_at_write = None
            was_assumed = 0
            first_mastered_at = None

        newly_mastered = False
        lost_mastery = False
        prev_strength = (self._strength_now(row["strength"] or 0, row["last_seen"], now,
                                            reinforcements) if row else 0.0)
        if assumed:
            # Placement credit: assumed known, not proven. It opens gates so the
            # reader starts at the right level, but it does NOT count as a
            # passing attempt — proving the node still requires two genuine
            # spaced passes, so `assumed` can never launder into `proven`.
            level = max(level, score)
            last_pass = now
            if mastered_at is None:
                mastered_at = now
            # The reverse direction must hold too: a node genuinely earned
            # (first_mastered_at set) must not be demoted back to `assumed` by
            # a later placement re-seed — that would hide real evidence behind
            # the same flag that means "never earned at all".
            was_assumed = 1 if first_mastered_at is None else 0
            strength = max(prev_strength, 0.8)
        else:
            if score >= PASS:
                passes += 1
                first_pass = first_pass or now
                last_pass = now
                # "Proven" means two passes, genuinely spaced. Until that is
                # earned the node stays flagged `assumed`, even after a real
                # attempt — placement credit must never launder into proof.
                earned = (level >= PASS and passes >= 2
                          and (now - first_pass) >= prove_gap)
                if earned:
                    newly_mastered = mastered_at is None or bool(was_assumed)
                    mastered_at = mastered_at or now
                    was_assumed = 0
                    # Set once, on genuine earning, and never cleared by a later
                    # failure — `ever_proven_set` read `mastered_at` directly,
                    # which the failure branch below sets back to NULL, so
                    # failing a re-sitting erased the record that the node had
                    # ever been proven at all: the Journey view and the journal
                    # both went from one entry to zero.
                    first_mastered_at = first_mastered_at or now
                # A pass refreshes the memory; a mastered node returns to full.
                strength = 1.0 if mastered_at is not None else min(level, 0.79)
                # Each genuine pass makes it last longer, not merely resets the
                # clock — the spacing effect, applied to the node as well as to
                # the card. It must be spaced the same way review_card requires:
                # without the gap, sitting the same node's quiz repeatedly in one
                # sitting bought a reinforcement per attempt and pinned the
                # half-life at its ceiling — 31 papers, 31 reinforcements.
                last_r = row["reinforced_at"] if row and "reinforced_at" in row.keys() else None
                if not last_r or (now - last_r) >= min_gap:
                    reinforcements += 1
                    reinforced_at_write = now
                else:
                    reinforced_at_write = last_r
            else:
                # Failing is evidence of forgetting — it must never look fresher.
                # A failed *mastered* node loses its mastery and must be re-proven
                # by another spaced pass, so gates and counts can regress.
                strength = min(prev_strength, score)
                if mastered_at is not None:
                    mastered_at = None
                    lost_mastery = True
                    passes = min(passes, 1)
                    first_pass = now  # re-proving starts a fresh spaced window
                # Forgetting it means it was not as durable as the count claimed.
                reinforcements = max(1, reinforcements - 1)
        state = (level, attempts, passes, first_pass, last_pass, strength, now,
                 was_assumed, mastered_at, reinforcements,
                 reinforced_at_write, first_mastered_at)
        if row:
            # Compare every mastery field this calculation consumed.  Attempts
            # alone is not a sufficient revision: a simultaneous card review
            # can change strength/mastered_at without incrementing it.  `IS`
            # is SQLite's null-safe equality, so optional timestamps participate
            # in the same comparison without special cases.
            changed = 1 if self._cas_mastery(c, reader_id, node_id, row, state) else 0
        else:
            # Two first attempts may both observe no row.  INSERT OR IGNORE is
            # the creation-side CAS; the loser loops and applies its evidence
            # to the row the winner just created.
            changed = c.execute(
                """INSERT OR IGNORE INTO mastery(
                       reader_id, node_id, level, attempts, passes, first_pass_at,
                       last_pass_at, strength, last_seen, assumed, mastered_at,
                       reinforcements, reinforced_at, first_mastered_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (reader_id, node_id) + state).rowcount
        if changed != 1:
            return None
        return level, mastered_at is not None, newly_mastered, lost_mastery

    def record_attempt(self, node_id: str, score: float, assumed: bool = False,
                       seconds: Optional[float] = None,
                       items: int = 0, reader_id: int = 1) -> Dict:
        """Record a graded attempt (score 0..1). Returns mastery + xp_gained.

        `seconds`/`items` are how long this paper took the reader and how many
        questions were on it. They exist so the book can tell them how long
        tonight will take *from their own record* rather than from a number
        somebody guessed — see `pace()`. They are clamped there, not trusted
        here, and nothing about mastery or XP reads them.
        """
        now = time.time()
        score = max(0.0, min(1.0, score))
        with _lock, self._conn() as c:
            # Whether this node had EVER been earned before this attempt. The
            # 60 XP below is a first-mastery bonus, but `newly` only means
            # "mastered_at was NULL a moment ago" — and the failure branch sets
            # it back to NULL. So failing a mastered node and re-proving it paid
            # the full bonus again, every cycle, for a node the reader had
            # already been paid for once. `first_mastered_at` is written once
            # and never cleared, which is exactly the question being asked here.
            _prior = c.execute(
                "SELECT first_mastered_at FROM mastery WHERE reader_id=? AND node_id=?",
                (reader_id, node_id)).fetchone()
            first_ever = not (_prior and _prior["first_mastered_at"])
            level, mastered, newly, lost = self._apply_attempt(
                c, reader_id, node_id, score, assumed, now)
            # The dated appointment this attempt just made, handed back at the
            # moment it is made instead of left for the next page to discover.
            # A first pass opens a spaced window (see `pending_proofs`), and
            # the result splash is the one place the reader is certainly
            # looking when it opens. None once the node is mastered — there is
            # nothing left to seal — and None for an attempt that never
            # passed, which has no window yet.
            _pend = c.execute(
                "SELECT first_pass_at, mastered_at FROM mastery WHERE reader_id=? AND node_id=?",
                (reader_id, node_id)).fetchone()
            _prof = c.execute("SELECT age FROM profile WHERE reader_id=?",
                             (reader_id,)).fetchone()
            ready_at = None
            if _pend and _pend["first_pass_at"] and _pend["mastered_at"] is None:
                ready_at = _pend["first_pass_at"] + _mastery_min_interval(
                    _prof["age"] if _prof else None)
            xp = 0
            if not assumed:
                # Effort XP is paid once per node per day, so repeating the same
                # quiz cannot farm points; mastery still pays its bonus.
                #
                # Only an attempt that actually *paid* spends the day's slot.
                # Counting every attempt meant a failed one — which earns
                # nothing, being below the 0.5 floor — silently consumed it, so
                # missing a node and then going back and mastering it paid zero
                # while passing first time paid full. Ten nodes struggled with
                # and then learned earned 0 XP against 120 for ten first-try
                # passes: the reader who needed a second run at it was the one
                # the book paid least, which inverts the whole point of the
                # schedule. Failing is not farming, and this is the same
                # `score >= 0.5` line the payment itself uses.
                # A floor, not a straight line: below half marks is closer to
                # guessing than to retrieval, and paying it proportionally
                # meant 343 randomly-answered papers (mean score 0.198, zero
                # masteries) still earned 660 XP — 3.6x an honest day's worth.
                # XP should track successful retrieval, not mere participation.
                # INSERT OR IGNORE is the cross-instance decision: unlike the
                # former events SELECT, exactly one HTTP-autocommit request can
                # own this node's local-day slot.
                effort_claimed = False
                if score >= 0.5:
                    local_day = datetime.date.fromordinal(_local_day(now)).isoformat()
                    effort_claimed = c.execute(
                        """INSERT OR IGNORE INTO attempt_effort_claims(
                               reader_id, node_id, local_day, claimed_at) VALUES(?,?,?,?)""",
                        (reader_id, node_id, local_day, now)).rowcount == 1
                xp = ((round(score * 12) if effort_claimed else 0)
                      + (60 if newly and first_ever else 0))
                payload = {"node": node_id, "score": round(score, 2),
                           "mastered": newly}
                per = _per_item_seconds(seconds, items)
                if per is not None:
                    payload["per_item"] = per
                c.execute(
                    "INSERT INTO events(kind, payload, at, xp, reader_id) "
                    "VALUES('attempt',?,?,?,?)",
                    (json.dumps(payload), now, xp, reader_id))
        proven = node_id in self.proven_set(reader_id)
        return {"node_id": node_id, "level": round(level, 3),
                "mastered": mastered, "newly_mastered": newly,
                "proven": proven, "lost_mastery": lost, "xp_gained": xp,
                "ready_at": ready_at}

    def seed_assumed(self, node_ids: List[str], reader_id: int = 1):
        """Bulk placement credit (assumed known)."""
        now = time.time()
        with _lock, self._conn() as c:
            for nid in node_ids:
                self._apply_attempt(c, reader_id, nid, 0.85, True, now)

    def burn_item(self, node_id: str, fingerprint: str, reader_id: int = 1):
        """Record that the book has shown this item's answer to this reader.

        Immediate feedback teaches, and it must stay. But the key it reveals
        cannot then be the evidence that the reader knows the thing: a paper
        could simply be abandoned after reading its answers and a clean one sat
        moments later. The first-commitment lock stopped that *within* a paper;
        this stops it across papers.
        """
        with _lock, self._conn() as c:
            c.execute("""INSERT INTO burned(reader_id, node_id, fingerprint, at) VALUES(?,?,?,?)
                         ON CONFLICT(reader_id, node_id, fingerprint) DO UPDATE SET at=?""",
                      (reader_id, node_id, fingerprint, time.time(), time.time()))

    def burned_map(self, node_id: str, window_days: float = 7.0,
                   reader_id: int = 1) -> dict:
        """When each of this node's items last had its answer shown."""
        cutoff = time.time() - window_days * DAY
        with _lock, self._conn() as c:
            rows = c.execute(
                "SELECT fingerprint, at FROM burned WHERE reader_id=? AND node_id=? AND at>=?",
                (reader_id, node_id, cutoff)).fetchall()
        return {r["fingerprint"]: r["at"] for r in rows}

    def burned_set(self, node_id: str, window_days: float = 7.0,
                   before: float = None, reader_id: int = 1) -> set:
        """Items whose answers this reader has been shown recently.

        The window means a node never becomes permanently unprovable — after a
        week without being told, remembering it is evidence again, which is the
        same reasoning the spaced-passes rule rests on.
        """
        cutoff = time.time() - window_days * DAY
        with _lock, self._conn() as c:
            if before:
                # Only what was already spent when this paper went out — an
                # answer committed during the sitting counts, whatever it was.
                rows = c.execute(
                    "SELECT fingerprint FROM burned WHERE reader_id=? AND node_id=? AND at>=? AND at<?",
                    (reader_id, node_id, cutoff, before)).fetchall()
            else:
                rows = c.execute(
                    "SELECT fingerprint FROM burned WHERE reader_id=? AND node_id=? AND at>=?",
                    (reader_id, node_id, cutoff)).fetchall()
        return {r["fingerprint"] for r in rows}

    def revoke_assumed(self, node_ids: List[str], reader_id: int = 1):
        """Drop placement/age credit for these nodes.

        Age seeds credit at onboarding on the assumption a nine-year-old knows
        primary-school material. A placement check is real evidence, and when it
        says otherwise the assumption has to go — otherwise a reader placed at
        stage 0 keeps 89 nodes marked known, and the book teaches around them.

        Only `assumed` rows are touched: anything actually proven stands.
        """
        if not node_ids:
            return 0
        with _lock, self._conn() as c:
            c.executemany(
                "DELETE FROM mastery WHERE reader_id=? AND node_id=? AND assumed=1",
                [(reader_id, nid) for nid in node_ids])
            return c.total_changes

    def mastered_count(self, reader_id: int = 1) -> int:
        return len(self.mastered_set(reader_id))

    def proven_count(self, reader_id: int = 1) -> int:
        with _lock, self._conn() as c:
            return c.execute(
                "SELECT COUNT(*) FROM mastery WHERE reader_id=? AND mastered_at IS NOT NULL AND assumed=0",
                (reader_id,)
            ).fetchone()[0]

    # ---------- spaced repetition (SM-2) ----------

    def add_cards(self, cards: List[Dict], reader_id: int = 1) -> int:
        now = time.time()
        added = 0
        with _lock, self._conn() as c:
            for card in cards:
                front = (card.get("front") or "").strip()
                back = (card.get("back") or "").strip()
                if not front or not back:
                    continue
                try:
                    # Due after RELEARN_DELAY, not this instant. A card created
                    # and graded in the same breath is not a memory test — it
                    # let a decayed node be restored to full strength in zero
                    # elapsed time by minting three cards and answering them.
                    c.execute(
                        """INSERT OR IGNORE INTO srs_cards(reader_id, front, back, node_id, article,
                                                  due, created_at, origin)
                           VALUES(?,?,?,?,?,?,?,?)""",
                        (reader_id, front, back, card.get("node_id", ""),
                         card.get("article", ""), now + RELEARN_DELAY, now,
                         card.get("origin", "book")),
                    )
                    added += c.execute("SELECT changes()").fetchone()[0]
                except Exception:
                    pass
        return added

    def due_cards(self, limit: int = 20, reader_id: int = 1) -> List[Dict]:
        """Due cards, interleaved so you don't get a run of same-article cards."""
        now = time.time()
        with _lock, self._conn() as c:
            # Take the oldest few from *each* node rather than the oldest few
            # overall. Prefetching `limit * 3` by due date and round-robining
            # inside that window only interleaves when the deck is already
            # balanced: 60 cards due on one node and 5 on another produced a
            # queue that was 100% the first node, and the second never appeared.
            # A backlog after a break is exactly when interleaving matters most.
            rows = c.execute(
                """SELECT * FROM (
                       SELECT *, ROW_NUMBER() OVER (
                           PARTITION BY COALESCE(NULLIF(node_id,''), article, '')
                           ORDER BY due) AS rn
                       FROM srs_cards WHERE reader_id=? AND due <= ?)
                   WHERE rn <= ? ORDER BY due""",
                (reader_id, now, max(3, limit)),
            ).fetchall()
        cards = [dict(r) for r in rows]
        # Round-robin by topic so a session never becomes a run of one subject.
        buckets: Dict[str, List[Dict]] = {}
        for cd in cards:
            buckets.setdefault(cd.get("node_id") or cd.get("article") or "", []).append(cd)
        order = list(buckets)
        out = []
        while order and len(out) < limit:
            for key in list(order):
                if len(out) >= limit:
                    break
                if buckets[key]:
                    out.append(buckets[key].pop(0))
                if not buckets[key]:
                    order.remove(key)
        return out

    @staticmethod
    def _lapses_of(row) -> int:
        return row["lapses"] or 0

    # A card that is overdue, or that is sitting at the bottom of the ladder
    # after a lapse, is not evidence of current retention. It is not zero
    # evidence either — the reader did learn the thing once — so an unhealthy
    # card is worth this much rather than nothing.
    UNHEALTHY_CARD_WEIGHT = 0.6

    def _deck_health(self, c, reader_id: int, node_id: str, now: float) -> float:
        """0..1 — how well this node's whole deck is currently standing.

        A node is not its easiest card. A single confident review used to set
        node strength to 1.0 outright, so a reader who kept one trivial card
        alive kept the node reading fully retained while every other card in it
        was lapsed and overdue. Averaging over the node's book cards makes the
        restore a claim about the node, which is what the gates read it as.

        Reader-authored cards are excluded for the same reason they cannot
        restore strength on their own: they are the reader's notes, and a
        neglected pile of them should not be able to hold a node down any more
        than a fresh pile could prop it up.
        """
        rows = c.execute(
            "SELECT due, reps, lapses FROM srs_cards "
            "WHERE reader_id=? AND node_id=? AND COALESCE(origin,'book')='book'",
            (reader_id, node_id)).fetchall()
        if not rows:
            return 1.0
        healthy = 0.0
        for r in rows:
            ok = (r["due"] or 0) > now and (r["reps"] or 0) > 0
            healthy += 1.0 if ok else self.UNHEALTHY_CARD_WEIGHT
        return healthy / len(rows)

    REVIEW_XP_DAILY_CAP = 120
    CALIBRATION_WINDOW = 10          # recent quiz sittings considered
    # Below this many pooled rated answers we do not claim to have measured
    # anything. Without a floor, one sitting with a single confident-and-wrong
    # answer produced a rate of 1.0, which capped every self-graded restore and
    # froze durability growth on a sample size of one. Six is the smallest
    # sample at which a single miss (1/6 = 0.17) cannot on its own clear the
    # 1/3 limit — the threshold needs at least two observations to trip.
    CALIBRATION_MIN_SAMPLE = 6
    OVERCONFIDENCE_LIMIT = 1 / 3     # beyond this, self-grades are discounted
    # The discount reaches full force at twice the limit. Between the two the
    # penalty ramps linearly: 0.333 and 0.334 must not be different kinds of
    # learner, and a measured quantity with a hard cliff in the middle of its
    # plausible range reports the cliff more than it reports the reader.
    CALIBRATION_FULL_DISCOUNT = 2 / 3
    OVERCONFIDENT_RESTORE_CAP = 0.85  # fully-discounted strength restore for q>=4
    UNDERCONFIDENCE_LIMIT = 1 / 3     # beyond this, a hesitant q=3 is credited up
    UNDERCONFIDENT_Q3_FLOOR = 0.7     # fully-credited floor, instead of the usual 0.5

    @classmethod
    def _miscalibration(cls, rate: float, limit: float) -> float:
        """How far past `limit` this rate is, as a 0..1 fraction of the ramp.

        0.0 means "calibrated, no adjustment"; 1.0 means "as miscalibrated as
        we are willing to model". Everything the calibration model does is
        scaled by this one number, so the two directions and the several
        things a grade buys all move together and continuously.
        """
        span = cls.CALIBRATION_FULL_DISCOUNT - limit
        if span <= 0:
            return 1.0 if rate > limit else 0.0
        return max(0.0, min(1.0, (rate - limit) / span))

    def _calibration_rates(self, c, reader_id: int = 1,
                           window: int = CALIBRATION_WINDOW) -> "tuple":
        """(overconfident, underconfident) rates, each over its own population.

        Overconfidence is the fraction of recent *confident* answers that were
        wrong; underconfidence is the fraction of recent *hesitant* answers
        that were right. They are deliberately not two numerators over one
        shared denominator — that was the previous shape, and it made each
        figure a rate over a population it was not about, diluted by every
        mid-confidence answer that could not contribute to either numerator.

        Reads the last `window` 'calibration' events (logged by the quiz route
        with per-sitting counts) and pools them. Takes an open connection:
        callers already hold `_lock`, which is not reentrant.

        Both directions come out of one query because miscalibration is one
        phenomenon with two signs, and reading only the sign that costs the
        reader something is not measurement — it is a penalty wearing a
        measurement's clothes.
        """
        rows = c.execute(
            "SELECT payload FROM events WHERE reader_id=? AND kind='calibration' "
            "ORDER BY at DESC LIMIT ?", (reader_id, window)).fetchall()
        over = under = confident = hesitant = sample = 0
        for r in rows:
            try:
                p = json.loads(r["payload"])
            except (ValueError, TypeError):
                continue
            total = int(p.get("total") or 0)
            over += int(p.get("overconfident") or 0)
            under += int(p.get("underconfident") or 0)
            # Events written before the per-direction counts existed carry only
            # `total`. Falling back to it reproduces the old (diluted) reading
            # for that sitting rather than dividing by zero and reporting a
            # confident reader as perfectly calibrated.
            confident += int(p.get("confident_total", total) or 0)
            hesitant += int(p.get("hesitant_total", total) or 0)
            sample += total
        # The floor is over the pooled rated answers, not per direction: it is
        # a statement about how much we have watched this reader do, and a
        # reader who has answered plenty but rated few of them confidently is
        # measured, not unmeasured.
        if sample < self.CALIBRATION_MIN_SAMPLE:
            return 0.0, 0.0
        return (over / confident if confident else 0.0,
                under / hesitant if hesitant else 0.0)

    def _overconfidence_rate(self, c, reader_id: int = 1,
                             window: int = CALIBRATION_WINDOW) -> float:
        """Fraction of recent confident quiz answers that were wrong."""
        return self._calibration_rates(c, reader_id, window)[0]

    def _underconfidence_rate(self, c, reader_id: int = 1,
                              window: int = CALIBRATION_WINDOW) -> float:
        """Fraction of recent hesitant quiz answers that were nonetheless right."""
        return self._calibration_rates(c, reader_id, window)[1]

    def overconfidence_rate(self, window: int = CALIBRATION_WINDOW,
                            reader_id: int = 1) -> float:
        """Public wrapper for the reader's recent overconfidence rate."""
        with _lock, self._conn() as c:
            return self._overconfidence_rate(c, reader_id, window)

    def underconfidence_rate(self, window: int = CALIBRATION_WINDOW,
                             reader_id: int = 1) -> float:
        """Public wrapper for the reader's recent underconfidence rate."""
        with _lock, self._conn() as c:
            return self._underconfidence_rate(c, reader_id, window)

    def _review_xp_today(self, c, reader_id: int = 1) -> int:
        """XP already paid for reviews since local midnight."""
        start = _local_midnight(time.time())
        row = c.execute("SELECT COALESCE(SUM(xp), 0) FROM events "
                        "WHERE reader_id=? AND kind='review' AND at>=?",
                        (reader_id, start)).fetchone()
        return int(row[0] or 0)

    def _apply_review_mastery(self, c, reader_id: int, node_id: str, card, quality: int,
                              now: float, min_gap: float):
        """Apply one card's evidence to mastery with optimistic retry.

        Card scheduling is already complete when this runs. Only the mastery
        consequence is retried: if a quiz attempt changes the row between read
        and write, the review is recalculated from that new state rather than
        overwriting it with the stale strength snapshot.
        """
        while True:
            mastery = c.execute(
                "SELECT * FROM mastery WHERE reader_id=? AND node_id=?",
                (reader_id, node_id)).fetchone()
            if mastery is None:
                return

            state = {name: mastery[name] for name in self._MASTERY_STATE_COLUMNS}
            # Start from what the reader retains *now*, not the strength frozen
            # at the last write. Subtracting a lapse from raw 1.0 could raise a
            # two-year-decayed memory from near zero back above the proven gate.
            strength = self._strength_now(
                mastery["strength"] or 0, mastery["last_seen"], now,
                mastery["reinforcements"])
            # A reader-written card is their own note, not independent proof.
            # Its successes cannot self-certify a node, although failing the
            # easiest, most familiar wording is still evidence of forgetting.
            reader_card = (card["origin"] or "book") != "book"
            # last_seen is the decay clock's zero point. It moves only when the
            # grade is admissible evidence; merely grading one's own note as
            # correct must not make an old memory look fresh.
            touch_clock = False

            if quality >= 4 and not reader_card:
                # Confident successful recall restores current standing. A
                # small additive nudge converged below the freshness gate once
                # SM-2 intervals outgrew it, so an on-schedule learner could be
                # reported as faded forever.
                #
                # This grade is self-reported, however. Recent quiz calibration
                # discounts both its restore and its durability payment on one
                # continuous ramp: a reader just over the 1/3 error limit must
                # not become a different kind of learner at a hard cliff
                # (Dunning & Kruger 1999; Koriat & Bjork 2005).
                discount = self._miscalibration(
                    self._overconfidence_rate(c, reader_id), self.OVERCONFIDENCE_LIMIT)
                target = 1.0 - discount * (1.0 - self.OVERCONFIDENT_RESTORE_CAP)
                # One easy card cannot carry a whole node while sibling cards
                # are lapsed or overdue. Deck health scales the restore to the
                # actual state of all cards attached to the node.
                strength = max(
                    strength, target * self._deck_health(c, reader_id, node_id, now))
                touch_clock = True

                # Only a spaced and credible success extends half-life. Paying
                # full reinforcement after discounting the same grade's restore
                # let overconfidence ratchet durability to the ceiling. Credit
                # remains fractional because _half_life is defined on reals.
                last_reinforced = mastery["reinforced_at"]
                credit = 1.0 - discount
                if (credit > 0 and (not last_reinforced
                                    or (now - last_reinforced) >= min_gap)):
                    state["reinforcements"] = (
                        (mastery["reinforcements"]
                         if mastery["reinforcements"] is not None else 1)
                        + credit)
                    state["reinforced_at"] = now
            elif quality == 3 and not reader_card:
                # Effortful successful retrieval is evidence, not a no-op: it
                # restarts decay and applies a modest floor rather than the full
                # q>=4 restore. The opposite calibration signal matters too—a
                # consistently underconfident reader's hesitant-but-correct
                # recall is stronger than their self-grade claims—so this uses
                # the same graded ramp without buying reinforcements (Bjork;
                # Roediger & Karpicke 2006; Koriat, Sheffer & Ma'ayan 2002).
                credit = self._miscalibration(
                    self._underconfidence_rate(c, reader_id), self.UNDERCONFIDENCE_LIMIT)
                floor = 0.5 + credit * (self.UNDERCONFIDENT_Q3_FLOOR - 0.5)
                strength = max(strength, floor)
                touch_clock = True
            elif quality < 3:
                # Failure counts even on a reader-authored card, but it can only
                # move knowledge downward. The gentler 0.15 penalty recognises
                # that self-written prompts can be ambiguous; only a book card
                # can revoke mastery outright below. Because the subtraction is
                # from already-decayed strength, restarting the clock here can
                # never make the memory look fresher than it was before.
                strength = max(0.0, strength - (0.15 if reader_card else 0.25))
                touch_clock = True

            if (quality < 3 and not reader_card
                    and mastery["mastered_at"] is not None and strength <= 0.2):
                # A hard miss on independent evidence means the node must be
                # re-proven. Keep at most one pass and restart its spacing
                # window, while first_mastered_at still preserves its history.
                state["strength"] = strength
                state["last_seen"] = now
                state["mastered_at"] = None
                state["passes"] = min(mastery["passes"] or 0, 1)
                state["first_pass_at"] = now
            elif touch_clock:
                state["strength"] = strength
                state["last_seen"] = now

            desired = tuple(state[name] for name in self._MASTERY_STATE_COLUMNS)
            previous = tuple(mastery[name] for name in self._MASTERY_STATE_COLUMNS)
            if desired == previous or self._cas_mastery(
                    c, reader_id, node_id, mastery, desired):
                return

    def review_card(self, card_id: int, quality: int,
                    seconds: Optional[float] = None,
                    reader_id: int = 1) -> Dict:
        """SM-2. quality: 0 (blank) .. 5 (perfect). A lapse also lowers the
        related node's strength and can flag it for refresh."""
        now = time.time()
        quality = max(0, min(5, quality))
        with _lock, self._conn() as c:
            # Scoped by reader as well as id: srs_cards.id is a plain
            # autoincrement, not unique per reader, so without this a reader
            # who knew or guessed another reader's card id could grade and
            # mutate their card. A mismatch reads as "no such card" rather
            # than a 403 — the row genuinely does not exist for this reader.
            row = c.execute("SELECT * FROM srs_cards WHERE id=? AND reader_id=?",
                            (card_id, reader_id)).fetchone()
            if not row:
                return {"error": "no such card"}
            prof_row = c.execute("SELECT age FROM profile WHERE reader_id=?",
                                 (reader_id,)).fetchone()
            age = prof_row["age"] if prof_row else None
            min_gap = _reinforce_min_gap(age)
            first_step, second_step = _sm2_first_steps(age)
            # Reviewing a card that isn't due yet is welcome, but a *success*
            # on it is practice, not progress: it moves no schedule, pays no
            # XP, and cannot refresh a faded node. Otherwise one card can be
            # drilled all afternoon for unlimited credit, and a card the
            # reader wrote themselves would be enough to restore mastery the
            # book had let decay.
            #
            # A *failure* on an early card is a different animal, and the
            # anti-farming argument does not cover it. Blanking on a card a
            # day before it was due is genuine evidence of forgetting — the
            # memory did not survive even the scheduled interval — and
            # discarding it meant a reader could watch themselves fail a card
            # cold while the book kept its node reading as proven until the
            # calendar caught up. Evidence is asymmetric here on purpose:
            # early success proves nothing (the short gap made it easy, and
            # rewarding it invites drilling), but early failure proves plenty
            # (the short gap made it *easier*, and they still missed). So a
            # failed early review flows through the full path — the card
            # lapses, the node's strength drops, mastery can be revoked —
            # while a successful early one still returns without effect.
            # There is no farming route through failure: q<3 pays zero XP and
            # only ever moves strength downward.
            counts = (row["due"] or 0) <= now or quality < 3
            if not counts:
                return {"id": card_id, "next_days": round(((row["due"] or now) - now) / DAY, 1),
                        "xp_gained": 0, "lapses": self._lapses_of(row), "early": True}
            ef, interval, reps, lapses = row["ef"], row["interval"], row["reps"], row["lapses"] or 0
            # Every grade that counts increments this, and nothing ever resets
            # it. `reps` cannot do this job: the lapse branch below sets it to
            # 0, which is correct for SM-2 (it is a ladder position, not a
            # tally) and ruinous for any rate computed over it — see deck_stats.
            reviews = (row["reviews"] if "reviews" in row.keys() else None) or 0
            reviews += 1
            if quality < 3:
                reps, interval, lapses = 0, 0, lapses + 1
                # A card you keep failing is a "leech": make it easier (shorter
                # intervals) rather than letting it return like an easy card.
                # Canonical SM-2 applies the same quality-sensitive polynomial
                # on failure as on success — a total blank (q=0, -0.8) is much
                # stronger evidence of difficulty than a near-miss (q=2, -0.32).
                # The old flat -0.2 treated them identically, so genuinely hard
                # cards eased off too slowly and near-misses too fast.
                ef = max(1.3, ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
            else:
                if reps == 0:
                    # Age-scaled learning steps — see _sm2_first_steps. 1 and 6
                    # days for a teenager or adult, hours for a small child.
                    interval = first_step
                elif reps == 1:
                    interval = second_step
                else:
                    # Documented deviation from canonical SM-2: the interval is
                    # multiplied by the *previous* EF — the EF update for this
                    # grade happens below, after scheduling. SuperMemo's paper
                    # applies the freshly-updated EF to the same interval; using
                    # the prior one (as Anki does) schedules on the difficulty
                    # the card had demonstrated *up to* this review, which is
                    # slightly conservative for improving cards and avoids one
                    # good day instantly stretching the next gap.
                    interval = round(interval * ef, 1)
                # SM-2's ladder is unbounded, and strength decay is not — a card
                # scheduled 1,225 days out left its node reading faded for the
                # entire gap between reviews, correct and on time. Capping the
                # interval is what keeps "reviewed on schedule" and "reads as
                # proven" the same claim.
                interval = min(interval, MAX_INTERVAL_DAYS)
                reps += 1
            if quality >= 3:
                ef = max(1.3, ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
            due = now + max(interval, 10 / 1440) * DAY
            c.execute(
                "UPDATE srs_cards SET ef=?, interval=?, reps=?, lapses=?, reviews=?, due=? "
                "WHERE id=? AND reader_id=?",
                (ef, interval, reps, lapses, reviews, due, card_id, reader_id),
            )
            # Feed the outcome back to node mastery strength — the deck is the
            # memory, so repeated lapses can un-master a node entirely.
            node_id = row["node_id"]
            if node_id:
                self._apply_review_mastery(c, reader_id, node_id, row, quality, now, min_gap)
            # Only successful retrieval pays — a blank is practice, not progress.
            if lapses >= 6 and quality < 3:
                # A card failed this often is badly formed or too hard: park it
                # for a week rather than grinding the reader on it daily.
                due = now + 7 * DAY
                c.execute("UPDATE srs_cards SET due=? WHERE id=? AND reader_id=?",
                          (due, card_id, reader_id))
                log.info("leech card %s parked after %d lapses", card_id, lapses)
            xp = 5 if quality >= 4 else (3 if quality >= 3 else 0)
            # A day's reviewing is worth a day's credit. The due check stops one
            # card being drilled all afternoon, but not two hundred cards being
            # written and graded in a sitting — which paid 1,000 XP for nothing.
            # Streaks and levels are built on this number, so it needs a ceiling.
            room = max(0, self.REVIEW_XP_DAILY_CAP - self._review_xp_today(c, reader_id))
            xp = min(xp, room)
            payload = {"card": card_id, "q": quality}
            per = _per_item_seconds(seconds, 1)
            if per is not None:
                payload["per_item"] = per
            c.execute(
                "INSERT INTO events(kind, payload, at, xp, reader_id) "
                "VALUES('review',?,?,?,?)",
                (json.dumps(payload), now, xp, reader_id))
        return {"id": card_id, "next_days": round(max((due - now) / DAY, 0.01), 2),
                "xp_gained": xp, "lapses": lapses}

    def deck_stats(self, reader_id: int = 1) -> Dict:
        now = time.time()
        with _lock, self._conn() as c:
            total = c.execute("SELECT COUNT(*) FROM srs_cards WHERE reader_id=?",
                              (reader_id,)).fetchone()[0]
            due = c.execute("SELECT COUNT(*) FROM srs_cards WHERE reader_id=? AND due <= ?",
                            (reader_id, now)).fetchone()[0]
            # Deck shape, for anything that has to price *maintenance* rather
            # than count today's queue — pacing.roadmap() reads these to turn
            # its flat per-node review estimate into this reader's own. Kept
            # here rather than in pacing because the deck is this module's
            # business and the schema is private to it.
            # MAX(reviews, reps+lapses) per row, not plain SUM(reviews): a row
            # written before the `reviews` column existed and not touched since
            # the migration backfill still carries its history in reps+lapses,
            # and `reviews` can never legitimately be the smaller of the two.
            agg = c.execute(
                "SELECT COALESCE(SUM(MAX(COALESCE(reviews,0), "
                "                       COALESCE(reps,0) + COALESCE(lapses,0))), 0), "
                "COALESCE(SUM(lapses),0), "
                "COUNT(DISTINCT node_id) FROM srs_cards "
                "WHERE reader_id=? AND node_id IS NOT NULL", (reader_id,)
            ).fetchone()
            graded, lapses, nodes = int(agg[0]), int(agg[1]), int(agg[2])
            with_node = c.execute(
                "SELECT COUNT(*) FROM srs_cards WHERE reader_id=? AND node_id IS NOT NULL",
                (reader_id,)).fetchone()[0]
            # A day needs a tomorrow. `next_due` is the next moment the deck
            # has anything to say (None when nothing at all is scheduled
            # ahead — an answer in its own right, not a zero); `due_tomorrow`
            # is everything that will be waiting by the end of tomorrow,
            # today's unreviewed backlog included, because that is what the
            # reader will actually meet when they open the book. Both are
            # served by idx_cards_due.
            next_due = c.execute(
                "SELECT MIN(due) FROM srs_cards WHERE reader_id=? AND due > ?",
                (reader_id, now)).fetchone()[0]
            due_tomorrow = c.execute(
                "SELECT COUNT(*) FROM srs_cards WHERE reader_id=? AND due <= ?",
                (reader_id, _end_of_tomorrow(now))).fetchone()[0]
        # A lapse resets a card to the bottom of the ladder, so it is the unit
        # of *extra* review cost. The denominator is every graded review ever
        # taken, which makes this the observed failure rate of the deck, not a
        # per-card average that a few leeches would dominate.
        #
        # It used to be SUM(reps) + SUM(lapses), which was wrong in a way that
        # compounded all the way out to the reader's estimated finish date.
        # `reps` is reset to 0 by every lapse, so a card with ten successes and
        # then one failure reported reps=0, lapses=1 — a lapse rate of 1.0 for
        # a card the reader gets right 91% of the time. pacing's
        # srs_minutes_per_node multiplies the whole curriculum by
        # (1 + 2*lapse_rate), so the inflated rate pushed estimated_years
        # toward its 36 min/node ceiling, roughly tripling the honest figure.
        return {"total": total, "due": due,
                "cards_with_node": with_node, "nodes_with_cards": nodes,
                "cards_per_node": (with_node / nodes) if nodes else 0.0,
                "reviews_graded": graded, "lapses": lapses,
                "lapse_rate": (lapses / graded) if graded else 0.0,
                "next_due": next_due, "due_tomorrow": int(due_tomorrow)}

    def nodes_needing_refresh(self, limit: int = 8, reader_id: int = 1) -> List[str]:
        """Mastered nodes whose strength has decayed or that have a due card —
        the deck telling us what to reinforce."""
        now = time.time()
        with _lock, self._conn() as c:
            rows = c.execute(
                """SELECT node_id, strength, last_seen, reinforcements, assumed, passes
                   FROM mastery WHERE reader_id=? AND mastered_at IS NOT NULL""",
                (reader_id,)).fetchall()
        out = []
        for r in rows:
            s = self._standing_strength(r, now)
            if s < 0.5:
                out.append((r["node_id"], s))
        out.sort(key=lambda x: x[1])
        return [n for n, _ in out[:limit]]

    # ---------- reading log / motivation ----------

    READ_XP_DAILY_CAP = 30    # ~10 distinct articles' worth; a real day's reading

    def _read_xp_today(self, c, reader_id: int = 1) -> int:
        start = _local_midnight(time.time())
        row = c.execute("SELECT COALESCE(SUM(xp), 0) FROM events "
                        "WHERE reader_id=? AND kind='read' AND at>=?",
                        (reader_id, start)).fetchone()
        return int(row[0] or 0)

    def log_reading(self, title: str, seconds: float = 0, reader_id: int = 1):
        """Log an article open. Pays at most one channel's worth of XP a day.

        "Only the first open of a title pays" assumed a small library. The
        shelf holds hundreds of thousands of titles, plus live Wikipedia as a
        fallback with no floor at all — so a reader (or a script) clicking
        "Surprise me" repeatedly turned a first-party button into an unbounded
        XP farm: every click is a *different* title, so the guard never once
        engaged. The event still logs unconditionally, so the day's reading
        quest still ticks — only the payment is capped.
        """
        now = time.time()
        with _lock, self._conn() as c:
            first_ever = c.execute(
                "SELECT 1 FROM reading_log WHERE reader_id=? AND title=? LIMIT 1",
                (reader_id, title)).fetchone() is None
            c.execute(
                "INSERT INTO reading_log(reader_id, title, opened_at, seconds) VALUES(?,?,?,?)",
                (reader_id, title, now, seconds))
            room = max(0, self.READ_XP_DAILY_CAP - self._read_xp_today(c, reader_id))
            xp = min(3, room) if first_ever else 0
            c.execute(
                "INSERT INTO events(kind, payload, at, xp, reader_id) VALUES('read',?,?,?,?)",
                (json.dumps({"title": title}), now, xp, reader_id))

    def reading_stats(self, reader_id: int = 1) -> Dict:
        with _lock, self._conn() as c:
            n = c.execute("SELECT COUNT(DISTINCT title) FROM reading_log WHERE reader_id=?",
                          (reader_id,)).fetchone()[0]
            recent = c.execute(
                "SELECT title, MAX(opened_at) m FROM reading_log WHERE reader_id=? "
                "GROUP BY title ORDER BY m DESC LIMIT 12", (reader_id,)
            ).fetchall()
        return {"articles_read": n, "recent": [r["title"] for r in recent]}

    @staticmethod
    def _total_xp(c, reader_id: int = 1) -> int:
        """Lifetime XP, read through a connection the caller already holds."""
        row = c.execute("SELECT COALESCE(SUM(xp),0) FROM events WHERE reader_id=?",
                        (reader_id,)).fetchone()
        return int(row[0] or 0)

    def total_xp(self, reader_id: int = 1) -> int:
        with _lock, self._conn() as c:
            return self._total_xp(c, reader_id)

    def xp_today(self, reader_id: int = 1) -> int:
        start = _local_midnight(time.time())
        with _lock, self._conn() as c:
            row = c.execute(
                "SELECT COALESCE(SUM(xp),0) FROM events WHERE reader_id=? AND at>=?",
                (reader_id, start)).fetchone()
        return int(row[0] or 0)

    def _bridged_run_ending_at(self, days: List[int], anchor: int) -> tuple:
        """(run_length, freezes_used) for the run of active days ending at or
        including `anchor`, bridging gaps against a freeze budget that
        renews after STREAK_FREEZE_RENEW_DAYS — i.e. treating `anchor` as
        "the present" for this one computation.

        Walks backward from the anchor (the direction that matters: for a
        FIXED right edge, spending budget on the gap nearest the anchor
        first is what makes the most of it — walking the other way spent
        budget on whichever gap came first chronologically, regardless of
        whether a nearer, more relevant gap needed it more, the exact class
        of bug already fixed once for best_streak_days()'s own greedy scan).
        A gap is affordable when its size, plus whatever OTHER bridges are
        still within STREAK_FREEZE_RENEW_DAYS of it, fits the budget — so an
        old bridge that has since aged out no longer competes with a new
        one, but two gaps close together in time still draw from one shared
        budget, exactly as a single non-renewing count would. An unaffordable
        gap spends nothing: the run ends there outright rather than the
        attempt itself being charged.
        """
        return _bridged_run_ending_at(days, anchor)

    def _streak_walk(self, reader_id: int = 1) -> tuple:
        """Every streak-related number the app shows, from one shared
        source of truth: (current_streak, freezes_left_now, best_streak_ever).

        Replaced two functions that each carried their own copy of an
        anchor-and-walk over the same data — five separate rounds fixed the
        same day-boundary bug in one and missed it in the other, discovered
        only when the two disagreed. Sharing the walk made THAT bug class
        structurally impossible. It did not fix a second, deeper problem
        both copies still had: freeze usage was a lifetime debt that never
        cleared, so a reader with a genuinely excellent eleven-month run and
        two sick days near its start saw "0 rest days left" every day since
        (nothing ever earns it back), and a single fresh missed day eleven
        months later then cost over a month of streak length — not because
        that new miss was expensive alone, but because paying for it left no
        budget for the ancient debt too. best_streak_days(), free to choose
        any window rather than one anchored at today, read the very same
        connected history as tens of days longer — the exact "two functions,
        two answers" shape this session keeps finding, just in a part of the
        walk the earlier shared-implementation fix didn't reach.

        _bridged_run_ending_at() is the one place both concepts now live:
        streak_days()/freezes_left() anchor it at today (or yesterday, while
        today's box is still open); best_streak_days() anchors it at every
        active day in the reader's history and keeps the longest.
        """
        with _lock, self._conn() as c:
            rows = self._streak_day_rows(c, reader_id)
        return _streak_walk_from_rows(rows, _local_day(time.time()))

    @staticmethod
    def _streak_day_rows(c, reader_id: int = 1) -> tuple:
        """The reader's distinct active local days, oldest first.

        Split out from `_streak_walk` so a caller that already holds a
        connection (see `get_profile`) reads them through it rather than
        opening a second one — the same rows, the same order, one round trip
        instead of two. Returned as a plain tuple of ISO date strings because
        that is the cache key `_streak_walk_from_rows` is memoised on, and a
        list of sqlite3.Row objects is neither hashable nor comparable across
        two reads of identical data.
        """
        return tuple(r["d"] for r in c.execute(
            "SELECT DISTINCT date(at, 'unixepoch', 'localtime') d "
            "FROM events WHERE reader_id=? ORDER BY d ASC", (reader_id,)).fetchall())

    def streak_days(self, reader_id: int = 1) -> int:
        """Consecutive local days with activity, bridging missed days against
        a freeze budget that renews over time (see STREAK_FREEZE_RENEW_DAYS)
        so one missed day doesn't wipe the streak.

        Buckets by local day in SQL so a heavy user's long streak is never
        truncated by an event-row limit. Each row is converted to its own
        local calendar date — not a single offset applied to every row — since
        a fixed offset assumes local midnight sits at a constant distance from
        the epoch, which a DST transition breaks: identical study behaviour
        read as streak 38 in a DST-free window and streak 2 across the US
        fall-back, because the day that transition falls on is 25 hours long.
        """
        return self._streak_walk(reader_id)[0]

    def best_streak_days(self, reader_id: int = 1) -> int:
        """The longest run the reader has ever put together, past or present.

        `prune()` keeps one row per calendar day forever specifically so this
        number survives past the retention window — a durable record that
        was being computed nowhere and shown nowhere, so a reader's best
        stretch was invisible the moment their current streak broke. Comes
        from the same walk as streak_days() and freezes_left(), so a past
        streak is graded by exactly the rule today's is.
        """
        return self._streak_walk(reader_id)[2]

    def streak_milestone(self, reader_id: int = 1) -> Optional[int]:
        """Return a milestone (3/7/30/100/365) if today's activity just reached
        one, so the book can celebrate it exactly once."""
        streak = self.streak_days(reader_id)
        if streak in (3, 7, 30, 100, 365) and self.active_today(reader_id):
            return streak
        return None

    def freezes_left(self, reader_id: int = 1) -> int:
        """How many single-day gaps are currently available to spend.

        Shares its walk with streak_days() and best_streak_days() via
        _streak_walk() — the three used to carry independent copies of this
        logic and repeatedly drifted out of sync. One shared implementation
        means they can no longer disagree about where "today" starts, how a
        gap gets bridged, or how long a spent freeze stays spent.
        """
        return self._streak_walk(reader_id)[1]

    def active_today(self, reader_id: int = 1) -> bool:
        start = _local_midnight(time.time())
        with _lock, self._conn() as c:
            return c.execute(
                "SELECT 1 FROM events WHERE reader_id=? AND at>=? LIMIT 1",
                (reader_id, start)).fetchone() is not None

    def journal(self, limit: int = 40, reader_id: int = 1) -> List[Dict]:
        """A timeline of masteries, chapters, and stage ascensions for the
        'your journey' view — built from data we already keep.

        Reads `first_mastered_at`, which is set once and never cleared, rather
        than `mastered_at`, which a later failed re-sitting resets to NULL —
        that made the Journey view lose its entry for a node the moment the
        reader's memory of it faded and they failed a check on it.
        """
        with _lock, self._conn() as c:
            mast = c.execute(
                "SELECT node_id, COALESCE(first_mastered_at, mastered_at) AS at "
                "FROM mastery WHERE reader_id=? "
                "AND COALESCE(first_mastered_at, mastered_at) IS NOT NULL "
                "AND assumed=0 ORDER BY at DESC LIMIT ?",
                (reader_id, limit)).fetchall()
            asc = c.execute(
                "SELECT kind, payload, at FROM events "
                "WHERE reader_id=? AND kind IN ('ascension','chapter') "
                "ORDER BY at DESC LIMIT ?", (reader_id, limit)).fetchall()
        items = [{"kind": "mastered", "node_id": r["node_id"], "at": r["at"]} for r in mast]
        for r in asc:
            try:
                items.append({"kind": r["kind"], "at": r["at"], **json.loads(r["payload"])})
            except Exception:
                pass
        items.sort(key=lambda x: x.get("at") or 0, reverse=True)
        return items[:limit]

    # ---------- how long this takes *this* reader ----------

    # Enough samples that one interrupted sitting cannot set the estimate, and
    # few enough that a reader who has sped up is not held to last spring's
    # pace. A median, not a mean, for the same reason.
    PACE_MIN_SAMPLES = 6
    PACE_WINDOW = 60

    def pace(self, kind: str, reader_id: int = 1) -> Optional[float]:
        """Median seconds per item for this reader on `kind`, or None.

        None means "not measured yet" and callers must say so rather than
        quietly substituting a default and presenting it as the reader's own
        number. The book is allowed to estimate; it is not allowed to imply it
        measured something it did not.
        """
        with self._conn() as c:
            rows = c.execute(
                "SELECT payload FROM events WHERE reader_id=? AND kind=? ORDER BY at DESC LIMIT ?",
                (reader_id, kind, self.PACE_WINDOW),
            ).fetchall()
        vals = []
        for r in rows:
            try:
                v = json.loads(r["payload"] or "{}").get("per_item")
            except Exception:
                continue
            if isinstance(v, (int, float)):
                vals.append(float(v))
        if len(vals) < self.PACE_MIN_SAMPLES:
            return None
        vals.sort()
        mid = len(vals) // 2
        return vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2

    def log_event(self, kind: str, payload: Dict, xp: int = 0, reader_id: int = 1):
        with _lock, self._conn() as c:
            c.execute(
                "INSERT INTO events(kind, payload, at, xp, reader_id) VALUES(?,?,?,?,?)",
                (kind, json.dumps(payload), time.time(), xp, reader_id))

    # ---------- placement ----------

    PLACEMENT_COOLING = 7 * DAY  # a settled placement can be re-measured after this

    def placement_state(self, reader_id: int = 1) -> Dict[str, Dict]:
        with _lock, self._conn() as c:
            rows = c.execute("SELECT * FROM placement WHERE reader_id=?",
                             (reader_id,)).fetchall()
        return {r["domain"]: {"stage": r["stage"], "asked": json.loads(r["asked"]),
                              "done": bool(r["done"]),
                              "settled_at": r["settled_at"]} for r in rows}

    def placement_update(self, domain: str, stage: int, asked: List[str], done: bool,
                         reader_id: int = 1):
        now = time.time()
        with _lock, self._conn() as c:
            # settled_at records when the domain settled, so re-measurement can
            # apply a cooling period; it is kept across further done writes and
            # cleared if the domain is somehow marked unsettled again.
            c.execute(
                """INSERT INTO placement(reader_id, domain, stage, asked, done, settled_at)
                   VALUES(?,?,?,?,?,?)
                   ON CONFLICT(reader_id, domain) DO UPDATE SET stage=?, asked=?, done=?,
                     settled_at=CASE WHEN ?
                                     THEN COALESCE(placement.settled_at, ?)
                                     ELSE NULL END""",
                (reader_id, domain, stage, json.dumps(asked), int(done),
                 now if done else None,
                 stage, json.dumps(asked), int(done), int(done), now),
            )

    def reopen_placement(self, domain: str, cooling_days: float = 7.0,
                         reader_id: int = 1) -> bool:
        """Re-open a settled placement for re-measurement after a cooling period.

        A placement check is one sitting on one day — a noisy measurement —
        and settling a domain on it *forever* means a bad morning fixes the
        reader's level for good. This lets the server offer a re-measurement:
        if the domain's placement is settled and at least `cooling_days` have
        passed since it settled, the `done` flag is cleared (the recorded
        stage and asked-question history are kept, so the next sitting starts
        from the same rung and avoids repeating items) and True is returned.
        Returns False if the domain is not settled, or is still cooling —
        the 409 the server sends today remains correct in that window.

        Server wiring is one line in the placement route:
            learner.reopen_placement(domain)
        Only assumed/placement bookkeeping changes; nothing proven is touched.
        """
        now = time.time()
        with _lock, self._conn() as c:
            r = c.execute(
                "SELECT done, settled_at FROM placement WHERE reader_id=? AND domain=?",
                (reader_id, domain)).fetchone()
            if not r or not r["done"]:
                return False
            # Rows settled before settled_at existed have no timestamp; they
            # are by definition old enough, so treat them as past cooling.
            if r["settled_at"] and (now - r["settled_at"]) < cooling_days * DAY:
                return False
            c.execute(
                "UPDATE placement SET done=0, settled_at=NULL WHERE reader_id=? AND domain=?",
                (reader_id, domain))
            return True

    # ---------- maintenance ----------

    def backup(self, dest_dir: str, keep: int = 5):
        """Consistent online backup of the whole learner record, rotating a few
        generations. The single DB is the reader's irreplaceable multi-year
        history, so this runs at startup and daily."""
        os.makedirs(dest_dir, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime())
        dest = os.path.join(dest_dir, "primer-{}.db".format(stamp))
        try:
            with _lock, self._conn() as src:
                bck = sqlite3.connect(dest)
                with bck:
                    src.backup(bck)
                bck.close()
            # A backup you have not verified is not a backup: check the copy is
            # structurally sound and actually contains the reader's record.
            check = sqlite3.connect(dest)
            try:
                status = check.execute("PRAGMA integrity_check").fetchone()[0]
                rows = check.execute("SELECT COUNT(*) FROM mastery").fetchone()[0]
            finally:
                check.close()
            if status != "ok":
                log.error("backup failed integrity check (%s): %s", status, dest)
                os.remove(dest)
                return None
            log.info("backup verified: %s (%d mastery rows)", os.path.basename(dest), rows)
        except Exception as exc:
            log.error("backup failed: %s: %s", exc.__class__.__name__, exc)
            try:
                os.remove(dest)
            except OSError:
                pass
            return None
        backups = sorted(f for f in os.listdir(dest_dir) if f.endswith(".db"))
        for old in backups[:-keep]:
            try:
                os.remove(os.path.join(dest_dir, old))
            except OSError:
                pass
        return dest

    # ---------------- readers & sessions (Google identity) ----------------

    def upsert_google_reader(self, google_sub: str, email: str, name: str) -> int:
        """Find or create the reader row for this Google identity.

        Keyed on `google_sub`, Google's stable subject id — never on email,
        which can change or be reused by a different person. Insert-first,
        not select-then-branch: two callback requests for the same brand-new
        identity (a double-click, a retried request) would otherwise both see
        no existing row and both try to create one, and only one can win the
        UNIQUE constraint. Losing that race is not an error here — it just
        means the row now exists, so the fall-through UPDATE finds it.
        """
        now = time.time()
        with _lock, self._conn() as c:
            try:
                c.execute(
                    "INSERT INTO readers(google_sub, email, name, created_at) "
                    "VALUES (?,?,?,?)", (google_sub, email, name, now))
            except sqlite3.IntegrityError:
                c.execute("UPDATE readers SET email=?, name=? WHERE google_sub=?",
                         (email, name, google_sub))
            row = c.execute("SELECT id FROM readers WHERE google_sub=?",
                            (google_sub,)).fetchone()
        return int(row[0])

    def reader_for_static_account(self, slot_key: str, label: str) -> int:
        """Find or create the reader row for a static username/password
        account — see server.py's multi-account password gate.

        The same identity-row shape Google sign-in uses, keyed by `slot_key`
        (e.g. "static:2") instead of a real Google subject, so the two can
        never collide — Google's own subject values are purely numeric,
        never colon-separated. See `_is_real_google_sub` in server.py, which
        is what keeps a static account from reading as Google-signed-in.
        """
        return self.upsert_google_reader(slot_key, "", label)

    def get_reader(self, reader_id: int) -> Optional[Dict]:
        with self._conn() as c:
            row = c.execute(
                "SELECT id, google_sub, email, name, created_at FROM readers "
                "WHERE id=?", (reader_id,)).fetchone()
        if row is None:
            return None
        return {"id": row[0], "google_sub": row[1], "email": row[2],
                "name": row[3], "created_at": row[4]}

    def claim_legacy_reader(self, reader_id: int, google_sub: str, email: str,
                            name: str) -> bool:
        """Move a Google identity onto reader_id=1, the one profile every
        database had before this feature existed — one time, one direction.

        `reader_id` is the caller's own (already-authenticated) reader id, the
        empty row their Google sign-in was given by default. False means
        reader_id=1 was already claimed — by this identity or another — and
        nothing changed. The identity's placeholder row is freed of its
        google_sub *before* reader_id=1 claims it, so the UNIQUE constraint on
        google_sub never has to hold the same value on two rows at once; if a
        crash lands between the two statements, the identity is briefly
        homeless (both rows google_sub=NULL) but the caller's live session
        still resolves via its own reader_id, and simply retrying the claim —
        which re-checks reader_id=1 is still unclaimed — completes it.
        """
        with _lock, self._conn() as c:
            row = c.execute("SELECT google_sub FROM readers WHERE id=1").fetchone()
            if row is None or row[0] is not None or reader_id == 1:
                return False
            c.execute("UPDATE readers SET google_sub=NULL WHERE id=?", (reader_id,))
            changed = c.execute(
                "UPDATE readers SET google_sub=?, email=?, name=? "
                "WHERE id=1 AND google_sub IS NULL",
                (google_sub, email, name)).rowcount
        return changed == 1

    def create_session(self, reader_id: int, ttl: float = 60 * 60 * 24 * 180) -> str:
        """A new session token for this reader, persisted so sign-out — a real
        DELETE — can end it. The stateless HMAC cookie the password gate uses
        has no such handle: there is nothing to delete, only a secret to
        rotate, which is the outer gate's job, not this inner one's."""
        token = secrets.token_urlsafe(24)
        now = time.time()
        with _lock, self._conn() as c:
            c.execute(
                "INSERT INTO sessions(token, reader_id, created_at, expires_at) "
                "VALUES (?,?,?,?)", (token, reader_id, now, now + ttl))
        return token

    def reader_for_session(self, token: str) -> Optional[int]:
        if not token:
            return None
        with self._conn() as c:
            row = c.execute(
                "SELECT reader_id FROM sessions WHERE token=? AND expires_at > ?",
                (token, time.time())).fetchone()
        return int(row[0]) if row else None

    def delete_session(self, token: str):
        with _lock, self._conn() as c:
            c.execute("DELETE FROM sessions WHERE token=?", (token,))

    def events_today(self, kind: str, reader_id: int = 1) -> bool:
        """Has an event of this kind been logged since local midnight?

        The server asked this by reaching through _conn() into the events
        table, which made a private cursor part of its interface. The
        question belongs here, next to the table that answers it.
        """
        with self._conn() as c:
            row = c.execute(
                "SELECT 1 FROM events WHERE reader_id=? AND kind=? AND at>=? LIMIT 1",
                (reader_id, kind, _local_midnight(time.time())),
            ).fetchone()
        return row is not None

    def events_today_count(self, kind: str, reader_id: int = 1) -> int:
        """How many events of this kind since local midnight.

        `events_today` answers yes/no, and a yes/no is exactly why one graded
        card could stand for a whole day's reviewing: the day's work was
        described with the only question this table could be asked. Same
        query, same day boundary, counted instead of existence-checked — so
        a step can fill rather than merely tick.
        """
        with self._conn() as c:
            row = c.execute(
                "SELECT COUNT(*) FROM events WHERE reader_id=? AND kind=? AND at>=?",
                (reader_id, kind, _local_midnight(time.time())),
            ).fetchone()
        return int(row[0] or 0)

    def last_active_before_today(self, reader_id: int = 1) -> Optional[float]:
        """When the reader was last here before today began, or None.

        None is a real answer with its own meaning — a reader whose entire
        history is today's — and it must never be read as "long ago": the
        difference is a fresh profile being greeted as a lapsed one on its
        first afternoon. Today's own events are excluded on purpose, so the
        answer does not change under the reader as they work. Served by
        idx_events_at.

        One caveat, stated where it can be checked: `prune()` keeps a single
        representative row per calendar day beyond its retention window, so
        past ~400 days this returns that day's FIRST event rather than its
        last. The day is right; the hour may not be. Everything downstream
        measures an absence in whole local days, which that cannot move.
        """
        with _lock, self._conn() as c:
            row = c.execute(
                "SELECT MAX(at) FROM events WHERE reader_id=? AND at < ?",
                (reader_id, _local_midnight(time.time()))).fetchone()
        return row[0] if row and row[0] is not None else None

    def prune(self, keep_days: int = 400):
        """Cap the append-only logs so years of daily use don't grow unbounded.
        Aggregate counts are preserved in mastery/deck; raw rows beyond the
        window are trimmed.

        `streak_days()` counts distinct local calendar days across every event,
        zero-XP included — a day whose only activity was an early review or a
        reading-cap hit still counts. Deleting every zero-XP row past the
        window used to erase the only trace of days like that, silently
        truncating any streak longer than `keep_days`. One representative row
        per day is kept even past the window; only the redundant extras go.
        """
        cutoff = time.time() - keep_days * DAY
        with _lock, self._conn() as c:
            c.execute("DELETE FROM reading_log WHERE opened_at < ?", (cutoff,))
            # Even an aggressive `prune(0)` must not reopen today's unique XP
            # slot. Claims are tiny; retain the current local day regardless
            # of the requested history horizon.
            claim_cutoff = min(cutoff, _local_midnight(time.time()))
            c.execute("DELETE FROM attempt_effort_claims WHERE claimed_at < ?",
                      (claim_cutoff,))
            keep_ids = {r[0] for r in c.execute(
                "SELECT MIN(id) FROM events WHERE at < ? "
                "GROUP BY date(at, 'unixepoch', 'localtime')", (cutoff,))}
            stale = [r[0] for r in c.execute(
                "SELECT id FROM events WHERE at < ? AND xp = 0", (cutoff,)).fetchall()
                if r[0] not in keep_ids]
            if stale:
                c.executemany("DELETE FROM events WHERE id=?", [(i,) for i in stale])


# --------------------------------------------------------------------------
# The streak walk, as free functions over plain data.
#
# It lives out here, and it is memoised, because of how often it is asked for.
# One /api/today asks four separate questions that are all this one walk —
# streak_days, best_streak_days, freezes_left, and streak_milestone (which
# asks streak_days again) — and each used to re-run it from scratch: measured
# at 11 ms a walk on a four-hundred-day history, that was 36 of the
# endpoint's 57 ms spent computing the same three numbers four times.
#
# The walk is a pure function of two things: the set of days the reader was
# active, and which day is today. Nothing else in the record can move its
# answer. So the memo below is exact rather than a staleness trade: a new
# event on a day already in the set cannot change the result, and an event on
# a NEW day changes the key. The cache is small on purpose — a handful of
# entries covers "today, this reader" with room for the day to roll over
# mid-process and for tests to hold several fixtures at once.
# --------------------------------------------------------------------------


def _bridged_run_ending_at(days, anchor: int) -> tuple:
    """(run_length, freezes_used) for the run of active days ending at or
    including `anchor` — see LearnerStore._bridged_run_ending_at for the rules
    this enacts and why the walk runs backward from a fixed right edge.

    `days` is ascending and distinct. The old shape of this function filtered
    the whole history into a `relevant` list on every call, which is O(history)
    work per anchor before the walk even starts — and the walk is called once
    per active day. A bisect for the right edge and a backwards index walk is
    the same traversal, in the same order, over the same values, without
    materialising a copy of the past for each one.
    """
    hi = bisect.bisect_right(days, anchor)
    if not hi:
        return 0, 0
    run = 0
    # Every bridged day, ever, across the whole walk — never pruned
    # mid-walk. An earlier version filtered this down to "nearby the gap
    # being evaluated" and reassigned it, which silently discarded
    # recent, still-live spends the moment an OLDER gap got processed:
    # bridging an ancient sick day 330 days back dropped the record of
    # yesterday's miss from the list entirely, so freezes_left() at the
    # end read 2 (full budget) when only 1 was truly still outstanding.
    # "Nearby" must stay a read-only view taken for one gap's own
    # affordability check, never the list itself.
    spent: List[int] = []
    expect = anchor
    for i in range(hi - 1, -1, -1):
        d = days[i]
        gap = expect - d
        if gap:
            nearby = 0
            for sp in spent:
                if sp - d < STREAK_FREEZE_RENEW_DAYS:
                    nearby += 1
            if nearby + gap > STREAK_FREEZES:
                break
            spent.extend(range(d + 1, d + 1 + gap))
        run += 1
        expect = d - 1
    # Freezes "used" as of the anchor itself — the ones still unexpired.
    used = 0
    for sp in spent:
        if anchor - sp < STREAK_FREEZE_RENEW_DAYS:
            used += 1
    return run, used


def _streak_walk_from_days(days, today: int) -> tuple:
    """(current_streak, freezes_left, best_streak) from the day list alone."""
    if not days:
        return 0, STREAK_FREEZES, 0
    # Anchor to the reader's most recent activity when it's today or
    # yesterday — today's box hasn't closed yet, so nothing has been
    # missed there. Fall back to yesterday for a genuinely stale streak,
    # where the gap to the present is real and must be charged.
    anchor = days[-1] if days[-1] >= today - 1 else today - 1
    current, used = _bridged_run_ending_at(days, anchor)
    # The best run is the longest one ending at any active day. Seeding the
    # maximum with the current run and scanning newest-first turns that into
    # a search that can stop early: a run ending at days[i] can be at most
    # i + 1 days long, because that is how many days precede it, so once the
    # index falls to the best already found no earlier anchor can beat it.
    # Every anchor is still *considered*; the ones skipped are the ones whose
    # own ceiling is proof they would lose. Same answer, without walking the
    # whole history once per day of it.
    best = current
    for i in range(len(days) - 1, -1, -1):
        if i + 1 <= best:
            break
        run = _bridged_run_ending_at(days, days[i])[0]
        if run > best:
            best = run
    return current, max(0, STREAK_FREEZES - used), best


@functools.lru_cache(maxsize=8)
def _streak_walk_from_rows(iso_days: tuple, today: int) -> tuple:
    """The memoised walk. `iso_days` is the tuple of 'YYYY-MM-DD' strings the
    events table hands back, ascending; `today` is the reader's local day."""
    return _streak_walk_from_days(
        tuple(datetime.date.fromisoformat(d).toordinal() for d in iso_days),
        today)


def _local_day(ts: float) -> int:
    # Index of the local calendar day; consecutive days differ by exactly 1.
    # Uses the calendar date directly rather than dividing an epoch timestamp
    # by 86400 — a "day" is not always 86400 seconds long. Identical study
    # behaviour read as streak 38 in a DST-free window and streak 2 across the
    # US fall-back, because a single day is 23 or 25 hours across the
    # transition and epoch division does not know that.
    lt = time.localtime(ts)
    return datetime.date(lt.tm_year, lt.tm_mon, lt.tm_mday).toordinal()


def _end_of_tomorrow(ts: float) -> float:
    """Local midnight at the far end of tomorrow — the horizon for "what is
    waiting when I open this again".

    Deliberately not `_local_midnight(ts) + 2 * DAY`: that is the "a day is
    always 86400 seconds" assumption `_local_midnight` exists below to refuse,
    and across a DST transition it puts the boundary an hour off — counting an
    hour of the day after tomorrow as tomorrow, or dropping tomorrow's last
    hour. Two calendar days on, then midnight.
    """
    lt = time.localtime(ts)
    day = datetime.date(lt.tm_year, lt.tm_mon, lt.tm_mday) + datetime.timedelta(days=2)
    return time.mktime(datetime.datetime(day.year, day.month, day.day).timetuple())


def _local_midnight(ts: float) -> float:
    # Subtracting hour/min/sec in seconds from the epoch timestamp assumes a
    # day is always 86400 seconds — the exact _local_day flaw fixed above,
    # left unfixed here. On a DST transition the wall-clock hour and the
    # elapsed-seconds-since-midnight disagree by an hour, landing the
    # "midnight" boundary on the wrong side of true midnight: XP daily caps
    # and the "already attempted today" guard both read from this, so they
    # either count an hour of yesterday against today's cap (spring-forward)
    # or drop an hour of today out of every "since midnight" sum
    # (fall-back). Build the boundary from the calendar date directly.
    lt = time.localtime(ts)
    midnight = datetime.datetime(lt.tm_year, lt.tm_mon, lt.tm_mday)
    return time.mktime(midnight.timetuple())
