"""Learning sequences: the authored content, the marking, and the reader's record.

Every curriculum module carries at least one short interactive sequence
(introduce, demonstrate, predict, check, explain, transfer). These tests keep
that true as the curriculum grows, keep the answer keys on the server, and
play a sequence end to end through the HTTP API against a throwaway database.
"""
import json
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from primer.curriculum import Curriculum  # noqa: E402
from primer.learning_games import authoring, catalog, evaluators, exprs  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module")
def curr():
    return Curriculum()


@pytest.fixture(scope="module")
def cat(curr):
    return catalog.Catalog(curr.nodes)


def _steps(seq):
    return [beat for beat in seq["beats"] if beat["kind"] == "step"]


def _norm(text):
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


# ------------------------------------------------------------------ content

def test_every_sequence_file_loads_without_problems(cat):
    assert cat.problems == [], cat.problems[:10]


def test_every_curriculum_module_has_a_learning_sequence(curr, cat):
    missing = sorted(set(curr.nodes) - set(cat.covered()))
    assert not missing, "modules without a learning sequence: %s" % missing[:20]


def test_every_step_can_be_solved_by_its_own_answer(curr, cat):
    unsolvable = []
    for node_id in cat.covered():
        for seq in cat.sequences(node_id):
            for step in _steps(seq):
                answer = evaluators.solution(step)
                state = {"revealed": answer.get("revealed")} if step["type"] == "clues" else {}
                if evaluators.evaluate(step, answer, state)["correct"] is False:
                    unsolvable.append((seq["id"], step["id"]))
    assert not unsolvable, unsolvable[:10]


def test_authored_sequences_follow_the_teaching_loop(curr, cat):
    """Introduce, demonstrate, then checked steps of more than one kind, each
    with a hint and an explanation, ending on a transfer to a fresh case."""
    authored = 0
    for node_id in cat.covered():
        for seq in cat.sequences(node_id):
            if seq["origin"]["kind"] != "authored":
                continue
            authored += 1
            kinds = [beat["kind"] for beat in seq["beats"]]
            assert kinds[:2] == ["intro", "demo"], seq["id"]
            steps = _steps(seq)
            assert len(steps) >= 3, seq["id"]
            assert len({s["type"] for s in steps}) >= 2, seq["id"]
            assert steps[-1]["transfer"] and not any(s["transfer"] for s in steps[:-1]), seq["id"]
            for step in steps:
                assert step["hints"] and step["why"], (seq["id"], step["id"])
                for option in step.get("options") or []:
                    if not option["correct"]:
                        assert option.get("error") and option.get("feedback"), (seq["id"], step["id"], option["text"])
            assert seq["objective"] and seq.get("next"), seq["id"]
    assert authored >= len(curr.nodes) - 120, "only %d authored sequences" % authored


def test_clinical_radiology_sequences_await_a_radiologist(curr, cat):
    """Clinical content written without a reviewed reporting reference must say
    so, to the reader and in the coverage report, until a radiologist checks it."""
    for node_id in cat.covered():
        if not node_id.startswith("rad."):
            continue
        for seq in cat.sequences(node_id):
            origin = seq["origin"]
            if origin["kind"] == "derived":
                assert origin["review"] == "reference-reviewed", seq["id"]
            else:
                assert origin.get("review_by") == "radiologist", seq["id"]
                assert origin["review"] == "awaiting specialist review", seq["id"]


def test_no_learning_step_reuses_a_quiz_question(curr, cat):
    """The module quiz certifies; the sequence teaches. A step that repeats a
    quiz prompt would let practice stand in for the assessment."""
    collisions = []
    for node_id in cat.covered():
        quiz = {_norm(q.get("prompt", "")) for q in curr.nodes[node_id].get("quiz") or []}
        for seq in cat.sequences(node_id):
            for step in _steps(seq):
                if _norm(step["prompt"]) in quiz:
                    collisions.append((seq["id"], step["prompt"][:60]))
    assert not collisions, collisions[:10]


def test_the_reader_link_inventory_matches_the_reader():
    """Links written directly into web/app.js are recorded for the sequences."""
    from tools import learning_games_inventory as inventory
    with open(inventory.READER, encoding="utf-8") as handle:
        expected = inventory.render(inventory.extract(handle.read()))
    with open(inventory.RECORD, encoding="utf-8") as handle:
        assert handle.read() == expected, "run python tools/learning_games_inventory.py"


def test_the_coverage_report_is_current(curr, cat):
    from tools import learning_games_report as report
    with open(report.REPORT, encoding="utf-8") as handle:
        assert handle.read() == report.build(curr, cat), "run python tools/learning_games_report.py"


def test_public_steps_carry_no_answers_or_explanations(cat):
    """Keys, feedback and explanations stay on the server until a reader answers."""
    secret_keys = {"why", "answers", "accept", "need", "sufficient", "wrong", "target",
                   "feedback", "error", "correct", "solution", "miss", "card"}
    for node_id in cat.covered():
        for seq in cat.sequences(node_id):
            for step in _steps(seq):
                public = catalog.public_step(step, "seed")
                assert not secret_keys & set(public), (seq["id"], step["id"], secret_keys & set(public))
                text = json.dumps(public, ensure_ascii=False)
                assert step["why"] not in text, (seq["id"], step["id"])
                for option in step.get("options") or []:
                    if option.get("feedback"):
                        assert option["feedback"] not in text, (seq["id"], step["id"])


def test_number_theory_sequences_come_from_the_recorded_observations(cat):
    """The Number Theory sequences cite the observation each one was built from."""
    sources = {seq["origin"]["source"] for seq in cat.sequences("math.2.primes")}
    observed = {name[:-5] for name in os.listdir(os.path.join(ROOT, "data/learning-observations"))
                if name.endswith(".json")}
    assert len(cat.sequences("math.2.primes")) >= 7
    assert "brilliant-2026-11-05-divisibility" in sources
    assert sources <= observed, sorted(sources - observed)


# ------------------------------------------------------------ authoring rules

GOOD = """@ math.2.primes
~ Tiny
goal: Decide whether a number is even by looking only at its last digit.
intro: An even number ends in 0, 2, 4, 6 or 8.
demo: 3,148 ends in 8, so it is even.
P: Is 57 even?
  + No :: It ends in 7.
  - Yes :: [any-digit] Only the last digit matters, and 7 is odd.
  hint: Look at the last digit.
  why: 57 ends in 7, which is odd.
F: Fill the digit.
  frame: 1,23__ is even when the blank is 4
  answer: 4
  hint: Choose an even digit.
  why: A number ending in 4 is even.
>P: Is 1,000,002 even?
  + Yes :: It ends in 2.
  - No :: [length-matters] Its length does not matter.
  hint: Only the last digit matters.
  why: It ends in 2.
done: Next, try divisibility by 5.
"""


def test_a_well_formed_sequence_validates():
    [seq] = authoring.parse(GOOD, "inline.lg")
    authoring.validate(seq, 2)
    assert [beat.get("id") for beat in seq["beats"]] == ["intro", "demo", "s1", "s2", "s3"]


def test_a_step_without_an_explanation_is_rejected_with_its_line():
    broken = GOOD.replace("  why: 57 ends in 7, which is odd.\n", "")
    [seq] = authoring.parse(broken, "inline.lg")
    with pytest.raises(authoring.AuthoringError) as error:
        authoring.validate(seq, 2)
    assert "why" in str(error.value) and "inline.lg" in str(error.value)


def test_a_distractor_must_name_the_reasoning_error():
    [seq] = authoring.parse(GOOD.replace("[any-digit] ", ""), "inline.lg")
    with pytest.raises(authoring.AuthoringError):
        authoring.validate(seq, 2)


def test_the_transfer_task_must_come_last():
    swapped = GOOD.replace(">P: Is 1,000,002 even?", "P: Is 1,000,002 even?").replace("P: Is 57 even?", ">P: Is 57 even?")
    [seq] = authoring.parse(swapped, "inline.lg")
    with pytest.raises(authoring.AuthoringError):
        authoring.validate(seq, 2)


# ------------------------------------------------------------------ marking

def test_the_expression_language_is_arithmetic_only():
    assert exprs.evaluate("2 × 3 + 4", {}) == 10
    assert exprs.same_number("0.5", "1/2")
    for hostile in ("__import__('os')", "open('x')", "(1).__class__", "x.y", "9 ** 999999", "lambda: 1"):
        with pytest.raises(exprs.ExpressionError):
            exprs.evaluate(hostile, {"x": 1})


def test_digit_repair_is_marked_by_exact_arithmetic():
    finder = evaluators._RepairDigit.repairable_positions
    for number, divisor in (("57236", 8), ("1001", 7), ("98765432109876543210123", 16)):
        brute = []
        for index in range(len(number)):
            for digit in "0123456789":
                if digit == number[index] or (index == 0 and digit == "0"):
                    continue
                if int(number[:index] + digit + number[index + 1:]) % divisor == 0:
                    brute.append(len(number) - index)
                    break
        assert finder(number, divisor) == brute


def test_a_right_decision_without_the_evidence_is_not_credited(cat):
    step = next(s for seq in cat.sequences("math.2.primes") for s in _steps(seq) if s["type"] == "clues")
    answer = evaluators.solution(step)
    verdict = evaluators.evaluate(step, {"choice": answer["choice"]}, {"revealed": []})
    assert verdict["correct"] is False and verdict["error"] == "decided-without-evidence"
    verdict = evaluators.evaluate(step, {"choice": answer["choice"]}, {"revealed": answer["revealed"]})
    assert verdict["correct"] is True


def test_an_explore_target_starts_false_and_is_reachable(cat):
    explored = 0
    for node_id in cat.covered():
        for seq in cat.sequences(node_id):
            for step in _steps(seq):
                if step["type"] != "explore":
                    continue
                explored += 1
                start = {p["id"]: p["start"] for p in step["params"]}
                assert not evaluators.evaluate(step, {"values": start}, {})["correct"], (seq["id"], step["id"])
                assert evaluators.evaluate(step, evaluators.solution(step), {})["correct"], (seq["id"], step["id"])
    assert explored >= 40


# --------------------------------------------------------------------- API

NODE = "math.2.primes"


@pytest.fixture
def reader(tmp_path):
    import primer.server as srv
    from fastapi.testclient import TestClient
    from primer.learner import LearnerStore
    from primer.wiki import WikiService

    saved = srv.learner, srv.wiki, srv.BACKUP_DIR
    try:
        db = str(tmp_path / "learning-games.db")
        srv.learner = LearnerStore(db)
        srv.wiki = WikiService(db)
        srv.BACKUP_DIR = str(tmp_path / "backups")
        with TestClient(srv.app) as client:
            client.post("/api/profile", json={"name": "Reader", "age": 12, "hours_per_week": 6,
                                              "breadth": "balanced", "domains": ["math"]})
            yield client, srv
    finally:
        srv.learner, srv.wiki, srv.BACKUP_DIR = saved


def _post(client, action, body):
    return client.post("/api/learning-games/%s/%s" % (NODE, action), json=body)


def test_a_locked_module_shows_only_its_introduction(reader):
    client, _ = reader
    data = client.get("/api/learning-games/" + NODE).json()
    assert data["locked"] and data["unlock_requirements"]
    assert {beat["kind"] for beat in data["current"]["beats"]} <= {"intro", "demo"}
    attempt = _post(client, "check", {"sequence": data["current"]["slug"], "step": "s1", "response": {}})
    assert attempt.status_code == 409


def test_a_sequence_played_end_to_end_records_study_not_mastery(reader):
    client, srv = reader
    srv.learner.seed_assumed([nid for nid, n in srv.curr.nodes.items() if n["stage"] <= 1])
    data = client.get("/api/learning-games/" + NODE).json()
    assert not data["locked"]
    current = data["current"]
    slug = current["slug"]
    payload = json.dumps(current, ensure_ascii=False)
    seq = catalog.for_curriculum(srv.curr).sequence(NODE, slug)
    for step in _steps(seq):
        assert step["why"] not in payload, "explanation shipped before an answer"
    mastery_before = srv.learner.mastery_map().get(NODE, 0)
    xp_before = client.get("/api/state").json()["profile"]["xp"]

    first = next(beat for beat in current["beats"] if beat["kind"] == "step")
    step = next(s for s in _steps(seq) if s["id"] == first["id"])
    right = catalog.public_solution(step)
    if step["type"] in authoring.CHOICE_TYPES and step["type"] != "clues":
        wrong = next(o["id"] for o in first["options"] if o["id"] != right["choice"])
        miss = _post(client, "check", {"sequence": slug, "step": first["id"], "response": {"choice": wrong}}).json()
        assert miss["correct"] is False and miss["feedback"]
        assert miss["state"]["attempts"] == 1
        again = _post(client, "check", {"sequence": slug, "step": first["id"], "response": {"choice": wrong}}).json()
        assert again["state"]["attempts"] == 1, "an identical retry is not a second attempt"
        early = _post(client, "reveal", {"sequence": slug, "step": first["id"]})
        assert early.status_code == 409, "the answer is not shown after a single try"
        hint = _post(client, "hint", {"sequence": slug, "step": first["id"]}).json()
        assert len(hint["state"]["hints_shown"]) == 1

    last = None
    for beat in current["beats"]:
        if beat["kind"] != "step":
            continue
        step = next(s for s in _steps(seq) if s["id"] == beat["id"])
        answer = catalog.public_solution(step)
        if step["type"] == "clues":
            for clue in answer["enough"]:
                _post(client, "clue", {"sequence": slug, "step": beat["id"], "clue": clue})
            answer = {"choice": answer["choice"]}
        last = _post(client, "check", {"sequence": slug, "step": beat["id"], "response": answer}).json()
        assert last["correct"] is True, (beat["id"], last)
    done = last["completed"]
    assert done and done["first"] and done["xp_gained"] > 0
    assert done["study_note"] and "quiz" in done["study_note"].lower()
    xp_after = client.get("/api/state").json()["profile"]["xp"]
    assert xp_after - xp_before == done["xp_gained"] <= 6

    # Settled steps cannot be farmed: a second submission pays nothing more.
    repeat = _post(client, "check", {"sequence": slug, "step": first["id"], "response": {}}).json()
    assert repeat.get("already")
    assert client.get("/api/state").json()["profile"]["xp"] == xp_after

    # Study never writes mastery; any card it mints is marked as study.
    assert srv.learner.mastery_map().get(NODE, 0) == mastery_before
    with srv.learner._conn() as conn:
        origins = {row[0] for row in conn.execute("SELECT origin FROM srs_cards WHERE node_id = ?", (NODE,))}
    assert origins <= {"activity"}

    # Replaying starts a fresh run that earns nothing new.
    _post(client, "restart", {"sequence": slug})
    replay = client.get("/api/learning-games/%s?sequence=%s" % (NODE, slug)).json()["current"]
    assert replay["done"] == 0 and replay["plays"] >= 1
