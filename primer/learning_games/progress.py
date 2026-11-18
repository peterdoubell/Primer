"""Reader-specific checkpoints for learning sequences.

Three small tables beside the rest of the learner record.  They hold where a
reader is in a sequence and how each step went, so a sequence can be resumed
on another day or another device, and so the same submission arriving twice
changes nothing the second time.

What these tables are *not* is evidence.  Nothing here feeds ``mastery``: a
sequence is study, marked as study, and the quiz remains the only thing that
can prove a module.  Growth is paid through the same ``events`` ledger every
other channel uses, once per sequence, under a daily cap — the same shape as
the reading channel, for the same reason (a first-party button must not be an
unbounded farm).
"""
from __future__ import annotations

import datetime
import hashlib
import json
import threading
import time
from typing import Dict, List, Optional, Tuple

from .. import learner as learner_module

# A sequence is three to five minutes of checked work: worth more than opening
# an article (3), less than a passing quiz (up to 12), and never mastery.
SEQUENCE_XP = 6
XP_DAILY_CAP = 30
# Two different wrong responses, and the book will show the answer rather than
# leave a reader stuck on a study step.
REVEAL_AFTER = 2

_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS lg_steps (
        reader_id INTEGER NOT NULL DEFAULT 1,
        node_id TEXT NOT NULL, slug TEXT NOT NULL, step_id TEXT NOT NULL,
        fingerprint TEXT NOT NULL,
        attempts INTEGER DEFAULT 0,
        hints INTEGER DEFAULT 0,
        status TEXT DEFAULT 'open',
        first_try INTEGER DEFAULT 0,
        last_response TEXT DEFAULT '',
        detail TEXT DEFAULT '{}',
        updated_at REAL,
        PRIMARY KEY (reader_id, node_id, slug, step_id))""",
    """CREATE TABLE IF NOT EXISTS lg_sequences (
        reader_id INTEGER NOT NULL DEFAULT 1,
        node_id TEXT NOT NULL, slug TEXT NOT NULL,
        started_at REAL, updated_at REAL, completed_at REAL,
        plays INTEGER DEFAULT 0,
        cursor TEXT DEFAULT '',
        xp_paid INTEGER DEFAULT 0,
        run_done INTEGER DEFAULT 0,
        PRIMARY KEY (reader_id, node_id, slug))""",
    """CREATE TABLE IF NOT EXISTS lg_days (
        reader_id INTEGER NOT NULL DEFAULT 1,
        node_id TEXT NOT NULL, local_day TEXT NOT NULL, at REAL NOT NULL,
        PRIMARY KEY (reader_id, node_id, local_day))""",
)
_ready = set()
_ready_lock = threading.Lock()


def _local_day(now: float) -> str:
    return datetime.date.fromordinal(learner_module._local_day(now)).isoformat()


def response_key(response: Dict) -> str:
    packed = json.dumps(response, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(packed.encode("utf-8")).hexdigest()[:16]


class ProgressStore:
    """Checkpoint reads and writes against one learner store."""

    def __init__(self, learner_store):
        self.learner = learner_store
        self._ensure()

    def _ensure(self) -> None:
        key = (self.learner.db_path, learner_module.store.turso_url() or "")
        with _ready_lock:
            if key in _ready:
                return
            with learner_module._lock, self.learner._conn() as c:
                for statement in _SCHEMA:
                    c.execute(statement)
            _ready.add(key)

    # ------------------------------------------------------------ reads

    def load(self, reader_id: int, node_id: str, slug: str) -> Tuple[Optional[Dict], Dict[str, Dict]]:
        with learner_module._lock, self.learner._conn() as c:
            return self._load(c, reader_id, node_id, slug)

    @staticmethod
    def _load(c, reader_id, node_id, slug):
        seq = c.execute(
            "SELECT * FROM lg_sequences WHERE reader_id=? AND node_id=? AND slug=?",
            (reader_id, node_id, slug)).fetchone()
        rows = c.execute(
            "SELECT * FROM lg_steps WHERE reader_id=? AND node_id=? AND slug=?",
            (reader_id, node_id, slug)).fetchall()
        steps = {}
        for row in rows:
            entry = dict(row)
            try:
                entry["detail"] = json.loads(entry.get("detail") or "{}")
            except ValueError:
                entry["detail"] = {}
            steps[entry["step_id"]] = entry
        return (dict(seq) if seq else None), steps

    def overview(self, reader_id: int, node_id: str) -> Dict[str, Dict]:
        """Sequence rows for one module, keyed by slug, with solved-step counts."""
        with learner_module._lock, self.learner._conn() as c:
            rows = c.execute("SELECT * FROM lg_sequences WHERE reader_id=? AND node_id=?",
                             (reader_id, node_id)).fetchall()
            done = c.execute(
                "SELECT slug, step_id, fingerprint, status FROM lg_steps "
                "WHERE reader_id=? AND node_id=? AND status IN ('solved','revealed')",
                (reader_id, node_id)).fetchall()
        out = {row["slug"]: dict(row, done=[]) for row in rows}
        for row in done:
            out.setdefault(row["slug"], {"done": []})["done"].append(
                {"step_id": row["step_id"], "fingerprint": row["fingerprint"]})
        return out

    # ----------------------------------------------------------- writes

    def _touch(self, c, reader_id, node_id, slug, now, cursor=None) -> None:
        c.execute(
            "INSERT OR IGNORE INTO lg_sequences(reader_id, node_id, slug, started_at, updated_at) "
            "VALUES(?,?,?,?,?)", (reader_id, node_id, slug, now, now))
        if cursor is None:
            c.execute("UPDATE lg_sequences SET updated_at=? WHERE reader_id=? AND node_id=? AND slug=?",
                      (now, reader_id, node_id, slug))
        else:
            c.execute("UPDATE lg_sequences SET updated_at=?, cursor=? "
                      "WHERE reader_id=? AND node_id=? AND slug=?",
                      (now, cursor, reader_id, node_id, slug))

    def _row(self, c, reader_id, node_id, slug, step) -> Dict:
        """This step's checkpoint, started afresh if the step's content changed."""
        row = c.execute(
            "SELECT * FROM lg_steps WHERE reader_id=? AND node_id=? AND slug=? AND step_id=?",
            (reader_id, node_id, slug, step["id"])).fetchone()
        if row is not None and row["fingerprint"] == step["fingerprint"]:
            entry = dict(row)
            try:
                entry["detail"] = json.loads(entry.get("detail") or "{}")
            except ValueError:
                entry["detail"] = {}
            return entry
        c.execute(
            "INSERT OR REPLACE INTO lg_steps(reader_id, node_id, slug, step_id, fingerprint, "
            "attempts, hints, status, first_try, last_response, detail, updated_at) "
            "VALUES(?,?,?,?,?,0,0,'open',0,'','{}',?)",
            (reader_id, node_id, slug, step["id"], step["fingerprint"], time.time()))
        return {"reader_id": reader_id, "node_id": node_id, "slug": slug, "step_id": step["id"],
                "fingerprint": step["fingerprint"], "attempts": 0, "hints": 0, "status": "open",
                "first_try": 0, "last_response": "", "detail": {}}

    def _save(self, c, row: Dict, now: float) -> None:
        c.execute(
            "UPDATE lg_steps SET attempts=?, hints=?, status=?, first_try=?, last_response=?, "
            "detail=?, updated_at=? WHERE reader_id=? AND node_id=? AND slug=? AND step_id=?",
            (row["attempts"], row["hints"], row["status"], row["first_try"], row["last_response"],
             json.dumps(row["detail"], sort_keys=True), now,
             row["reader_id"], row["node_id"], row["slug"], row["step_id"]))

    def step(self, reader_id: int, node_id: str, slug: str, step: Dict) -> Dict:
        with learner_module._lock, self.learner._conn() as c:
            return self._row(c, reader_id, node_id, slug, step)

    def wrong(self, reader_id: int, node_id: str, slug: str, step: Dict, key: str) -> Dict:
        """Count a wrong response once: sending the same one again is not a new attempt."""
        now = time.time()
        with learner_module._lock, self.learner._conn() as c:
            row = self._row(c, reader_id, node_id, slug, step)
            if row["status"] == "open" and row["last_response"] != key:
                row["attempts"] += 1
                row["last_response"] = key
                self._save(c, row, now)
            self._touch(c, reader_id, node_id, slug, now, step["id"])
            return row

    def settle(self, reader_id: int, node_id: str, slug: str, step: Dict, status: str) -> Tuple[Dict, bool]:
        """Mark a step solved or revealed.  Returns (row, changed): the first settlement stands."""
        now = time.time()
        with learner_module._lock, self.learner._conn() as c:
            row = self._row(c, reader_id, node_id, slug, step)
            changed = row["status"] == "open"
            if changed:
                row["status"] = status
                row["first_try"] = int(status == "solved" and row["attempts"] == 0)
                self._save(c, row, now)
                self._touch(c, reader_id, node_id, slug, now, step["id"])
            return row, changed

    def hint(self, reader_id: int, node_id: str, slug: str, step: Dict) -> Dict:
        now = time.time()
        with learner_module._lock, self.learner._conn() as c:
            row = self._row(c, reader_id, node_id, slug, step)
            if row["status"] == "open" and row["hints"] < len(step.get("hints") or []):
                row["hints"] += 1
                self._save(c, row, now)
                self._touch(c, reader_id, node_id, slug, now, step["id"])
            return row

    def clue(self, reader_id: int, node_id: str, slug: str, step: Dict, number: int) -> Dict:
        now = time.time()
        with learner_module._lock, self.learner._conn() as c:
            row = self._row(c, reader_id, node_id, slug, step)
            revealed = sorted(set(row["detail"].get("revealed") or []) | {number})
            if row["status"] == "open" and revealed != row["detail"].get("revealed"):
                row["detail"]["revealed"] = revealed
                self._save(c, row, now)
                self._touch(c, reader_id, node_id, slug, now, step["id"])
            return row

    def cursor(self, reader_id: int, node_id: str, slug: str, beat_id: str) -> None:
        with learner_module._lock, self.learner._conn() as c:
            self._touch(c, reader_id, node_id, slug, time.time(), beat_id)

    def restart(self, reader_id: int, node_id: str, slug: str) -> None:
        """Clear a sequence's step checkpoints for another run.

        The sequence row survives: its first completion, its play count and
        whatever growth it paid are history, and replaying must not rewrite
        them or earn them twice.
        """
        with learner_module._lock, self.learner._conn() as c:
            c.execute("DELETE FROM lg_steps WHERE reader_id=? AND node_id=? AND slug=?",
                      (reader_id, node_id, slug))
            c.execute("UPDATE lg_sequences SET cursor='', run_done=0, updated_at=? "
                      "WHERE reader_id=? AND node_id=? AND slug=?",
                      (time.time(), reader_id, node_id, slug))

    def studied_today(self, reader_id: int, node_id: str, slug: str) -> None:
        """One zero-growth event per module per local day.

        A reader who works half a sequence has studied today; the streak is a
        count of days with study in them, so the ledger should say so.  The
        claim row makes this exactly once however many steps follow.
        """
        now = time.time()
        with learner_module._lock, self.learner._conn() as c:
            claimed = c.execute(
                "INSERT OR IGNORE INTO lg_days(reader_id, node_id, local_day, at) VALUES(?,?,?,?)",
                (reader_id, node_id, _local_day(now), now)).rowcount == 1
            if claimed:
                c.execute(
                    "INSERT INTO events(kind, payload, at, xp, reader_id) VALUES('activity',?,?,0,?)",
                    (json.dumps({"node": node_id, "sequence": slug, "completed": False}), now, reader_id))

    def complete(self, reader_id: int, node_id: str, slug: str, steps: List[Dict],
                 rows: Dict[str, Dict]) -> Dict:
        """Close a run of a sequence.  Idempotent per run; growth is paid once ever."""
        now = time.time()
        total = len(steps)
        unaided = sum(1 for s in steps if rows.get(s["id"], {}).get("status") == "solved")
        first_try = sum(1 for s in steps if rows.get(s["id"], {}).get("first_try"))
        with learner_module._lock, self.learner._conn() as c:
            self._touch(c, reader_id, node_id, slug, now)
            seq = c.execute("SELECT * FROM lg_sequences WHERE reader_id=? AND node_id=? AND slug=?",
                            (reader_id, node_id, slug)).fetchone()
            if seq["run_done"]:
                return {"first": False, "repeat": True, "xp_gained": 0, "plays": seq["plays"],
                        "steps": total, "unaided": unaided, "first_try": first_try}
            first = seq["completed_at"] is None
            xp = 0
            if first:
                earned = int(round(SEQUENCE_XP * unaided / float(total))) if total else 0
                start = learner_module._local_midnight(now)
                paid = c.execute(
                    "SELECT COALESCE(SUM(xp), 0) FROM events WHERE reader_id=? AND kind='activity' AND at>=?",
                    (reader_id, start)).fetchone()[0] or 0
                xp = max(0, min(earned, XP_DAILY_CAP - int(paid)))
            # The claim is the UPDATE itself: only the request that flips
            # run_done from 0 may write the event, on one instance or several.
            claimed = c.execute(
                "UPDATE lg_sequences SET run_done=1, plays=plays+1, updated_at=?, "
                "completed_at=COALESCE(completed_at, ?), xp_paid=xp_paid+? "
                "WHERE reader_id=? AND node_id=? AND slug=? AND run_done=0",
                (now, now, xp, reader_id, node_id, slug)).rowcount == 1
            if not claimed:
                return {"first": False, "repeat": True, "xp_gained": 0, "plays": seq["plays"],
                        "steps": total, "unaided": unaided, "first_try": first_try}
            c.execute(
                "INSERT INTO events(kind, payload, at, xp, reader_id) VALUES('activity',?,?,?,?)",
                (json.dumps({"node": node_id, "sequence": slug, "completed": True, "steps": total,
                             "unaided": unaided, "first_try": first_try, "first": first}),
                 now, xp, reader_id))
        return {"first": first, "repeat": False, "xp_gained": xp, "plays": seq["plays"] + 1,
                "steps": total, "unaided": unaided, "first_try": first_try}
