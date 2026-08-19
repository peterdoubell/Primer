"""Served-paper ("sitting") persistence.

A sitting is a quiz/practice/placement paper the server has issued and must
later grade from its own copy — scoring never trusts a client-supplied answer
key. Sittings are short-lived but they are state the reader paid for: they are
persisted in the learner database so a server restart cannot void an open
paper or the commit/burn record that keeps the single-use and reveal-order
rules honest.

The store is dict-like on purpose: the server and the tests keep the exact
interface the original in-memory OrderedDict had. The database path is
resolved through a callable at query time, not bound at construction, so
rebinding the server's learner store rebinds this store with it.
"""

import json
import sqlite3
import time

from . import store

SERVED_LIMIT = 200
SERVED_TTL = 12 * 3600   # a paper is a sitting, not a standing offer


class SittingProxy(dict):
    """A sitting as a mutable dict view. Top-level assignment writes through to
    the store, so a caller (or a test) that adjusts, say, `at` is adjusting the
    persistent record, not a copy that evaporates on the next read."""

    def __init__(self, store, token, data):
        super().__init__(data)
        self._store, self._token = store, token

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        # A proxy is only ever a view of an existing sitting.  In particular,
        # it must not regain insert semantics after another request has claimed
        # the token: `/check` can hold this object while `/submit` deletes the
        # row, and INSERT OR REPLACE here used to resurrect the consumed paper.
        # An update that matches no row is deliberately a no-op.
        self._store._replace_if_present(self._token, dict(self))


class SittingStore:
    """Served papers, persisted next to the rest of the learner record."""

    def __init__(self, db_path_fn):
        # A callable, not a path: the live path belongs to whichever learner
        # store the server currently holds.
        self._db_path_fn = db_path_fn

    def _conn(self):
        # No WAL here, as before: this store has always taken the journal mode
        # the learner store already set on the same file. Local by default,
        # Turso when TURSO_DATABASE_URL is set — see primer/store.py.
        conn = store.connect(self._db_path_fn(), wal=False)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS sittings ("
            " token TEXT PRIMARY KEY, at REAL, data TEXT)")
        return conn

    @staticmethod
    def _decode(row):
        entry = json.loads(row[1])
        entry["at"] = row[0]
        # JSON object keys are strings; `committed` is keyed by question id,
        # which is an int everywhere else. Undo the round-trip.
        committed = entry.get("committed") or {}
        entry["committed"] = {int(k): v for k, v in committed.items()}
        return entry

    @staticmethod
    def _encode(entry):
        payload = {k: v for k, v in entry.items() if k != "at"}
        return (float(entry.get("at", time.time())), json.dumps(payload))

    def get(self, token, default=None):
        with self._conn() as c:
            row = c.execute("SELECT at, data FROM sittings WHERE token=?",
                            (token,)).fetchone()
        if row is None:
            return default
        return SittingProxy(self, token, self._decode(row))

    def __getitem__(self, token):
        entry = self.get(token)
        if entry is None:
            raise KeyError(token)
        return entry

    def __contains__(self, token):
        return self.get(token) is not None

    def __setitem__(self, token, entry):
        at, payload = self._encode(entry)
        with self._conn() as c:
            c.execute("INSERT OR REPLACE INTO sittings(token, at, data) VALUES(?,?,?)",
                      (token, at, payload))

    def _replace_if_present(self, token, entry):
        """Persist a proxy mutation only while its sitting still exists.

        Returning whether the row was present makes the primitive useful to a
        caller that needs to distinguish a live mutation from a submit that won
        the race.  SittingProxy itself intentionally keeps normal dict
        assignment syntax and therefore ignores the return value.
        """
        at, payload = self._encode(entry)
        with self._conn() as c:
            changed = c.execute(
                "UPDATE sittings SET at=?, data=? WHERE token=?",
                (at, payload, token)).rowcount
        return changed == 1

    def commit_answer(self, token, question_id, answer, committed_at=None):
        """Record the first answer for one question with optimistic CAS.

        Each connection may belong to a different serverless instance, so a
        process lock cannot protect this read/modify/write.  The raw JSON read
        from the row is the compare value: either this update linearises before
        a concurrent claim or it matches nothing and retries against the new
        state.  Once a claim has deleted the row, the method returns None and
        can never recreate it.
        """
        qid = int(question_id)
        committed_at = time.time() if committed_at is None else committed_at
        while True:
            with self._conn() as c:
                row = c.execute(
                    "SELECT at, data FROM sittings WHERE token=?", (token,)
                ).fetchone()
                if row is None:
                    return None
                entry = self._decode(row)
                committed = dict(entry.get("committed") or {})
                committed.setdefault(qid, {"answer": answer, "at": committed_at})
                entry["committed"] = committed
                at, payload = self._encode(entry)
                changed = c.execute(
                    "UPDATE sittings SET at=?, data=? "
                    "WHERE token=? AND at=? AND data=?",
                    (at, payload, token, row[0], row[1])).rowcount
            if changed == 1:
                return committed[qid]

    def pop(self, token, default=None):
        with self._conn() as c:
            # One statement is the claim.  That matters over Turso's HTTP
            # transport, where SELECT followed by DELETE would be two separate
            # autocommits and two instances could both return the selected
            # paper.  RETURNING is supported by libSQL and modern SQLite.
            # Python 3.9 can still be linked against pre-3.35 SQLite, so retain
            # an atomic BEGIN IMMEDIATE fallback for that local-only case.
            if (isinstance(c, sqlite3.Connection)
                    and sqlite3.sqlite_version_info < (3, 35, 0)):
                c.execute("BEGIN IMMEDIATE")
                row = c.execute("SELECT at, data FROM sittings WHERE token=?",
                                (token,)).fetchone()
                if row is not None:
                    c.execute("DELETE FROM sittings WHERE token=?", (token,))
            else:
                row = c.execute(
                    "DELETE FROM sittings WHERE token=? RETURNING at, data",
                    (token,)).fetchone()
        if row is None:
            return default
        return self._decode(row)

    def sweep(self, now: float):
        """TTL sweep plus the size cap, oldest first — the same eviction the
        in-memory OrderedDict applied, now in one SQL breath."""
        with self._conn() as c:
            c.execute("DELETE FROM sittings WHERE at < ?", (now - SERVED_TTL,))
            c.execute(
                "DELETE FROM sittings WHERE token IN ("
                " SELECT token FROM sittings ORDER BY at DESC"
                " LIMIT -1 OFFSET ?)", (SERVED_LIMIT,))
