"""Tests that go through the real store, the real graph and the real routes.

An auditor put this better than a docstring usually can. Two serious defects
were live in a tree that ran 1,255 tests green, and the suite could not see
either one, because every test of the code that held them handed it a literal
dict on a synthetic graph:

  * The roadmap's "measured instructional rate" read `reading_log.seconds`, a
    column nothing had ever written to. Ten unit tests passed on hand-built
    reading dicts while `reading_minutes_by_title()` returned `{}` for every
    real reader and the plan never moved by a minute.
  * An adult placed at Frontier in one field dropped to stage 0 — the whole
    pre-reader interface — on one failed check in a second field. No test had
    ever sat two placements in a row.

So these are deliberately end-to-end: a real `LearnerStore`, the real
`Curriculum`, and HTTP. A unit test that mocks the path the defect lives on is
not evidence about the defect.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture()
def app_client(tmp_path):
    import primer.server as srv
    from primer.learner import LearnerStore
    from primer.wiki import WikiService
    from fastapi.testclient import TestClient
    srv.learner = LearnerStore(str(tmp_path / "e2e.db"))
    srv.wiki = WikiService(str(tmp_path / "e2e.db"))
    srv.BACKUP_DIR = str(tmp_path / "backups")
    with TestClient(srv.app) as c:
        c.post("/api/profile", json={"name": "Ada", "age": 34, "hours_per_week": 10,
                                     "breadth": "balanced", "domains": ["math"],
                                     "pronouns": "she"})
        yield c


def _stage(client):
    prof = client.get("/api/state").json().get("profile") or {}
    return prof.get("stage"), (prof.get("settings") or {}).get("placed") or {}


def _sit_placement(client, domain, ace):
    """Walk a field's whole placement staircase, acing or failing every rung."""
    import primer.server as srv
    last = {}
    for _ in range(14):
        paper = client.get("/api/placement/next?domain=" + domain).json()
        if paper.get("done") or not paper.get("questions"):
            return last
        served = srv._SERVED.get(paper["token"])["questions"]
        answers = [(str(q.get("answer", "")) if ace else "zzz") for q in served]
        last = client.post("/api/placement/submit",
                           json={"domain": domain, "stage": paper["stage"],
                                 "token": paper["token"], "answers": answers}).json()
        if last.get("done"):
            return last
    return last


def test_one_weak_field_does_not_drop_a_frontier_reader_to_the_nursery(app_client):
    """Round 22's only CRITICAL, and it was reachable in two sittings.

    The global stage is the median of what has been measured — but at two
    measurements the lower median IS the minimum, so acing one field and
    failing a check in another put the reader at stage 0. `stage <= 1` is not
    a number: it is young mode, Simple English articles, and the story frozen
    at page one, for a reader the book had just measured at Frontier.
    """
    _sit_placement(app_client, "math", ace=True)
    high, placed = _stage(app_client)
    assert high >= 4, "expected a strong math placement, got %s (%s)" % (high, placed)

    _sit_placement(app_client, "history", ace=False)
    after, placed = _stage(app_client)
    assert after >= high - 1, \
        "one field dropped the reader %d stages: %s" % (high - after, placed)
    assert after > 1, "a measured Frontier reader was put in the pre-reader interface"


def test_a_specialist_field_is_not_recorded_below_its_own_floor(app_client):
    """Radiology's only rung is graduate. Failing it means "not placed into
    radiology" — not "reads at preschool level", which is what a recorded 0
    said, and it then fed that 0 into the general median."""
    _sit_placement(app_client, "math", ace=True)
    before, _ = _stage(app_client)
    _sit_placement(app_client, "radiology", ace=False)
    after, placed = _stage(app_client)
    assert placed.get("radiology") != 0, "a floor-5 field was recorded at stage 0"
    assert after == before, "a specialist sitting moved the general reading level"


def test_reading_time_is_actually_recorded_and_actually_moves_the_plan(app_client):
    """`reading_log.seconds` existed for years and nothing ever wrote to it.

    This test exists because the unit tests for the pacing term all passed
    while the column stayed empty, so the term was a documented per-reader
    correction wired to nothing.
    """
    import primer.server as srv

    titles = []
    for node in srv.curr.nodes.values():
        for title in node.get("articles") or []:
            if title not in titles:
                titles.append(title)
        if len(titles) >= 20:
            break
    assert len(titles) >= 20

    before = app_client.get("/api/roadmap").json()
    assert before["instructional_rate"]["measured"] is False
    assert before["instructional_rate"]["factor"] == 1.0

    for title in titles[:20]:
        r = app_client.post("/api/reading/time", json={"title": title, "seconds": 9 * 60})
        assert r.json()["recorded"] is True

    assert srv.learner.reading_minutes_by_title() != {}, "the column is still empty"

    after = app_client.get("/api/roadmap").json()
    rate = after["instructional_rate"]
    assert rate["measured"] is True
    assert rate["clamped"] is False, "an ordinary reader must not land on a bound"
    assert rate["factor"] > 1.0
    assert after["estimated_years"] > before["estimated_years"], \
        "a slower reader was given the same plan as an average one"


def test_an_implausible_reading_row_is_refused_not_clamped(app_client):
    """The clock is the reader's browser. An article left open overnight is not
    eight hours of reading, and clamping it to the ceiling would still put a
    number nobody spent into the estimate."""
    r = app_client.post("/api/reading/time", json={"title": "Anything", "seconds": 8 * 3600})
    assert r.json()["recorded"] is False
    r = app_client.post("/api/reading/time", json={"title": "Anything", "seconds": 3})
    assert r.json()["recorded"] is False


def test_the_practice_path_returns_the_mark_it_recorded(app_client, monkeypatch):
    """"One paper, one mark" was fixed on the quiz path and left standing on
    this one: the drill splash tallied its own booleans against a paper the
    server may have shortened and scored with partial credit."""
    import primer.server as srv
    monkeypatch.setattr(srv, "_locked_lesson_response", lambda node, reader_id: None)
    node_id = "math.0.counting"
    gen = srv.curr.nodes[node_id]["practice"]
    paper = app_client.get("/api/practice/%s?n=6&level=0&node_id=%s" % (gen, node_id)).json()
    served = srv._SERVED.get(paper["token"])["questions"]
    answers = [str(q.get("answer", "")) for q in served]
    r = app_client.post("/api/attempt", json={"node_id": node_id, "answers": answers,
                                              "token": paper["token"], "seconds": 60}).json()
    assert "result" in r, "the drill screen has no server mark to show"
    assert set(r["result"]) >= {"score", "right", "total"}
    assert r["result"]["total"] == len(served)


def test_the_drill_prefers_what_this_reader_got_wrong(app_client, monkeypatch):
    """Adaptivity of any kind. There was none: `level` was accepted and
    ignored, and nothing about the reader reached the generator, so a child who
    cannot tell a mammal from a bird met that question no more often than any
    other. The deck already knew — every card in it was minted from a missed
    item — and the drill had never read it."""
    import primer.server as srv
    monkeypatch.setattr(srv, "_locked_lesson_response", lambda node, reader_id: None)
    node_id = "bio.0.animals"
    gen = srv.curr.nodes[node_id]["practice"]

    # Find a prompt this drill really can serve, and file it as missed.
    seen = srv.practice.generate_set(gen, 6, level=0)
    sore = [q["prompt"] for q in seen if q.get("kind") != "order"][:2]
    assert sore
    srv.learner.add_cards([{"front": p, "back": "x", "node_id": node_id, "article": ""}
                           for p in sore])
    assert set(srv.learner.missed_fronts(node_id)) >= set(sore)

    hits = 0
    for _ in range(12):
        paper = app_client.get("/api/practice/%s?n=6&level=0&node_id=%s"
                               % (gen, node_id)).json()
        hits += sum(1 for q in paper["questions"] if q["prompt"] in sore)
    assert hits >= 12, "the drill ignored the reader's own missed items (%d)" % hits


def test_a_clean_deck_changes_nothing(app_client, monkeypatch):
    """A reader who has missed nothing must see exactly the old drill."""
    import primer.server as srv
    monkeypatch.setattr(srv, "_locked_lesson_response", lambda node, reader_id: None)
    node_id = "bio.0.plants"
    gen = srv.curr.nodes[node_id]["practice"]
    assert srv.learner.missed_fronts(node_id) == []
    paper = app_client.get("/api/practice/%s?n=6&level=0&node_id=%s"
                           % (gen, node_id)).json()
    assert len(paper["questions"]) == 6
