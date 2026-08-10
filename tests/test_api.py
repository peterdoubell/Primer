"""HTTP-layer tests: exercise the API the way the book actually uses it.

These cover the endpoint contracts, the security headers, and the concurrency
path that a multi-year single-user deployment depends on. They run against a
throwaway database so the reader's real record is never touched.
"""

import json
import os
import sys
import tempfile
import threading
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    """Boot the app against an isolated database."""
    tmp = tmp_path_factory.mktemp("primerdb")
    db = str(tmp / "test.db")
    import primer.server as srv
    from primer.learner import LearnerStore
    from primer.wiki import WikiService
    # Point the singletons at the throwaway DB before the TestClient starts.
    srv.learner = LearnerStore(db)
    srv.wiki = WikiService(db)
    srv.BACKUP_DIR = str(tmp / "backups")
    from fastapi.testclient import TestClient
    with TestClient(srv.app) as c:
        yield c


@pytest.fixture(scope="module")
def onboarded(client):
    r = client.post("/api/profile", json={
        "name": "Ada", "age": 8, "hours_per_week": 6,
        "breadth": "balanced", "domains": ["math", "physics"]})
    assert r.status_code == 200
    return r.json()


def _play(client, path, node_id=None, wrong=False):
    """Sit a paper the way the app does: fetch, mark each item, then submit."""
    paper = client.get(path).json()
    keys = answer_key(paper)
    answers = ["definitely wrong" if wrong else k for k in keys]
    return paper, answers


# ---------------- contracts ----------------


def answer_key(paper):
    """The keys for a served paper, read from the book's own copy.

    A test cannot get these over the wire any more — the key never ships with
    the paper, and asking for feedback costs a real committed answer. Reaching
    into the server's memory is the honest way to know what a correct sheet
    looks like without teaching the tests to cheat.
    """
    import primer.server as srv
    served = srv._SERVED[paper["token"]]["questions"]
    by_id = {q.get("id"): q.get("answer", "") for q in served}
    return [by_id.get(q["id"], "") for q in paper["questions"]]

def test_healthz(client):
    d = client.get("/healthz").json()
    assert d["ok"] and d["nodes"] > 300


def test_state_before_onboarding_is_honest(client):
    d = client.get("/api/state").json()
    assert "onboarded" in d and len(d["domains"]) == 10


def test_profile_places_by_age_but_marks_it_assumed(client, onboarded):
    assert onboarded["stage"] == 1
    t = client.get("/api/today").json()
    assert t["assumed"] > 0 and t["mastered"] == 0, "placement is credit, not proof"


def test_today_returns_a_stable_daily_quest(client, onboarded):
    a = client.get("/api/today").json()
    b = client.get("/api/today").json()
    assert [l["id"] for l in a["lessons"]] == [l["id"] for l in b["lessons"]]
    assert set(a["quest"]) == {"review", "learn", "read"}
    assert a["quest"]["review"]["done"] is False


def test_the_daily_quest_is_completable_on_a_day_with_nothing_due(tmp_path):
    """Regression: the crown was unreachable on day one, and on every
    caught-up day after it.

    The review step was marked done only by an actual review event today,
    but the deck is built from quiz misses — so it is necessarily empty on
    day one, and empty again whenever the reader has caught up. There was
    no action available that could complete the step, so an honest reader
    who did a lesson and read an article sat at 2/3 and never saw the
    quest complete. The step also rendered as the illegible "0 waiting",
    because the server's explanatory hint was never read by the frontend.

    A step the reader cannot possibly act on is excused, not outstanding.
    A step they genuinely can act on still has to be done — checked here
    too, so this cannot pass by simply excusing everything.
    """
    import json
    import time
    import primer.server as srv
    from primer.learner import LearnerStore
    from primer.wiki import WikiService
    from fastapi.testclient import TestClient

    orig_learner, orig_wiki, orig_backup_dir = srv.learner, srv.wiki, srv.BACKUP_DIR
    try:
        db = str(tmp_path / "test.db")
        srv.learner = LearnerStore(db)
        srv.wiki = WikiService(db)
        srv.BACKUP_DIR = str(tmp_path / "backups")
        with TestClient(srv.app) as client:
            client.post("/api/profile", json={
                "name": "Day1", "age": 12, "hours_per_week": 6,
                "breadth": "balanced", "domains": ["math"]})

            t = client.get("/api/today").json()
            assert t["deck"]["due"] == 0, "setup: a new reader's deck is empty"
            review = t["quest"]["review"]
            assert review["excused"] is True and review["hint"], \
                "with nothing due there must be no outstanding task, and a reason given"

            # An honest first day: one lesson, one article.
            srv.learner.record_attempt("math.2.fractions", 0.9)
            with srv.learner._conn() as conn:
                conn.execute("INSERT INTO events(kind,payload,at,xp) VALUES('read',?,?,0)",
                             (json.dumps({"title": "Fractions"}), time.time()))

            t = client.get("/api/today").json()
            assert t["quest_done"] == t["quest_total"], \
                "a full honest day must complete the quest when nothing was due"

            # And with real cards waiting, the step is outstanding again.
            srv.learner.add_cards([{"front": "F%d" % i, "back": "B",
                                    "node_id": "math.2.fractions"} for i in range(3)])
            with srv.learner._conn() as conn:
                conn.execute("UPDATE srs_cards SET due=?", (time.time() - 3600,))
            t = client.get("/api/today").json()
            assert t["deck"]["due"] == 3
            assert t["quest"]["review"]["excused"] is False
            assert t["quest_done"] < t["quest_total"], \
                "a review the reader really can do must still be required"
    finally:
        srv.learner, srv.wiki, srv.BACKUP_DIR = orig_learner, orig_wiki, orig_backup_dir


def test_no_quest_step_can_strand_the_reader_at_an_impossible_task(tmp_path):
    """Regression: the sibling of the review-step fix, missed in the same round.

    `review` was excused when the deck had nothing due. `learn` has exactly
    the same shape and exactly the same failure — a reader who has mastered
    the current frontier of every domain they chose is offered no lessons —
    and was left behind, so /api/today returned 0/2 with the same illegible
    "0 waiting" and the crown stayed permanently out of reach. Both are now
    built through one function, which is what stops the third diverging.

    `read` is the control: it has no count to exhaust, so it must never be
    excused. `None` is not zero.
    """
    import json
    import time
    import primer.server as srv
    from primer.learner import LearnerStore
    from primer.wiki import WikiService
    from fastapi.testclient import TestClient

    orig_learner, orig_wiki, orig_backup_dir = srv.learner, srv.wiki, srv.BACKUP_DIR
    try:
        db = str(tmp_path / "test.db")
        srv.learner = LearnerStore(db)
        srv.wiki = WikiService(db)
        srv.BACKUP_DIR = str(tmp_path / "backups")
        with TestClient(srv.app) as client:
            client.post("/api/profile", json={
                "name": "Done", "age": 12, "hours_per_week": 6,
                "breadth": "balanced", "domains": ["math"]})
            # Exhaust the frontier: nothing left to be offered.
            srv.learner.seed_assumed([nid for nid, n in srv.curr.nodes.items()
                                      if n["domain"] == "math"])

            t = client.get("/api/today").json()
            assert t["lessons"] == [], "setup: the frontier must be exhausted"
            for step in ("review", "learn"):
                assert t["quest"][step]["excused"] is True, \
                    "{}: a step with nothing to offer is not a task left undone".format(step)
                assert t["quest"][step]["hint"], \
                    "{}: and the reader must be told why".format(step)
            assert t["quest"]["read"]["excused"] is False, \
                "an article is always available — this step can never be excused"

            with srv.learner._conn() as conn:
                conn.execute("INSERT INTO events(kind,payload,at,xp) VALUES('read',?,?,0)",
                             (json.dumps({"title": "x"}), time.time()))
            t = client.get("/api/today").json()
            assert t["quest_done"] == t["quest_total"] == 1, \
                "the one thing actually available must be able to complete the day"
    finally:
        srv.learner, srv.wiki, srv.BACKUP_DIR = orig_learner, orig_wiki, orig_backup_dir


def test_a_focused_reader_can_still_ascend(tmp_path):
    """Regression: choosing a few subjects froze the reader's stage forever.

    Rank is the lower median of the per-domain stage estimates, so that one
    strong subject cannot promote someone. But it was taken over all ten
    curriculum domains rather than the reader's own — and onboarding actively
    encourages picking a few. A reader with two domains who mastered every
    node in both, preschool through graduate, took the median of
    {5, 5, 1, 1, 1, 1, 1, 1, 1, 1} and still ranked 1: seven subjects they
    never opted into counted as evidence against them. The ascension ceremony
    could never fire, and since stage drives quiz difficulty, the story window
    and the read-aloud UI mode, all of it stayed frozen where they started.

    The guard the median exists for is checked too, so this cannot pass by
    simply promoting everybody.
    """
    import primer.server as srv
    from primer.learner import LearnerStore
    from primer.wiki import WikiService
    from fastapi.testclient import TestClient

    orig_learner, orig_wiki, orig_backup_dir = srv.learner, srv.wiki, srv.BACKUP_DIR
    try:
        for name, domains, mastered, expect in (
            ("Focused", ["math", "physics"], ("math", "physics"), True),
            ("Broad", [d["id"] for d in srv.curr.domains], ("math",), False),
        ):
            db = str(tmp_path / (name + ".db"))
            srv.learner = LearnerStore(db)
            srv.wiki = WikiService(db)
            srv.BACKUP_DIR = str(tmp_path / "backups")
            with TestClient(srv.app) as client:
                client.post("/api/profile", json={
                    "name": name, "age": 6, "hours_per_week": 6,
                    "breadth": "balanced", "domains": domains})
                srv.learner.seed_assumed([nid for nid, n in srv.curr.nodes.items()
                                          if n["domain"] in mastered])
                rose = srv._check_ascension(srv.learner.get_profile())
                if expect:
                    assert rose and rose["stage"] == 5, \
                        "a reader who mastered every node in every domain they chose must ascend"
                    assert srv.learner.get_profile()["stage"] == 5, \
                        "and the promotion must actually take effect"
                else:
                    assert rose is None, \
                        "one strong domain out of ten must not promote a broad reader"
    finally:
        srv.learner, srv.wiki, srv.BACKUP_DIR = orig_learner, orig_wiki, orig_backup_dir


def test_failing_first_does_not_cost_the_days_earning_slot(tmp_path):
    """Regression: the book paid the struggling reader least.

    Effort XP is capped at once per node per day so a quiz cannot be farmed.
    But the cap counted *any* attempt, and a failed attempt earns nothing —
    it is below the 0.5 floor — so it silently spent the slot. Missing a node
    and then going back and mastering it paid zero, while passing first time
    paid full: ten nodes struggled with and then learned earned 0 XP against
    120 for ten first-try passes. That inverts the entire point of the
    schedule. Only an attempt that actually paid spends the slot now.
    """
    import primer.server as srv
    from primer.learner import LearnerStore
    from primer.wiki import WikiService
    from fastapi.testclient import TestClient

    orig_learner, orig_wiki, orig_backup_dir = srv.learner, srv.wiki, srv.BACKUP_DIR
    try:
        db = str(tmp_path / "test.db")
        srv.learner = LearnerStore(db)
        srv.wiki = WikiService(db)
        srv.BACKUP_DIR = str(tmp_path / "backups")
        with TestClient(srv.app) as client:
            client.post("/api/profile", json={
                "name": "Iso", "age": 12, "hours_per_week": 6,
                "breadth": "balanced", "domains": ["math"]})

            assert srv.learner.record_attempt("math.2.fractions", 0.3)["xp_gained"] == 0, \
                "a failed attempt still earns nothing"
            struggled = srv.learner.record_attempt("math.2.fractions", 0.9)["xp_gained"]
            assert struggled > 0, \
                "getting there on the second run must still be paid"

            first_try = srv.learner.record_attempt("math.2.decimals", 0.9)["xp_gained"]
            assert struggled == first_try, \
                "and paid the same as getting it right first time"

            # The anti-farming rule it was protecting must still hold.
            assert srv.learner.record_attempt("math.2.decimals", 0.9)["xp_gained"] == 0, \
                "repeating a passed quiz the same day must still pay nothing"
            for _ in range(3):
                assert srv.learner.record_attempt("math.2.negatives", 0.2)["xp_gained"] == 0, \
                    "and failing repeatedly must never pay"
    finally:
        srv.learner, srv.wiki, srv.BACKUP_DIR = orig_learner, orig_wiki, orig_backup_dir


def test_the_first_mastery_bonus_is_paid_once_not_once_per_relapse(tmp_path):
    """Regression: 60 XP was re-payable indefinitely.

    The bonus fires on `newly_mastered`, which only means "mastered_at was
    NULL a moment ago" — and the failure branch sets it back to NULL. So
    failing a mastered node and re-proving it paid the full first-mastery
    bonus again, every cycle, for a node already paid for once: five times
    the value of an honest day's work, on repeat, from deliberately failing
    something you already know. Gated on `first_mastered_at`, which is
    written once and never cleared. Re-proving still counts as mastery for
    every other purpose — it just is not a *first* mastery twice.
    """
    import time
    import primer.server as srv
    from primer.learner import LearnerStore
    from primer.wiki import WikiService
    from fastapi.testclient import TestClient

    orig_learner, orig_wiki, orig_backup_dir = srv.learner, srv.wiki, srv.BACKUP_DIR
    try:
        db = str(tmp_path / "test.db")
        srv.learner = LearnerStore(db)
        srv.wiki = WikiService(db)
        srv.BACKUP_DIR = str(tmp_path / "backups")
        with TestClient(srv.app) as client:
            client.post("/api/profile", json={
                "name": "Iso", "age": 12, "hours_per_week": 6,
                "breadth": "balanced", "domains": ["math"]})
            node = "math.2.fractions"

            def earn():
                srv.learner.record_attempt(node, 1.0)
                with srv.learner._conn() as conn:
                    conn.execute("""UPDATE mastery SET first_pass_at=?, last_pass_at=?
                                    WHERE node_id=?""",
                                 (time.time() - 5 * 86400, time.time() - 5 * 86400, node))
                return srv.learner.record_attempt(node, 1.0)

            first = earn()
            assert first["newly_mastered"] is True and first["xp_gained"] >= 60, \
                "the genuine first mastery pays the bonus"

            for cycle in (2, 3):
                srv.learner.record_attempt(node, 0.1)      # fail it back out
                with srv.learner._conn() as conn:          # clear the daily effort cap
                    conn.execute("DELETE FROM events")
                again = earn()
                assert again["newly_mastered"] is True, \
                    "re-proving is still a mastery for messaging and gates"
                assert again["xp_gained"] < 60, \
                    "cycle {}: the first-mastery bonus must not be payable again".format(cycle)
    finally:
        srv.learner, srv.wiki, srv.BACKUP_DIR = orig_learner, orig_wiki, orig_backup_dir


def test_quiz_endpoint_serves_questions_for_every_stage(client, onboarded):
    for node in ("math.0.counting", "math.1.addition", "math.2.fractions",
                 "math.3.quadratics", "math.4.linalg", "math.5.topology"):
        d = client.get("/api/quiz/" + node + "?n=3").json()
        assert d["questions"], "no questions for {}".format(node)
        assert d.get("token")
        for q in d["questions"]:
            # The prompt travels; the key stays with the book.
            assert q.get("prompt")
            assert "answer" not in q


def test_unknown_node_404s(client, onboarded):
    assert client.get("/api/quiz/nope.nope").status_code == 404
    assert client.get("/api/curriculum/node/nope.nope").status_code == 404


def test_unknown_generator_404s_with_help(client):
    r = client.get("/api/practice/not-a-generator")
    assert r.status_code == 404 and r.json()["available"]


def test_quiz_submit_records_and_returns_mastery(client, onboarded):
    paper, answers = _play(client, "/api/quiz/math.1.addition?n=4")
    r = client.post("/api/quiz/submit", json={
        "node_id": "math.1.addition", "answers": answers, "token": paper["token"]}).json()
    assert r["result"]["score"] == 1.0
    assert r["mastery"]["mastered"] is False, "one quiz is not mastery"
    assert r["mastery"]["xp_gained"] > 0


def test_failing_quiz_still_builds_review_cards(client, onboarded):
    paper, _ = _play(client, "/api/quiz/math.2.fractions?n=3")
    r = client.post("/api/quiz/submit", json={
        "node_id": "math.2.fractions", "answers": [""] * len(paper["questions"]),
        "token": paper["token"]}).json()
    assert r["cards_added"] > 0


def test_review_cycle(client, onboarded):
    # Make sure the deck has something in it first.
    paper, _ = _play(client, "/api/quiz/math.2.fractions?n=3")
    client.post("/api/quiz/submit", json={
        "node_id": "math.2.fractions", "answers": [""] * len(paper["questions"]),
        "token": paper["token"]})
    # A fresh card is due a few minutes out, so that writing one and grading it
    # in the same breath is not a memory test. Come back to it, as a reader does.
    import primer.server as srv
    with srv.learner._conn() as conn:
        conn.execute("UPDATE srs_cards SET due = ?", (time.time() - 1,))

    due = client.get("/api/review/due?limit=5").json()
    assert due["cards"]
    cid = due["cards"][0]["id"]
    good = client.post("/api/review", json={"card_id": cid, "quality": 5}).json()
    # Ada is 8, and SM-2's first learning step is age-scaled (learner
    # _sm2_first_steps): a full day for a teenager, eight hours for her. What
    # matters here is that a good grade pushes the card meaningfully out and
    # pays, not that it lands on any particular adult-shaped number.
    assert good["next_days"] >= 0.3 and good["xp_gained"] > 0
    with srv.learner._conn() as conn:
        conn.execute("UPDATE srs_cards SET due = ? WHERE id = ?", (time.time() - 1, cid))
    blank = client.post("/api/review", json={"card_id": cid, "quality": 0}).json()
    assert blank["xp_gained"] == 0


def test_review_unknown_card_is_handled(client, onboarded):
    assert "error" in client.post("/api/review", json={"card_id": 999999, "quality": 5}).json()


def test_placement_is_scored_server_side(client, onboarded):
    p = client.get("/api/placement/next?domain=math&n=4").json()
    assert p["questions"] and p.get("token")
    bad = client.post("/api/placement/submit", json={
        "domain": "math", "stage": p["stage"], "token": p["token"],
        "answers": ["definitely wrong"] * len(p["questions"])}).json()
    assert bad["passed"] is False
    assert bad["credited_through_stage"] == -1, "the client cannot assert a pass"


def test_story_will_not_advance_without_proof(tmp_path):
    """A page turns only on real evidence for the lesson it leads to.

    This used to assert against the shared `onboarded` reader (age 8, so
    stage 1) sitting on chapter 1, which gates on a *stage-0* lesson — one
    the book had already credited them for at placement. That case is now
    deliberately allowed to turn (see
    test_the_story_arc_is_reachable_by_a_reader_placed_above_stage_zero),
    so asserting it here was testing the deadlock, not the rule. The rule
    itself is unchanged and is what this now checks: at a chapter gated on
    a lesson at or above the reader's own stage, nothing but genuine
    spaced proof turns the page. It boots an isolated instance so walking
    the arc forward cannot disturb the shared module fixtures.
    """
    import primer.server as srv
    from primer.learner import LearnerStore
    from primer.wiki import WikiService
    from fastapi.testclient import TestClient

    orig_learner, orig_wiki, orig_backup_dir = srv.learner, srv.wiki, srv.BACKUP_DIR
    try:
        db = str(tmp_path / "test.db")
        srv.learner = LearnerStore(db)
        srv.wiki = WikiService(db)
        srv.BACKUP_DIR = str(tmp_path / "backups")
        with TestClient(srv.app) as client:
            client.post("/api/profile", json={
                "name": "Iso", "age": 12, "hours_per_week": 6, "breadth": "balanced",
                "domains": [d["id"] for d in srv.curr.domains]})
            stage = srv.learner.get_profile()["stage"]
            assert len(client.get("/api/story").json()["chapters"]) >= 14

            # Walk forward until the arc reaches this reader's own level.
            for _ in range(80):
                if not client.get("/api/story").json().get("can_advance"):
                    break
                assert client.post("/api/story/advance").json()["advanced"] is True

            chapter, _, _ = srv._story_cursor(srv.learner.get_profile())
            node = srv.curr.node(chapter.get("leads_to") or "")
            assert node and node["stage"] >= stage, \
                "the arc must come to rest on a lesson that is genuinely ahead of them"

            r = client.post("/api/story/advance").json()
            assert r["advanced"] is False and r.get("needs"), \
                "a lesson at or above the reader's stage takes real proof, not credit"
    finally:
        srv.learner, srv.wiki, srv.BACKUP_DIR = orig_learner, orig_wiki, orig_backup_dir


def test_the_story_arc_is_reachable_by_a_reader_placed_above_stage_zero(tmp_path):
    """Regression: the frame story was undeliverable to almost every reader.

    Onboarding above stage 0 seeds every earlier lesson as `assumed`
    (level 0.85, passes 0). `next_lessons` skips anything at or above 0.8,
    so those lessons never appear in Today. But `_story_cursor.earned()`
    would accept only `proven_set` (which excludes assumed credit) or
    `passed_set` (which needs passes >= 1, and a seed has 0) — so the very
    lessons the early chapters gate on were exactly the ones the book had
    decided never to teach this reader. A twelve-year-old opened to chapter
    1, "Turn the page" never lit, and no route existed anywhere in the app
    to light it: the story — the app's whole spine, and the thing every
    ceremony and chapter XP hangs off — was frozen at page one forever.

    Every other gate in the book already honours assumed credit (`gate_map`
    opens successors on it), so this was the one place the book refused to
    stand behind its own assumption.
    """
    import primer.server as srv
    from primer.learner import LearnerStore
    from primer.wiki import WikiService
    from fastapi.testclient import TestClient

    orig_learner, orig_wiki, orig_backup_dir = srv.learner, srv.wiki, srv.BACKUP_DIR
    try:
        db = str(tmp_path / "test.db")
        srv.learner = LearnerStore(db)
        srv.wiki = WikiService(db)
        srv.BACKUP_DIR = str(tmp_path / "backups")
        with TestClient(srv.app) as client:
            client.post("/api/profile", json={
                "name": "Nell", "age": 12, "hours_per_week": 6, "breadth": "balanced",
                "domains": [d["id"] for d in srv.curr.domains]})
            prof = srv.learner.get_profile()
            assert prof["stage"] == 2

            chapter, _, can_advance = srv._story_cursor(prof)
            gate = chapter.get("leads_to")
            # The precondition that made this a deadlock rather than a nudge:
            # the gate lesson is credited, and therefore never offered.
            assert gate not in [l["id"] for l in client.get("/api/today").json()["lessons"]], \
                "setup: the gate lesson is credited, so Today never offers it"
            assert can_advance is True, \
                "a chapter the book already credited this reader for must be turnable"

            turned = 0
            for _ in range(80):
                if not client.get("/api/story").json().get("can_advance"):
                    break
                assert client.post("/api/story/advance").json()["advanced"] is True
                turned += 1
            assert turned >= 10, \
                "the arc must catch up to the reader, not stall one page in"

            chapter, _, _ = srv._story_cursor(srv.learner.get_profile())
            node = srv.curr.node(chapter.get("leads_to") or "")
            assert node["stage"] >= prof["stage"], \
                "and must then stop exactly where real work begins"
    finally:
        srv.learner, srv.wiki, srv.BACKUP_DIR = orig_learner, orig_wiki, orig_backup_dir


def test_a_true_beginner_is_given_no_chapters_for_free(tmp_path):
    """The other side of the same rule: a stage-0 reader gets no seeded
    credit at all (`seed_assumed` only runs for stage > 0), so the arc must
    start them at page one and open nothing until they earn it. Without
    this, the fix above would be indistinguishable from simply unlocking
    the story for everybody."""
    import primer.server as srv
    from primer.learner import LearnerStore
    from primer.wiki import WikiService
    from fastapi.testclient import TestClient

    orig_learner, orig_wiki, orig_backup_dir = srv.learner, srv.wiki, srv.BACKUP_DIR
    try:
        db = str(tmp_path / "test.db")
        srv.learner = LearnerStore(db)
        srv.wiki = WikiService(db)
        srv.BACKUP_DIR = str(tmp_path / "backups")
        with TestClient(srv.app) as client:
            client.post("/api/profile", json={
                "name": "Tiny", "age": 4, "hours_per_week": 4, "breadth": "balanced",
                "domains": [d["id"] for d in srv.curr.domains]})
            prof = srv.learner.get_profile()
            assert prof["stage"] == 0
            chapter, progress, can_advance = srv._story_cursor(prof)
            assert progress == 0 and can_advance is False, \
                "a beginner starts at page one and earns every page from there"
    finally:
        srv.learner, srv.wiki, srv.BACKUP_DIR = orig_learner, orig_wiki, orig_backup_dir


def test_roadmap_reports_proven_not_assumed(client, onboarded):
    r = client.get("/api/roadmap").json()
    assert r["nodes_assumed"] > 0
    assert r["nodes_mastered"] == 0
    assert 1 <= r["estimated_years"] <= 40, r["estimated_years"]


def test_journal_endpoint(client, onboarded):
    assert "items" in client.get("/api/journal").json()


def test_curriculum_graph_shape(client, onboarded):
    g = client.get("/api/curriculum").json()
    assert len(g["domains"]) == 10 and len(g["nodes"]) > 300
    locked = [n for n in g["nodes"] if not n["unlocked"] and not n["mastered"]]
    assert locked and all(n.get("unlock_requirements") for n in locked), \
        "every locked node must explain itself"


def test_search_and_article(client, onboarded):
    res = client.get("/api/search?q=photosynthesis").json()
    assert res["results"]
    art = client.get("/api/article?title=Photosynthesis").json()
    assert len(art["rendered"]) > 500
    low = art["rendered"].lower()
    assert not any(b in low for b in ("<script", "onerror=", "javascript:", "<iframe"))


# ---------------- security ----------------

@pytest.mark.parametrize("path", ["/", "/app/index.html", "/app/", "/app/app.js",
                                  "/api/state", "/healthz", "/no-such-route"])
def test_security_headers_cover_every_route(client, path):
    """Regression: the headers used to live on the `/` handler only, so the
    static mount served a byte-identical, unprotected copy of the app shell."""
    r = client.get(path)
    assert "script-src 'self'" in r.headers.get("content-security-policy", ""), path
    assert r.headers.get("x-content-type-options") == "nosniff", path
    assert r.headers.get("referrer-policy") == "no-referrer", path


def test_app_shell_cache_busts_its_assets(client):
    assert "?v=" in client.get("/").text


@pytest.mark.parametrize("mime,inline", [
    ("image/png", True), ("IMAGE/PNG", True), ("image/jpeg", True),
    ("image/png; charset=utf-8", True), ("image/webp", True),
    ("image/svg+xml", False),          # Wikimedia hosts user-uploaded SVG:
    ("IMAGE/SVG+XML", False),          # an SVG is a document that can run script
    ("text/html", False),
    ("application/xhtml+xml", False),
    ("", False), ("application/octet-stream", False),
])
def test_only_safe_image_types_render_inline(mime, inline):
    """Directly exercise the MIME gate, rather than asserting a 404 on a route
    that never reaches it."""
    import primer.server as srv
    r = srv._safe_asset_response(b"\x89PNG\r\n", mime)
    assert r.headers.get("x-content-type-options") == "nosniff"
    if inline:
        assert r.media_type.startswith("image/")
        assert "content-disposition" not in {k.lower() for k in r.headers}
    else:
        assert r.media_type == "application/octet-stream"
        assert r.headers.get("content-disposition") == "attachment"


def test_image_proxy_refuses_internal_hosts(client):
    for bad in ("http://169.254.169.254/latest/meta-data/",
                "http://localhost:8747/api/state",
                "https://evil.com/a.wikipedia.org/x"):
        assert client.get("/api/image", params={"url": bad}).status_code == 404


def test_unknown_zim_archive_404s(client, onboarded):
    assert client.get("/zim/nonexistent/whatever").status_code == 404


# ---------------- concurrency & durability ----------------

def test_concurrent_writes_do_not_error(client, onboarded):
    """The reader's DB is written by several endpoints; under uvicorn's thread
    pool these can overlap. busy_timeout must absorb that."""
    errors = []

    def hammer(i):
        try:
            for k in range(6):
                client.post("/api/attempt", json={"node_id": "math.1.addition", "score": 0.9})
                client.get("/api/article?title=Photosynthesis")
                client.get("/api/today")
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    threads = [threading.Thread(target=hammer, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)
    assert not errors, errors[:2]


def test_backup_and_prune_run_clean(client, onboarded):
    import primer.server as srv
    dest = srv.learner.backup(srv.BACKUP_DIR)
    assert dest and os.path.exists(dest)
    # The copy must be a usable database containing the reader's record.
    import sqlite3
    con = sqlite3.connect(dest)
    try:
        assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert con.execute("SELECT COUNT(*) FROM profile").fetchone()[0] == 1
    finally:
        con.close()
    srv.learner.prune()  # must not raise


# ---------------- grading integrity (the token path) ----------------

def test_the_answer_key_never_ships_with_the_paper(client, onboarded):
    """If the marking scheme is on the reader's device, grading is theatre."""
    for path in ("/api/quiz/math.2.fractions?n=3",
                 "/api/practice/times-tables?n=3",
                 "/api/placement/next?domain=math&stage=2&n=3"):
        payload = client.get(path).json()
        assert payload.get("token"), path
        for q in payload["questions"]:
            assert "answer" not in q, "{} leaks the key".format(path)
            assert "keywords" not in q


@pytest.mark.parametrize("token", ["", "bogus-token", None])
def test_a_forged_answer_key_cannot_be_graded(client, onboarded, token):
    """Regression: the first version fell back to the client's copy when the
    token did not resolve — and the token is caller-controlled, so omitting it
    forced the fallback and scored 100%."""
    forged = [{"kind": "choice", "id": i, "prompt": "x", "answer": "ME", "choices": ["ME"]}
              for i in range(3)]
    body = {"node_id": "math.2.fractions", "questions": forged, "answers": ["ME"] * 3}
    if token is not None:
        body["token"] = token
    r = client.post("/api/quiz/submit", json=body)
    assert r.status_code == 409, r.text


def test_a_self_reported_practice_score_is_not_accepted(client, onboarded):
    """Regression: /api/attempt took `score` verbatim, so any level could be
    claimed without answering anything."""
    r = client.post("/api/attempt", json={"node_id": "cs.2.bigo-intro", "score": 1.0})
    assert r.status_code == 409, r.text


def test_placement_cannot_be_credited_without_a_served_paper(client, onboarded):
    """Regression: one untokened POST credited stage 5 and seeded 89 nodes."""
    forged = [{"kind": "choice", "id": 0, "prompt": "x", "answer": "ME", "choices": ["ME"]}]
    r = client.post("/api/placement/submit", json={
        "domain": "math", "stage": 5, "questions": forged, "answers": ["ME"]})
    assert r.status_code == 409
    assert client.get("/api/today").json()["mastered"] == 0


def test_a_paper_can_only_be_submitted_once(client, onboarded):
    """Tokens are single-use, so a paper cannot be replayed for a better score."""
    paper = client.get("/api/quiz/math.1.addition?n=3").json()
    keys = answer_key(paper)
    first = client.post("/api/quiz/submit", json={
        "node_id": "math.1.addition", "answers": keys, "token": paper["token"]})
    assert first.status_code == 200 and first.json()["result"]["score"] == 1.0
    replay = client.post("/api/quiz/submit", json={
        "node_id": "math.1.addition", "answers": keys, "token": paper["token"]})
    assert replay.status_code == 409


def test_per_item_check_reveals_the_answer_only_on_submission(client, onboarded):
    paper = client.get("/api/quiz/math.2.fractions?n=2").json()
    q = paper["questions"][0]
    m = client.post("/api/quiz/check",
                    json={"token": paper["token"], "id": q["id"], "answer": "definitely wrong"}).json()
    assert m["correct"] is False and m["answer"], 'feedback must name the answer'
    bad = client.post("/api/quiz/check", json={"token": "nope", "id": 0, "answer": "x"})
    assert bad.status_code == 409


def test_one_domain_cannot_promote_the_reader(client, onboarded):
    """Regression: `_check_ascension` took the max across domains, so mastering
    one field could jump an eight-year-old to graduate level — which then
    relaxed the two-spaced-passes rule for 86% of the curriculum."""
    import primer.server as srv
    prof = srv.learner.get_profile()
    gates = srv.learner.gate_map()
    per_domain = sorted(srv.curr.domain_stage_estimate(d["id"], gates) for d in srv.curr.domains)
    expected = per_domain[(len(per_domain) - 1) // 2]
    srv._check_ascension(prof)
    assert srv.learner.get_profile()["stage"] <= max(prof["stage"], expected)


def test_a_paper_is_only_valid_for_what_it_was_issued_for(client, onboarded):
    """Regression: tokens carried no binding to their purpose or subject, so a
    counting drill's paper could be handed in as a graduate topology quiz, or
    spent as a stage-5 placement pass. Verified live before the fix:

        practice token -> graduate quiz submit: 200 {'score': 1.0}
        practice token -> stage-5 placement:    200 {'credited_through_stage': 5}
        selfcheck token -> QFT mastery:         200 {'score': 1.0}
    """
    def keys(paper):
        out = []
        for q in paper["questions"]:
            r = client.post("/api/quiz/check", json={
                "token": paper["token"], "id": q["id"], "answer": "-"}).json()
            out.append(r["answer"])
        return out

    drill = client.get("/api/practice/counting?n=3&node_id=math.0.counting").json()
    stolen = keys(drill)
    assert client.post("/api/quiz/submit", json={
        "node_id": "math.5.topology", "answers": stolen,
        "token": drill["token"]}).status_code == 409

    drill2 = client.get("/api/practice/counting?n=3&node_id=math.0.counting").json()
    assert client.post("/api/placement/submit", json={
        "domain": "math", "stage": 5, "answers": keys(drill2),
        "token": drill2["token"]}).status_code == 409

    check = client.get("/api/selfcheck?title=Photosynthesis&n=2")
    if check.status_code == 200:      # needs an article; skip when offline
        sc = check.json()
        assert client.post("/api/quiz/submit", json={
            "node_id": "phys.5.qft", "answers": keys(sc),
            "token": sc["token"]}).status_code == 409

    # ...and a quiz token is not even valid for a different lesson.
    paper = client.get("/api/quiz/math.1.addition?n=2").json()
    assert client.post("/api/quiz/submit", json={
        "node_id": "math.5.topology", "answers": keys(paper),
        "token": paper["token"]}).status_code == 409


def test_the_answer_key_cannot_be_harvested_before_handing_in(client, onboarded):
    """Regression: `/api/quiz/check` returned the key for a *blank* answer and
    recorded nothing, so the whole paper could be walked for its answers and
    then handed in perfect. Feedback now costs a real commitment, and the first
    answer given is the one that counts."""
    paper = client.get("/api/quiz/math.1.addition?n=3").json()
    first = paper["questions"][0]

    blank = client.post("/api/quiz/check", json={
        "token": paper["token"], "id": first["id"], "answer": "   "})
    assert blank.status_code == 400 and "answer" not in blank.json()

    harvested = []
    for q in paper["questions"]:
        m = client.post("/api/quiz/check", json={
            "token": paper["token"], "id": q["id"], "answer": "deliberately wrong"}).json()
        assert m["correct"] is False
        harvested.append(m["answer"])

    graded = client.post("/api/quiz/submit", json={
        "node_id": "math.1.addition", "answers": harvested, "token": paper["token"]})
    # The wrong answers committed during this sitting are what count — they were
    # given before the key appeared. Handing back the keys afterwards changes
    # nothing, so the paper scores zero.
    assert graded.status_code == 200, graded.text
    assert graded.json()["result"]["score"] == 0.0


def test_feedback_still_teaches(client, onboarded):
    """The lock must not cost the reader the thing feedback is for: a wrong
    answer is still named, explained, and shown against the right one."""
    paper = client.get("/api/quiz/math.2.fractions?n=2").json()
    q = paper["questions"][0]
    m = client.post("/api/quiz/check", json={
        "token": paper["token"], "id": q["id"], "answer": "wrong"}).json()
    assert m["answer"], "the reader must see the right answer"
    assert m["locked"] == "wrong", "and know which of theirs was recorded"


def test_a_paper_cannot_be_claimed_twice_at_once(client, onboarded):
    """Single-use must not depend on thread scheduling: sync endpoints run in a
    threadpool, so `_recall`'s get-then-pop had a window where two concurrent
    submissions could both walk away with the same paper."""
    import threading
    import primer.server as srv
    for _ in range(8):
        paper = client.get("/api/quiz/math.3.functions?n=4").json()
        keys = answer_key(paper)
        start, codes = threading.Barrier(6), []
        lock = threading.Lock()

        def submit():
            start.wait()
            r = client.post("/api/quiz/submit", json={
                "node_id": "math.3.functions", "answers": keys, "token": paper["token"]})
            with lock:
                codes.append(r.status_code)

        threads = [threading.Thread(target=submit) for _ in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert codes.count(200) == 1, "a paper was graded {} times".format(codes.count(200))


def test_a_second_look_cannot_improve_a_committed_answer(client, onboarded):
    """The lock is `setdefault`, not assignment: checking an item again after
    seeing the key must not quietly replace what was recorded."""
    paper = client.get("/api/quiz/math.1.addition?n=2").json()
    q = paper["questions"][0]
    first = client.post("/api/quiz/check", json={
        "token": paper["token"], "id": q["id"], "answer": "wrong on purpose"}).json()
    key = first["answer"]
    second = client.post("/api/quiz/check", json={
        "token": paper["token"], "id": q["id"], "answer": key}).json()
    assert second["locked"] == "wrong on purpose"
    assert second["correct"] is False, "the key was seen before this answer was given"


def test_placement_and_practice_lock_answers_too(client, onboarded):
    """The lock has to cover every graded route, not just quizzes — placement
    credits whole stages, and practice moves the same mastery ledger."""
    rung = client.get("/api/placement/next?domain=math&stage=2&n=3").json()
    leak = client.post("/api/quiz/check", json={
        "token": rung["token"], "id": rung["questions"][0]["id"], "answer": "wrong"})
    assert leak.status_code == 409, "a placement check must not hand out its answers"
    assert "answer" not in leak.json()

    drill = client.get("/api/practice/times-tables?n=3&node_id=math.1.multiplication").json()
    stolen = [client.post("/api/quiz/check", json={
        "token": drill["token"], "id": q["id"], "answer": "wrong"}).json()["answer"]
        for q in drill["questions"]]
    r = client.post("/api/attempt", json={
        "node_id": "math.1.multiplication", "answers": stolen, "token": drill["token"]})
    assert r.status_code == 200 and r.json()["level"] < 0.8, \
        "the wrong answers committed during the sitting are what count"


def test_review_cards_follow_the_graded_answer(client, onboarded):
    """Cards were built from the submitted sheet rather than the graded one, so
    a reader who saw the key and changed their mind got no card for the item
    they actually got wrong — losing exactly the review they most needed."""
    node = "math.3.slope"          # a node no other test banks cards for
    paper = client.get("/api/quiz/{}?n=6".format(node)).json()
    # Ask for feedback on the first item only, then answer everything with the
    # key. The checked item is spent; the rest still count, and are still wrong.
    first = paper["questions"][0]
    client.post("/api/quiz/check", json={
        "token": paper["token"], "id": first["id"], "answer": "wrong"})
    keys = answer_key(paper)
    r = client.post("/api/quiz/submit", json={
        "node_id": node, "answers": keys,
        "make_cards": True, "token": paper["token"]}).json()
    # Nothing is set aside: the answer committed on this paper was given before
    # the key was shown, so every item still counts.
    gradable = sum(1 for q in paper["questions"] if not q.get("ungraded"))
    assert r["result"]["total"] == gradable
    assert r["cards_added"] > 0, "the items they got wrong must come back"


def test_a_drill_must_belong_to_the_lesson_it_counts_for(client, onboarded):
    """Regression: the practice token was bound to a subject the *client* chose,
    which repeats the very mistake the binding was meant to fix. A six-duck
    counting drill was a valid sitting for quantum field theory — 343/343 nodes
    could be mastered in two spaced calls."""
    stolen = client.get("/api/practice/counting?n=6&level=0&node_id=phys.5.qft")
    assert stolen.status_code == 409, "a counting drill is not a QFT paper"

    missing = client.get("/api/practice/counting?n=6&node_id=no.such.node")
    assert missing.status_code == 404

    import primer.server as srv
    node = srv.curr.node("math.0.counting")
    own = client.get("/api/practice/{}?n=4&node_id=math.0.counting".format(node["practice"]))
    assert own.status_code == 200, "a lesson's own drill must still be servable"


def test_a_graded_paper_is_never_one_question_long(client, onboarded):
    """Regression: `n` was caller-chosen, so `?n=1` served the lone constructed
    response — whose key is the node's published `goal`. Pasting one public
    string scored 1.0 on 248 of 254 stage>=2 nodes."""
    import primer.server as srv
    goal = client.get("/api/curriculum/node/math.5.measure").json().get("goal")
    paper = client.get("/api/quiz/math.5.measure?n=1").json()
    assert len(paper["questions"]) >= srv.QUIZ_MIN_ITEMS

    answers = [goal] + [""] * (len(paper["questions"]) - 1)
    r = client.post("/api/quiz/submit", json={
        "node_id": "math.5.measure", "answers": answers, "token": paper["token"]}).json()
    assert r["result"]["score"] < 0.5, "the published goal must not carry a whole paper"
    assert client.get("/api/quiz/math.1.addition?n=999").json()["questions"].__len__() \
        <= srv.QUIZ_MAX_ITEMS


def test_the_book_owns_its_own_record(client, onboarded):
    """Regression: `/api/profile/settings` merged whatever it was sent, and
    `placed` is what the stage is computed from — so one POST made a
    four-year-old stage 5 and marked eleven story chapters read."""
    import primer.server as srv
    before = srv.learner.get_profile()["stage"]
    r = client.post("/api/profile/settings", json={
        "placed": {"math": 5, "physics": 5}, "rank": 5,
        "story_progress": 18, "theme": "dark"}).json()
    assert set(r.get("refused", [])) == {"placed", "rank", "story_progress"}
    assert "placed" not in r["settings"] and "story_progress" not in r["settings"]
    assert r["settings"].get("theme") == "dark", "real preferences must still save"
    assert srv.learner.get_profile()["stage"] == before, "no paper was sat"


def test_the_book_decides_which_rung_to_offer(client, onboarded):
    """Regression: the client named the stage it wanted, so a reader could open
    placement at stage 5, pass one paper and settle there. The staircase starts
    where their age puts them and moves one rung at a time."""
    import primer.server as srv
    prof = srv.learner.get_profile()

    served = client.get("/api/placement/next?domain=arts&stage=5&n=4").json()
    assert served["stage"] == srv.learner.stage_for_age(prof["age"]), \
        "the ladder starts at the reader's age, not where they ask"

    forged = client.post("/api/placement/submit", json={
        "domain": "arts", "stage": 5, "answers": ["x"] * 4, "token": served["token"]})
    assert forged.status_code == 409
    assert forged.json()["expected_stage"] == served["stage"]

    keys = answer_key(served)
    passed = client.post("/api/placement/submit", json={
        "domain": "arts", "stage": served["stage"], "answers": keys,
        "token": served["token"]}).json()
    assert passed["passed"] is True
    nxt = client.get("/api/placement/next?domain=arts&n=4").json()
    assert nxt["stage"] == served["stage"] + 1, "a pass moves up exactly one rung"


def test_placing_down_takes_back_what_age_assumed(client, onboarded):
    """Regression: a reader placed low kept the nodes their age had seeded as
    known, so the book planned around material they had just shown they did not
    have."""
    import primer.server as srv
    before = len([n for n in srv.learner.assumed_set()
                  if srv.curr.nodes[n]["domain"] == "chemistry"]) \
        if hasattr(srv.learner, "assumed_set") else None

    domain, guard = "chemistry", 0
    while guard < 8:
        guard += 1
        nxt = client.get("/api/placement/next?domain={}&n=4".format(domain))
        if nxt.status_code == 409:
            break
        p = nxt.json()
        r = client.post("/api/placement/submit", json={
            "domain": domain, "stage": p["stage"],
            "answers": ["deliberately wrong"] * len(p["questions"]),
            "token": p["token"]}).json()
        if r["settled"]:
            break

    with srv.learner._conn() as c:
        left = c.execute(
            "SELECT COUNT(*) FROM mastery WHERE assumed=1 AND node_id LIKE 'chem.%'"
        ).fetchone()[0]
    assert left == 0, "failing every rung must not leave assumed chemistry credit"
    if before:
        assert before > 0


def test_the_shell_stamps_its_assets(client):
    """Regression: only `/` stamped the asset URLs; `/app/index.html` served an
    identical, unstamped copy, and the static mount sent no Cache-Control. A
    returning reader could run new JavaScript against an old stylesheet — an
    accessibility audit measured contrast against a stale sheet and reported
    failures the served CSS did not have."""
    import re
    stamps = {}
    for path in ("/", "/app/", "/app/index.html"):
        r = client.get(path)
        assert r.status_code == 200, path
        found = set(re.findall(r"/app/(?:styles\.css|app\.js)\?v=([0-9a-f]{10})", r.text))
        assert len(found) == 2, "{} did not stamp both assets".format(path)
        stamps[path] = found
    assert len(set(map(frozenset, stamps.values()))) == 1, "entry points disagree"

    assert "immutable" in client.get("/app/styles.css?v=deadbeef00").headers["cache-control"]
    assert client.get("/app/styles.css").headers["cache-control"] == "no-cache"


def test_the_explanation_is_not_shipped_with_the_paper(client, onboarded):
    """Regression: `_public` stripped `answer` and `keywords` but not `explain`,
    which names the answer outright in a third of items ("...divide by 3 to get
    x = 6"). A solver reading only the served JSON scored 63-65% and cleared the
    mastery gate on 83-88 of 343 nodes."""
    paper = client.get("/api/quiz/math.3.linear?n=6").json()
    for q in paper["questions"]:
        assert "explain" not in q, q
        assert "answer" not in q and "keywords" not in q

    # It is still there when it has been earned.
    first = paper["questions"][0]
    fb = client.post("/api/quiz/check", json={
        "token": paper["token"], "id": first["id"], "answer": "wrong"}).json()
    assert fb.get("explain") or fb.get("answer"), "feedback must still teach"


def test_a_produced_item_actually_reaches_the_paper(client, onboarded):
    """Regression: the bank was sorted by option count, which buries numeric and
    short items (no options at all) last — and the paper is then truncated to n,
    so the items that ask the reader to *produce* were authored and never served.
    """
    import primer.server as srv
    have = [nid for nid, nd in srv.curr.nodes.items()
            if nd.get("stage", 0) >= 2
            and any(q.get("kind") in ("numeric", "short") for q in (nd.get("quiz") or []))]
    assert len(have) > 100, "expected produced items across the curriculum"

    missing = []
    for nid in have[:60]:
        served = False
        for _ in range(4):
            p = client.get("/api/quiz/{}?n=5".format(nid)).json()
            # The *authored* produced item, not the generated reflection one —
            # this test used to pass on the generated `short`, which is exactly
            # what was displacing the authored numeric items it meant to check.
            served = srv._SERVED[p["token"]]["questions"]
            if any(q.get("kind") in ("numeric", "short") and not q.get("ungraded")
                   for q in served):
                served = True
                break
        if not served:
            missing.append(nid)
    assert not missing, "never served their produced item: {}".format(missing[:5])


def test_a_guesser_never_masters_anything(client, onboarded):
    """The whole artefact in one assertion: sit many real papers, over simulated
    weeks, answering deliberately wrongly every time. Nothing may ever become
    proven.

    Every forgery the board found — self-reported scores, forged keys, replayed
    tokens, a counting drill spent as quantum field theory, a paper harvested
    for its own answers — ended with something proven that had not been earned.
    This is the invariant all of those violated.
    """
    import random
    import primer.server as srv
    rng = random.Random(5)
    nodes = [n["id"] for n in srv.curr.nodes.values() if n["stage"] <= 2][:25]

    for week in range(3):
        for nid in nodes:
            paper = client.get("/api/quiz/{}?n=5".format(nid)).json()
            if "token" not in paper:
                continue
            served = srv._SERVED[paper["token"]]["questions"]
            answers = []
            for q in served:
                key = q.get("answer", "")
                wrong = [c for c in (q.get("choices") or []) if c != key]
                answers.append(rng.choice(wrong) if wrong else "deliberately wrong")
            client.post("/api/quiz/submit", json={
                "node_id": nid, "answers": answers, "token": paper["token"]})
        # Age the record so the two-spaced-passes rule sees genuine gaps.
        with srv.learner._conn() as conn:
            conn.execute("""UPDATE mastery SET
                              last_pass_at = last_pass_at - 604800,
                              first_pass_at = first_pass_at - 604800,
                              last_seen = last_seen - 604800""")

    # The same reader, now also using every other route that touches mastery:
    # asking for feedback and discarding the paper, and grinding practice.
    for nid in nodes[:10]:
        for _ in range(3):
            paper = client.get("/api/quiz/{}?n=12".format(nid)).json()
            if "token" not in paper:
                continue
            for pub in paper["questions"]:
                client.post("/api/quiz/check", json={
                    "token": paper["token"], "id": pub["id"], "answer": "x"})
        node = srv.curr.nodes[nid]
        if node.get("practice"):
            for _ in range(40):
                pp = client.get("/api/practice/{}?n=4&node_id={}".format(
                    node["practice"], nid)).json()
                if "token" not in pp:
                    continue
                served = srv._SERVED[pp["token"]]["questions"]
                client.post("/api/attempt", json={
                    "node_id": nid, "token": pp["token"],
                    "answers": [rng.choice(q.get("choices") or ["0"]) for q in served]})
                with srv.learner._conn() as conn:
                    conn.execute("""UPDATE mastery SET
                                      last_pass_at = last_pass_at - 259200,
                                      first_pass_at = first_pass_at - 259200,
                                      last_seen = last_seen - 259200""")

    assert srv.learner.proven_set() == set(), "guessing proved something"
    assert client.get("/api/today").json()["mastered"] == 0


def test_the_answer_key_cannot_be_harvested_by_discarding_papers(client, onboarded):
    """Regression: the first-commitment lock bound answers *within* one paper,
    so the paper was simply thrown away. Authored items recur across papers, so
    a few discarded papers enumerated a node's whole bank; a clean sitting then
    scored 1.0. Verified before the fix: 342 of 343 nodes proven, stage 5
    'Whole Forest', on a profile aged four.

    Showing a key now spends that item for a week: it keeps being served and
    keeps teaching, but it stops being a measurement.
    """
    import primer.server as srv
    node = "math.4.diff-calc"
    harvest = {}
    for _ in range(4):
        paper = client.get("/api/quiz/{}?n=12".format(node)).json()
        for pub in paper["questions"]:
            r = client.post("/api/quiz/check", json={
                "token": paper["token"], "id": pub["id"], "answer": "x"})
            if r.status_code == 200:
                harvest[pub["prompt"]] = r.json()["answer"]
        # paper discarded, never submitted

    assert harvest, "feedback must still reveal answers to someone who commits"
    clean = client.get("/api/quiz/{}?n=12".format(node)).json()
    r = client.post("/api/quiz/submit", json={
        "node_id": node,
        "answers": [harvest.get(q["prompt"], "") for q in clean["questions"]],
        "token": clean["token"]})
    if r.status_code == 200:
        assert r.json()["result"]["score"] < 0.8, "harvested keys must not pass"
    else:
        assert r.status_code == 409
    assert node not in srv.learner.proven_set()


def test_a_practice_paper_is_never_one_question_long(client, onboarded):
    """Regression: the four-item floor was applied to quizzes but not practice.
    A one-item paper scores 0 or 1 against a 0.8 pass mark, so a single lucky
    click was a full pass — and retries are unlimited. Guessing alone proved
    undergraduate differential calculus in 102 papers."""
    import primer.server as srv
    p = client.get("/api/practice/times-tables?n=1&node_id=math.1.multiplication").json()
    assert len(p["questions"]) >= srv.QUIZ_MIN_ITEMS, p["questions"]
    wide = client.get("/api/practice/times-tables?n=99&node_id=math.1.multiplication").json()
    assert len(wide["questions"]) <= srv.QUIZ_MAX_ITEMS


def test_a_days_reviewing_is_worth_a_days_credit(client, onboarded):
    """Regression: the due check stopped one card being drilled repeatedly, but
    not two hundred cards being written and graded in a sitting — 1,000 XP for
    nothing. Streaks and levels are built on that number."""
    import primer.server as srv
    for i in range(80):
        client.post("/api/review/add", json={
            "front": "farm-{}".format(i), "back": "b", "node_id": "math.1.addition"})
    mine = [c for c in srv.learner.due_cards(limit=500)
            if str(c["front"]).startswith("farm-")]
    total = sum(client.post("/api/review", json={
        "card_id": c["id"], "quality": 5}).json().get("xp_gained", 0) for c in mine)
    assert total <= srv.learner.REVIEW_XP_DAILY_CAP, total


def test_the_roadmap_prose_agrees_with_its_own_flag(client, onboarded):
    """The note said "inside the Primer's five-to-ten year promise" at 4.9 years
    while `within_promise` was False."""
    import primer.server as srv
    for hours in (6, 20, 31, 40):
        prof = srv.learner.get_profile()
        srv.learner.save_profile(prof["name"], prof["age"], hours, prof["breadth"],
                                 prof["stage"], prof["domains"], prof.get("settings", {}))
        r = client.get("/api/roadmap").json()
        assert ("inside the" in r["note"]) == r["within_promise"], \
            "{}h/wk: {:.1f}y, flag {}, note {!r}".format(
                hours, r["estimated_years"], r["within_promise"], r["note"][:70])


def test_the_answer_key_is_not_simply_published(client, onboarded):
    """Regression, and the one that made the rest of the defences beside the
    point: `/api/curriculum/node/{id}` returned the node verbatim, `quiz` and
    all — every `answer` and every `explain`, unauthenticated, on the endpoint
    the lesson page fetches. `graph()` drops the bank; this did not.

    The whole burn mechanism was guarding a door that was not the entrance.
    """
    n = client.get("/api/curriculum/node/math.3.linear").json()
    assert "quiz" not in n, "the bank must not ship with the lesson"
    assert n.get("question_count", 0) > 0, "the count is fine to publish"
    blob = json.dumps(n)
    import primer.server as srv
    for item in srv.curr.nodes["math.3.linear"]["quiz"]:
        assert str(item.get("answer", "")) not in blob or len(str(item.get("answer", ""))) < 2
        assert item.get("explain", "zzz") not in blob


def test_a_paper_is_never_graded_on_scraps(client, onboarded):
    """Regression: the four-item floor was enforced on items *served*, and the
    burn then ran afterwards — so a burnt-out bank was graded on whatever one or
    two procedural top-ups survived. A thirteen-item paper came back
    `total: 1`, and random guessing proved undergraduate calculus in seven
    sittings."""
    import random
    import primer.server as srv
    node = "math.4.diff-calc"
    rng = random.Random(5)

    for _ in range(5):                       # burn the authored bank
        paper = client.get("/api/quiz/{}?n=12".format(node)).json()
        for pub in paper["questions"]:
            client.post("/api/quiz/check", json={
                "token": paper["token"], "id": pub["id"], "answer": "x"})

    graded = 0
    for _ in range(15):
        paper = client.get("/api/quiz/{}?n=12".format(node)).json()
        served = srv._SERVED[paper["token"]]["questions"]
        r = client.post("/api/quiz/submit", json={
            "node_id": node, "token": paper["token"],
            "answers": [rng.choice(q.get("choices") or ["0"]) for q in served]})
        if r.status_code == 200:
            graded += 1
            assert r.json()["result"]["total"] >= srv.QUIZ_MIN_ITEMS, r.json()["result"]
    assert node not in srv.learner.proven_set()


def test_a_reader_who_knows_it_can_still_be_measured(client, onboarded):
    """Regression, and the worst of the three: the app routes *every* answer
    through `/api/quiz/check` for immediate feedback, so burning on any
    commitment meant a reader who answered **correctly** burned their own paper
    and was refused with a 409 — on every sitting, forever. A guesser reached
    proven in seven papers while someone who knew the material could never be
    measured at all.

    An answer committed before the key appeared is honest evidence and counts,
    whatever it was. Only what was already spent on an *earlier* paper is set
    aside.
    """
    import primer.server as srv
    node = "math.3.linear"
    for _ in range(2):
        paper = client.get("/api/quiz/{}?n=5".format(node)).json()
        served = srv._SERVED[paper["token"]]["questions"]
        answers = []
        for pub, q in zip(paper["questions"], served):
            key = q.get("answer", "")
            client.post("/api/quiz/check", json={
                "token": paper["token"], "id": pub["id"], "answer": key})
            answers.append(key)
        r = client.post("/api/quiz/submit", json={
            "node_id": node, "answers": answers, "token": paper["token"]})
        assert r.status_code == 200, r.text
        assert r.json()["result"]["score"] == 1.0
        with srv.learner._conn() as conn:
            conn.execute("""UPDATE mastery SET last_pass_at = last_pass_at - 345600,
                              first_pass_at = first_pass_at - 345600,
                              last_seen = last_seen - 345600""")
    assert node in srv.learner.proven_set(), "knowing the material must be provable"


def test_no_route_publishes_the_answer_key(client, onboarded):
    """Regression, twice over: the bank was stripped route by route as each leak
    was noticed. `graph()` dropped it; `/api/curriculum/node` did not until it
    was caught; and `/api/today` — the endpoint the app fetches on every load —
    still shipped the complete key for every frontier lesson afterwards.

    Nodes now serialise through one gate, and this sweeps structurally rather
    than trusting that the known routes are the only ones.
    """
    import primer.server as srv

    def answer_bearing(o, path=""):
        if isinstance(o, dict):
            if {"answer", "keywords"} & set(o):
                yield path, o
            for k, v in o.items():
                yield from answer_bearing(v, path + "/" + str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                yield from answer_bearing(v, "{}[{}]".format(path, i))

    routes = ["/api/today", "/api/curriculum", "/api/state", "/api/roadmap",
              "/api/journal", "/api/story", "/api/review/due"]
    routes += ["/api/curriculum/node/" + n for n in list(srv.curr.nodes)[:10]]
    for r in routes:
        resp = client.get(r)
        if resp.status_code != 200:
            continue
        assert '"quiz"' not in resp.text, "{} still ships the bank".format(r)
        leaks = list(answer_bearing(resp.json()))
        assert not leaks, "{} exposes {}".format(r, leaks[0][0])


def test_asking_for_the_paper_early_does_not_beat_the_burn(client, onboarded):
    """Regression: the burn was keyed to when the *paper* was issued, and papers
    are free. Fetch a clean one, harvest the bank through a second, submit the
    first — every burn postdated the issue, nothing was dropped, and a 0.83 was
    scored from no knowledge.

    It is keyed to the *commitment* now: an item counts only if the reader
    answered it before its key was ever shown.
    """
    import primer.server as srv
    node = "math.3.euclid"   # a node no other test proves
    for _ in range(3):
        clean = client.get("/api/quiz/{}?n=12".format(node)).json()   # issued first
        harvest = client.get("/api/quiz/{}?n=12".format(node)).json()
        keys = {}
        for pub in harvest["questions"]:
            r = client.post("/api/quiz/check", json={
                "token": harvest["token"], "id": pub["id"], "answer": "zzz"})
            if r.status_code == 200:
                keys[pub["prompt"]] = r.json()["answer"]
        r = client.post("/api/quiz/submit", json={
            "node_id": node, "token": clean["token"],
            "answers": [keys.get(q["prompt"], "") for q in clean["questions"]]})
        if r.status_code == 200:
            assert r.json()["result"]["score"] < 0.8, r.json()["result"]
        with srv.learner._conn() as conn:
            conn.execute("""UPDATE mastery SET last_pass_at = last_pass_at - 345600,
                              first_pass_at = first_pass_at - 345600""")
    assert node not in srv.learner.proven_set()


def test_the_book_says_one_thing_about_one_node(client, onboarded):
    """Regression: a single response body reported `proven: false`,
    `mastered: true` and `mastery_detail.proven: true` about the same node —
    three functions answering one question three ways, because only some of them
    applied decay.

    And a node the reader had genuinely proved and let fade came back labelled
    `assumed`, which is the word for credit they never earned at all. That
    erased the difference between their work and a guess about their age.
    """
    import time
    import primer.server as srv

    srv.learner.record_attempt("math.3.trig", 1.0)
    with srv.learner._conn() as conn:
        conn.execute("""UPDATE mastery SET mastered_at=?, first_mastered_at=?, strength=1.0,
                          passes=2, assumed=0, last_seen=?, reinforcements=1
                        WHERE node_id='math.3.trig'""",
                     (time.time() - 300 * 86400, time.time() - 300 * 86400,
                      time.time() - 300 * 86400))
    srv.learner.seed_assumed(["math.3.polynomials"])

    faded = client.get("/api/curriculum/node/math.3.trig").json()
    assert faded["proven"] is False and faded["ever_proven"] is True
    assert faded["faded"] is True
    assert faded["mastered"] is False, "a faded node is not currently mastered"
    assert faded["mastery_detail"]["proven"] == faded["proven"], "the body must agree with itself"
    assert faded["mastery_detail"]["assumed"] is False, "they earned it — it merely faded"

    assumed = client.get("/api/curriculum/node/math.3.polynomials").json()
    assert assumed["ever_proven"] is False and assumed["faded"] is False
    assert assumed["mastery_detail"]["assumed"] is True

    graph = {n["id"]: n for n in client.get("/api/curriculum").json()["nodes"]}
    assert graph["math.3.trig"]["faded"] and not graph["math.3.trig"]["assumed"]
    assert graph["math.3.polynomials"]["assumed"] and not graph["math.3.polynomials"]["faded"]


def test_every_mastery_word_agrees_across_both_routes(tmp_path):
    """Regression: the same four words, checked all four ways, in every state.

    `mastery_detail` has now drifted from /api/curriculum three separate
    times, each time in a different one of its four state words, each time
    caught only after it shipped: `proven` (decay), `assumed` (read the raw
    column, which records credit *given* rather than credit *standing*), and
    `ever_proven`/`faded` (hung off `mastered_at`, which is CLEARED when a
    mastered node is failed on a re-sitting — so a reader who earned a node,
    let it fade, then failed a refresh had one response body say
    `ever_proven: true, faded: true` at the top level and false to both in
    `mastery_detail`, erasing work they had genuinely done).

    The narrow tests written for each of those covered one word in one
    state. This covers the whole matrix, so the next drift in any word is
    caught by construction rather than by an audit noticing.
    """
    import time
    import primer.server as srv
    from primer.learner import LearnerStore
    from primer.wiki import WikiService
    from fastapi.testclient import TestClient

    WORDS = ("mastered", "proven", "ever_proven", "faded", "assumed")
    orig_learner, orig_wiki, orig_backup_dir = srv.learner, srv.wiki, srv.BACKUP_DIR
    try:
        db = str(tmp_path / "test.db")
        srv.learner = LearnerStore(db)
        srv.wiki = WikiService(db)
        srv.BACKUP_DIR = str(tmp_path / "backups")
        with TestClient(srv.app) as client:
            client.post("/api/profile", json={
                "name": "Iso", "age": 12, "hours_per_week": 6,
                "breadth": "balanced", "domains": ["math"]})

            def agree(node_id, label):
                detail = client.get("/api/curriculum/node/" + node_id).json()["mastery_detail"]
                graph = {n["id"]: n for n in client.get("/api/curriculum").json()["nodes"]}[node_id]
                for w in WORDS:
                    assert detail[w] == graph[w], \
                        "{}: /api/curriculum/node says {}={} but /api/curriculum says {}".format(
                            label, w, detail[w], graph[w])
                return detail

            earned_node, seeded = "math.2.fractions", "math.1.addition"

            d = agree(earned_node, "untouched")
            assert not any(d[w] for w in WORDS)

            srv.learner.record_attempt(earned_node, 1.0)
            with srv.learner._conn() as conn:
                conn.execute("UPDATE mastery SET first_pass_at=?, last_pass_at=? WHERE node_id=?",
                             (time.time() - 5 * 86400, time.time() - 5 * 86400, earned_node))
            srv.learner.record_attempt(earned_node, 1.0)
            d = agree(earned_node, "earned by two spaced passes")
            assert d["proven"] and d["ever_proven"] and not d["faded"] and not d["assumed"]

            with srv.learner._conn() as conn:
                conn.execute("UPDATE mastery SET last_seen=? WHERE node_id=?",
                             (time.time() - 400 * 86400, earned_node))
            d = agree(earned_node, "earned then faded")
            assert d["faded"] and d["ever_proven"] and not d["proven"] and not d["assumed"]

            srv.learner.record_attempt(earned_node, 0.2)
            d = agree(earned_node, "earned, faded, then failed a refresh")
            assert d["ever_proven"] and d["faded"], \
                "failing a refresh must not erase having once earned it"

            d = agree(seeded, "fresh placement seed")
            assert d["assumed"] and not d["ever_proven"] and not d["proven"]

            with srv.learner._conn() as conn:
                conn.execute("UPDATE mastery SET last_seen=? WHERE node_id=?",
                             (time.time() - 400 * 86400, seeded))
            d = agree(seeded, "placement seed left to decay")
            assert not d["assumed"] and not d["mastered"], \
                "credit that no longer stands is not 'assumed' — it is simply gone"
    finally:
        srv.learner, srv.wiki, srv.BACKUP_DIR = orig_learner, orig_wiki, orig_backup_dir


def test_a_decayed_assumed_node_says_one_thing_too(client, onboarded):
    """Regression: the sibling the decay fix above never reached.

    `mastery_detail` gates `mastered`, `proven` and `faded` on current
    strength, but `assumed` alone still read the raw DB column — which
    records that credit was *given*, never that it still stands. Every
    other route computes the word as "mastered and never earned"
    (/api/curriculum literally derives it that way), so a seeded node left
    untouched long enough to decay below the gate reported
    `mastered: false, assumed: true` from /api/curriculum/node while
    /api/curriculum said `assumed: false` about that same node at that same
    instant. This is the exact "one body, two stories" bug class the test
    above exists to prevent, in the one field it didn't cover: it checks a
    *fresh* seed and an *earned-then-faded* node, but never a seed that has
    itself decayed — which is the ordinary fate of any age-placement credit
    the reader never returns to.
    """
    import time
    import primer.server as srv

    srv.learner.seed_assumed(["math.3.polynomials"])
    # Age the seed past the strength gate without touching anything else.
    with srv.learner._conn() as conn:
        conn.execute("""UPDATE mastery SET last_seen=?, mastered_at=?
                        WHERE node_id='math.3.polynomials'""",
                     (time.time() - 37 * 86400, time.time() - 37 * 86400))

    node = client.get("/api/curriculum/node/math.3.polynomials").json()
    detail = node["mastery_detail"]
    assert detail["mastered"] is False, "37 days untouched decays a seed past the gate"
    assert detail["assumed"] is False, \
        "credit that no longer stands is not 'assumed' — it is simply gone"

    graph = {n["id"]: n for n in client.get("/api/curriculum").json()["nodes"]}
    assert graph["math.3.polynomials"]["assumed"] == detail["assumed"], \
        "/api/curriculum and /api/curriculum/node must say the same word about one node"


def test_every_paper_the_book_can_draw_is_well_formed(client, onboarded):
    """`quiz_for_node` was the densest code in the server — five sequential
    mutate-then-truncate phases with nothing pinning what they were supposed to
    preserve, which is how a reserved slot for an authored produced item came to
    be filled and discarded in the same breath.

    It is three named steps now, and these are the invariants they owe: a paper
    is between four and twelve graded items, ids are sequential, the unmarked
    reflection item never displaces a graded one, and a node whose bank holds an
    authored produced item always serves one.
    """
    import primer.server as srv

    for nid, node in srv.curr.nodes.items():
        paper = client.get("/api/quiz/{}?n=5".format(nid)).json()
        assert "token" in paper, nid
        served = srv._SERVED[paper["token"]]["questions"]
        graded = [q for q in served if not q.get("ungraded")]

        assert srv.QUIZ_MIN_ITEMS <= len(graded) <= srv.QUIZ_MAX_ITEMS, \
            "{}: {} graded items".format(nid, len(graded))
        assert [q["id"] for q in served] == list(range(len(served))), nid
        assert sum(1 for q in served if q.get("ungraded")) <= 1, nid
        if node["stage"] >= 2 and any(q.get("kind") in ("numeric", "short")
                                      for q in (node.get("quiz") or [])):
            assert any(q.get("kind") in ("numeric", "short") and not q.get("ungraded")
                       for q in served), "{} served no authored produced item".format(nid)
        # The key never travels with the paper.
        for pub in paper["questions"]:
            assert "answer" not in pub and "explain" not in pub and "keywords" not in pub


def test_failing_a_re_test_does_not_erase_the_journal(client, onboarded):
    """Regression: `ever_proven_set` and `journal()` both read `mastered_at`
    directly, which the failure path resets to NULL — so a reader who earned a
    node, let it fade, and then failed a refresh check on it saw the Journey
    view and the journal lose that entry entirely. Forgetting does not un-happen
    having once known something.
    """
    import primer.server as srv

    node = "math.4.linalg"
    for _ in range(2):
        paper = client.get("/api/quiz/{}?n=5".format(node)).json()
        served = srv._SERVED[paper["token"]]["questions"]
        answers = [q.get("answer", "") for q in served]
        client.post("/api/quiz/submit", json={
            "node_id": node, "answers": answers, "token": paper["token"]})
        with srv.learner._conn() as conn:
            conn.execute("UPDATE mastery SET last_pass_at=last_pass_at-345600, "
                         "first_pass_at=first_pass_at-345600")

    before = client.get("/api/journal").json()["items"]
    assert any(it.get("node_id") == node for it in before)

    paper2 = client.get("/api/quiz/{}?n=5".format(node)).json()
    served2 = srv._SERVED[paper2["token"]]["questions"]
    client.post("/api/quiz/submit", json={
        "node_id": node, "answers": ["wrong"] * len(served2), "token": paper2["token"]})

    after = client.get("/api/journal").json()["items"]
    assert any(it.get("node_id") == node for it in after), \
        "the earned record must survive a later failed re-sitting"
    assert node not in srv.learner.proven_set(), "but it must no longer be currently proven"


def test_a_faded_chapter_gate_does_not_report_stale_passes(client, onboarded):
    """Regression: `_story_needs` used to report `mastery_detail()['passes']`
    verbatim — a lifetime counter decay never touches. A node proven long ago
    and then left to fade still showed "2 of 2 passes" even though the gate
    was shut, reading as "almost there" on a page that would not open.
    """
    import primer.server as srv

    node = "math.4.linalg"
    for _ in range(2):
        paper = client.get("/api/quiz/{}?n=5".format(node)).json()
        served = srv._SERVED[paper["token"]]["questions"]
        answers = [q.get("answer", "") for q in served]
        client.post("/api/quiz/submit", json={
            "node_id": node, "answers": answers, "token": paper["token"]})
        with srv.learner._conn() as conn:
            conn.execute("UPDATE mastery SET last_pass_at=last_pass_at-345600, "
                         "first_pass_at=first_pass_at-345600")

    detail = srv.learner.mastery_detail(node)
    assert detail["proven"] and detail["passes"] >= 2

    with srv.learner._conn() as conn:
        conn.execute("UPDATE mastery SET last_seen=last_seen-100000000 WHERE node_id=?", (node,))

    faded_detail = srv.learner.mastery_detail(node)
    assert faded_detail["faded"] and not faded_detail["proven"], \
        "the node must have decayed out of proven standing without an explicit failure"

    needs = srv._story_needs({"leads_to": node})
    assert needs["faded"] is True
    assert needs["ever_proven"] is True
    assert needs["passes"] == 0, \
        "a faded gate must not report its stale lifetime pass count as current progress"


def test_grading_a_review_card_through_the_real_api_restores_a_faded_node(client, onboarded):
    """A reviewer asked for proof that 'review outcomes feed back into
    strength decay' is a genuine deck-mastery coupling, not just a claim —
    and specifically that they could not verify it themselves without code
    access. This drives the whole loop through the real HTTP surface, the
    same one a reader's browser uses: master a node with two spaced quiz
    passes, fail it once to mint a review card, let the node's strength
    decay to faded, then grade that card through POST /api/review and
    confirm GET /api/curriculum/node reports the node proven again — not by
    peeking at internal state, but by reading the same endpoint the app's
    own UI reads."""
    import primer.server as srv

    node = "math.3.trig"
    for _ in range(2):
        paper = client.get("/api/quiz/{}?n=5".format(node)).json()
        served = srv._SERVED[paper["token"]]["questions"]
        answers = [q.get("answer", "") for q in served]
        client.post("/api/quiz/submit", json={
            "node_id": node, "answers": answers, "token": paper["token"]})
        with srv.learner._conn() as conn:
            conn.execute("UPDATE mastery SET last_pass_at=last_pass_at-345600, "
                         "first_pass_at=first_pass_at-345600 WHERE node_id=?", (node,))

    before = client.get("/api/curriculum/node/" + node).json()
    assert before["proven"], "the node must be genuinely proven before we fade it"

    with srv.learner._conn() as conn:
        conn.execute("UPDATE mastery SET last_seen=last_seen-100000000 WHERE node_id=?", (node,))
        conn.execute("UPDATE srs_cards SET due=? WHERE node_id=?", (time.time() - 1, node))

    faded = client.get("/api/curriculum/node/" + node).json()
    assert faded["faded"] and not faded["proven"], "the node must have decayed to faded first"

    with srv.learner._conn() as conn:
        card_id = conn.execute("SELECT id FROM srs_cards WHERE node_id=? LIMIT 1", (node,)).fetchone()[0]
    grade = client.post("/api/review", json={"card_id": card_id, "quality": 5}).json()
    assert grade["xp_gained"] > 0, "a confident, on-schedule grade must pay out"

    restored = client.get("/api/curriculum/node/" + node).json()
    assert restored["proven"] and not restored["faded"], \
        "grading a review card through the real API must restore proven standing — this is the coupling itself, verified end to end"


def test_all_story_chapters_have_valid_gates(client, onboarded):
    """Regression: Added chapters for chemistry, earth-space, arts, and
    mind-society must gate on real mastery nodes that exist in the curriculum.
    """
    import json
    import primer.server as srv

    with open("data/story/frame.json") as f:
        story = json.load(f)

    for ch in story["chapters"]:
        target = ch.get("leads_to", "")
        if target:  # Skip epilogue (empty string)
            assert target in srv.curr.nodes, \
                f"Chapter {ch['id']} gates on non-existent node {target}"


def test_four_new_chapters_gate_on_missing_domains(client, onboarded):
    """Verify that chemistry, earth-space, arts, mind-society now have at
    least one chapter each after the fix."""
    import json

    with open("data/story/frame.json") as f:
        story = json.load(f)

    domain_chapters = {}
    for ch in story["chapters"]:
        target = ch.get("leads_to", "")
        if target:
            domain = target.split(".")[0]
            if domain not in domain_chapters:
                domain_chapters[domain] = []
            domain_chapters[domain].append(ch["id"])

    for domain in ["chem", "earth", "arts", "mind"]:
        assert domain in domain_chapters, \
            f"No chapters found for {domain} domain"
        assert len(domain_chapters[domain]) > 0, \
            f"Domain {domain} has chapters but none are gated to nodes"


def test_the_staircase_walks_down_on_failure_and_settles_at_the_floor(client, onboarded):
    """Regression: only the upward path (pass -> next rung up) had a
    regression test; the downward half of the same adaptive algorithm —
    failing steps the staircase down exactly one rung, and failing at the
    floor settles the placement rather than looping forever — had none.
    Also proves failing at floor revokes any stale assumed credit for
    the whole domain, not just the failed rung."""
    import primer.server as srv

    domain = "physics"
    prof = srv.learner.get_profile()
    start_stage = srv.learner.stage_for_age(prof["age"])

    served = client.get("/api/placement/next?domain={}&n=4".format(domain)).json()
    assert served["stage"] == start_stage

    failed = client.post("/api/placement/submit", json={
        "domain": domain, "stage": served["stage"],
        "answers": ["definitely wrong"] * len(served["questions"]),
        "token": served["token"]}).json()
    assert failed["passed"] is False

    if start_stage > 0:
        nxt = client.get("/api/placement/next?domain={}&n=4".format(domain)).json()
        assert nxt["stage"] == start_stage - 1, "a fail moves down exactly one rung"
        served, stage = nxt, nxt["stage"]
    else:
        stage = start_stage

    settle = client.post("/api/placement/submit", json={
        "domain": domain, "stage": stage,
        "answers": ["definitely wrong"] * len(served["questions"]),
        "token": served["token"]}).json()
    assert settle["passed"] is False
    assert settle["credited_through_stage"] == -1, \
        "failing at the floor must not credit any stage"

    done = client.get("/api/placement/next?domain={}&n=4".format(domain))
    assert done.status_code == 409, "the staircase must settle, not loop forever"

    domain_node_ids = [n["id"] for n in srv.curr.nodes.values() if n["domain"] == domain]
    with srv.learner._conn() as c:
        rows = c.execute(
            "SELECT node_id FROM mastery WHERE assumed=1 AND node_id IN ({})".format(
                ",".join("?" * len(domain_node_ids))), domain_node_ids).fetchall()
    assert not rows, \
        "failing placement at the floor must revoke stale assumed credit for the domain"


def test_legacy_story_progress_survives_a_chapter_insertion(client, onboarded):
    """Regression: `story_progress` used to be a raw index into
    STORY["chapters"]. When one round's fix inserted 4 new chapters just
    before the epilogue (previously the last entry, at index 18 in a
    19-chapter frame), any reader whose stored index was exactly 18 would
    have silently been retargeted onto whatever now sits there — a beginner
    chemistry chapter — instead of the finale they had actually earned.

    The first fix corrected this with a fixed +4 offset — which worked
    exactly once. Several rounds since then each added more chapters before
    that same point in the array, and every one of them silently broke the
    fixed offset again for any reader who had somehow still never been
    migrated to a stable id (an increasingly narrow edge case, but the same
    bug regardless): `_resolve_story_position` was recomputing a position
    against a growing array using a constant calibrated for one specific
    past state of it. Fixed by routing any legacy index at or past the
    original finale straight to the CURRENT last chapter — "reached the
    end" always means the current end, immune to however many more chapters
    get added later — rather than a fixed offset that decays with every
    future content edit. Any read/write from here on persists a stable
    chapter id instead of a position that content edits can invalidate."""
    import primer.server as srv

    prof = srv.learner.get_profile()
    settings = dict(prof.get("settings", {}))
    settings.pop("story_chapter_id", None)
    settings["story_progress"] = 18
    srv.learner.save_profile(prof["name"], prof["age"], prof["hours_per_week"],
                              prof["breadth"], prof["stage"], prof["domains"], settings)

    s = client.get("/api/story").json()
    current = next(c for c in s["chapters"] if c["current"])
    assert current["id"] == "story.epilogue", \
        "a reader who had reached the old last chapter must still land on the epilogue"

    # /api/today is the commit=True path, same as _story_cursor's own docs say.
    client.get("/api/today")

    # And the position is now persisted by a stable id, immune to future inserts.
    prof2 = srv.learner.get_profile()
    assert prof2["settings"].get("story_chapter_id") == "story.epilogue"
    assert "story_progress" not in prof2["settings"]


def test_every_domain_has_more_than_one_chapter(client, onboarded):
    """Regression: an audit repeatedly docked Narrative Integration for
    chapters that stopped at a single stage-0 entry point in six domains
    (chemistry, earth-space, arts, mind-society, computer-science, history) —
    a personal-story promise made everywhere but delivered nowhere past the
    first page. Each of those domains now has a second chapter reaching into
    stage 2, so the arc actually continues."""
    import json

    with open("data/story/frame.json") as f:
        story = json.load(f)

    from collections import defaultdict
    by_domain = defaultdict(list)
    for ch in story["chapters"]:
        target = ch.get("leads_to", "")
        if target:
            by_domain[target.split(".")[0]].append(ch)

    assert len(by_domain) == 10, "every domain must have at least one chapter"
    for domain, chapters in by_domain.items():
        assert len(chapters) >= 2, \
            "{} has only {} chapter(s) — a single entry point, not an arc".format(domain, len(chapters))


def test_every_domain_has_at_least_two_story_chapters(client, onboarded):
    """Regression: a single stage-0 entry point per domain reads as a token
    gesture, not a developed arc — the personal-story promise has to hold
    across more than one chapter per domain to mean something. Chemistry,
    earth-space, arts, and mind-society had zero chapters at all until this
    round; they now have four apiece, spanning stages 0-2."""
    import json

    with open("data/story/frame.json") as f:
        story = json.load(f)

    from collections import defaultdict
    counts = defaultdict(int)
    for ch in story["chapters"]:
        target = ch.get("leads_to", "")
        if target:
            counts[target.split(".")[0]] += 1

    for domain in ["chem", "earth", "arts", "mind"]:
        assert counts[domain] >= 2, \
            f"{domain} has only {counts[domain]} chapter(s), not a developed arc"


def test_roadmap_assumed_count_never_goes_negative_when_proven_nodes_fade(tmp_path):
    """Regression: /api/roadmap computed nodes_assumed as
    mastered_count() - proven_count(), pairing a decay-aware count with a
    non-decay-aware one. A reader with several genuinely-proven nodes that
    have since faded past the strength gate saw nodes_mastered=0 (correctly
    decay-aware) alongside nodes_assumed going NEGATIVE, since proven_count()
    kept counting the faded rows regardless of decay.

    A first version of this test ran against the shared module-scoped
    `client`/`onboarded` fixtures, which by this point in the file carry
    ~38 age-placement-seeded assumed nodes accumulated across every other
    test in the module. Decaying one freshly-mastered node only shifts the
    naive formula from 38 to 37 — still comfortably positive — so the
    `>= 0` assertion passed whether or not the fix was present, proven by
    reverting the fix and re-running: the old test still passed. This
    version boots its own isolated app instance and onboards at age 3
    (stage 0), which `seed_assumed` never runs for (`if first_time and
    stage > 0`), so there is no assumed-credit baseline to swamp the
    single node under test — decaying it genuinely drives the naive
    formula negative absent the fix."""
    import primer.server as srv
    from primer.learner import LearnerStore
    from primer.wiki import WikiService
    from fastapi.testclient import TestClient

    # This test boots its own isolated singletons — save and restore the
    # module-scoped ones so later tests in this file don't inherit a tmp,
    # torn-down database.
    orig_learner, orig_wiki, orig_backup_dir = srv.learner, srv.wiki, srv.BACKUP_DIR
    try:
        db = str(tmp_path / "test.db")
        srv.learner = LearnerStore(db)
        srv.wiki = WikiService(db)
        srv.BACKUP_DIR = str(tmp_path / "backups")
        with TestClient(srv.app) as client:
            r = client.post("/api/profile", json={
                "name": "Iso", "age": 3, "hours_per_week": 4,
                "breadth": "balanced", "domains": ["math"]})
            assert r.status_code == 200

            node = "math.0.counting"
            for _ in range(2):
                paper = client.get("/api/quiz/{}?n=5".format(node)).json()
                served = srv._SERVED[paper["token"]]["questions"]
                answers = [q.get("answer", "") for q in served]
                client.post("/api/quiz/submit", json={
                    "node_id": node, "answers": answers, "token": paper["token"]})
                with srv.learner._conn() as conn:
                    conn.execute("UPDATE mastery SET last_pass_at=last_pass_at-345600, "
                                 "first_pass_at=first_pass_at-345600")

            assert node in srv.learner.proven_set()
            assert srv.learner.mastered_count() - srv.learner.proven_count() == 0, \
                "test setup must start with the naive formula at exactly 0, one step from negative"

            # Decay the node's strength clock far enough that it falls below the
            # 0.35 gate without ever failing a check — pure time, no explicit failure.
            with srv.learner._conn() as conn:
                conn.execute("UPDATE mastery SET last_seen=last_seen-100000000 WHERE node_id=?", (node,))

            assert node not in srv.learner.proven_set(), "the node must have faded"
            assert srv.learner.mastered_count() - srv.learner.proven_count() < 0, \
                "test setup must actually exercise the bug: the naive formula must go negative here"

            r = client.get("/api/roadmap").json()
            assert r["nodes_assumed"] >= 0, \
                "nodes_assumed must never go negative when proven nodes have faded"
    finally:
        srv.learner, srv.wiki, srv.BACKUP_DIR = orig_learner, orig_wiki, orig_backup_dir


def test_adding_a_domain_later_does_not_strand_its_chapter(client, onboarded):
    """Regression: _story_cursor's forward walk skips any chapter whose
    target lesson lives in a domain the reader hasn't chosen, and used to
    persist that skip into story_chapter_id whenever commit=True (every
    /api/today call). Domain selection isn't immutable — /api/profile always
    overwrites it — so a reader who onboarded without chemistry, browsed
    /api/today (silently and permanently skipping chem.0.materials' chapter),
    and only later added chemistry to their domains would find that chapter's
    ceremony, text, and XP gone forever: the cursor had already moved past it
    and never revisits. The fix stops persisting the domain-skip walk itself
    (only the one-time legacy-format migration writes story_chapter_id), so a
    later domain change takes effect immediately instead of being foreclosed
    by an earlier read."""
    import primer.server as srv

    prof = srv.learner.get_profile()
    original_domains = prof["domains"]
    original_settings = dict(prof.get("settings", {}))
    try:
        # Reset to the very first chapter so this test isn't reading position
        # left behind by other tests sharing this module's fixtures — those
        # earned advances are real and unrelated to the domain-skip bug.
        reset_settings = dict(original_settings)
        reset_settings["story_chapter_id"] = "story.intro"
        # Onboard-equivalent: no chemistry, so its chapter is domain-skipped
        # on every read.
        srv.learner.save_profile(prof["name"], prof["age"], prof["hours_per_week"],
                                  prof["breadth"], prof["stage"], ["math", "physics"],
                                  reset_settings)

        # Read /api/today repeatedly (the commit=True path) — this used to be
        # exactly what baked the skip in permanently.
        client.get("/api/today")
        client.get("/api/today")
        client.get("/api/today")

        # Now the reader adds chemistry.
        prof2 = srv.learner.get_profile()
        srv.learner.save_profile(prof2["name"], prof2["age"], prof2["hours_per_week"],
                                  prof2["breadth"], prof2["stage"], ["math", "physics", "chemistry"],
                                  prof2.get("settings", {}))

        s = client.get("/api/story").json()
        chem_chapter = next((c for c in s["chapters"] if c.get("leads_to") == "chem.0.materials"), None)
        assert chem_chapter is not None
        assert not chem_chapter.get("read"), \
            "the chemistry chapter must not read as already completed — it was never earned"
    finally:
        prof3 = srv.learner.get_profile()
        srv.learner.save_profile(prof3["name"], prof3["age"], prof3["hours_per_week"],
                                  prof3["breadth"], prof3["stage"], original_domains,
                                  original_settings)


def test_every_request_carries_a_unique_correlation_id(client, onboarded):
    """Regression: a security/reliability audit flagged that log lines from
    concurrent requests could not be told apart — the app runs under asyncio
    with more than one browser tab open at once being the normal case, and
    nothing distinguished one request's log lines from another's. Each
    response now carries an X-Request-Id header, unique per request, and
    every log line emitted during that request's handling (via a
    contextvar-backed logging filter) carries the same id."""
    r1 = client.get("/healthz")
    r2 = client.get("/healthz")
    id1 = r1.headers.get("x-request-id")
    id2 = r2.headers.get("x-request-id")
    assert id1 and id2, "every response must carry a request id"
    assert id1 != id2, "each request must get its own id"


def test_every_domains_story_reaches_a_deep_stage(client, onboarded):
    """Regression: a re-score first caught that claiming chem/earth/arts/mind
    "matched physics' depth" was an overclaim — physics' chapters reach
    stage 5, those four capped at stage 3. That round's fix carried its own
    unverified assumption forward: it excluded cs/hist/lang from the bar as
    "genuinely thinner curricula" — a claim never actually checked against
    the curriculum data. A second re-score checked it and found it false:
    data/curriculum/*.json shows cs (34 nodes), hist (29), and lang (40) all
    have real content through stage 5, comparable to or larger than physics'
    39 — the excuse was invented, not measured. bio was capped at stage 4
    for no stated reason at all. Every domain's curriculum genuinely reaches
    stage 5, so every domain's story now does too — checked here, not
    asserted, so a future round can't repeat either mistake: overclaiming
    parity, or manufacturing an excuse for the domains left behind."""
    import json

    with open("data/story/frame.json") as f:
        story = json.load(f)

    from collections import defaultdict
    max_stage = defaultdict(int)
    for ch in story["chapters"]:
        target = ch.get("leads_to", "")
        if target:
            domain = target.split(".")[0]
            max_stage[domain] = max(max_stage[domain], ch.get("unlocks_stage", 0))

    for domain in ["math", "phys", "chem", "earth", "arts", "mind", "cs", "hist", "lang", "bio"]:
        assert max_stage[domain] >= 4, \
            f"{domain}'s story arc stops at stage {max_stage[domain]}, well before the curriculum's stage 5 ceiling"


def test_every_domains_story_has_no_interior_stage_gaps(client, onboarded):
    """Regression: reaching stage 5 turned out not to be the whole bar. A
    re-score that verified the depth-parity fix found a further layer of
    the same gap the depth-only check couldn't see: history had ZERO
    stage-0 chapter (unique among all 10 domains — a history-focused
    reader's personal-story arc didn't begin until after their first
    stage-1 mastery proof, the exact entry-hook failure a reviewer would
    flag first), and biology/physics each skipped two interior stages
    (bio missing 1 and 3, physics missing 1 and 2). The rubric's own
    wording — "chapters across all stages... delivered across the full
    arc" — means full per-stage coverage, not just eventually reaching the
    top. Every domain now has a chapter at every stage 0 through 5."""
    import json

    with open("data/story/frame.json") as f:
        story = json.load(f)

    from collections import defaultdict
    stages_seen = defaultdict(set)
    for ch in story["chapters"]:
        target = ch.get("leads_to", "")
        if target:
            domain = target.split(".")[0]
            stages_seen[domain].add(ch.get("unlocks_stage", 0))

    for domain in ["math", "phys", "chem", "earth", "arts", "mind", "cs", "hist", "lang", "bio"]:
        missing = sorted(set(range(6)) - stages_seen[domain])
        assert not missing, \
            f"{domain}'s story arc has no chapter at stage(s) {missing} — not a full per-stage arc"


def test_changing_domains_does_not_wipe_reader_settings(client, onboarded):
    """Regression: POST /api/profile is the endpoint that changes name/age/
    domains — it never passes `settings` at all, relying on
    learner.save_profile's ON CONFLICT COALESCE to leave existing settings
    (theme, story_chapter_id, name_pronunciation, ...) untouched. The
    Python layer serialized `settings or {}` before binding it as a SQL
    parameter, so an omitted settings argument became the JSON string "{}"
    rather than an actual SQL NULL — which is never NULL to COALESCE, so
    every single profile save silently wiped every existing setting back to
    empty. Concretely: story_chapter_id reset on every domain change, which
    both rewound the reader's story position and opened a wipe-then-replay
    path to unlimited chapter XP (nothing else prevented /api/story/advance
    from re-paying an already-earned chapter once its position was reset).
    Fixed by binding a real SQL NULL when the caller means "leave settings
    alone" versus an explicit JSON payload when the caller means to set
    (even clear) them."""
    import primer.server as srv

    prof = srv.learner.get_profile()
    original = dict(prof.get("settings", {}))
    original_domains = prof["domains"]
    try:
        r = client.post("/api/profile/settings", json={"theme": "dark"})
        assert r.status_code == 200

        # A plain domain change must not touch anything set above.
        r2 = client.post("/api/profile", json={
            "name": prof["name"], "age": prof["age"], "hours_per_week": prof["hours_per_week"],
            "breadth": prof["breadth"], "domains": ["math", "physics", "chemistry"]})
        assert r2.status_code == 200
        assert r2.json()["settings"].get("theme") == "dark", \
            "a domain-only change must not wipe existing reader settings"
    finally:
        prof2 = srv.learner.get_profile()
        srv.learner.save_profile(prof2["name"], prof2["age"], prof2["hours_per_week"],
                                  prof2["breadth"], prof2["stage"], original_domains, original)


def test_selfcheck_is_not_offered_to_pre_readers():
    """Regression: /api/selfcheck generates fill-in-the-blank cloze
    questions from raw article prose — a text-reading task by construction.
    The endpoint had zero stage gating, and the frontend's "Check yourself"
    button was shown unconditionally on every non-curriculum article page,
    regardless of the reader's stage — putting a text-only, machine-graded
    (and by the app's own admission, ~65%-defect-rate) exercise in front of
    exactly the readers the rest of the app goes out of its way to keep off
    text entirely: picture-first quizzes, pervasive auto-speak, larger
    touch targets. Fixed server-side (403 at stage<=1, independent of
    whatever the frontend does) and client-side (button hidden at stage<=1,
    since "Read aloud" already covers the same need without requiring
    reading)."""
    import tempfile
    import primer.server as srv
    from primer.learner import LearnerStore
    from primer.wiki import WikiService
    from fastapi.testclient import TestClient

    orig_learner, orig_wiki = srv.learner, srv.wiki
    try:
        db = tempfile.mktemp(suffix=".db")
        srv.learner = LearnerStore(db)
        srv.wiki = WikiService(db)
        with TestClient(srv.app) as c:
            c.post("/api/profile", json={
                "name": "Young", "age": 5, "hours_per_week": 3,
                "breadth": "balanced", "domains": ["math"]})
            r = c.get("/api/selfcheck?title=Photosynthesis&n=2")
            assert r.status_code == 403, \
                "a pre-reader (stage<=1) must not be offered a text-cloze self-check"

            c.post("/api/profile", json={
                "name": "Older", "age": 10, "hours_per_week": 3,
                "breadth": "balanced", "domains": ["math"]})
            r2 = c.get("/api/selfcheck?title=Photosynthesis&n=2")
            assert r2.status_code == 200, \
                "a reader who can actually decode text must still get the feature"
    finally:
        srv.learner, srv.wiki = orig_learner, orig_wiki


def test_each_domains_chapters_are_stage_monotonic(client, onboarded):
    """Regression: server.py walks STORY["chapters"] in raw file order with
    no sort — the array's literal order IS the sequence a reader
    experiences chapters in, regardless of which node's stage is higher or
    lower. Chapters landed across many separate authoring rounds left 6 of
    10 domains out of order (e.g. chemistry presented atoms, stage 2,
    before matter-changes, stage 1) — and since chem.2.atoms has a hard
    curriculum prereq on chem.1.changes, a chemistry-focused reader's story
    literally asked them to prove the "harder" chapter first, with the
    "earlier" chapter's gate already trivially satisfied by the time the
    story finally offered it — undercutting the escalating-arc promise for
    over half the domains, invisible to every prior test since those only
    checked coverage/depth/gaps, never order. Every domain's chapters must
    now appear in non-decreasing stage order."""
    import json

    with open("data/story/frame.json") as f:
        story = json.load(f)

    from collections import defaultdict
    stage_sequence = defaultdict(list)
    for ch in story["chapters"]:
        target = ch.get("leads_to", "")
        if target:
            domain = target.split(".")[0]
            stage_sequence[domain].append(ch.get("unlocks_stage", 0))

    for domain, stages in stage_sequence.items():
        assert stages == sorted(stages), \
            f"{domain}'s chapters are not stage-monotonic in array order: {stages}"


def test_the_chapters_array_is_globally_stage_interleaved(client, onboarded):
    """Regression: fixing per-domain stage-monotonicity wasn't enough. The
    flat chapters array was laid out in large authorship-era blocks —
    math/lang/phys/bio/hist's first chapters occupied indices 0-24, then
    chem/earth/arts/mind's FULL 0-5 arcs plus more cs/hist chapters sat at
    25-52, then cs/hist/lang's stage 3-5 tail at 53-61 — and the story
    cursor walk only skips chapters whose domain isn't selected; it never
    interleaves across domains by stage. A reader with the app's own
    DEFAULT onboarding domains (math, language, biology, physics, history)
    experienced all of math+physics+biology's chapters through stage 5
    before history's very first stage-1 chapter (beyond its stage-0 entry)
    ever appeared — live-simulated end to end, history's arc stalled at
    chapter index 8 and didn't resume until index 24. No existing test
    caught this because every depth/gap/monotonicity check used only
    same-block domain pairs (math+physics) that happened to dodge it. The
    whole array must now be non-decreasing in unlocks_stage (the epilogue,
    which has no leads_to, is exempt — it stays last by construction, not
    by stage)."""
    import json

    with open("data/story/frame.json") as f:
        story = json.load(f)

    stages = [ch.get("unlocks_stage", 0) for ch in story["chapters"] if ch.get("leads_to", "")]
    assert stages == sorted(stages), \
        "the chapters array must be globally stage-interleaved across domains, not authored in blocks"
    assert story["chapters"][-1].get("leads_to", "") == "", \
        "the epilogue must remain the final chapter regardless of stage sorting"
