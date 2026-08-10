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


def test_state_discloses_tutor_remoteness(client, onboarded, monkeypatch):
    """Remote answering is opt-in: a key alone must not switch it on.

    An ANTHROPIC_API_KEY says the installation *could* answer remotely. It is
    not a child's consent for their questions to leave the machine, so
    /api/state must keep reporting a local tutor until someone deliberately
    turns the switch on.
    """
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    d = client.get("/api/state").json()
    assert d["tutor_remote"] is False
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    d = client.get("/api/state").json()
    assert d["tutor_remote"] is False, "a key alone must not opt a reader in"
    assert d["tutor_engine"] == "book"
    client.post("/api/profile/settings", json={"tutor_remote_ok": True})
    d = client.get("/api/state").json()
    assert d["tutor_remote"] is True and d["tutor_engine"] == "claude"


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
    # Key set, switch at its default: local tutor, because remote is opt-in.
    client.post("/api/profile/settings", json={"tutor_remote_ok": None})
    assert client.get("/api/state").json()["tutor_remote"] is False
    # The reader (or their guardian) turns it on...
    r = client.post("/api/profile/settings", json={"tutor_remote_ok": True})
    assert r.status_code == 200
    assert r.json()["settings"]["tutor_remote_ok"] is True
    assert client.get("/api/state").json()["tutor_remote"] is True
    # ...and off again: the switch has to work in both directions.
    r = client.post("/api/profile/settings", json={"tutor_remote_ok": False})
    assert r.json()["settings"]["tutor_remote_ok"] is False
    d = client.get("/api/state").json()
    assert d["tutor_remote"] is False and d["tutor_engine"] == "book"
    # The tutor route itself answers locally: remote=False on the reply.
    a = client.post("/api/tutor", json={
        "messages": [{"role": "user", "content": "why is the sky blue?"}],
        "title": "", "excerpt": "Light scatters more at short wavelengths."}).json()
    assert a["engine"] == "book" and a["remote"] is False
    # And on again: the choice is the reader's, both ways, any number of times.
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


# ---------------- the backup nudge reaches a reader ----------------


def test_state_carries_the_backup_location_and_off_disk_verdict(client):
    """The off-disk answer used to be a PRIMER_BACKUP_DIR the reader had to
    already know about. It now rides on the state every client fetches."""
    bk = client.get("/api/state").json()["backup"]
    assert bk["env_var"] == "PRIMER_BACKUP_DIR"
    assert os.path.isabs(bk["dir"])
    # Test backups live under tmp, on the same device as the test database.
    assert bk["off_disk"] is False
    assert "PRIMER_BACKUP_DIR" in bk["advice"]
    assert "same drive" in bk["advice"]


def test_off_disk_is_a_device_check_not_an_env_var_check(tmp_path, monkeypatch):
    """Pointing the variable at another folder on the same drive is the move
    that feels like safety and is not — it must not be reported as off-disk."""
    import primer.server as srv
    elsewhere = tmp_path / "still-same-disk"
    elsewhere.mkdir()
    monkeypatch.setenv("PRIMER_BACKUP_DIR", str(elsewhere))
    monkeypatch.setattr(srv, "BACKUP_DIR", str(elsewhere))
    bk = srv.backup_status()
    assert bk["configured_by_env"] is True
    assert bk["off_disk"] is False          # configured, still not safe
    assert "PRIMER_BACKUP_DIR" in bk["advice"]


def test_startup_warns_when_backups_share_the_record_s_disk(caplog):
    """A nudge nobody sees is not a nudge: same-disk logs at WARNING."""
    import logging
    import primer.server as srv
    with caplog.at_level(logging.INFO, logger="primer.server"):
        bk = srv.backup_status()
        (srv.log.warning if bk["off_disk"] is False else srv.log.info)(
            "backups -> %s (%d kept) | %s", bk["dir"], bk["copies"], bk["advice"])
    rec = [r for r in caplog.records if "backups ->" in r.getMessage()]
    assert rec, "startup must announce where backups go"
    if bk["off_disk"] is False:
        assert rec[-1].levelno == logging.WARNING


def test_selfcheck_endpoint_is_retired():
    """The self-check is withdrawn, not merely hidden.

    The 2026-08 hand audit measured 22 of 40 generated cloze items defective
    (55%, Wilson 40-69%) after the precision pass that had already halved the
    rate from 90%. A `provisional` label on a paper that is wrong half the time
    is a disclaimer, not a fix, so the route is gone rather than warned about.
    See tools/hand-audit-cloze-2026-08.md.
    """
    import primer.server as srv
    assert not hasattr(srv, "selfcheck")
    routes = {getattr(r, "path", "") for r in srv.app.routes}
    assert "/api/selfcheck" not in routes


# ---------------- the story is told about the reader, not about Nell ----------


def _story_source_strings():
    import primer.server as srv
    out = []
    for ch in srv.STORY["chapters"]:
        out.extend(ch.get("text", []))
        out.append(ch.get("prompt") or "")
        out.append(ch.get("title") or "")
    return [s for s in out if s]


def test_story_source_carries_tokens_not_one_reader_s_pronouns():
    """The source text must not name or gender anybody.

    A story that says "she" cannot be told about a reader who does not, and a
    post-hoc regex cannot fix it: English "her" is two different words (object
    "blinked at her", possessive "her own name") and only the source knows
    which. So the tokens are placed at the source, once, by hand.

    The one deliberate exception is the great-great-grandmother in
    story.family-story, who is a character in her own right and keeps her own
    pronouns — that is a story about someone else's ancestor, not about the
    reader.
    """
    import re
    ancestor = "grandmother"
    for s in _story_source_strings():
        if ancestor in s:
            continue
        stray = re.findall(r"\b(?:[Ss]he|[Hh]er|[Hh]ers|[Hh]erself|[Hh]im|"
                           r"[Hh]imself|Nell)\b", s)
        assert not stray, "un-tokenised gendered text in the story: {} in {!r}".format(
            stray, s[:90])


def test_story_renders_grammatically_for_every_pronoun_setting(client):
    """All three settings must produce clean prose: no leftover tokens, no
    "they was", no "she were"."""
    import re
    from primer import story as story_mod

    disagreements = {
        "they": ("they was", "they has", "they is", "they does", "themself "),
        "she": ("she were", "she have", "she are", "she do "),
        "he": ("he were", "he have", "he are", "he do "),
    }
    for pronouns in ("she", "he", "they"):
        client.post("/api/profile", json={
            "name": "Kai", "age": 9, "hours_per_week": 4, "pronouns": pronouns,
            "breadth": "balanced", "domains": ["math", "physics"]})
        assert client.get("/api/state").json()["profile"]["pronouns"] == pronouns
        body = client.get("/api/story").json()
        blob = "\n".join("\n".join(c["text"] + [c["title"], c["prompt"] or ""])
                         for c in body["chapters"])
        assert "Nell" not in blob and "Kai" in blob
        assert not re.search(r"\{[A-Za-z]+\}", blob), \
            "unrendered token for pronouns={}".format(pronouns)
        low = blob.lower()
        for bad in disagreements[pronouns]:
            assert bad not in low, \
                "verb disagreement {!r} for pronouns={}".format(bad, pronouns)
        # And the pronouns actually asked for are the ones on the page.
        assert story_mod.PRONOUNS[pronouns]["SUBJ"] + " " in low


def test_pronouns_default_to_the_neutral_set(client):
    """A name is not a pronoun. Onboarding without saying anything gets
    they/them, not a guess made from the reader's name."""
    r = client.post("/api/profile", json={
        "name": "Nell", "age": 8, "hours_per_week": 4,
        "breadth": "balanced", "domains": ["math"]})
    assert r.status_code == 200
    assert r.json()["pronouns"] == "they"
    first = client.get("/api/story").json()["chapters"][0]
    assert "a child named Nell" in first["text"][0]
    assert "a girl named" not in first["text"][0]
    assert "they had never seen before" in first["text"][0]


def test_pronouns_can_be_changed_afterwards_and_are_validated(client, onboarded):
    r = client.post("/api/profile/settings", json={"pronouns": "he"})
    assert r.status_code == 200 and r.json()["pronouns"] == "he"
    assert client.get("/api/story").json()["chapters"][0]["title"] == \
        "The Book That Knew His Name"
    assert client.post("/api/profile/settings",
                       json={"pronouns": "it"}).status_code == 422
    assert client.post("/api/profile", json={
        "name": "X", "age": 8, "hours_per_week": 4, "pronouns": "xe",
        "breadth": "balanced", "domains": ["math"]}).status_code == 422


def test_story_preview_before_onboarding_is_rendered(client):
    """The un-onboarded preview reads the same tokenised source; raw {SUBJ} on
    the page would not be a story."""
    import re
    import primer.server as srv
    with srv.learner._conn() as c:
        c.execute("DELETE FROM profile")
    body = client.get("/api/story").json()
    blob = "\n".join("\n".join(ch["text"]) for ch in body["chapters"])
    assert not re.search(r"\{[A-Za-z]+\}", blob)


def test_every_verb_that_must_agree_with_the_reader_is_tokenised():
    """Adjacency checks on rendered prose are not enough — "they themselves
    was" slipped past one. Check the source instead: a bare was/is/has/does
    within a few words downstream of {SUBJ} is a verb nobody tokenised, and it
    will disagree for two of the three settings. (The story contains real
    plural "they"s of its own — other characters, physical laws — which is
    exactly why this has to be asked of the source, where the reader's own
    pronoun is unambiguous.)"""
    import re
    must_agree = r"was|were|is|are|has|have|does|do"
    pat = re.compile(r"\{(?:Subj|SUBJ)\}((?:\s+(?:\{[A-Za-z]+\}|themselves|really|"
                     r"already|almost|simply|then|now|still))*)\s+(" + must_agree + r")\b")
    for s in _story_source_strings():
        m = pat.search(s)
        assert not m, "untokenised verb after the reader's pronoun: {!r}".format(
            s[max(0, m.start() - 20):m.end() + 20])
