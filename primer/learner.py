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

import datetime
import json
import logging
import os
import shutil
import sqlite3
import threading
import time
from typing import Dict, List, Optional

log = logging.getLogger("primer.learner")

_lock = threading.Lock()

DAY = 86400.0
PASS = 0.8                       # score that counts as a passing attempt
MASTERY_MIN_INTERVAL = 2 * DAY   # min gap between 1st and 2nd pass to master
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
# It grows *linearly* and caps at a year. Doubling per reinforcement was an
# over-correction that switched decay off altogether: it saturated after about
# seven reviews, so a reader who drilled a node daily for three weeks pinned its
# half-life at the ceiling and it still read as proven four years later. Fixing
# "everything evaporates" by making nothing evaporate is not a fix.
#
# The step is tuned against SM-2's own growth, not chosen freely: SM-2's review
# interval grows multiplicatively (roughly x2.5 per pass) while a smaller step
# grew this linearly, so intervals outran the half-life mid-ramp even though
# both eventually reached their caps — a card reviewed exactly on schedule still
# read its node as faded partway through. 2.2 keeps strength at or above the
# gate for every step of that ramp, verified by simulation and by an end-to-end
# on-schedule review test.
#
# A reinforcement also has to be *spaced* to count. Massed repetition does not
# build durable memory, and letting it do so here meant a node could be made
# permanent in a single sitting.
RELEARN_DELAY = 10 * 60          # a new card waits before it can be cashed
STRENGTH_HALF_LIFE = 30 * DAY
STRENGTH_HALF_LIFE_MAX = 365 * DAY
STRENGTH_HALF_LIFE_STEP = 2.2
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


def _reinforce_min_gap(age: Optional[float]) -> float:
    if age is None:
        return REINFORCE_MIN_GAP
    for ceiling, gap in REINFORCE_MIN_GAP_BY_AGE:
        if age < ceiling:
            return gap
    return REINFORCE_MIN_GAP
# SM-2's interval is unbounded — a well-remembered card reaches 1,225 days at
# its 7th review and 12,934 at its 9th. Strength decay is capped at a 365-day
# half-life, so a card scheduled that far out left its node reading unproven
# for the whole gap between reviews: correct, on time, and still faded. This is
# the largest gap a card may go, chosen so a fresh strength of 1.0 cannot decay
# below the 0.35 gate before the next review even at the slowest half-life —
# 365 * log(0.35, 0.5) ≈ 553 days, with margin for the review itself being late.
MAX_INTERVAL_DAYS = 500
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
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=8000")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with _lock, self._conn() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS profile (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    name TEXT, age REAL, hours_per_week REAL,
                    breadth TEXT, stage INTEGER, domains TEXT,
                    created_at REAL, settings TEXT DEFAULT '{}'
                );
                CREATE TABLE IF NOT EXISTS mastery (
                    node_id TEXT PRIMARY KEY,
                    level REAL DEFAULT 0,          -- 0..1 exponential moving avg
                    attempts INTEGER DEFAULT 0,
                    passes INTEGER DEFAULT 0,      -- attempts scoring >= PASS
                    first_pass_at REAL,
                    last_pass_at REAL,
                    strength REAL DEFAULT 0,       -- decays; refreshed by review
                    last_seen REAL,
                    assumed INTEGER DEFAULT 0,     -- credited by placement, untested
                    mastered_at REAL
                );
                CREATE TABLE IF NOT EXISTS srs_cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    front TEXT, back TEXT, node_id TEXT, article TEXT,
                    ef REAL DEFAULT 2.5, interval REAL DEFAULT 0,
                    reps INTEGER DEFAULT 0, lapses INTEGER DEFAULT 0,
                    due REAL, created_at REAL,
                    UNIQUE(front, node_id)
                );
                CREATE TABLE IF NOT EXISTS reading_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT, opened_at REAL, seconds REAL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT, payload TEXT, at REAL, xp INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS placement (
                    domain TEXT PRIMARY KEY,
                    stage INTEGER, asked TEXT DEFAULT '[]', done INTEGER DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_events_at ON events(at);
                CREATE TABLE IF NOT EXISTS burned(
                    node_id TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    at REAL NOT NULL,
                    PRIMARY KEY (node_id, fingerprint)
                );
                CREATE INDEX IF NOT EXISTS idx_burned_node ON burned(node_id, at);
                CREATE INDEX IF NOT EXISTS idx_cards_due ON srs_cards(due);
                CREATE INDEX IF NOT EXISTS idx_reading_title ON reading_log(title);
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
            ]:
                try:
                    c.execute(ddl)
                except sqlite3.OperationalError:
                    pass

    # ---------- profile ----------

    def get_profile(self) -> Optional[Dict]:
        with _lock, self._conn() as c:
            row = c.execute("SELECT * FROM profile WHERE id=1").fetchone()
        if not row:
            return None
        p = dict(row)
        p["domains"] = json.loads(p["domains"] or "[]")
        p["settings"] = json.loads(p["settings"] or "{}")
        s = min(int(p["stage"] or 0), 5)
        p["stage_name"] = STAGE_NAMES[s]
        p["stage_span"] = STAGE_SPAN[s]
        p["title"] = STAGE_TITLES[s]
        p["xp"] = self.total_xp()
        p["streak"] = self.streak_days()
        return p

    def save_profile(self, name: str, age: float, hours_per_week: float,
                     breadth: str, stage: int, domains: List[str],
                     settings: Optional[Dict] = None) -> Dict:
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
                """INSERT INTO profile(id, name, age, hours_per_week, breadth, stage, domains, created_at, settings)
                   VALUES(1,?,?,?,?,?,?,?,?)
                   ON CONFLICT(id) DO UPDATE SET name=excluded.name, age=excluded.age,
                     hours_per_week=excluded.hours_per_week, breadth=excluded.breadth,
                     stage=excluded.stage, domains=excluded.domains,
                     settings=COALESCE(excluded.settings, profile.settings)""",
                (name, age, hours_per_week, breadth, stage, json.dumps(domains),
                 time.time(), payload),
            )
        return self.get_profile()

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
        half_life = min(
            STRENGTH_HALF_LIFE * (1 + STRENGTH_HALF_LIFE_STEP * max(0, (reinforcements or 1) - 1)),
            STRENGTH_HALF_LIFE_MAX)
        return strength * (0.5 ** ((now - last_seen) / half_life))

    def mastery_map(self) -> Dict[str, float]:
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
            rows = c.execute("SELECT node_id, level FROM mastery").fetchall()
        return {r["node_id"]: r["level"] for r in rows}

    def mastered_set(self) -> set:
        """Nodes currently standing as mastered — earned or assumed, not faded.

        Decay applies here for the same reason it applies to `proven_set` and
        `gate_map`: three functions answering one question three different ways
        put `proven: false`, `mastered: true` and `mastery_detail.proven: true`
        in a single response body.
        """
        now = time.time()
        with _lock, self._conn() as c:
            rows = c.execute(
                """SELECT node_id, strength, last_seen, reinforcements FROM mastery
                   WHERE mastered_at IS NOT NULL""").fetchall()
        return {r["node_id"] for r in rows
                if self._strength_now(r["strength"] or 0, r["last_seen"], now,
                                      r["reinforcements"]) >= 0.35}

    def gate_map(self) -> Dict[str, float]:
        """Map for the curriculum's unlock/gate logic: 1.0 for genuinely
        mastered nodes, otherwise the raw level capped below the 0.8 gate so a
        not-yet-mastered node can never open the next one.

        Mastery that has decayed below half strength no longer counts as open —
        forgotten foundations re-lock what they used to unlock, until refreshed.
        """
        now = time.time()
        with _lock, self._conn() as c:
            rows = c.execute(
                "SELECT node_id, level, mastered_at, strength, last_seen, reinforcements "
                "FROM mastery").fetchall()
        out = {}
        for r in rows:
            if r["mastered_at"] is not None:
                s = self._strength_now(r["strength"] or 0, r["last_seen"], now,
                                       r["reinforcements"])
                out[r["node_id"]] = 1.0 if s >= 0.35 else min(r["level"], 0.79)
            else:
                out[r["node_id"]] = min(r["level"], 0.79)
        return out

    def passed_set(self) -> set:
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
                   FROM mastery WHERE passes >= 1""").fetchall()
        return {r["node_id"] for r in rows
                if self._strength_now(r["strength"] or 0, r["last_seen"], now,
                                      r["reinforcements"]) >= 0.35}

    def mastery_detail(self, node_id: str) -> Dict:
        """What this node still needs, in terms the book can explain."""
        with _lock, self._conn() as c:
            r = c.execute(
                """SELECT level, passes, first_pass_at, mastered_at, assumed,
                          strength, last_seen, reinforcements, first_mastered_at
                   FROM mastery WHERE node_id=?""", (node_id,)).fetchone()
        if not r:
            return {"passes": 0, "passes_needed": 2, "ready_at": None,
                    "mastered": False, "proven": False, "assumed": False,
                    "ever_proven": False, "faded": False}
        ready_at = None
        if r["first_pass_at"]:
            ready = r["first_pass_at"] + MASTERY_MIN_INTERVAL
            ready_at = ready if ready > time.time() else None
        fresh = self._strength_now(r["strength"] or 0, r["last_seen"], time.time(),
                                   r["reinforcements"]) >= 0.35
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
            "assumed": mastered and not proven and not ever_proven,
        }

    def proven_count_current(self) -> int:
        """Proven nodes whose memory has not decayed away — the honest headline
        number, matching what the gates actually treat as open."""
        now = time.time()
        with _lock, self._conn() as c:
            rows = c.execute(
                """SELECT strength, last_seen, reinforcements FROM mastery
                   WHERE mastered_at IS NOT NULL AND assumed=0""").fetchall()
        return sum(1 for r in rows
                   if self._strength_now(r["strength"] or 0, r["last_seen"], now,
                                         r["reinforcements"]) >= 0.35)

    def proven_set(self) -> set:
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
                   WHERE mastered_at IS NOT NULL AND assumed=0"""
            ).fetchall()
        return {r["node_id"] for r in rows
                if self._strength_now(r["strength"] or 0, r["last_seen"], now,
                                      r["reinforcements"]) >= 0.35}

    def ever_proven_set(self) -> set:
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
                "SELECT node_id FROM mastery WHERE first_mastered_at IS NOT NULL"
            ).fetchall()
        return {r["node_id"] for r in rows}

    def _apply_attempt(self, c, node_id: str, score: float, assumed: bool, now: float):
        prof_row = c.execute("SELECT age FROM profile WHERE id=1").fetchone()
        min_gap = _reinforce_min_gap(prof_row["age"] if prof_row else None)
        row = c.execute("SELECT * FROM mastery WHERE node_id=?", (node_id,)).fetchone()
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
                          and (now - first_pass) >= MASTERY_MIN_INTERVAL)
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
        c.execute(
            """INSERT INTO mastery(node_id, level, attempts, passes, first_pass_at,
                                   last_pass_at, strength, last_seen, assumed,
                                   mastered_at, reinforcements, reinforced_at,
                                   first_mastered_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(node_id) DO UPDATE SET level=?, attempts=?, passes=?,
                 first_pass_at=?, last_pass_at=?, strength=?, last_seen=?, assumed=?,
                 mastered_at=?, reinforcements=?, reinforced_at=?, first_mastered_at=?""",
            (node_id, level, attempts, passes, first_pass, last_pass, strength, now,
             was_assumed, mastered_at, reinforcements, reinforced_at_write, first_mastered_at,
             level, attempts, passes, first_pass, last_pass, strength, now,
             was_assumed, mastered_at, reinforcements, reinforced_at_write, first_mastered_at),
        )
        return level, mastered_at is not None, newly_mastered, lost_mastery

    def record_attempt(self, node_id: str, score: float, assumed: bool = False) -> Dict:
        """Record a graded attempt (score 0..1). Returns mastery + xp_gained."""
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
                "SELECT first_mastered_at FROM mastery WHERE node_id=?",
                (node_id,)).fetchone()
            first_ever = not (_prior and _prior["first_mastered_at"])
            level, mastered, newly, lost = self._apply_attempt(c, node_id, score, assumed, now)
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
                day_start = _local_midnight(now)
                already = c.execute(
                    """SELECT 1 FROM events WHERE kind='attempt' AND at >= ?
                       AND json_extract(payload, '$.node') = ?
                       AND json_extract(payload, '$.score') >= 0.5 LIMIT 1""",
                    (day_start, node_id)).fetchone()
                # A floor, not a straight line: below half marks is closer to
                # guessing than to retrieval, and paying it proportionally
                # meant 343 randomly-answered papers (mean score 0.198, zero
                # masteries) still earned 660 XP — 3.6x an honest day's worth.
                # XP should track successful retrieval, not mere participation.
                xp = ((0 if already or score < 0.5 else round(score * 12))
                      + (60 if newly and first_ever else 0))
                c.execute("INSERT INTO events(kind, payload, at, xp) VALUES('attempt',?,?,?)",
                          (json.dumps({"node": node_id, "score": round(score, 2),
                                       "mastered": newly}), now, xp))
        proven = node_id in self.proven_set()
        return {"node_id": node_id, "level": round(level, 3),
                "mastered": mastered, "newly_mastered": newly,
                "proven": proven, "lost_mastery": lost, "xp_gained": xp}

    def seed_assumed(self, node_ids: List[str]):
        """Bulk placement credit (assumed known)."""
        now = time.time()
        with _lock, self._conn() as c:
            for nid in node_ids:
                self._apply_attempt(c, nid, 0.85, True, now)

    def burn_item(self, node_id: str, fingerprint: str):
        """Record that the book has shown this item's answer to this reader.

        Immediate feedback teaches, and it must stay. But the key it reveals
        cannot then be the evidence that the reader knows the thing: a paper
        could simply be abandoned after reading its answers and a clean one sat
        moments later. The first-commitment lock stopped that *within* a paper;
        this stops it across papers.
        """
        with _lock, self._conn() as c:
            c.execute("""INSERT INTO burned(node_id, fingerprint, at) VALUES(?,?,?)
                         ON CONFLICT(node_id, fingerprint) DO UPDATE SET at=?""",
                      (node_id, fingerprint, time.time(), time.time()))

    def burned_map(self, node_id: str, window_days: float = 7.0) -> dict:
        """When each of this node's items last had its answer shown."""
        cutoff = time.time() - window_days * DAY
        with _lock, self._conn() as c:
            rows = c.execute(
                "SELECT fingerprint, at FROM burned WHERE node_id=? AND at>=?",
                (node_id, cutoff)).fetchall()
        return {r["fingerprint"]: r["at"] for r in rows}

    def burned_set(self, node_id: str, window_days: float = 7.0,
                   before: float = None) -> set:
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
                    "SELECT fingerprint FROM burned WHERE node_id=? AND at>=? AND at<?",
                    (node_id, cutoff, before)).fetchall()
            else:
                rows = c.execute(
                    "SELECT fingerprint FROM burned WHERE node_id=? AND at>=?",
                    (node_id, cutoff)).fetchall()
        return {r["fingerprint"] for r in rows}

    def revoke_assumed(self, node_ids: List[str]):
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
            c.executemany("DELETE FROM mastery WHERE node_id=? AND assumed=1",
                          [(nid,) for nid in node_ids])
            return c.total_changes

    def mastered_count(self) -> int:
        return len(self.mastered_set())

    def proven_count(self) -> int:
        with _lock, self._conn() as c:
            return c.execute(
                "SELECT COUNT(*) FROM mastery WHERE mastered_at IS NOT NULL AND assumed=0"
            ).fetchone()[0]

    # ---------- spaced repetition (SM-2) ----------

    def add_cards(self, cards: List[Dict]) -> int:
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
                        """INSERT OR IGNORE INTO srs_cards(front, back, node_id, article,
                                                  due, created_at, origin)
                           VALUES(?,?,?,?,?,?,?)""",
                        (front, back, card.get("node_id", ""),
                         card.get("article", ""), now + RELEARN_DELAY, now,
                         card.get("origin", "book")),
                    )
                    added += c.execute("SELECT changes()").fetchone()[0]
                except Exception:
                    pass
        return added

    def due_cards(self, limit: int = 20) -> List[Dict]:
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
                       FROM srs_cards WHERE due <= ?)
                   WHERE rn <= ? ORDER BY due""",
                (now, max(3, limit)),
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

    REVIEW_XP_DAILY_CAP = 120
    CALIBRATION_WINDOW = 10          # recent quiz sittings considered
    OVERCONFIDENCE_LIMIT = 1 / 3     # above this, self-grades are discounted
    OVERCONFIDENT_RESTORE_CAP = 0.85  # capped strength restore for q>=4

    def _overconfidence_rate(self, c, window: int = CALIBRATION_WINDOW) -> float:
        """Fraction of recent confident quiz answers that were wrong.

        Reads the last `window` 'calibration' events (logged by the quiz
        route with per-sitting overconfident/underconfident/total counts) and
        pools them. Takes an open connection: callers already hold `_lock`,
        which is not reentrant.
        """
        rows = c.execute(
            "SELECT payload FROM events WHERE kind='calibration' "
            "ORDER BY at DESC LIMIT ?", (window,)).fetchall()
        over = total = 0
        for r in rows:
            try:
                p = json.loads(r["payload"])
            except (ValueError, TypeError):
                continue
            over += int(p.get("overconfident") or 0)
            total += int(p.get("total") or 0)
        return over / total if total else 0.0

    def overconfidence_rate(self, window: int = CALIBRATION_WINDOW) -> float:
        """Public wrapper for the reader's recent overconfidence rate."""
        with _lock, self._conn() as c:
            return self._overconfidence_rate(c, window)

    def _review_xp_today(self, c) -> int:
        """XP already paid for reviews since local midnight."""
        start = _local_midnight(time.time())
        row = c.execute("SELECT COALESCE(SUM(xp), 0) FROM events "
                        "WHERE kind='review' AND at>=?", (start,)).fetchone()
        return int(row[0] or 0)

    def review_card(self, card_id: int, quality: int) -> Dict:
        """SM-2. quality: 0 (blank) .. 5 (perfect). A lapse also lowers the
        related node's strength and can flag it for refresh."""
        now = time.time()
        quality = max(0, min(5, quality))
        with _lock, self._conn() as c:
            row = c.execute("SELECT * FROM srs_cards WHERE id=?", (card_id,)).fetchone()
            if not row:
                return {"error": "no such card"}
            prof_row = c.execute("SELECT age FROM profile WHERE id=1").fetchone()
            min_gap = _reinforce_min_gap(prof_row["age"] if prof_row else None)
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
                    interval = 1
                elif reps == 1:
                    interval = 6
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
                "UPDATE srs_cards SET ef=?, interval=?, reps=?, lapses=?, due=? WHERE id=?",
                (ef, interval, reps, lapses, due, card_id),
            )
            # Feed the outcome back to node mastery strength — the deck is the
            # memory, so repeated lapses can un-master a node entirely.
            node_id = row["node_id"]
            if node_id:
                m = c.execute("SELECT strength, mastered_at, passes, reinforced_at, "
                              "last_seen, reinforcements FROM mastery WHERE node_id=?",
                              (node_id,)).fetchone()
                if m:
                    # The adjustment below has to start from what the reader
                    # actually retains *right now*, not the value frozen at the
                    # last write. Reading the raw stored strength meant a single
                    # blank review could raise a node that had decayed to
                    # near-zero straight back to "proven": strength 1.0 minus
                    # 0.25 is 0.75, comfortably above the 0.35 gate, even though
                    # two years untouched had left the true value at 0.001.
                    strength = self._strength_now(m["strength"] or 0, m["last_seen"],
                                                  now, m["reinforcements"])
                    # A card the reader wrote is their own note, not evidence.
                    # Letting it feed strength meant `front:"q", back:"a"`,
                    # self-graded 5, fully restored a decayed gate.
                    reader_card = (row["origin"] or "book") != "book"
                    # last_seen is the decay clock's zero point, so it may only
                    # move on real evidence — a reader-card grade, of either
                    # sign, is not that, and writing it unconditionally let
                    # `/api/review/add` then a single quality-0 grade restore a
                    # two-year-faded node to a fresh clock.
                    touch_clock = False
                    if quality >= 4 and not reader_card:
                        # A confident, successful review is full evidence of
                        # current retention — the same standing a fresh quiz
                        # pass already gets. A small additive nudge instead
                        # compounded into a permanent failure mode: once the
                        # interval between reviews grew faster than the +0.15
                        # could repay, strength converged to a fixed point
                        # under the 0.35 gate and stayed there forever, so a
                        # node reviewed exactly on schedule for years still
                        # read as faded.
                        #
                        # Calibration modulation: quality here is *self-graded*,
                        # and the quiz route measures how trustworthy this
                        # reader's confidence actually is (miscalibration —
                        # confident-and-wrong — is well documented; Dunning &
                        # Kruger 1999; Koriat & Bjork 2005 on foresight bias).
                        # When more than a third of their recently confident
                        # quiz answers were wrong, a self-graded 4-5 is weaker
                        # evidence than it claims, so the restore is capped
                        # below full rather than taken at face value.
                        overconfident = (self._overconfidence_rate(c)
                                         > self.OVERCONFIDENCE_LIMIT)
                        if overconfident:
                            strength = max(strength, self.OVERCONFIDENT_RESTORE_CAP)
                        else:
                            strength = 1.0
                        touch_clock = True
                        # Only a *spaced* success builds durability. Without the
                        # gap, minting cards and grading them in one sitting
                        # made a node permanent in zero elapsed time.
                        #
                        # And only a *credible* one. The cap above already says
                        # this self-grade is weaker evidence than it claims —
                        # but a `reinforcements` bump is the more consequential
                        # payment of the two: strength resets on the next real
                        # pass anyway, while the half-life extension is
                        # permanent. Discounting the restore and then paying
                        # full durability growth on the same distrusted grade
                        # let an overconfident reader ratchet a node's half-
                        # life to the ceiling on evidence the calibration
                        # model had just declared unreliable. One discount,
                        # applied to everything the grade buys: while the
                        # reader's confident quiz answers are wrong more than a
                        # third of the time, a self-graded success neither
                        # fully restores nor lengthens the half-life.
                        last_r = m["reinforced_at"] if "reinforced_at" in m.keys() else None
                        if (not overconfident
                                and (not last_r or (now - last_r) >= min_gap)):
                            c.execute("UPDATE mastery SET reinforcements = "
                                      "COALESCE(reinforcements, 1) + 1, reinforced_at=? "
                                      "WHERE node_id=?", (now, node_id))
                    elif quality == 3 and not reader_card:
                        # Correct with serious difficulty. This used to leave
                        # the node untouched entirely — no strength, no clock —
                        # which threw away the strongest kind of evidence there
                        # is: effortful successful retrieval (the "desirable
                        # difficulties" and testing-effect literature — Bjork;
                        # Roediger & Karpicke 2006 — finds hard-won recall more
                        # potent for retention than easy recall). Not full
                        # restoration (that is q>=4's claim), but a partial
                        # refresh: the decay clock restarts, and strength is
                        # floored at a modest level above the 0.35 gate.
                        strength = max(strength, 0.5)
                        touch_clock = True
                    elif quality < 3 and not reader_card:
                        strength = max(0.0, strength - 0.25)
                        touch_clock = True
                    if (quality < 3 and (row["origin"] or "book") == "book"
                            and m["mastered_at"] is not None and strength <= 0.2):
                        # Forgotten badly enough to need re-proving.
                        c.execute(
                            """UPDATE mastery SET strength=?, last_seen=?, mastered_at=NULL,
                               passes=?, first_pass_at=? WHERE node_id=?""",
                            (strength, now, min(m["passes"] or 0, 1), now, node_id))
                    elif touch_clock:
                        c.execute("UPDATE mastery SET strength=?, last_seen=? WHERE node_id=?",
                                  (strength, now, node_id))
            # Only successful retrieval pays — a blank is practice, not progress.
            if lapses >= 6 and quality < 3:
                # A card failed this often is badly formed or too hard: park it
                # for a week rather than grinding the reader on it daily.
                due = now + 7 * DAY
                c.execute("UPDATE srs_cards SET due=? WHERE id=?", (due, card_id))
                log.info("leech card %s parked after %d lapses", card_id, lapses)
            xp = 5 if quality >= 4 else (3 if quality >= 3 else 0)
            # A day's reviewing is worth a day's credit. The due check stops one
            # card being drilled all afternoon, but not two hundred cards being
            # written and graded in a sitting — which paid 1,000 XP for nothing.
            # Streaks and levels are built on this number, so it needs a ceiling.
            room = max(0, self.REVIEW_XP_DAILY_CAP - self._review_xp_today(c))
            xp = min(xp, room)
            c.execute("INSERT INTO events(kind, payload, at, xp) VALUES('review',?,?,?)",
                      (json.dumps({"card": card_id, "q": quality}), now, xp))
        return {"id": card_id, "next_days": round(max((due - now) / DAY, 0.01), 2),
                "xp_gained": xp, "lapses": lapses}

    def deck_stats(self) -> Dict:
        now = time.time()
        with _lock, self._conn() as c:
            total = c.execute("SELECT COUNT(*) FROM srs_cards").fetchone()[0]
            due = c.execute("SELECT COUNT(*) FROM srs_cards WHERE due <= ?", (now,)).fetchone()[0]
        return {"total": total, "due": due}

    def nodes_needing_refresh(self, limit: int = 8) -> List[str]:
        """Mastered nodes whose strength has decayed or that have a due card —
        the deck telling us what to reinforce."""
        now = time.time()
        with _lock, self._conn() as c:
            rows = c.execute(
                """SELECT node_id, strength, last_seen, reinforcements FROM mastery
                   WHERE mastered_at IS NOT NULL""").fetchall()
        out = []
        for r in rows:
            s = self._strength_now(r["strength"] or 0, r["last_seen"], now, r["reinforcements"])
            if s < 0.5:
                out.append((r["node_id"], s))
        out.sort(key=lambda x: x[1])
        return [n for n, _ in out[:limit]]

    # ---------- reading log / motivation ----------

    READ_XP_DAILY_CAP = 30    # ~10 distinct articles' worth; a real day's reading

    def _read_xp_today(self, c) -> int:
        start = _local_midnight(time.time())
        row = c.execute("SELECT COALESCE(SUM(xp), 0) FROM events "
                        "WHERE kind='read' AND at>=?", (start,)).fetchone()
        return int(row[0] or 0)

    def log_reading(self, title: str, seconds: float = 0):
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
                "SELECT 1 FROM reading_log WHERE title=? LIMIT 1", (title,)).fetchone() is None
            c.execute("INSERT INTO reading_log(title, opened_at, seconds) VALUES(?,?,?)",
                      (title, now, seconds))
            room = max(0, self.READ_XP_DAILY_CAP - self._read_xp_today(c))
            xp = min(3, room) if first_ever else 0
            c.execute("INSERT INTO events(kind, payload, at, xp) VALUES('read',?,?,?)",
                      (json.dumps({"title": title}), now, xp))

    def reading_stats(self) -> Dict:
        with _lock, self._conn() as c:
            n = c.execute("SELECT COUNT(DISTINCT title) FROM reading_log").fetchone()[0]
            recent = c.execute(
                "SELECT title, MAX(opened_at) m FROM reading_log GROUP BY title ORDER BY m DESC LIMIT 12"
            ).fetchall()
        return {"articles_read": n, "recent": [r["title"] for r in recent]}

    def total_xp(self) -> int:
        with _lock, self._conn() as c:
            row = c.execute("SELECT COALESCE(SUM(xp),0) FROM events").fetchone()
        return int(row[0] or 0)

    def xp_today(self) -> int:
        start = _local_midnight(time.time())
        with _lock, self._conn() as c:
            row = c.execute("SELECT COALESCE(SUM(xp),0) FROM events WHERE at>=?", (start,)).fetchone()
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
        relevant = [d for d in days if d <= anchor]
        if not relevant:
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
        for d in reversed(relevant):
            gap = expect - d
            if gap:
                nearby = [s for s in spent if s - d < STREAK_FREEZE_RENEW_DAYS]
                if len(nearby) + gap > STREAK_FREEZES:
                    break
                spent.extend(d + 1 + i for i in range(gap))
            run += 1
            expect = d - 1
        # Freezes "used" as of the anchor itself — the ones still unexpired.
        used = sum(1 for s in spent if anchor - s < STREAK_FREEZE_RENEW_DAYS)
        return run, used

    def _streak_walk(self) -> tuple:
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
            rows = c.execute(
                "SELECT DISTINCT date(at, 'unixepoch', 'localtime') d "
                "FROM events ORDER BY d ASC").fetchall()
        if not rows:
            return 0, STREAK_FREEZES, 0
        days = [datetime.date.fromisoformat(r["d"]).toordinal() for r in rows]
        today = _local_day(time.time())
        # Anchor to the reader's most recent activity when it's today or
        # yesterday — today's box hasn't closed yet, so nothing has been
        # missed there. Fall back to yesterday for a genuinely stale streak,
        # where the gap to the present is real and must be charged.
        anchor = days[-1] if days[-1] >= today - 1 else today - 1
        current, used = self._bridged_run_ending_at(days, anchor)
        best = max((self._bridged_run_ending_at(days, a)[0] for a in days), default=0)
        best = max(best, current)
        return current, max(0, STREAK_FREEZES - used), best

    def streak_days(self) -> int:
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
        return self._streak_walk()[0]

    def best_streak_days(self) -> int:
        """The longest run the reader has ever put together, past or present.

        `prune()` keeps one row per calendar day forever specifically so this
        number survives past the retention window — a durable record that
        was being computed nowhere and shown nowhere, so a reader's best
        stretch was invisible the moment their current streak broke. Comes
        from the same walk as streak_days() and freezes_left(), so a past
        streak is graded by exactly the rule today's is.
        """
        return self._streak_walk()[2]

    def streak_milestone(self) -> Optional[int]:
        """Return a milestone (3/7/30/100/365) if today's activity just reached
        one, so the book can celebrate it exactly once."""
        streak = self.streak_days()
        if streak in (3, 7, 30, 100, 365) and self.active_today():
            return streak
        return None

    def freezes_left(self) -> int:
        """How many single-day gaps are currently available to spend.

        Shares its walk with streak_days() and best_streak_days() via
        _streak_walk() — the three used to carry independent copies of this
        logic and repeatedly drifted out of sync. One shared implementation
        means they can no longer disagree about where "today" starts, how a
        gap gets bridged, or how long a spent freeze stays spent.
        """
        return self._streak_walk()[1]

    def active_today(self) -> bool:
        start = _local_midnight(time.time())
        with _lock, self._conn() as c:
            return c.execute("SELECT 1 FROM events WHERE at>=? LIMIT 1", (start,)).fetchone() is not None

    def journal(self, limit: int = 40) -> List[Dict]:
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
                "FROM mastery WHERE COALESCE(first_mastered_at, mastered_at) IS NOT NULL "
                "AND assumed=0 ORDER BY at DESC LIMIT ?",
                (limit,)).fetchall()
            asc = c.execute(
                "SELECT kind, payload, at FROM events WHERE kind IN ('ascension','chapter') "
                "ORDER BY at DESC LIMIT ?", (limit,)).fetchall()
        items = [{"kind": "mastered", "node_id": r["node_id"], "at": r["at"]} for r in mast]
        for r in asc:
            try:
                items.append({"kind": r["kind"], "at": r["at"], **json.loads(r["payload"])})
            except Exception:
                pass
        items.sort(key=lambda x: x.get("at") or 0, reverse=True)
        return items[:limit]

    def log_event(self, kind: str, payload: Dict, xp: int = 0):
        with _lock, self._conn() as c:
            c.execute("INSERT INTO events(kind, payload, at, xp) VALUES(?,?,?,?)",
                      (kind, json.dumps(payload), time.time(), xp))

    # ---------- placement ----------

    PLACEMENT_COOLING = 7 * DAY  # a settled placement can be re-measured after this

    def placement_state(self) -> Dict[str, Dict]:
        with _lock, self._conn() as c:
            rows = c.execute("SELECT * FROM placement").fetchall()
        return {r["domain"]: {"stage": r["stage"], "asked": json.loads(r["asked"]),
                              "done": bool(r["done"]),
                              "settled_at": r["settled_at"]} for r in rows}

    def placement_update(self, domain: str, stage: int, asked: List[str], done: bool):
        now = time.time()
        with _lock, self._conn() as c:
            # settled_at records when the domain settled, so re-measurement can
            # apply a cooling period; it is kept across further done writes and
            # cleared if the domain is somehow marked unsettled again.
            c.execute(
                """INSERT INTO placement(domain, stage, asked, done, settled_at)
                   VALUES(?,?,?,?,?)
                   ON CONFLICT(domain) DO UPDATE SET stage=?, asked=?, done=?,
                     settled_at=CASE WHEN ?
                                     THEN COALESCE(placement.settled_at, ?)
                                     ELSE NULL END""",
                (domain, stage, json.dumps(asked), int(done),
                 now if done else None,
                 stage, json.dumps(asked), int(done), int(done), now),
            )

    def reopen_placement(self, domain: str, cooling_days: float = 7.0) -> bool:
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
            r = c.execute("SELECT done, settled_at FROM placement WHERE domain=?",
                          (domain,)).fetchone()
            if not r or not r["done"]:
                return False
            # Rows settled before settled_at existed have no timestamp; they
            # are by definition old enough, so treat them as past cooling.
            if r["settled_at"] and (now - r["settled_at"]) < cooling_days * DAY:
                return False
            c.execute("UPDATE placement SET done=0, settled_at=NULL WHERE domain=?",
                      (domain,))
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

    def events_today(self, kind: str) -> bool:
        """Has an event of this kind been logged since local midnight?

        The server asked this by reaching through _conn() into the events
        table, which made a private cursor part of its interface. The
        question belongs here, next to the table that answers it.
        """
        with self._conn() as c:
            row = c.execute(
                "SELECT 1 FROM events WHERE kind=? AND at>=? LIMIT 1",
                (kind, _local_midnight(time.time())),
            ).fetchone()
        return row is not None

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
            keep_ids = {r[0] for r in c.execute(
                "SELECT MIN(id) FROM events WHERE at < ? "
                "GROUP BY date(at, 'unixepoch', 'localtime')", (cutoff,))}
            stale = [r[0] for r in c.execute(
                "SELECT id FROM events WHERE at < ? AND xp = 0", (cutoff,)).fetchall()
                if r[0] not in keep_ids]
            if stale:
                c.executemany("DELETE FROM events WHERE id=?", [(i,) for i in stale])


def _local_day(ts: float) -> int:
    # Index of the local calendar day; consecutive days differ by exactly 1.
    # Uses the calendar date directly rather than dividing an epoch timestamp
    # by 86400 — a "day" is not always 86400 seconds long. Identical study
    # behaviour read as streak 38 in a DST-free window and streak 2 across the
    # US fall-back, because a single day is 23 or 25 hours across the
    # transition and epoch division does not know that.
    lt = time.localtime(ts)
    return datetime.date(lt.tm_year, lt.tm_mon, lt.tm_mday).toordinal()


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
