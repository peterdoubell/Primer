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
        self._store[self._token] = dict(self)


class SittingStore:
    """Served papers, persisted next to the rest of the learner record."""

    def __init__(self, db_path_fn):
        # A callable, not a path: the live path belongs to whichever learner
        # store the server currently holds.
        self._db_path_fn = db_path_fn

    def _conn(self):
        conn = sqlite3.connect(self._db_path_fn(), timeout=15)
        conn.execute("PRAGMA busy_timeout=8000")
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
        payload = {k: v for k, v in entry.items() if k != "at"}
        with self._conn() as c:
            c.execute("INSERT OR REPLACE INTO sittings(token, at, data) VALUES(?,?,?)",
                      (token, float(entry.get("at", time.time())), json.dumps(payload)))

    def pop(self, token, default=None):
        with self._conn() as c:
            row = c.execute("SELECT at, data FROM sittings WHERE token=?",
                            (token,)).fetchone()
            c.execute("DELETE FROM sittings WHERE token=?", (token,))
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
