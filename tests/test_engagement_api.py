"""The server half of the engagement round: the shape of a day.

Seven things the API could not previously say, all of them additive — the
current client reads none of these keys and must keep working exactly as it
did, which is why every assertion below is about a key that is *new*:

  /api/today      lessons[].resume/passes/ready_at — the appointment the
                  engine already made, carried to the front of the day
  /api/today      pending[]  — the appointments that did not fit the five
  /api/today      tomorrow{} — a day that has a tomorrow
  /api/today      absence{}  — how long the reader was gone, and what was kept
  /api/today      quest[].done_count/goal — a step that fills, not a checkbox
  /api/review/due goal       — the deck's own stopping point
  /api/quiz/submit story_unlocked — the page delivered where it was earned,
                  handed over WITHOUT being turned

Every test builds its own temporary database. Nothing here touches
content/primer.db.

Run:  python3 -m pytest tests/test_engagement_api.py -q
"""

import contextlib
import datetime
import json
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from primer.learner import (  # noqa: E402
    DAY, LearnerStore, _end_of_tomorrow, _mastery_min_interval,
)
from primer.wiki import WikiService  # noqa: E402


@contextlib.contextmanager
def book(tmp_path, name="Ada", age=8, domains=("math", "physics")):
    """An onboarded reader with a database of their own.

    Function-scoped on purpose: every test here is about the state of one
    day, and a shared database would let one day's events colour the next.
    """
    import primer.server as srv
    from fastapi.testclient import TestClient

    db = str(tmp_path / "engagement.db")
    saved = (srv.learner, srv.wiki, srv.BACKUP_DIR)
    srv.learner = LearnerStore(db)
    srv.wiki = WikiService(db)
    srv.BACKUP_DIR = str(tmp_path / "backups")
    try:
        with TestClient(srv.app) as client:
            r = client.post("/api/profile", json={
                "name": name, "age": age, "hours_per_week": 6,
                "breadth": "balanced", "domains": list(domains)})
            assert r.status_code == 200
            yield client, srv
    finally:
        srv.learner, srv.wiki, srv.BACKUP_DIR = saved


def _frontier(srv, domains):
    """Exactly the candidates `today()` will draw from, in its own terms."""
    return [n["id"] for n in srv.curr.next_lessons(
        srv.learner.gate_map(), domains, per_domain=1)]


def _sql(srv, statement, *args):
    with srv.learner._conn() as c:
        return c.execute(statement, args).fetchall()


def _cards_due_now(srv, count, node_id="math.2.fractions"):
    srv.learner.add_cards([{"front": "front %d" % i, "back": "back %d" % i,
                            "node_id": node_id} for i in range(count)])
    _sql(srv, "UPDATE srs_cards SET due=?", time.time() - 3600)


def _pass_paper(client, srv, node_id, make_cards=False):
    """Sit one paper and answer it out of the book's own key."""
    paper = client.get("/api/quiz/{}?n=5".format(node_id)).json()
    assert "token" in paper, paper
    served = srv._SERVED[paper["token"]]["questions"]
    return client.post("/api/quiz/submit", json={
        "node_id": node_id, "token": paper["token"], "make_cards": make_cards,
        "answers": [q.get("answer", "") for q in served]}).json()


def _age_the_proving_gap(srv, node_id, days=4):
    """Move a node's passes back in time so the next one can prove it."""
    _sql(srv, "UPDATE mastery SET first_pass_at=first_pass_at-?, "
              "last_pass_at=last_pass_at-? WHERE node_id=?",
         days * DAY, days * DAY, node_id)


def _local_days_ago(days):
    """Local noon, `days` calendar days back — never 86400*days, which lands
    on the wrong side of midnight across a DST change."""
    day = datetime.date.today() - datetime.timedelta(days=days)
    return time.mktime(datetime.datetime(day.year, day.month, day.day, 12).timetuple())


# ---------------- rank 1: the appointment leads the day ----------------


def test_a_started_lesson_leads_the_day_and_the_rest_still_holds_its_order(tmp_path):
    """A lesson one earned pass short of mastery comes back first, and only
    two of them ever do.

    Before this, whether the reader met their half-proved lesson again was
    roughly a coin flip: the day's five were drawn from a seeded shuffle that
    knew nothing about open loops. The cap is the other half of the fix —
    uncapped, a reader with six half-done lessons opens the book to a day
    made entirely of debt.
    """
    domains = ["math", "physics", "biology", "cs", "chemistry", "history"]
    with book(tmp_path, domains=domains) as (client, srv):
        candidates = _frontier(srv, domains)
        assert len(candidates) >= 6, "setup: one frontier lesson per domain"

        started = candidates[:3]
        for node_id in started:
            srv.learner.record_attempt(node_id, 0.9)

        today = client.get("/api/today").json()
        lessons = today["lessons"]
        assert len(lessons) == 5

        resumed = [n for n in lessons if n.get("resume")]
        assert len(resumed) == 2, "at most two of the five may be debt"
        assert [n["id"] for n in lessons[:2]] == [n["id"] for n in resumed], \
            "the open loops lead the day"
        for n in resumed:
            assert n["passes"] == 1
            assert isinstance(n["ready_at"], float) and n["ready_at"] > time.time()
        for n in lessons[2:]:
            assert "resume" not in n and "ready_at" not in n, \
                "a lesson never started carries no appointment"

        # The third appointment is not shown, and is not silently forgotten.
        left_over = set(started) - {n["id"] for n in lessons}
        assert len(left_over) == 1
        waiting = {p["id"]: p for p in today["pending"]}
        assert set(waiting) == left_over
        entry = waiting[left_over.pop()]
        assert entry["title"] and entry["title"] != entry["id"]
        assert isinstance(entry["ready_at"], float)

        # And the day is still the same day on a refresh — the reason the
        # shuffle is seeded at all.
        again = client.get("/api/today").json()
        assert [n["id"] for n in again["lessons"]] == [n["id"] for n in lessons]
        assert [p["id"] for p in again["pending"]] == [p["id"] for p in today["pending"]]


def test_an_appointment_that_has_come_due_leads_the_ones_that_have_not(tmp_path):
    """`ready_at` is never nulled once it has elapsed, so "ready now" has to
    sort ahead of "ready tomorrow" rather than collapse into a null."""
    with book(tmp_path, domains=("math", "physics")) as (client, srv):
        candidates = _frontier(srv, ["math", "physics"])
        assert len(candidates) == 2
        for node_id in candidates:
            srv.learner.record_attempt(node_id, 0.9)

        before = client.get("/api/today").json()["lessons"]
        assert all(n.get("resume") for n in before[:2])
        second = before[1]["id"]

        # That one's proving window opened a month ago.
        _sql(srv, "UPDATE mastery SET first_pass_at=? WHERE node_id=?",
             time.time() - 30 * DAY, second)

        after = client.get("/api/today").json()["lessons"]
        assert after[0]["id"] == second, "an appointment already open comes first"
        assert after[0]["ready_at"] < time.time()
        assert after[1]["ready_at"] > time.time()


def test_tomorrow_is_only_ever_what_is_waiting(tmp_path):
    """The crown's full stop becomes a sentence — but only where there is
    something true to say. Every field here is null-able for exactly that
    reason: a new reader must never be told about a tomorrow they do not have.
    """
    with book(tmp_path) as (client, srv):
        fresh = client.get("/api/today").json()
        tomorrow = fresh["tomorrow"]
        assert tomorrow["due_tomorrow"] == 0
        assert tomorrow["next_due"] is None
        assert tomorrow["next_ready"] is None
        assert tomorrow["streak_next"] == fresh["streak"] + 1
        assert tomorrow["milestone"] == {"days": 3, "away": 3 - fresh["streak"]}

        # Two cards in the backlog, one genuinely scheduled for tomorrow.
        _cards_due_now(srv, 3)
        noon_tomorrow = _local_days_ago(-1)   # negative: local noon tomorrow
        card_id = _sql(srv, "SELECT id FROM srs_cards ORDER BY id LIMIT 1")[0][0]
        _sql(srv, "UPDATE srs_cards SET due=? WHERE id=?", noon_tomorrow, card_id)

        node_id = _frontier(srv, ["math"])[0]
        srv.learner.record_attempt(node_id, 0.9)

        today = client.get("/api/today").json()
        tomorrow = today["tomorrow"]
        assert tomorrow["due_tomorrow"] == 3, "the backlog is waiting too"
        assert tomorrow["next_due"] == pytest.approx(noon_tomorrow)
        # A 7-11 year old's proving window is 16 hours: this appointment
        # really does fall before the end of tomorrow.
        expected = _sql(srv, "SELECT first_pass_at FROM mastery WHERE node_id=?",
                        node_id)[0][0] + _mastery_min_interval(8)
        assert expected < _end_of_tomorrow(time.time())
        assert tomorrow["next_ready"] == pytest.approx(expected)


def test_an_appointment_past_tomorrow_is_not_tomorrows_news(tmp_path):
    """An adult's proving window is two days, which is past the horizon — the
    lesson is still named among today's five, but `tomorrow` stays quiet
    about it rather than promising a date it cannot keep."""
    with book(tmp_path, age=34) as (client, srv):
        node_id = _frontier(srv, ["math"])[0]
        srv.learner.record_attempt(node_id, 0.9)

        today = client.get("/api/today").json()
        assert today["lessons"][0]["id"] == node_id
        assert today["lessons"][0]["resume"] is True
        assert today["lessons"][0]["ready_at"] > _end_of_tomorrow(time.time())
        assert today["tomorrow"]["next_ready"] is None


# ---------------- rank 2: the page turns where it was earned ----------------


def test_mastery_hands_over_the_page_without_turning_it(tmp_path):
    """The chapter arrives with the confetti — and `/api/story/advance` is
    still the only thing that moves the reader forward.

    That separation is the whole design: the response is a READ of the story
    cursor, so a splash re-opened from history cannot grant the chapter's 15
    XP a second time. The advance below proves the writer still works, and
    the event count proves this endpoint is not one.
    """
    with book(tmp_path, domains=("math",)) as (client, srv):
        target = srv.STORY["chapters"][0]["leads_to"]
        assert target == "math.0.counting", "setup: the first chapter's lesson"

        # A stage 0-1 lesson takes three spaced passes now (see
        # server._evidence_bar): the first two hand nothing over.
        first = _pass_paper(client, srv, target)
        _pass_paper(client, srv, target)
        assert first["mastery"]["newly_mastered"] is False, \
            "one pass is not proof — the gap has to be kept"
        assert first["story_unlocked"] is None

        _age_the_proving_gap(srv, target)
        second = _pass_paper(client, srv, target)
        assert second["mastery"]["newly_mastered"] is True

        unlocked = second["story_unlocked"]
        assert unlocked is not None
        assert unlocked["number"] == 1
        assert unlocked["title"] == unlocked["chapter"]["title"]
        assert unlocked["chapter"]["leads_to"] == target
        assert "{" not in unlocked["title"], "the chapter arrives personalised"

        # Nothing was written. The page is offered, not turned.
        story = client.get("/api/story").json()
        assert story["progress"] == 0 and story["can_advance"] is True
        assert _sql(srv, "SELECT COUNT(*) FROM events WHERE kind='chapter'")[0][0] == 0

        # And the sole writer still is one.
        advanced = client.post("/api/story/advance").json()
        assert advanced == {"progress": 1, "advanced": True, "xp_gained": 15}
        assert _sql(srv, "SELECT COUNT(*) FROM events WHERE kind='chapter'")[0][0] == 1


def test_mastering_some_other_lesson_does_not_turn_the_page(tmp_path):
    """`newly_mastered` is not enough: the page turns only where the open
    chapter was actually waiting."""
    with book(tmp_path, domains=("math",)) as (client, srv):
        target = srv.STORY["chapters"][0]["leads_to"]
        _pass_paper(client, srv, target)
        _age_the_proving_gap(srv, target)
        _pass_paper(client, srv, target)
        _age_the_proving_gap(srv, target)
        _pass_paper(client, srv, target)   # third: a stage 0-1 lesson takes three

        other = next(n for n in _frontier(srv, ["math"]) if n != target)
        _pass_paper(client, srv, other)
        _age_the_proving_gap(srv, other)
        _pass_paper(client, srv, other)   # three spaced passes for a stage 0-1 lesson
        _age_the_proving_gap(srv, other)
        result = _pass_paper(client, srv, other)

        assert result["mastery"]["newly_mastered"] is True
        assert result["story_unlocked"] is None, \
            "the chapter is still waiting on its own lesson"


# ---------------- rank 4: a day with a bottom ----------------


def test_the_review_step_fills_instead_of_ticking(tmp_path):
    """One graded card used to complete the whole day's reviewing.

    The goal is priced against the cards done PLUS the cards left, so it
    cannot recede as the reader meets it: five of five stays five of five,
    never "five of the fifteen that are left".
    """
    with book(tmp_path) as (client, srv):
        _cards_due_now(srv, 5)

        step = client.get("/api/today").json()["quest"]["review"]
        assert (step["done_count"], step["goal"], step["done"]) == (0, 5, False)
        assert step["count"] == 5, "the old availability count is untouched"

        cards = client.get("/api/review/due").json()["cards"]
        for card in cards[:2]:
            client.post("/api/review", json={"card_id": card["id"], "quality": 5})

        step = client.get("/api/today").json()["quest"]["review"]
        assert (step["done_count"], step["goal"], step["done"]) == (2, 5, False), \
            "two of five is two of five, not a completed day"

        for card in cards[2:5]:
            client.post("/api/review", json={"card_id": card["id"], "quality": 5})

        step = client.get("/api/today").json()["quest"]["review"]
        assert (step["done_count"], step["goal"], step["done"]) == (5, 5, True)


def test_the_day_has_a_ceiling_and_the_deck_names_the_same_one(tmp_path):
    """A 200-card backlog becomes a finishable twelve — and the deck stops
    where the tile said it would, or the number on the tile is a lie."""
    with book(tmp_path) as (client, srv):
        _cards_due_now(srv, 40)

        today = client.get("/api/today").json()
        assert today["quest"]["review"]["goal"] == 12
        assert today["quest"]["review"]["count"] == 40, "what is waiting is still said"
        assert client.get("/api/review/due").json()["goal"] == 12


def test_an_empty_deck_is_still_excused_and_still_yields_the_crown(tmp_path):
    """The excusal rule is the one thing this change may not touch: a step
    with nothing available to do has always been excused rather than left
    blocking the crown, and `goal == 0` has to mean exactly what `count == 0`
    used to mean.
    """
    with book(tmp_path) as (client, srv):
        today = client.get("/api/today").json()
        review = today["quest"]["review"]
        assert review["goal"] == 0 and review["done"] is False
        assert review["excused"] is True and review["hint"]

        read = today["quest"]["read"]
        assert read["goal"] == 1 and read["excused"] is False, \
            "an article is always available — this step can never be excused"
        assert today["quest"]["learn"]["goal"] == 1

        srv.learner.record_attempt("math.2.fractions", 0.9)
        _sql(srv, "INSERT INTO events(kind,payload,at,xp) VALUES('read',?,?,0)",
             json.dumps({"title": "Fractions"}), time.time())

        today = client.get("/api/today").json()
        assert today["quest_done"] == today["quest_total"], \
            "an honest day with nothing due still completes"


# ---------------- rank 5: the book kept your place ----------------


def test_a_first_afternoon_is_not_a_lapse(tmp_path):
    """A reader whose whole history is today has no absence to report, and
    `None` from the store means exactly that — never "long ago"."""
    with book(tmp_path) as (client, srv):
        assert client.get("/api/today").json()["absence"] is None


def test_the_book_says_how_long_it_waited_and_what_it_kept(tmp_path):
    """Backward-looking, every field. How long, what still stands, which
    chapter is waiting, and a best streak that is a record rather than a
    thing recently lost."""
    with book(tmp_path) as (client, srv):
        _sql(srv, "INSERT INTO events(kind,payload,at,xp) VALUES('read',?,?,0)",
             json.dumps({"title": "Butterflies"}), _local_days_ago(19))

        today = client.get("/api/today").json()
        absence = today["absence"]
        assert absence["days_away"] == 19
        assert absence["last_seen"] == pytest.approx(_local_days_ago(19))
        assert absence["standing"] == today["mastered"]
        assert absence["best_streak"] == today["best_streak"]
        assert absence["chapter_title"] == today["story"]["title"]


def test_a_returning_day_asks_for_five_cards_not_twelve(tmp_path):
    """The backlog is not a debt to be collected on the first afternoon
    back, and the deck has to agree with the tile about it."""
    with book(tmp_path) as (client, srv):
        _cards_due_now(srv, 40)
        assert client.get("/api/today").json()["quest"]["review"]["goal"] == 12

        _sql(srv, "INSERT INTO events(kind,payload,at,xp) VALUES('read',?,?,0)",
             json.dumps({"title": "Butterflies"}), _local_days_ago(19))

        assert client.get("/api/today").json()["quest"]["review"]["goal"] == 5
        assert client.get("/api/review/due").json()["goal"] == 5


def test_an_absence_older_than_the_log_can_vouch_for_is_left_unsaid(tmp_path):
    """Past the retention window `prune()` keeps one representative row per
    day, so "when were you last here" stops being a measurement. Unknown is
    said as unknown — and it must not quietly ease the day either, or the
    book would be reasoning from a number it just refused to report.
    """
    with book(tmp_path) as (client, srv):
        _cards_due_now(srv, 40)
        _sql(srv, "INSERT INTO events(kind,payload,at,xp) VALUES('read',?,?,0)",
             json.dumps({"title": "Long ago"}), _local_days_ago(500))

        today = client.get("/api/today").json()
        assert today["absence"] is None
        assert today["quest"]["review"]["goal"] == 12


# ---------------- rank 11 wiring: a tally is an answer ----------------


def test_the_young_ordering_step_keeps_a_tally_item(tmp_path):
    """A `tally` asks a child to count and hand back a number — a produced
    answer, not a recognition item.

    Left off the keep list it is classified as droppable, and because it is
    spliced in last it is the first thing dropped: the one question shape
    built for these readers, removed for exactly the readers it was built
    for. The paper still ships exactly n items.
    """
    import primer.server as srv

    node = srv.curr.node("math.0.counting")
    tally = {"kind": "tally", "prompt": "Touch each apple.",
             "items": ["\U0001F34E"] * 4, "answer": "4"}
    recognition = [{"kind": "choice", "prompt": "Which is %d?" % i,
                    "choices": ["1", "2"], "answer": "1"} for i in range(5)]

    paper = srv._add_young_ordering(recognition + [tally], node, 6, 0)

    assert len(paper) == 6
    assert tally in paper, "the counting question survives the ordering splice"
    assert sum(1 for q in paper if q.get("kind") == "order") == 1


# ---------------- the book learns to say how long ----------------
# Added for benchmark 12 (Ferriss): the product could not tell a reader what
# it was asking of them — not for a card, not for a quiz, not for the evening.
# These cover the three claims that makes: a per-item clock that cannot be
# poisoned, an estimate that says which kind of number it is, and a short
# sitting that is smaller without being lesser.


def test_a_per_item_reading_outside_the_plausible_band_is_discarded():
    from primer.learner import _per_item_seconds

    assert _per_item_seconds(100.0, 5) == 20.0
    # No items, no reading.
    assert _per_item_seconds(100.0, 0) is None
    # A hostile or absent client.
    assert _per_item_seconds(None, 5) is None
    assert _per_item_seconds("twenty", 5) is None
    assert _per_item_seconds(float("inf"), 5) is None
    # A reader who answered the door: discarded, not clamped. Clamping a
    # forty-minute interruption to five minutes still puts a number nobody
    # spent into the median.
    assert _per_item_seconds(40 * 60.0, 1) is None
    # And an impossibly fast one, which is the shape a script has.
    assert _per_item_seconds(1.0, 5) is None


def test_the_book_does_not_claim_to_have_timed_a_reader_it_has_not(tmp_path):
    with book(tmp_path) as (client, srv):
        pace = client.get("/api/today").json()["pace"]
        assert pace["measured"] is False
        assert pace["partly"] is False
        # A fresh book has real work priced on the bill: the total is a
        # positive number of minutes, and it is the sum of its own parts.
        # (Excused steps are legitimately zero, so "never zero" is not a
        # property any single step can promise.)
        assert pace["minutes_left"] > 0
        assert pace["minutes_left"] == sum(pace["steps"].values())
        assert srv.learner.pace("review") is None


def test_enough_timed_cards_and_the_estimate_becomes_the_readers_own(tmp_path):
    with book(tmp_path) as (client, srv):
        _cards_due_now(srv, 10)
        due = client.get("/api/review/due?limit=10").json()["cards"]
        # Ten seconds a card, comfortably inside the plausible band and well
        # under the 25s default, so the direction of the change is visible.
        for card in due[:srv.learner.PACE_MIN_SAMPLES]:
            client.post("/api/review",
                        json={"card_id": card["id"], "quality": 4, "seconds": 10.0})
        assert srv.learner.pace("review") == 10.0
        pace = client.get("/api/today").json()["pace"]
        # Only the cards have been timed; the learn step is still priced from
        # the default. That is "partly", not "measured" — the earlier version
        # of this test pinned the conflation in rather than catching it.
        assert pace["measured"] is False
        assert pace["partly"] is True
        assert pace["card_seconds"] == 10.0


def test_a_short_sitting_lowers_the_ask_and_never_the_deck(tmp_path):
    with book(tmp_path) as (client, srv):
        _cards_due_now(srv, 20)
        full = client.get("/api/review/due?limit=30").json()
        short = client.get("/api/review/due?limit=30&dose=short").json()
        assert full["goal"] > short["goal"] == srv.SHORT_DOSE_CARDS
        # The cards behind the ask are untouched: a smaller door into the same
        # room, not a different and lesser deck.
        assert len(short["cards"]) == len(full["cards"])
        assert short["stats"]["due"] == full["stats"]["due"]
        assert short["dose"] == "short" and full["dose"] == "full"


def test_an_excused_or_finished_step_costs_the_reader_no_minutes(tmp_path):
    with book(tmp_path) as (client, srv):
        today = client.get("/api/today").json()
        # A fresh reader's deck is empty, so the review step is excused — and
        # an excused step must not be priced, or the evening's total asks for
        # time against work the book has already said is not there.
        assert today["quest"]["review"]["excused"] is True
        assert today["pace"]["steps"]["review"] == 0


def test_the_short_door_opens_onto_work_the_day_still_owes(tmp_path):
    """Regression: the smallest sitting was chosen from the deck alone.

    `"review" if deck["due"] else "learn"` never asked whether either step was
    still on the bill. So a reader who sat their lesson that morning and whose
    deck was clear was offered "One lesson quiz, about 5 minutes" — a five
    minute door into the only room they had already left — while the one step
    still owed, the article, went unnamed. It is the minimum-effective-dose
    control, and it was pointing at finished work.
    """
    with book(tmp_path) as (client, srv):
        _pass_paper(client, srv, _frontier(srv, ["math", "physics"])[0])
        today = client.get("/api/today").json()
        quest, pace = today["quest"], today["pace"]
        # The state that used to mislead: learn done, deck clear, read owed.
        assert quest["learn"]["done"] is True
        assert quest["review"]["excused"] is True
        assert quest["read"]["done"] is False
        # There is no shorter version of "read one article" than reading one,
        # so the honest answer is that there is no smaller door — and an empty
        # kind with no minutes behind it is how the client is told to draw none.
        assert pace["short_kind"] == ""
        assert pace["short_minutes"] == 0

        # And when the deck does have something to say, the door opens on it.
        _cards_due_now(srv, 20)
        pace = client.get("/api/today").json()["pace"]
        assert pace["short_kind"] == "review"
        assert pace["short_cards"] == srv.SHORT_DOSE_CARDS
        assert pace["short_minutes"] > 0
