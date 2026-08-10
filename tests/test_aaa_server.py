"""AAA-round regression tests for the server-side fixes.

Each test pins one of the audit items: keyword-dump scoring, restart-proof
sittings, scale-aware distractor padding, typed settings, the tutor's
remote-disclosure flag, tiered backup retention, the bank checker's WARN
tier, and the defensive placement-reopen wiring. Everything runs against
throwaway databases and directories — the reader's real record is never
touched.
"""

import json
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    """Boot the app against an isolated database, the way test_api.py does."""
    tmp = tmp_path_factory.mktemp("aaadb")
    db = str(tmp / "test.db")
    import primer.server as srv
    from primer.learner import LearnerStore
    from primer.wiki import WikiService
    orig = (srv.learner, srv.wiki, srv.BACKUP_DIR)
    srv.learner = LearnerStore(db)
    srv.wiki = WikiService(db)
    srv.BACKUP_DIR = str(tmp / "backups")
    from fastapi.testclient import TestClient
    with TestClient(srv.app) as c:
        yield c
    srv.learner, srv.wiki, srv.BACKUP_DIR = orig


@pytest.fixture(scope="module")
def onboarded(client):
    r = client.post("/api/profile", json={
        "name": "Ada", "age": 8, "hours_per_week": 6,
        "breadth": "balanced", "domains": ["math", "physics"]})
    assert r.status_code == 200
    return r.json()


# ---------------- 1. short-answer structure requirement ----------------


def test_bare_keyword_dump_earns_reduced_credit():
    from primer.quiz import score_short_answer
    keys = ["photosynthesis", "sunlight", "energy"]
    dump = score_short_answer("photosynthesis sunlight energy", keys)
    real = score_short_answer(
        "Photosynthesis is how plants turn sunlight into energy.", keys)
    assert real == 1.0, "a legitimate sentence must keep full credit"
    assert dump <= 0.5, "an unordered keyword list is not writing"
    assert dump < real


def test_structure_check_spares_fuzzy_and_near_miss_answers():
    from primer.quiz import score_short_answer
    keys = ["finite", "balance", "anecdote"]
    # Word-building still counts, and a connective marks real structure.
    fuzzy = score_short_answer(
        "it is finitely bounded and balancing avoids anecdotal evidence", keys)
    assert fuzzy == 1.0
    # Single-keyword answers are exempt: one word can be the whole answer.
    assert score_short_answer("mitochondria", ["mitochondria"]) == 1.0
    # Partial-credit near misses are untouched.
    assert 0 < score_short_answer("only sunlight here",
                                  ["photosynthesis", "sunlight", "energy"]) < 1


# ---------------- 2. sittings survive a restart ----------------


def test_sitting_survives_simulated_restart(client, onboarded):
    import primer.server as srv
    qs = [{"id": 0, "kind": "numeric", "prompt": "2+2", "answer": "4"}]
    token = srv._remember(qs, "quiz", "math.1.addition")
    # A restart loses every Python object but keeps the DB. A fresh store over
    # the same file must still hold the paper, with its binding intact.
    fresh = srv._SittingStore()
    entry = fresh.get(token)
    assert entry is not None
    assert entry["purpose"] == "quiz" and entry["subject"] == "math.1.addition"
    assert entry["questions"][0]["answer"] == "4"


def test_sitting_pop_is_single_use_and_purpose_bound(client, onboarded):
    import primer.server as srv
    qs = [{"id": 0, "kind": "numeric", "prompt": "3+3", "answer": "6"}]
    token = srv._remember(qs, "quiz", "math.1.addition")
    # Wrong purpose or subject: refused, and the paper is NOT consumed.
    assert srv._recall(token, "placement", "math:5") is None
    assert srv._recall(token, "quiz", "math.9.fake") is None
    # Right binding: honoured exactly once.
    assert srv._recall(token, "quiz", "math.1.addition") is not None
    assert srv._recall(token, "quiz", "math.1.addition") is None


def test_sitting_ttl_still_expires(client, onboarded):
    import primer.server as srv
    qs = [{"id": 0, "kind": "numeric", "prompt": "4+4", "answer": "8"}]
    token = srv._remember(qs, "quiz", "math.1.addition")
    # The write-through proxy: mutating `at` must reach the persistent store.
    srv._SERVED[token]["at"] = time.time() - srv._SERVED_TTL - 1
    assert srv._recall(token, "quiz", "math.1.addition") is None


def test_committed_answers_persist_across_restart(client, onboarded):
    import primer.server as srv
    qs = [{"id": 0, "kind": "numeric", "prompt": "5+5", "answer": "10"}]
    token = srv._remember(qs, "quiz", "math.1.addition")
    r = client.post("/api/quiz/check", json={"token": token, "id": 0, "answer": "7"})
    assert r.status_code == 200 and r.json()["correct"] is False
    fresh = srv._SittingStore()
    entry = fresh.get(token)
    # Keys come back as ints, not JSON strings, and the first commitment stands.
    assert entry["committed"][0]["answer"] == "7"


# ---------------- 4. scale-aware distractor padding ----------------


def test_mc_padding_is_scale_aware():
    from primer import practice
    for _ in range(30):
        q = practice._mc("How many days in a leap year?", 366, [])
        assert len(q["choices"]) == 4
        assert len(set(q["choices"])) == 4, "padding must deduplicate"
        vals = [float(c) for c in q["choices"]]
        # The old randint(1, 99) noise sat two orders of magnitude below the
        # key; scale-aware padding stays within the key's own neighbourhood.
        assert all(36 <= v <= 3700 for v in vals), q["choices"]


def test_mc_padding_small_answers_still_work():
    from primer import practice
    for _ in range(30):
        q = practice._mc("2+1?", 3, [])
        assert len(q["choices"]) == 4 and "3" in q["choices"]
        assert len(set(q["choices"])) == 4


# ---------------- 7. typed settings body ----------------


def test_settings_rejects_wrong_value_types(client, onboarded):
    r = client.post("/api/profile/settings", json={"font_scale": "huge"})
    assert r.status_code == 422
    r = client.post("/api/profile/settings", json={"speak": "loudly"})
    assert r.status_code == 422


def test_settings_accepts_valid_types_and_refuses_foreign_keys(client, onboarded):
    r = client.post("/api/profile/settings",
                    json={"font_scale": 1.25, "theme": "dark", "rank": 5})
    assert r.status_code == 200
    d = r.json()
    assert d["settings"]["font_scale"] == 1.25
    assert d["settings"]["theme"] == "dark"
    assert "rank" in d.get("refused", [])
    assert "rank" not in d["settings"]


# ---------------- 10. tutor remote-disclosure flag ----------------


def test_tutor_reply_carries_remote_flag(client, onboarded, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = client.post("/api/tutor", json={
        "messages": [{"role": "user", "content": "why is the sky blue?"}],
        "title": "", "excerpt": "Light scatters more at short wavelengths."})
    d = r.json()
    assert d["engine"] == "book"
    assert d["remote"] is False, "offline engine must say nothing left the machine"


def test_state_discloses_tutor_remoteness(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    d = client.get("/api/state").json()
    assert d["tutor_remote"] is False
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    d = client.get("/api/state").json()
    assert d["tutor_remote"] is True


def test_llm_path_flags_remote_true():
    from primer import tutor
    import primer.tutor as t

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps({"content": [{"type": "text", "text": "hi"}]}).encode()

    orig = t.urllib.request.urlopen
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    t.urllib.request.urlopen = lambda req, timeout=60: _Resp()
    try:
        out = tutor.ask_llm([{"role": "user", "content": "hi"}], "T", "E", 2)
    finally:
        t.urllib.request.urlopen = orig
        del os.environ["ANTHROPIC_API_KEY"]
    assert out["remote"] is True and out["engine"] == "claude"


# ---------------- 11. tiered backup retention ----------------


def test_backup_retention_keeps_daily_weekly_monthly_tiers(tmp_path):
    import primer.server as srv
    d = str(tmp_path / "backups")
    os.makedirs(d)
    # One backup a day for 400 days ending today.
    now = time.time()
    names = []
    for i in range(400):
        stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(now - i * 86400))
        name = "primer-{}.db".format(stamp)
        open(os.path.join(d, name), "w").close()
        names.append(name)
    srv._prune_backups(d)
    left = sorted(os.listdir(d), reverse=True)
    # ~5 daily + up to 4 weekly + up to 12 monthly; small overlap tolerated,
    # but nothing like 400 — and the 5 newest dailies must all survive.
    assert 5 <= len(left) <= 21, left
    assert left[:5] == names[:5]
    # The horizon is long: something older than 6 months survives.
    six_months = time.strftime("%Y%m%d", time.localtime(now - 180 * 86400))
    assert any(f[7:15] < six_months for f in left), "long-horizon tier missing"


# ---------------- 3. check_banks WARN tier ----------------


def test_check_banks_warns_between_tiers(tmp_path, capsys):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "tools"))
    import check_banks
    assert 0 < check_banks.WARN_LENGTH_EDGE < check_banks.MAX_LENGTH_EDGE
    # A synthetic bank whose pick-by-longest edge lands between the tiers:
    # 40 items at 4 options (chance 25%); longest wins 12 (30%) → +5.0pp.
    def item(i, winner):
        opts = ["ab", "cdef", "ghijk", "l" * 18]   # clearly non-flat lengths
        ans = opts[3] if winner == "long" else opts[0] if winner == "short" else opts[1]
        return {"kind": "choice", "prompt": "Given situation {}, what follows?".format(i),
                "choices": opts, "answer": ans}
    winners = ["long"] * 12 + ["short"] * 10 + ["mid"] * 18
    items = [item(i, w) for i, w in enumerate(winners)]
    nodes = [{"id": "syn.{}".format(k), "stage": 2,
              "quiz": items[k * 10:(k + 1) * 10] + [
                  {"kind": "numeric", "prompt": "compute {}".format(k), "answer": "1"}]}
             for k in range(4)]
    path = tmp_path / "bank.json"
    path.write_text(json.dumps({"nodes": nodes}))
    problems = check_banks.audit(str(path))
    out = capsys.readouterr().out
    assert "WARN (drifting)" in out
    assert "margin to limit" in out
    assert not any(p[0] == "length is a tell" for p in problems), \
        "the WARN tier must not fail a bank under the hard threshold"


# ---------------- 9. defensive placement reopen ----------------


def test_placement_reopen_is_noop_without_store_support(client, onboarded):
    import primer.server as srv
    # A stub store without the feature (e.g. a minimal test double): the
    # wiring must degrade to a graceful no-op, never an AttributeError.
    class _Stub:
        db_path = srv.learner.db_path

        def placement_state(self):
            return {"math": {"done": True, "asked": [{"stage": 1, "passed": True}]}}

    orig = srv.learner
    srv.learner = _Stub()
    try:
        assert srv._placement_reopen("math") is False
    finally:
        srv.learner = orig


def test_placement_reopen_uses_the_fixed_store_interface(client, onboarded):
    """The server calls exactly `reopen_placement` — the one method the store
    ships — and honours its boolean verdict. No candidate-name guessing."""
    import primer.server as srv
    calls = []

    class _Stub:
        db_path = srv.learner.db_path

        def reopen_placement(self, domain):
            calls.append(domain)
            return len(calls) == 1   # first call reopens, second is refused

        def placement_state(self):
            return {"math": {"done": False, "asked": []}}

    orig = srv.learner
    srv.learner = _Stub()
    try:
        assert srv._placement_reopen("math") is True
        assert srv._placement_reopen("math") is False, \
            "the store's False (still cooling / not settled) must be final"
        assert calls == ["math", "math"]
    finally:
        srv.learner = orig


def test_settled_placement_can_be_remeasured_after_cooling(client, onboarded):
    import primer.server as srv
    srv.learner.placement_update("math", 1, [{"stage": 1, "passed": True},
                                             {"stage": 2, "passed": False}], True)
    assert client.get("/api/placement/next?domain=math").status_code == 409
    # Still cooling: the 409 stands even when asked to recheck.
    assert client.get("/api/placement/next?domain=math&recheck=true").status_code == 409
    with srv.learner._conn() as conn:   # age the settle past the cooling window
        conn.execute("UPDATE placement SET settled_at=? WHERE domain='math'",
                     (time.time() - 8 * 86400,))
    r = client.get("/api/placement/next?domain=math&recheck=true")
    assert r.status_code == 200
    # Re-measurement resumes at the settled frontier, not from scratch.
    assert r.json()["stage"] == 2
    # And the submit path accepts the same rung it just served.
    s = client.post("/api/placement/submit", json={
        "domain": "math", "stage": r.json()["stage"],
        "answers": [""] * 12, "token": r.json()["token"]})
    assert s.status_code == 200 and s.json()["settled"] is True


def test_placement_next_advertises_reopen_support(client, onboarded):
    import primer.server as srv
    # The 409 for a settled domain must say truthfully whether re-measuring
    # is possible — i.e. whether the store ships reopen_placement.
    srv.learner.placement_update("physics", 1, [{"stage": 1, "passed": True},
                                                {"stage": 2, "passed": False}], True)
    r = client.get("/api/placement/next?domain=physics")
    assert r.status_code == 409
    body = r.json()
    supported = callable(getattr(srv.learner, "reopen_placement", None))
    assert body["reopen_supported"] is supported


# ---------------- short-answer prefix false positives ----------------


def test_shared_prefix_alone_does_not_credit_unrelated_words():
    """A six-letter shared prefix is not word-building: 'transport' must not
    credit *transform*, 'collection' must not credit *collective* — only a
    genuine derivational suffix left over after the shared stem may match."""
    from primer.quiz import score_short_answer
    assert score_short_answer("we transport goods", ["transform"]) == 0.0
    assert score_short_answer("a fine collection", ["collective"]) == 0.0
    assert score_short_answer("great generosity", ["generation"]) == 0.0
    # Genuine derivation still counts.
    assert score_short_answer("an anecdotal report", ["anecdote"]) == 1.0
    assert score_short_answer("it is finitely bounded", ["finite"]) == 1.0


# ---------------- reader-owned tutor privacy switch ----------------


def test_tutor_remote_can_be_disabled_in_app(client, onboarded, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    # Key set and setting untouched: remote engine advertised.
    assert client.get("/api/state").json()["tutor_remote"] is True
    # The reader flips the in-app switch...
    r = client.post("/api/profile/settings", json={"tutor_remote_ok": False})
    assert r.status_code == 200
    assert r.json()["settings"]["tutor_remote_ok"] is False
    # ...and the app now discloses a local tutor even though the key remains.
    d = client.get("/api/state").json()
    assert d["tutor_remote"] is False and d["tutor_engine"] == "book"
    # The tutor route itself answers locally: remote=False on the reply.
    a = client.post("/api/tutor", json={
        "messages": [{"role": "user", "content": "why is the sky blue?"}],
        "title": "", "excerpt": "Light scatters more at short wavelengths."}).json()
    assert a["engine"] == "book" and a["remote"] is False
    # Switch back on: the choice is the reader's, both ways.
    client.post("/api/profile/settings", json={"tutor_remote_ok": True})
    assert client.get("/api/state").json()["tutor_remote"] is True


def test_tutor_messages_are_typed(client, onboarded):
    # A malformed message list is refused at the boundary, not deep in ask().
    r = client.post("/api/tutor", json={"messages": [{"role": "user"}]})
    assert r.status_code == 422
    r = client.post("/api/tutor", json={"messages": "hello"})
    assert r.status_code == 422


# ---------------- submit bodies carry no client question bank ----------------


def test_quiz_submit_has_no_questions_field(client, onboarded):
    """The model no longer declares `questions`; a client that still sends one
    is harmlessly ignored (the server grades from its own copy regardless)."""
    import primer.server as srv
    assert "questions" not in srv.QuizSubmitIn.model_fields
    assert "questions" not in srv.PlacementSubmitIn.model_fields


# ---------------- check_banks: the human half of the audit ----------------


def test_check_banks_sample_mode_draws_a_hand_audit_sheet(capsys):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "tools"))
    import check_banks
    import glob as _glob
    paths = sorted(_glob.glob(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "data", "curriculum", "*.json")))
    check_banks.sample_for_hand_audit(paths, 5)
    out = capsys.readouterr().out
    assert "Hand-audit sheet" in out
    assert "lower bound" in out
    assert out.count("\n  ") >= 5 or out.count(". [") >= 5
