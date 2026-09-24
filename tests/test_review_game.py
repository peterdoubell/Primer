"""Memory Garden uses the real scheduler without grading one reveal twice.

Every database in this module is disposable. The guarded game API protects
against lost responses and concurrent tabs while preserving the ordinary
deck's intentional treatment of a genuinely forgotten, not-yet-due card.
"""

import contextlib
import threading

import pytest

from primer import learner as learner_module
from primer.learner import DAY, LearnerStore


NOW = 1_900_000_000.0
NODE = "math.1.addition"


@pytest.fixture
def game_store(tmp_path, monkeypatch):
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)
    monkeypatch.setattr(learner_module.time, "time", lambda: NOW)
    store = LearnerStore(str(tmp_path / "game.db"))
    store.save_profile("Garden reader", 12, 3, "balanced", 1, ["math"])
    return store


def seed_card(store, reader_id=1, due=NOW - 60, front="What is two plus two?"):
    store.add_cards([{"front": front, "back": "Four", "node_id": NODE}],
                    reader_id=reader_id)
    with store._conn() as connection:
        connection.execute(
            "UPDATE srs_cards SET due=? WHERE reader_id=? AND front=?",
            (due, reader_id, front),
        )
        return dict(connection.execute(
            "SELECT * FROM srs_cards WHERE reader_id=? AND front=?",
            (reader_id, front),
        ).fetchone())


def grade(store, card, quality, **kwargs):
    return store.review_card(
        card["id"], quality, expected_due=card["due"],
        expected_reviews=card["reviews"], **kwargs,
    )


def snapshot(store, reader_id=1):
    """All review consequences, including zero-XP daily-quest events."""
    with store._conn() as connection:
        return {
            "cards": [dict(row) for row in connection.execute(
                "SELECT * FROM srs_cards WHERE reader_id=? ORDER BY id",
                (reader_id,),
            )],
            "mastery": [dict(row) for row in connection.execute(
                "SELECT * FROM mastery WHERE reader_id=? ORDER BY node_id",
                (reader_id,),
            )],
            "events": [dict(row) for row in connection.execute(
                "SELECT * FROM events WHERE reader_id=? ORDER BY id",
                (reader_id,),
            )],
        }


@pytest.mark.parametrize("quality, xp, delay", [(0, 0, 600), (3, 3, DAY), (5, 5, DAY)])
def test_lost_response_retry_grades_the_revealed_card_once(game_store, quality, xp, delay):
    game_store.record_attempt(NODE, 0.9)
    card = seed_card(game_store)

    # Imagine this successful response never reached the browser. Its retry
    # still has the revision originally displayed, including after a lapse.
    first = grade(game_store, card, quality, seconds=12)
    after_first = snapshot(game_store)
    retries = [grade(game_store, card, quality, seconds=12) for _ in range(7)]

    assert first["accepted"] is True
    assert first["xp_gained"] == xp
    assert first["next_due"] == pytest.approx(NOW + delay)
    assert all(result["accepted"] is False and result["stale"] is True
               and result["xp_gained"] == 0 for result in retries)
    assert all(result["next_due"] == first["next_due"] for result in retries)
    assert snapshot(game_store) == after_first
    assert game_store.events_today_count("review") == 1
    assert after_first["cards"][0]["reviews"] == 1
    assert after_first["cards"][0]["lapses"] == int(quality < 3)


@pytest.mark.parametrize("quality", [0, 5])
def test_a_fresh_matching_revision_still_cannot_review_a_future_card(game_store, quality):
    card = seed_card(game_store, due=NOW + 600)
    before = snapshot(game_store)

    result = grade(game_store, card, quality)

    assert result["accepted"] is False and result["stale"] is True
    assert result["xp_gained"] == 0
    assert result["next_due"] == NOW + 600
    assert snapshot(game_store) == before


@pytest.mark.parametrize("changed_column", ["due", "reviews"])
def test_each_part_of_the_displayed_revision_is_required(game_store, changed_column):
    card = seed_card(game_store)
    with game_store._conn() as connection:
        if changed_column == "due":
            connection.execute("UPDATE srs_cards SET due=due-1 WHERE id=?", (card["id"],))
        else:
            connection.execute("UPDATE srs_cards SET reviews=reviews+1 WHERE id=?", (card["id"],))
    before = snapshot(game_store)

    result = grade(game_store, card, 0)

    assert result["accepted"] is False and result["stale"] is True
    assert snapshot(game_store) == before


@pytest.mark.parametrize("age, delay", [(3, 3 * 3600), (8, 8 * 3600), (25, DAY)])
def test_success_reports_the_exact_age_scaled_due_time(game_store, age, delay):
    game_store.save_profile("Garden reader", age, 3, "balanced", 1, ["math"])
    card = seed_card(game_store)

    result = grade(game_store, card, 5)

    assert result["next_due"] == pytest.approx(NOW + delay)
    assert snapshot(game_store)["cards"][0]["due"] == result["next_due"]


def test_a_lapse_reports_ten_minutes_without_rounding_days(game_store):
    card = seed_card(game_store)
    result = grade(game_store, card, 0)
    assert result["next_due"] - NOW == 600
    assert snapshot(game_store)["cards"][0]["due"] == result["next_due"]


def test_six_genuine_due_lapses_still_park_a_difficult_card(game_store):
    card = seed_card(game_store)
    for _ in range(6):
        with game_store._conn() as connection:
            connection.execute("UPDATE srs_cards SET due=? WHERE id=?", (NOW - 1, card["id"]))
            card = dict(connection.execute(
                "SELECT * FROM srs_cards WHERE id=?", (card["id"],),
            ).fetchone())
        result = grade(game_store, card, 0)
        assert result["accepted"] is True
    assert result["lapses"] == 6
    assert result["next_due"] == NOW + 7 * DAY
    assert game_store.events_today_count("review") == 6


def test_game_grades_use_the_existing_daily_xp_cap(game_store):
    card = seed_card(game_store)
    with game_store._conn() as connection:
        connection.execute(
            "INSERT INTO events(kind,payload,at,xp,reader_id) VALUES('review','{}',?,?,1)",
            (NOW, game_store.REVIEW_XP_DAILY_CAP),
        )
    result = grade(game_store, card, 5)
    assert result["accepted"] is True
    assert result["xp_gained"] == 0
    assert result["next_due"] == NOW + DAY


def test_ordinary_deck_can_still_record_a_genuine_early_failure(game_store):
    card = seed_card(game_store, due=NOW + DAY)
    early_success = game_store.review_card(card["id"], 5)
    assert early_success["early"] is True and early_success["xp_gained"] == 0
    early_failure = game_store.review_card(card["id"], 0)
    assert early_failure["lapses"] == 1
    assert game_store.events_today_count("review") == 1
    assert snapshot(game_store)["cards"][0]["due"] == NOW + 600


def test_a_card_revision_cannot_be_used_by_another_reader(game_store):
    other = game_store.upsert_google_reader("garden-other", "other@example.com", "Other")
    card = seed_card(game_store)
    before = snapshot(game_store)
    assert grade(game_store, card, 0, reader_id=other) == {"error": "no such card"}
    assert snapshot(game_store) == before
    assert snapshot(game_store, other)["events"] == []


@pytest.mark.parametrize("quality", [0, 5])
def test_two_instances_with_the_same_card_snapshot_apply_one_grade(game_store, monkeypatch, quality):
    """Both workers read first; only a database CAS can resolve this race."""
    card = seed_card(game_store)
    other_store = LearnerStore(game_store.db_path)
    barrier = threading.Barrier(2)
    worker_state = threading.local()
    original_conn = LearnerStore._conn

    class SnapshotCursor:
        def __init__(self, cursor):
            self.cursor = cursor

        def fetchone(self):
            row = self.cursor.fetchone()
            if not getattr(worker_state, "read_card", False):
                worker_state.read_card = True
                barrier.wait(timeout=5)
            return row

    class SnapshotConnection:
        def __init__(self, connection):
            self.connection = connection

        def execute(self, sql, args=()):
            cursor = self.connection.execute(sql, args)
            normalized = " ".join(sql.upper().split())
            if normalized.startswith("SELECT * FROM SRS_CARDS WHERE ID="):
                return SnapshotCursor(cursor)
            return cursor

    @contextlib.contextmanager
    def simultaneous_conn(store):
        connection = original_conn(store)
        try:
            with connection:
                yield SnapshotConnection(connection)
        finally:
            connection.close()

    results, errors = [], []

    def run(store):
        try:
            results.append(grade(store, card, quality))
        except Exception as error:
            errors.append(error)

    # Real workers do not share a Python lock; deliberately remove that
    # protection and synchronize the stale reads, rather than hope for a race.
    with monkeypatch.context() as patch:
        patch.setattr(learner_module, "_lock", contextlib.nullcontext())
        patch.setattr(LearnerStore, "_conn", simultaneous_conn)
        workers = [threading.Thread(target=run, args=(store,))
                   for store in (game_store, other_store)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(timeout=10)
        assert not any(worker.is_alive() for worker in workers), "review workers deadlocked"

    assert errors == []
    assert sorted(result["accepted"] for result in results) == [False, True]
    assert game_store.events_today_count("review") == 1
    assert snapshot(game_store)["cards"][0]["reviews"] == 1
    assert sum(result["xp_gained"] for result in results) == (5 if quality == 5 else 0)


@pytest.fixture
def game_api(game_store, tmp_path, monkeypatch):
    # Set import-time paths too when this test file runs alone. No lifespan
    # is needed for these routes, so no background maintenance is started.
    monkeypatch.setenv("PRIMER_DB", str(tmp_path / "boot.db"))
    monkeypatch.setenv("PRIMER_BACKUP_DIR", str(tmp_path / "backups"))
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.delenv("PRIMER_ACCESS_PASSWORD", raising=False)
    from fastapi.testclient import TestClient
    from primer import server

    monkeypatch.setattr(server, "learner", game_store)
    client = TestClient(server.app)
    try:
        yield client, server
    finally:
        client.close()


def request_grade(card, quality=0):
    return {"card_id": card["id"], "quality": quality, "seconds": 12,
            "expected_due": card["due"], "expected_reviews": card["reviews"]}


def test_game_api_retry_cannot_duplicate_a_failure(game_api, game_store):
    client, _ = game_api
    card = seed_card(game_store)
    shown = client.get("/api/review/due?limit=5").json()["cards"][0]
    body = request_grade(shown)
    first = client.post("/api/review/game", json=body)
    second = client.post("/api/review/game", json=body)
    assert first.status_code == second.status_code == 200
    assert first.json()["accepted"] is True
    assert second.json()["accepted"] is False and second.json()["stale"] is True
    assert second.json()["xp_gained"] == 0
    assert game_store.events_today_count("review") == 1
    assert snapshot(game_store)["cards"][0]["id"] == card["id"]


@pytest.mark.parametrize("field, value", [
    ("expected_due", "missing"), ("expected_reviews", "missing"),
    ("expected_due", None), ("expected_reviews", None),
    ("expected_due", -1), ("expected_due", "NaN"), ("expected_due", "Infinity"),
    ("expected_reviews", -1), ("expected_reviews", 0.5),
])
def test_game_api_requires_a_finite_nonnegative_card_revision(game_api, game_store, field, value):
    client, _ = game_api
    card = seed_card(game_store)
    body = request_grade(card)
    if value == "missing":
        del body[field]
    else:
        body[field] = value
    before = snapshot(game_store)
    response = client.post("/api/review/game", json=body)
    assert response.status_code == 422
    assert snapshot(game_store) == before


def test_game_api_expired_session_does_not_write_to_either_reader(game_api, game_store):
    client, server = game_api
    reader = game_store.upsert_google_reader("garden-session", "garden@example.com", "Garden")
    token = game_store.create_session(reader)
    client.cookies.set(server.READER_COOKIE, token, domain="testserver.local")
    seed_card(game_store, reader_id=reader)
    seed_card(game_store, front="Default reader's card")
    shown = client.get("/api/review/due").json()["cards"][0]
    before_reader, before_default = snapshot(game_store, reader), snapshot(game_store)

    with game_store._conn() as connection:
        connection.execute("UPDATE sessions SET expires_at=? WHERE token=?", (NOW - 1, token))
    response = client.post("/api/review/game", json=request_grade(shown))

    assert response.status_code == 200
    assert response.json() == {"error": "no such card"}
    assert snapshot(game_store, reader) == before_reader
    assert snapshot(game_store) == before_default


@pytest.mark.parametrize("limit, expected", [(-10, 1), (0, 1), (5, 5), (10000, 50)])
def test_due_api_bounds_batch_size_and_excludes_future_cards(game_api, game_store, limit, expected):
    client, _ = game_api
    game_store.add_cards([{"front": "Question %d" % index, "back": "Answer", "node_id": NODE}
                          for index in range(60)])
    with game_store._conn() as connection:
        connection.execute("UPDATE srs_cards SET due=?", (NOW - 60,))
    future = seed_card(game_store, due=NOW + DAY, front="Future question")
    response = client.get("/api/review/due?limit=%s" % limit)
    assert response.status_code == 200
    cards = response.json()["cards"]
    assert len(cards) == expected
    assert all(card["due"] <= NOW and card["id"] != future["id"] for card in cards)


def test_game_api_keeps_empty_and_scheduled_decks_distinct(game_api, game_store):
    client, _ = game_api
    empty = client.get("/api/review/due").json()
    assert empty["cards"] == [] and empty["stats"]["total"] == 0
    assert empty["stats"]["next_due"] is None

    seed_card(game_store, due=NOW + 600)
    waiting = client.get("/api/review/due").json()
    assert waiting["cards"] == [] and waiting["stats"]["total"] == 1
    assert waiting["stats"]["due"] == 0
    assert waiting["stats"]["next_due"] == NOW + 600
