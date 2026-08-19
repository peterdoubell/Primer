"""Cross-instance learner-write regressions at the Turso HTTP boundary."""

import sqlite3
import threading
import time

import pytest

from primer import learner as learner_mod
from primer import store as store_mod


class _Result(object):
    def __init__(self, columns=(), rows=(), rows_affected=0,
                 last_insert_rowid=None):
        self.columns = columns
        self.rows = rows
        self.rows_affected = rows_affected
        self.last_insert_rowid = last_insert_rowid


class _FirstPair(object):
    """Pause exactly the first two mastery reads, never a CAS retry."""

    def __init__(self):
        self._barrier = threading.Barrier(2)
        self._lock = threading.Lock()
        self._remaining = 2
        self.armed = threading.Event()

    def wait(self):
        if not self.armed.is_set():
            return
        with self._lock:
            if self._remaining == 0:
                return
            self._remaining -= 1
        self._barrier.wait(timeout=5.0)


class _QuizBeforeReview(object):
    """Make the quiz CAS land before a review's stale mastery write."""

    def __init__(self):
        self.quiz_written = threading.Event()

    def before(self, normalized):
        if (threading.current_thread().name == "review-worker"
                and normalized.startswith("UPDATE MASTERY SET")):
            assert self.quiz_written.wait(timeout=5.0), "quiz write never arrived"

    def after(self, normalized):
        if (threading.current_thread().name == "quiz-worker"
                and normalized.startswith("UPDATE MASTERY SET")):
            self.quiz_written.set()


class _AutocommitClient(object):
    """Statement-autocommit libSQL stand-in backed by a shared SQLite file."""

    def __init__(self, path, mastery_reads=None, effort_claims=None,
                 write_order=None):
        self._raw = sqlite3.connect(path, timeout=5.0)
        self._raw.isolation_level = None
        self._raw.execute("PRAGMA busy_timeout=5000")
        self._mastery_reads = mastery_reads
        self._effort_claims = effort_claims
        self._write_order = write_order

    def execute(self, sql, params=None):
        normalized = " ".join(sql.upper().split())
        if self._write_order is not None:
            self._write_order.before(normalized)
        if (self._effort_claims is not None
                and normalized.startswith(
                    "INSERT OR IGNORE INTO ATTEMPT_EFFORT_CLAIMS")):
            # Pause before the unique reservation. With the old implementation
            # the equivalent pause happens after its non-atomic events read,
            # below, so this one regression exercises either implementation.
            self._effort_claims.wait()
        cur = self._raw.execute(sql, params or [])
        rows = cur.fetchall()
        columns = tuple(d[0] for d in cur.description) if cur.description else ()
        mastery_snapshot = (
            normalized.startswith("SELECT * FROM MASTERY WHERE NODE_ID=")
            or normalized.startswith(
                "SELECT STRENGTH, MASTERED_AT, PASSES, REINFORCED_AT, "
                "LAST_SEEN, REINFORCEMENTS FROM MASTERY WHERE NODE_ID="))
        if self._mastery_reads is not None and mastery_snapshot:
            # Rows are already materialised: both simulated instances now own
            # the same pre-update state, exactly as two Turso HTTP requests do.
            self._mastery_reads.wait()
        if (self._effort_claims is not None
                and normalized.startswith(
                    "SELECT 1 FROM EVENTS WHERE KIND='ATTEMPT' AND AT >=")):
            self._effort_claims.wait()
        if self._write_order is not None:
            self._write_order.after(normalized)
        return _Result(columns, rows,
                       cur.rowcount if cur.rowcount > 0 else 0,
                       cur.lastrowid)

    def close(self):
        self._raw.close()


class _ProcessLocalLock(object):
    """Each real serverless process owns a different learner._lock."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.mark.parametrize("seeded", [False, True])
def test_concurrent_turso_attempts_are_both_applied(tmp_path, monkeypatch, seeded):
    path = str(tmp_path / ("seeded.db" if seeded else "new.db"))
    first_pair = _FirstPair()

    def fake_connect(_db_path, named_rows=False, **_kwargs):
        client = _AutocommitClient(path, mastery_reads=first_pair)
        return store_mod._LibsqlConnection(
            "https://fake.turso.invalid", named_rows=named_rows, _client=client)

    monkeypatch.setattr(store_mod, "connect", fake_connect)
    one = learner_mod.LearnerStore("unused-one.db")
    two = learner_mod.LearnerStore("unused-two.db")
    one.save_profile("Nell", 9, 6, "balanced", 0, ["math"])
    before = 0
    if seeded:
        one.record_attempt("math.1.addition", 0.6)
        before = 1

    # The module lock is process-local in production.  Removing the shared
    # in-test copy makes these two stores behave like separate Vercel workers.
    monkeypatch.setattr(learner_mod, "_lock", _ProcessLocalLock())
    first_pair.armed.set()
    errors = []
    errors_lock = threading.Lock()

    def attempt(instance, score):
        try:
            instance.record_attempt("math.1.addition", score)
        except Exception as exc:  # pragma: no cover - assertion reports detail
            with errors_lock:
                errors.append(exc)

    threads = [
        threading.Thread(target=attempt, args=(one, 0.7)),
        threading.Thread(target=attempt, args=(two, 0.9)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10.0)

    assert not any(thread.is_alive() for thread in threads), "attempt race deadlocked"
    assert not errors
    with one._conn() as c:
        row = c.execute(
            "SELECT attempts FROM mastery WHERE node_id=?",
            ("math.1.addition",)).fetchone()
    assert row["attempts"] == before + 2


def test_review_retries_instead_of_overwriting_concurrent_quiz(tmp_path, monkeypatch):
    path = str(tmp_path / "review-quiz.db")
    mastery_reads = _FirstPair()
    write_order = _QuizBeforeReview()

    def fake_connect(_db_path, named_rows=False, **_kwargs):
        client = _AutocommitClient(
            path, mastery_reads=mastery_reads, write_order=write_order)
        return store_mod._LibsqlConnection(
            "https://fake.turso.invalid", named_rows=named_rows, _client=client)

    monkeypatch.setattr(store_mod, "connect", fake_connect)
    one = learner_mod.LearnerStore("unused-one.db")
    two = learner_mod.LearnerStore("unused-two.db")
    now = time.time()
    one.save_profile("Nell", 12, 6, "balanced", 0, ["math"])
    with one._conn() as c:
        c.execute(
            """INSERT INTO mastery(
                   node_id, level, attempts, passes, first_pass_at, last_pass_at,
                   strength, last_seen, assumed, mastered_at, reinforcements,
                   reinforced_at, first_mastered_at)
               VALUES(?,0.5,1,0,NULL,NULL,0.5,?,0,NULL,1,?,NULL)""",
            ("math.1.addition", now, now))
        card_id = c.execute(
            """INSERT INTO srs_cards(
                   front, back, node_id, article, ef, interval, reps, lapses,
                   reviews, due, created_at, origin)
               VALUES('q','a',?,'',2.5,0,0,0,0,?,?, 'book')""",
            ("math.1.addition", now - 60, now - learner_mod.DAY)).lastrowid

    # Simulate separate serverless processes, then make both requests read the
    # exact same mastery revision. The quiz is deliberately allowed to win the
    # first write; review must fail its CAS, reread, and subtract from 0.70.
    monkeypatch.setattr(learner_mod, "_lock", _ProcessLocalLock())
    mastery_reads.armed.set()
    errors = []
    results = {}
    errors_lock = threading.Lock()

    def run_quiz():
        try:
            results["quiz"] = one.record_attempt("math.1.addition", 1.0)
        except Exception as exc:  # pragma: no cover - assertion reports detail
            with errors_lock:
                errors.append(exc)

    def run_review():
        try:
            results["review"] = two.review_card(card_id, 0)
        except Exception as exc:  # pragma: no cover - assertion reports detail
            with errors_lock:
                errors.append(exc)

    threads = [
        threading.Thread(target=run_quiz, name="quiz-worker"),
        threading.Thread(target=run_review, name="review-worker"),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10.0)

    assert not any(thread.is_alive() for thread in threads), "review race deadlocked"
    assert not errors
    with one._conn() as c:
        row = c.execute(
            "SELECT level, attempts, strength FROM mastery WHERE node_id=?",
            ("math.1.addition",)).fetchone()
    assert row["attempts"] == 2
    assert row["level"] == pytest.approx(0.7)
    assert row["strength"] == pytest.approx(0.45, abs=0.002)
    assert results["review"]["lapses"] == 1


def test_daily_effort_xp_is_claimed_once_across_turso_instances(
        tmp_path, monkeypatch):
    path = str(tmp_path / "effort-claim.db")
    effort_claims = _FirstPair()

    def fake_connect(_db_path, named_rows=False, **_kwargs):
        client = _AutocommitClient(path, effort_claims=effort_claims)
        return store_mod._LibsqlConnection(
            "https://fake.turso.invalid", named_rows=named_rows, _client=client)

    monkeypatch.setattr(store_mod, "connect", fake_connect)
    one = learner_mod.LearnerStore("unused-one.db")
    two = learner_mod.LearnerStore("unused-two.db")
    one.save_profile("Nell", 12, 6, "balanced", 0, ["math"])
    monkeypatch.setattr(learner_mod, "_lock", _ProcessLocalLock())
    effort_claims.armed.set()
    errors = []
    results = []
    errors_lock = threading.Lock()

    def attempt(instance, score):
        try:
            results.append(instance.record_attempt("math.1.addition", score))
        except Exception as exc:  # pragma: no cover - assertion reports detail
            with errors_lock:
                errors.append(exc)

    threads = [
        threading.Thread(target=attempt, args=(one, 0.6)),
        threading.Thread(target=attempt, args=(two, 0.9)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10.0)

    assert not any(thread.is_alive() for thread in threads), "XP race deadlocked"
    assert not errors
    assert len(results) == 2
    # Exactly one successful retrieval owns the daily effort payment. Which
    # request wins is deliberately unspecified, but both attempts are logged.
    assert sorted(result["xp_gained"] for result in results) in ([0, 7], [0, 11])
    with one._conn() as c:
        claims = c.execute(
            "SELECT COUNT(*) FROM attempt_effort_claims").fetchone()[0]
        events = c.execute(
            "SELECT xp FROM events WHERE kind='attempt' ORDER BY id").fetchall()
        attempts = c.execute(
            "SELECT attempts FROM mastery WHERE node_id=?",
            ("math.1.addition",)).fetchone()[0]
    assert claims == 1
    assert len(events) == 2
    assert sorted(row["xp"] for row in events) in ([0, 7], [0, 11])
    assert attempts == 2


def test_effort_claim_schema_backfills_todays_existing_attempt(tmp_path, monkeypatch):
    path = str(tmp_path / "upgrade.db")
    wall = time.localtime()
    midday = time.mktime((wall.tm_year, wall.tm_mon, wall.tm_mday, 12, 0, 0,
                          0, 0, -1))
    monkeypatch.setattr(learner_mod.time, "time", lambda: midday)

    # Model the old schema immediately before attempt_effort_claims existed.
    raw = sqlite3.connect(path)
    raw.execute(
        """CREATE TABLE events(
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               kind TEXT, payload TEXT, at REAL, xp INTEGER DEFAULT 0)""")
    raw.execute(
        "INSERT INTO events(kind,payload,at,xp) VALUES('attempt',?,?,9)",
        ('{"node":"math.1.addition","score":0.75}', midday))
    raw.commit()
    raw.close()

    upgraded = learner_mod.LearnerStore(path)
    result = upgraded.record_attempt("math.1.addition", 0.9)

    assert result["xp_gained"] == 0
    with upgraded._conn() as c:
        claims = c.execute(
            "SELECT COUNT(*) FROM attempt_effort_claims").fetchone()[0]
        events = c.execute(
            "SELECT xp FROM events WHERE kind='attempt' ORDER BY id").fetchall()
    assert claims == 1
    assert [row["xp"] for row in events] == [9, 0]


def test_first_mastery_bonus_survives_spent_effort_slot(tmp_path):
    store = learner_mod.LearnerStore(str(tmp_path / "mastery-bonus.db"))
    store.save_profile("Nell", 12, 6, "balanced", 0, ["math"])
    node_id = "math.1.addition"
    first = store.record_attempt(node_id, 1.0)
    assert first["xp_gained"] == 12
    store.prune(0)  # even an aggressive cleanup must not reopen today's slot

    # Make the original pass genuinely spaced without crossing a local-day
    # boundary. The second attempt owns no effort XP, but first mastery still
    # carries its independent 60-point bonus.
    with store._conn() as c:
        c.execute(
            "UPDATE mastery SET first_pass_at=?, reinforced_at=? WHERE node_id=?",
            (time.time() - 3 * learner_mod.DAY,
             time.time() - 3 * learner_mod.DAY, node_id))
    second = store.record_attempt(node_id, 1.0)

    assert second["newly_mastered"] is True
    assert second["xp_gained"] == 60
    with store._conn() as c:
        events = c.execute(
            "SELECT xp FROM events WHERE kind='attempt' ORDER BY id").fetchall()
        claims = c.execute(
            "SELECT COUNT(*) FROM attempt_effort_claims WHERE node_id=?",
            (node_id,)).fetchone()[0]
    assert [row["xp"] for row in events] == [12, 60]
    assert claims == 1
