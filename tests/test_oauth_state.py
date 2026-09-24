"""OAuth state remains durable, bounded, and single use on both store backends."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import threading
from types import SimpleNamespace

import pytest

from primer import oauth_state, store
from primer.oauth_state import MAX_PENDING, MAX_RETURN_PATH, OAuthStateStore


class _SqliteHttpClient:
    """Exercise the real libSQL adapter with separately autocommitted statements."""

    def __init__(self, database):
        self.connection = sqlite3.connect(database, isolation_level=None, timeout=15)

    def execute(self, sql, parameters=None):
        cursor = self.connection.execute(sql, parameters or ())
        columns = tuple(item[0] for item in (cursor.description or ()))
        rows = cursor.fetchall()
        return SimpleNamespace(columns=columns, rows=rows,
                               rows_affected=max(0, cursor.rowcount),
                               last_insert_rowid=cursor.lastrowid)

    def close(self):
        self.connection.close()


@pytest.fixture(params=["sqlite", "http-libsql-adapter"])
def state_factory(tmp_path, request):
    database = tmp_path / "oauth-state.sqlite"

    def connection_factory():
        if request.param == "sqlite":
            return sqlite3.connect(database, timeout=15)
        return store._LibsqlConnection(
            "https://test.turso.invalid", named_rows=True,
            _client=_SqliteHttpClient(database),
        )

    return database, connection_factory


def test_state_persists_across_instances_and_contains_only_opaque_nonce(state_factory):
    database, factory = state_factory
    first = OAuthStateStore(factory)
    assert not database.exists(), "construction must not run a learner migration"
    nonce = first.issue("/#/review-game")
    assert re.fullmatch(r"[A-Za-z0-9_-]{43}", nonce)
    second_nonce = first.issue("/#/atlas")
    assert second_nonce != nonce
    assert "review" not in nonce
    assert OAuthStateStore(factory).consume(nonce) == "/#/review-game"
    assert OAuthStateStore(factory).consume(second_nonce) == "/#/atlas"


def test_state_can_be_consumed_by_another_process(state_factory):
    database, factory = state_factory
    nonce = OAuthStateStore(factory).issue("/#/node/math.0.counting")
    script = """
import json, sqlite3, sys
from primer.oauth_state import OAuthStateStore
state = OAuthStateStore(lambda: sqlite3.connect(sys.argv[1]))
print(json.dumps(state.consume(sys.argv[2])))
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(database), nonce],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, check=True,
    )
    assert json.loads(result.stdout) == "/#/node/math.0.counting"
    assert OAuthStateStore(factory).consume(nonce) is None


def test_missing_tampered_and_replayed_state_never_returns_a_destination(state_factory):
    _, factory = state_factory
    states = OAuthStateStore(factory)
    nonce = states.issue("/#/atlas")
    tampered = ("A" if nonce[0] != "A" else "B") + nonce[1:]
    assert states.consume(tampered) is None
    for bad in (None, "", "missing", "../bad", "x" * 100_000, "A" * 42 + "\n"):
        assert states.consume(bad) is None
    assert states.consume(nonce) == "/#/atlas"
    assert states.consume(nonce) is None


def test_expiry_is_exact_and_expired_rows_are_pruned(state_factory, monkeypatch):
    database, factory = state_factory
    now = [1_000.0]
    monkeypatch.setattr(oauth_state.time, "time", lambda: now[0])
    states = OAuthStateStore(factory)
    before_deadline = states.issue("/#/atlas")
    at_deadline = states.issue("/#/review")
    now[0] = 1_599.99
    assert states.consume(before_deadline) == "/#/atlas"
    now[0] = 1_600.0
    assert states.consume(at_deadline) is None
    expired = states.issue("/#/old")
    now[0] += 601
    current = states.issue("/#/new")
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT nonce FROM oauth_states").fetchall() == [(current,)]
    assert states.consume(expired) is None


def test_concurrent_consumers_cannot_replay_a_token(state_factory):
    _, factory = state_factory
    nonce = OAuthStateStore(factory).issue("/#/review-game")
    barrier = threading.Barrier(8)

    def consume(_):
        barrier.wait()
        return OAuthStateStore(factory).consume(nonce)

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(consume, range(8)))
    assert results.count("/#/review-game") == 1
    assert results.count(None) == 7


def test_pending_state_cap_keeps_recent_tokens_even_when_time_is_identical(state_factory, monkeypatch):
    database, factory = state_factory
    monkeypatch.setattr(oauth_state.time, "time", lambda: 1_000.0)
    states = OAuthStateStore(factory)
    tokens = [states.issue("/#/atlas") for _ in range(MAX_PENDING + 7)]
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM oauth_states").fetchone()[0] == MAX_PENDING
    assert all(states.consume(token) is None for token in tokens[:7])
    assert states.consume(tokens[-1]) == "/#/atlas"
    assert states.consume(tokens[7]) == "/#/atlas"


def test_concurrent_issuers_cannot_exceed_pending_cap(state_factory):
    database, factory = state_factory
    states = OAuthStateStore(factory)
    for _ in range(MAX_PENDING - 4):
        states.issue("/#/atlas")
    barrier = threading.Barrier(8)

    def issue(_):
        barrier.wait()
        return OAuthStateStore(factory).issue("/#/review")

    with ThreadPoolExecutor(max_workers=8) as executor:
        tokens = list(executor.map(issue, range(8)))
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM oauth_states").fetchone()[0] == MAX_PENDING
    assert all(states.consume(token) == "/#/review" for token in tokens)


def test_state_storage_is_independent_of_reader_tables(state_factory):
    database, factory = state_factory
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE profile (reader_id INTEGER PRIMARY KEY, name TEXT)")
        connection.execute("CREATE TABLE mastery (reader_id INTEGER, node_id TEXT, level REAL)")
        connection.executemany("INSERT INTO profile VALUES (?, ?)", [(1, "First"), (2, "Second")])
        connection.execute("INSERT INTO mastery VALUES (2, 'math.0.counting', 0.75)")
    nonce = OAuthStateStore(factory).issue("/#/atlas")
    with sqlite3.connect(database) as connection:
        connection.execute("DELETE FROM profile WHERE reader_id = 1")
    assert OAuthStateStore(factory).consume(nonce) == "/#/atlas"
    with sqlite3.connect(database) as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(oauth_states)")]
        assert "reader_id" not in columns
        assert connection.execute("SELECT * FROM mastery").fetchall() == [(2, "math.0.counting", 0.75)]
        assert connection.execute("SELECT * FROM profile").fetchall() == [(2, "Second")]


@pytest.mark.parametrize("path", [None, "", "https://example.com", "//example.com", "/\\example.com",
                                  "/\r\nLocation: evil", "/\x00", "/" + "x" * MAX_RETURN_PATH])
def test_invalid_return_paths_fail_before_opening_a_connection(path):
    def forbidden_connection():
        raise AssertionError("invalid data must not reach storage")

    with pytest.raises(ValueError, match="short local path"):
        OAuthStateStore(forbidden_connection).issue(path)


def test_return_path_length_limit_is_inclusive(state_factory):
    _, factory = state_factory
    path = "/" + "x" * (MAX_RETURN_PATH - 1)
    nonce = OAuthStateStore(factory).issue(path)
    assert OAuthStateStore(factory).consume(nonce) == path
