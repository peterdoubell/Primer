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
import tempfile

import pytest

# Before ANYTHING imports primer.server: that module attaches to the live
# reader's record at import unless PRIMER_DB points elsewhere. An auditor
# noticed the fixture below rebinds the store only after the import had
# already opened content/primer.db.
os.environ.setdefault("PRIMER_DB", os.path.join(tempfile.gettempdir(), "primer-e2e-import.db"))

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
        if paper.get("settled") or paper.get("done") or not paper.get("questions"):
            return last
        served = srv._SERVED.get(paper["token"])["questions"]
        answers = [(str(q.get("answer", "")) if ace else "zzz") for q in served]
        last = client.post("/api/placement/submit",
                           json={"domain": domain, "stage": paper["stage"],
                                 "token": paper["token"], "answers": answers}).json()
        if last.get("settled") or last.get("done"):
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
        if len(titles) >= 30:
            break
    assert len(titles) >= 30

    before = app_client.get("/api/roadmap").json()
    assert before["instructional_rate"]["measured"] is False
    assert before["instructional_rate"]["factor"] == 1.0

    # Thirty articles at nine minutes is 270 minutes: past both minimums
    # (twenty articles, a hundred minutes) the rate demands before it will
    # move a plan at all.
    for title in titles[:30]:
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
    """A reader who has missed nothing sees a plain drill — at the young
    paper length, which is the floor for a stage 0-1 lesson whatever the
    client asked for (see _evidence_bar)."""
    import primer.server as srv
    monkeypatch.setattr(srv, "_locked_lesson_response", lambda node, reader_id: None)
    node_id = "bio.0.plants"
    gen = srv.curr.nodes[node_id]["practice"]
    assert srv.learner.missed_fronts(node_id) == []
    paper = app_client.get("/api/practice/%s?n=6&level=0&node_id=%s"
                           % (gen, node_id)).json()
    assert len(paper["questions"]) == srv.YOUNG_DRILL_ITEMS
    assert len({q["prompt"] for q in paper["questions"]}) == srv.YOUNG_DRILL_ITEMS


def _recheck(client, domain, ace):
    """Re-measure a settled field: back-date the cooling and sit it again."""
    import primer.server as srv
    with srv.learner._conn() as c:
        c.execute("UPDATE placement SET settled_at = settled_at - ? WHERE domain=?",
                  (srv.learner.PLACEMENT_COOLING + 60, domain))
    srv.learner.reopen_placement(domain)
    return _sit_placement(client, domain, ace)


def test_passing_evidence_never_lowers_the_reading_level(app_client):
    """An auditor walked a Forest reader to the nursery by ACING maths four
    times: {math 5, history 0} has a lower median of 0, so every settle —
    perfect ones included — stepped the stage down one rung. A sitting whose
    own result is at or above the current stage must not lower it."""
    _sit_placement(app_client, "math", ace=True)
    _sit_placement(app_client, "history", ace=False)
    before, _ = _stage(app_client)
    for _ in range(4):
        _recheck(app_client, "math", ace=True)
        after, placed = _stage(app_client)
        assert after >= before, "acing maths lowered the stage to %s (%s)" % (after, placed)
        before = after
    assert before > 1


def test_a_lone_field_recheck_moves_one_rung_and_can_come_back(app_client):
    """The single-field branch had no cap: one failed re-check went 5 -> 0
    and no later pass could raise it. One rule now, every branch."""
    _sit_placement(app_client, "math", ace=True)
    high, _ = _stage(app_client)
    assert high >= 4
    _recheck(app_client, "math", ace=False)
    down, placed = _stage(app_client)
    assert down >= high - 1, "one failed re-check dropped %d rungs" % (high - down)
    _recheck(app_client, "math", ace=True)
    back, placed = _stage(app_client)
    assert back > down, "a passed re-check could not raise the stage (%s)" % placed


def test_sitting_a_specialist_first_does_not_freeze_the_stage(app_client):
    """Radiology sat first counted as "a prior measurement", so a perfect
    maths placement afterwards was min(0, 5) = 0."""
    _sit_placement(app_client, "radiology", ace=False)
    assert _stage(app_client)[0] == 0
    _sit_placement(app_client, "math", ace=True)
    stage, placed = _stage(app_client)
    assert stage >= 4, "maths after radiology froze the stage at %s (%s)" % (stage, placed)


def test_the_stage_never_moves_more_than_one_rung_across_many_sittings(app_client):
    """The invariant, asserted across a run of sittings rather than one pair."""
    prev, _ = _stage(app_client)
    first = True
    # Real field ids. An auditor found "bio" and "chem" here: both returned
    # 409 "already settled", the helper returned {}, the stage did not move,
    # and the six-sitting invariant was asserted over four sittings.
    for domain, ace in [("math", True), ("history", False), ("physics", True),
                        ("biology", False), ("chemistry", True), ("earth", False)]:
        _sit_placement(app_client, domain, ace)
        cur, placed = _stage(app_client)
        if not first:
            assert abs(cur - prev) <= 1, "%s moved %d -> %d (%s)" % (domain, prev, cur, placed)
        first = False
        prev = cur


def test_a_child_who_misses_two_is_not_locked_out(app_client, monkeypatch):
    """The loop was not closing; it was locking. The sore-first draw put the
    burned items FIRST, `_drop_burned` removed them at submit, and the sitting
    was refused for having too few items left — on every retry, for a week."""
    import primer.server as srv
    monkeypatch.setattr(srv, "_locked_lesson_response", lambda node, reader_id: None)
    node_id = "bio.0.animals"
    gen = srv.curr.nodes[node_id]["practice"]

    def sit(miss):
        paper = app_client.get("/api/practice/%s?n=5&level=0&node_id=%s" % (gen, node_id)).json()
        served = srv._SERVED.get(paper["token"])["questions"]
        answers = []
        for i, q in enumerate(served):
            a = "zzz" if i < miss else str(q.get("answer", ""))
            # honest use: check each answer as it is given, then submit
            app_client.post("/api/quiz/check", json={"node_id": node_id, "token": paper["token"],
                                                     "id": q["id"], "answer": a})
            answers.append(a)
        return app_client.post("/api/attempt", json={"node_id": node_id, "answers": answers,
                                                     "token": paper["token"], "seconds": 60})

    first = sit(miss=2)
    assert first.status_code == 200
    refused = 0
    for _ in range(5):
        r = sit(miss=0)
        if r.status_code == 409:
            refused += 1
    assert refused == 0, "%d of 5 honest retries were refused" % refused


def _sit_practice(client, node_id, answer_for):
    """One honest practice sitting: check each answer as given, then submit."""
    import primer.server as srv
    gen = srv.curr.nodes[node_id]["practice"]
    paper = client.get("/api/practice/%s?n=5&level=0&node_id=%s" % (gen, node_id)).json()
    served = srv._SERVED.get(paper["token"])["questions"]
    answers = []
    for i, q in enumerate(served):
        a = answer_for(i, q)
        client.post("/api/quiz/check", json={"node_id": node_id, "token": paper["token"],
                                             "id": q["id"], "answer": a})
        answers.append(a)
    return client.post("/api/attempt", json={"node_id": node_id, "answers": answers,
                                             "token": paper["token"], "seconds": 60})


def test_honest_practice_is_never_refused_at_any_miss_rate(app_client, monkeypatch):
    """The third audit reached past the two-miss test: miss four of five for
    six sittings, then answer everything right, and the reader who had just
    LEARNED the items was refused 3 of 3 times. Evidence and exposure are
    separate now — a sitting with too few countable items is graded, its
    misses become cards, and it records no mastery. Nobody is refused."""
    import primer.server as srv
    monkeypatch.setattr(srv, "_locked_lesson_response", lambda node, reader_id: None)
    node_id = "bio.0.animals"
    for miss in (5, 4, 3, 2):
        for _ in range(4):
            r = _sit_practice(app_client, node_id,
                              lambda i, q, m=miss: "zzz" if i < m else str(q.get("answer", "")))
            assert r.status_code == 200, (miss, r.status_code, r.json())
    for _ in range(3):
        r = _sit_practice(app_client, node_id, lambda i, q: str(q.get("answer", "")))
        assert r.status_code == 200, r.json()


def _days_pass(monkeypatch, days):
    """Advance the WALL CLOCK, not just the card table. The first version of
    the half-knower test aged `srs_cards.due` by SQL and never moved
    `time.time`, so the proving gap could never elapse and "never credited"
    was a property of the clock. A reader who knew everything was also never
    credited under it; the assertion could not fail."""
    import time as _t
    import primer.learner as L
    import primer.server as srv
    base = _t.time()
    monkeypatch.setattr(L.time, "time", lambda: base + days * 86400)
    monkeypatch.setattr(srv.time, "time", lambda: base + days * 86400)


def _run_days(app_client, monkeypatch, node_id, answer_for, days=45):
    import primer.server as srv
    for day in range(days):
        _days_pass(monkeypatch, day)
        r = _sit_practice(app_client, node_id, answer_for).json()
        if r.get("newly_mastered") or r.get("proven"):
            return day
    return None


def test_a_reader_who_knows_half_and_taps_the_rest_is_not_credited(app_client, monkeypatch):
    """The auditor's scenario, with the clock actually running and the
    unknowns answered the only way a child can answer them on a tap screen:
    by tapping one of the four. Under a five-item, one-miss, two-pass bar
    that reader was credited on every seed. The young bar is eight items,
    every one right, three spaced passes."""
    import random
    import primer.server as srv
    monkeypatch.setattr(srv, "_locked_lesson_response", lambda node, reader_id: None)
    node_id = "bio.0.plants"
    credited = []
    for seed in (1, 2):
        rnd = random.Random(seed)
        # A FIXED half, decided per item once and never growing: this reader
        # learns nothing from any sitting. (A first draft let the known set
        # grow by chance on every sitting, which is a learner, not a
        # half-knower — and a learner should be credited.)
        known = {}

        def knows(prompt):
            if prompt not in known:
                known[prompt] = rnd.random() < 0.5
            return known[prompt]

        def answer_for(i, q):
            if knows(q["prompt"]):
                return str(q.get("answer", ""))
            return rnd.choice(q.get("choices") or [str(q.get("answer", ""))])

        day = _run_days(app_client, monkeypatch, node_id, answer_for)
        credited.append(day)
        with srv.learner._conn() as c:
            for t in ("mastery", "srs_cards", "attempts"):
                try:
                    c.execute("DELETE FROM %s WHERE node_id=?" % t, (node_id,))
                except Exception:
                    pass
    assert credited == [None, None], "credited with mastery on days %s" % credited


def test_a_reader_who_learns_from_the_explanations_is_credited_in_days(app_client, monkeypatch):
    """The other side of the bar: a Seedling who learns every item she is
    shown, reviews daily, and answers honestly must be credited — in days,
    not a fortnight. Age 5, so the burn window is two days."""
    import primer.server as srv
    monkeypatch.setattr(srv, "_locked_lesson_response", lambda node, reader_id: None)
    app_client.post("/api/profile", json={"name": "Ada", "age": 5, "hours_per_week": 3,
                                          "breadth": "balanced", "domains": ["biology"],
                                          "pronouns": "she"})
    node_id = "bio.0.plants"
    learned = set()

    def answer_for(i, q):
        if q["prompt"] in learned:
            return str(q.get("answer", ""))
        learned.add(q["prompt"])   # shown the answer and its explanation
        return "zzz"

    day = _run_days(app_client, monkeypatch, node_id, answer_for, days=30)
    assert day is not None and day <= 14, "an honest learner was credited on day %s" % day



def test_a_reader_measured_at_forest_is_not_parked_in_the_nursery(app_client):
    """The one-rung cap throttled recovery as hard as demotion: fail maths
    once (stage 0), re-check a week later acing every rung, and the reader
    sat at stage 1 — the pre-reader interface — with a stage-5 result in
    hand, for a month of weekly re-checks. The cap is on distance from the
    evidence, not on velocity: upward moves go to the target."""
    _sit_placement(app_client, "math", ace=False)
    assert _stage(app_client)[0] == 0
    _recheck(app_client, "math", ace=True)
    stage, placed = _stage(app_client)
    assert stage >= 4, "a Forest result left the reader at stage %s (%s)" % (stage, placed)


def test_history_then_maths_lands_at_the_median_not_one_rung_up(app_client):
    _sit_placement(app_client, "history", ace=False)
    _sit_placement(app_client, "math", ace=True)
    stage, placed = _stage(app_client)
    # {0, 5}: the even count splits the difference. Grove, not Seedling.
    assert stage == 3, (stage, placed)


def test_ascension_writes_the_stage_through_the_same_policy(app_client, monkeypatch):
    """A second, uncapped writer: the ascension ceremony wrote max(stage,
    rank) over a lower median of assumed credit, and moved a reader from 1
    to 5 with two passes on a preschool node. One writer, one policy."""
    import primer.server as srv
    monkeypatch.setattr(srv, "_locked_lesson_response", lambda node, reader_id: None)
    _sit_placement(app_client, "history", ace=False)
    _sit_placement(app_client, "math", ace=True)
    before, _ = _stage(app_client)
    # Two passes on a stage-0 node: real evidence, but preschool evidence.
    node_id = "math.0.counting"
    for _ in range(2):
        with srv.learner._conn() as c:
            c.execute("UPDATE mastery SET first_pass_at = first_pass_at - 86400*2 WHERE node_id=?", (node_id,))
        _sit_practice(app_client, node_id, lambda i, q: str(q.get("answer", "")))
    after, placed = _stage(app_client)
    assert after <= max(before, 3), "a preschool pass moved the stage %d -> %d (%s)" % (before, after, placed)


def test_assumed_credit_does_not_open_the_graduate_gate(app_client):
    """The decision, written down: placement credit opens every rung up to
    undergraduate work; the graduate gate counts proven nodes only."""
    import primer.server as srv
    _sit_placement(app_client, "math", ace=True)
    gates = srv.learner.gate_map()
    proven = srv.learner.proven_set()
    assert not proven
    grad = [n for n in srv.curr.nodes.values() if n["domain"] == "math" and n["stage"] == 5]
    opened = [n["id"] for n in grad if srv.curr.unlocked(n, gates, proven)]
    assert not opened, "graduate nodes opened on assumed credit alone: %s" % opened[:3]
    under = [n for n in srv.curr.nodes.values() if n["domain"] == "math" and n["stage"] == 4]
    assert any(srv.curr.unlocked(n, gates, proven) for n in under), \
        "placement should still open undergraduate work"


def _prove(client, node_id, times=3):
    """Prove a node by spaced passes, back-dating each so the next counts.
    Three, because a stage 0-1 node now takes three (see _evidence_bar)."""
    import primer.server as srv
    for _ in range(times):
        with srv.learner._conn() as c:
            c.execute("UPDATE mastery SET first_pass_at = first_pass_at - 86400*3 WHERE node_id=?",
                      (node_id,))
        _sit_practice(client, node_id, lambda i, q: str(q.get("answer", "")))


def test_an_earned_stage_is_not_erased_by_a_first_failed_placement(app_client, monkeypatch):
    """The first-measurement branch wrote the raw result and never called the
    writer, so a reader who had EARNED stage 2 by proving thirteen maths
    nodes sat their first placement, failed it, and went to 0 in one sitting."""
    import primer.server as srv
    monkeypatch.setattr(srv, "_locked_lesson_response", lambda node, reader_id: None)
    for n in [n for n in srv.curr.nodes.values() if n["domain"] == "math" and n["stage"] <= 1]:
        _prove(app_client, n["id"])
    earned, _ = _stage(app_client)
    assert earned >= 1, "proving the nursery and stage 1 should have ascended the reader"
    _sit_placement(app_client, "history", ace=False)
    after, placed = _stage(app_client)
    assert after >= earned - 1, "first failed placement dropped %d -> %d (%s)" % (earned, after, placed)


def test_mastery_can_promote_a_reader_a_placement_demoted(app_client, monkeypatch):
    """`settings.rank` was a high-water mark: once a placement demoted a
    reader, mastery could never promote them back to any stage at or below
    the old rank. The evidence path must always be open from below."""
    import primer.server as srv
    monkeypatch.setattr(srv, "_locked_lesson_response", lambda node, reader_id: None)
    _sit_placement(app_client, "math", ace=True)
    high, _ = _stage(app_client)
    # Walk the reader down one rung a week until the pre-reader interface.
    for _ in range(6):
        _recheck(app_client, "math", ace=False)
        if _stage(app_client)[0] <= 1:
            break
    low, _ = _stage(app_client)
    assert low <= 1 < high
    # Now the evidence path: prove the nursery and stage 1 in maths.
    for n in [n for n in srv.curr.nodes.values() if n["domain"] == "math" and n["stage"] <= 1]:
        _prove(app_client, n["id"])
    after, placed = _stage(app_client)
    assert after > low, "mastery could not promote a demoted reader (%d, %s)" % (after, placed)


def test_every_surface_agrees_on_the_graduate_gate(app_client):
    """The map said open, the node page said locked, and the node page gave
    no reason. After an aced interview with nothing proved, every surface
    must say the same thing about every stage-5 node."""
    import primer.server as srv
    _sit_placement(app_client, "math", ace=True)
    graph = app_client.get("/api/curriculum").json()
    by_id = {n["id"]: n for n in graph["nodes"]}
    grad = [n for n in srv.curr.nodes.values() if n["domain"] == "math" and n["stage"] == 5]
    assert grad
    for n in grad:
        on_map = by_id[n["id"]]["unlocked"]
        page = app_client.get("/api/curriculum/node/" + n["id"]).json()
        quiz = app_client.get("/api/quiz/" + n["id"] + "?n=4").status_code
        assert on_map is False, "%s open on the map on assumed credit" % n["id"]
        assert page["unlocked"] is False, "%s open on the node page" % n["id"]
        assert quiz == 409, "%s quiz issued on assumed credit" % n["id"]
        assert page.get("unlock_requirements"), "%s locked with no reason given" % n["id"]
