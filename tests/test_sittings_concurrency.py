"""Deterministic regressions for sitting-token concurrency.

These tests stay at the persistence seam.  They do not need the FastAPI app,
and the fake HTTP client below gives the libSQL adapter the same statement-level
autocommit boundary Turso uses without touching a network database.
"""

import sqlite3
import threading
import time

import pytest

from primer import store as store_mod
from primer.sittings import SittingStore


@pytest.fixture(autouse=True)
def _no_inherited_turso(monkeypatch):
    monkeypatch.delenv(store_mod.URL_ENV, raising=False)
    monkeypatch.delenv(store_mod.TOKEN_ENV, raising=False)


def _paper():
    return {
        "at": 100.0,
        "questions": [{"id": 1, "answer": "four"}],
        "purpose": "quiz",
        "subject": "math.1.addition",
        "committed": {},
    }


def test_stale_proxy_cannot_resurrect_a_claimed_token(tmp_path):
    path = str(tmp_path / "sittings.db")
    sittings = SittingStore(lambda: path)
    sittings["tok"] = _paper()

    # `/check` has read this proxy; `/submit` wins and consumes the paper.
    stale_check = sittings["tok"]
    assert sittings.pop("tok")["subject"] == "math.1.addition"

    # The old proxy path used INSERT OR REPLACE and recreated the token here.
    stale_check["committed"] = {1: {"answer": "five", "at": 101.0}}
    assert sittings.get("tok") is None


def test_atomic_commit_is_first_answer_only_and_never_recreates_claimed_row(tmp_path):
    path = str(tmp_path / "commit.db")
    sittings = SittingStore(lambda: path)
    sittings["tok"] = _paper()

    first = sittings.commit_answer("tok", 1, "five", committed_at=101.0)
    second = sittings.commit_answer("tok", 1, "four", committed_at=102.0)
    assert first == second == {"answer": "five", "at": 101.0}

    claimed = sittings.pop("tok")
    assert claimed["committed"][1] == first
    assert sittings.commit_answer("tok", 1, "four", committed_at=103.0) is None
    assert sittings.get("tok") is None


def test_server_recall_returns_none_when_atomic_claim_loses(monkeypatch):
    import primer.server as server

    class _LosingStore(object):
        def get(self, token, default=None):
            assert token == "tok"
            return {"at": time.time(), "purpose": "quiz", "subject": "node"}

        def pop(self, token, default=None):
            assert token == "tok"
            # Another serverless instance deleted and received the row between
            # this request's valid lookup and its own atomic claim.
            return default

    monkeypatch.setattr(server, "_SERVED", _LosingStore())
    assert server._recall("tok", "quiz", "node") is None


class _Result(object):
    def __init__(self, columns=(), rows=(), rows_affected=0,
                 last_insert_rowid=None):
        self.columns = columns
        self.rows = rows
        self.rows_affected = rows_affected
        self.last_insert_rowid = last_insert_rowid


class _AutocommitClient(object):
    """A shared-file HTTP-client stand-in with controlled race points.

    With the former SELECT-then-DELETE pop, both SELECT result sets are
    materialised before either DELETE runs.  With DELETE RETURNING, both calls
    instead line up before the atomic statement and only one receives a row.
    """

    def __init__(self, path, barrier, armed):
        self._raw = sqlite3.connect(path, timeout=5.0)
        self._raw.isolation_level = None
        self._raw.execute("PRAGMA busy_timeout=5000")
        self._barrier = barrier
        self._armed = armed

    def execute(self, sql, params=None):
        normalized = " ".join(sql.upper().split())
        if (self._armed.is_set()
                and normalized.startswith("DELETE FROM SITTINGS")
                and "RETURNING" in normalized):
            self._barrier.wait(timeout=5.0)

        cur = self._raw.execute(sql, params or [])
        rows = cur.fetchall()
        columns = tuple(d[0] for d in cur.description) if cur.description else ()

        if (self._armed.is_set()
                and normalized.startswith("SELECT AT, DATA FROM SITTINGS")):
            # This branch is what makes the old implementation fail every time:
            # both claimants already own the same selected row before deletion.
            self._barrier.wait(timeout=5.0)

        return _Result(columns, rows,
                       cur.rowcount if cur.rowcount > 0 else 0,
                       cur.lastrowid)

    def close(self):
        self._raw.close()


def test_two_turso_instances_cannot_both_claim_one_paper(tmp_path, monkeypatch):
    path = str(tmp_path / "remote.db")
    barrier = threading.Barrier(2)
    armed = threading.Event()

    def fake_connect(_db_path, **_kwargs):
        client = _AutocommitClient(path, barrier, armed)
        return store_mod._LibsqlConnection(
            "https://fake.turso.invalid", _client=client)

    monkeypatch.setattr(store_mod, "connect", fake_connect)
    first_instance = SittingStore(lambda: "unused-a.db")
    second_instance = SittingStore(lambda: "unused-b.db")
    first_instance["tok"] = _paper()

    results = []
    errors = []
    result_lock = threading.Lock()
    armed.set()

    def claim(instance):
        try:
            result = instance.pop("tok", None)
            with result_lock:
                results.append(result)
        except Exception as exc:  # pragma: no cover - assertion reports detail
            with result_lock:
                errors.append(exc)

    threads = [
        threading.Thread(target=claim, args=(first_instance,)),
        threading.Thread(target=claim, args=(second_instance,)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10.0)
    armed.clear()

    assert not any(thread.is_alive() for thread in threads), "claim race deadlocked"
    assert not errors
    assert sum(result is not None for result in results) == 1
    assert first_instance.get("tok") is None
