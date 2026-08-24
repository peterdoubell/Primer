"""The Google identity layer: cross-reader isolation, claiming the legacy
profile, and the OAuth callback's rejection paths.

Google sign-in turns a single-tenant store into a multi-tenant one; these are
the load-bearing tests for the boundary that turn depends on — that one
reader's profile, mastery, deck, journal and in-flight quiz papers are
genuinely invisible and unwritable from another reader's session, that
reader_id=1 (the one profile every database had before this feature existed)
can be claimed exactly once, and that a callback carrying a token this app
cannot verify is refused rather than trusted. Everything runs against a
throwaway database; the reader's real record is never touched.
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def client(tmp_path):
    """A fresh app and database per test: reader isolation is exactly the
    property under test, so no state should carry between cases."""
    import primer.server as srv
    from primer.learner import LearnerStore
    from primer.wiki import WikiService
    db = str(tmp_path / "test.db")
    orig = (srv.learner, srv.wiki, srv.BACKUP_DIR)
    srv.learner = LearnerStore(db)
    srv.wiki = WikiService(db)
    srv.BACKUP_DIR = str(tmp_path / "backups")
    with TestClient(srv.app) as c:
        yield c
    srv.learner, srv.wiki, srv.BACKUP_DIR = orig


def _sign_in_as(client, google_sub, email="reader@example.com", name="Reader"):
    """Mint a real session for a Google identity directly against the store,
    bypassing the OAuth network dance — that flow is exercised on its own
    below. Returns the reader_id the session resolves to."""
    import primer.server as srv
    reader_id = srv.learner.upsert_google_reader(google_sub, email, name)
    token = srv.learner.create_session(reader_id)
    # Matches the domain TestClient's own Set-Cookie responses land under
    # (single-label "testserver" normalises to "testserver.local" in
    # http.cookiejar) — setting it unqualified instead lands on a second,
    # separate jar entry that a later real response cannot overwrite,
    # leaving a stale value behind it.
    client.cookies.set(srv.READER_COOKIE, token, domain="testserver.local")
    return reader_id


def _reader_cookie(client, srv):
    """The session cookie's current value, regardless of which domain httpx
    filed it under — see _sign_in_as for why more than one can exist."""
    for cookie in client.cookies.jar:
        if cookie.name == srv.READER_COOKIE:
            return cookie.value
    return None


def _onboard(client, name, domains=("math", "physics")):
    r = client.post("/api/profile", json={
        "name": name, "age": 9, "hours_per_week": 6,
        "breadth": "balanced", "domains": list(domains)})
    assert r.status_code == 200
    return r.json()


@pytest.fixture
def open_assessment_gate(monkeypatch):
    """Same fixture as test_api.py's: keeps sitting-mechanics tests
    independent of curriculum prerequisites, which are not what a token's
    reader-ownership check is about."""
    import primer.server as srv
    monkeypatch.setattr(srv, "_locked_lesson_response", lambda node, reader_id: None)


def _answer_key(token):
    """The graded key for a served paper, read from the book's own copy — see
    test_api.py's identical helper for why a test cannot get this over the
    wire."""
    import primer.server as srv
    served = srv._SERVED[token]["questions"]
    return {q.get("id"): q.get("answer", "") for q in served}


# ---------------- a session with no cookie is unaffected ----------------

def test_no_session_cookie_still_reaches_the_legacy_profile(client):
    """The single-tenant flow needs no Google account: no cookie must resolve
    to reader_id=1 exactly as every request did before this feature existed."""
    import primer.server as srv
    _onboard(client, "Legacy")
    assert client.get("/api/state").json()["profile"]["name"] == "Legacy"
    assert srv.learner.get_profile(reader_id=1)["name"] == "Legacy"


# ---------------- profile & state ----------------

def test_two_readers_get_two_separate_profiles(client):
    _sign_in_as(client, "sub-a", name="Reader A")
    a = _onboard(client, "Ada")
    client.cookies.clear()

    _sign_in_as(client, "sub-b", name="Reader B")
    b = _onboard(client, "Bea")
    assert a["name"] == "Ada" and b["name"] == "Bea"
    assert client.get("/api/state").json()["profile"]["name"] == "Bea"

    client.cookies.clear()
    _sign_in_as(client, "sub-a")
    assert client.get("/api/state").json()["profile"]["name"] == "Ada", \
        "signing back in as A must not have picked up B's edits"


def test_settings_saved_by_one_reader_do_not_touch_another(client):
    _sign_in_as(client, "sub-a")
    _onboard(client, "Ada")
    client.post("/api/profile/settings", json={"theme": "dark"})

    client.cookies.clear()
    _sign_in_as(client, "sub-b")
    _onboard(client, "Bea")
    saved = client.post("/api/profile/settings", json={"theme": "light"}).json()
    assert saved["settings"]["theme"] == "light"

    client.cookies.clear()
    _sign_in_as(client, "sub-a")
    assert client.get("/api/state").json()["profile"]["settings"]["theme"] == "dark"


# ---------------- mastery, decks and journal are invisible across readers --

def test_attempt_by_one_reader_does_not_appear_in_another_readers_curriculum(
        client, open_assessment_gate):
    import primer.server as srv
    node_id = "math.1.addition"
    assert srv.curr.node(node_id), "fixture assumes this node exists"

    _sign_in_as(client, "sub-a")
    _onboard(client, "Ada")
    paper = client.get("/api/quiz/" + node_id).json()
    keys = _answer_key(paper["token"])
    answers = [keys.get(q["id"], "") for q in paper["questions"]]
    sub = client.post("/api/quiz/submit", json={
        "node_id": node_id, "answers": answers, "token": paper["token"]})
    assert sub.status_code == 200

    a_node = client.get("/api/curriculum/node/" + node_id).json()
    assert a_node["mastery"] > 0, "setup: reader A must actually have progress here"

    client.cookies.clear()
    _sign_in_as(client, "sub-b")
    _onboard(client, "Bea")
    b_node = client.get("/api/curriculum/node/" + node_id).json()
    assert b_node["mastery"] == 0 and not b_node["proven"] and not b_node["mastered"], \
        "reader B must not see reader A's progress on a shared curriculum node"
    assert client.get("/api/today").json()["mastered"] == 0
    assert client.get("/api/roadmap").json()["nodes_mastered"] == 0
    assert client.get("/api/journal").json()["items"] == []


def test_a_review_card_cannot_be_seen_or_graded_by_a_different_reader(client):
    import primer.server as srv
    reader_a = _sign_in_as(client, "sub-a")
    _onboard(client, "Ada")
    added = client.post("/api/review/add", json={
        "front": "2+2", "back": "4", "node_id": "math.1.addition"}).json()["added"]
    assert added == 1
    # A fresh card is due after RELEARN_DELAY, not the instant it is written
    # (see add_cards) — /api/review/due is the wrong tool for "does the row
    # exist", so read the deck directly the way test_aaa_server.py does.
    with srv.learner._conn() as conn:
        card_id = conn.execute(
            "SELECT id FROM srs_cards WHERE reader_id=?", (reader_a,)).fetchone()[0]

    client.cookies.clear()
    _sign_in_as(client, "sub-b")
    _onboard(client, "Bea")
    assert client.get("/api/review/due").json()["cards"] == [], \
        "reader B must not see reader A's deck"
    graded = client.post("/api/review", json={"card_id": card_id, "quality": 5})
    # The lookup is scoped by (id, reader_id): a foreign id reads as "no such
    # card" — the row genuinely does not exist for this reader — not as a
    # successful grade of someone else's card.
    assert graded.status_code == 200
    assert graded.json() == {"error": "no such card"}

    # Reader B's refused grade must not have touched reader A's actual row —
    # in particular, must not have advanced it past its own due date.
    with srv.learner._conn() as conn:
        row = conn.execute(
            "SELECT reps, reviews FROM srs_cards WHERE id=? AND reader_id=?",
            (card_id, reader_a)).fetchone()
    assert row["reps"] == 0 and row["reviews"] == 0


# ---------------- a served paper belongs to the reader it was issued to ----

def test_a_quiz_papers_token_cannot_be_redeemed_by_a_different_reader(
        client, open_assessment_gate):
    node_id = "math.1.addition"

    _sign_in_as(client, "sub-a")
    _onboard(client, "Ada")
    paper = client.get("/api/quiz/" + node_id).json()
    token = paper["token"]

    client.cookies.clear()
    _sign_in_as(client, "sub-b")
    _onboard(client, "Bea")
    keys = _answer_key(token)
    answers = [keys.get(q["id"], "") for q in paper["questions"]]

    # /api/quiz/check: a foreign-owned token reads exactly like an unknown one.
    check = client.post("/api/quiz/check", json={
        "token": token, "id": paper["questions"][0]["id"], "answer": "x"})
    assert check.status_code == 409

    # /api/quiz/submit: refused, and nothing is recorded against reader B.
    sub = client.post("/api/quiz/submit", json={
        "node_id": node_id, "answers": answers, "token": token})
    assert sub.status_code == 409
    assert client.get("/api/curriculum/node/" + node_id).json()["mastery"] == 0

    # A refused foreign attempt must not have consumed the paper — it is
    # still reader A's to redeem.
    client.cookies.clear()
    _sign_in_as(client, "sub-a")
    keys_a = _answer_key(token)
    answers_a = [keys_a.get(q["id"], "") for q in paper["questions"]]
    sub_a = client.post("/api/quiz/submit", json={
        "node_id": node_id, "answers": answers_a, "token": token})
    assert sub_a.status_code == 200


def test_a_practice_papers_token_cannot_be_redeemed_by_a_different_reader(
        client, open_assessment_gate):
    node_id = "math.1.addition"

    _sign_in_as(client, "sub-a")
    _onboard(client, "Ada")
    paper = client.get("/api/practice/addition?node_id=" + node_id).json()

    client.cookies.clear()
    _sign_in_as(client, "sub-b")
    _onboard(client, "Bea")
    keys = _answer_key(paper["token"])
    answers = [keys.get(q["id"], "") for q in paper["questions"]]
    r = client.post("/api/attempt", json={
        "node_id": node_id, "answers": answers, "token": paper["token"]})
    assert r.status_code == 409
    assert client.get("/api/curriculum/node/" + node_id).json()["mastery"] == 0


def test_a_placement_papers_token_cannot_be_redeemed_by_a_different_reader(client):
    _sign_in_as(client, "sub-a")
    _onboard(client, "Ada")
    paper = client.get("/api/placement/next?domain=math").json()

    client.cookies.clear()
    _sign_in_as(client, "sub-b")
    _onboard(client, "Bea")
    r = client.post("/api/placement/submit", json={
        "domain": "math", "stage": paper["stage"],
        "answers": [""] * len(paper["questions"]), "token": paper["token"]})
    assert r.status_code == 409


# ---------------- claiming the legacy profile ----------------

def test_claim_requires_the_correct_access_password(monkeypatch, client):
    import primer.server as srv
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV, "secret")
    # Setting the outer gate's password engages it for every route (not only
    # when hosted) — Basic auth is how curl/CI satisfy it, and how these
    # cases satisfy it here without a second, unrelated cookie dance.
    client.auth = ("primer", "secret")
    # The legacy profile: what every database already held before Google
    # sign-in existed, filed under no cookie at all — reader_id=1.
    _onboard(client, "Legacy")

    _sign_in_as(client, "sub-claim")
    assert client.get("/api/state").json()["profile"] is None, \
        "setup: a freshly signed-in identity starts with no profile of its own"

    wrong = client.post("/api/account/claim", json={"password": "nope"})
    assert wrong.status_code == 401
    assert client.get("/api/account").json()["reader_id"] != 1

    right = client.post("/api/account/claim", json={"password": "secret"})
    assert right.status_code == 200 and right.json()["claimed"] is True
    assert client.get("/api/account").json()["reader_id"] == 1
    assert client.get("/api/state").json()["profile"]["name"] == "Legacy", \
        "claiming must hand the identity the pre-existing legacy profile"


def test_claim_is_refused_without_a_configured_access_password(client):
    _sign_in_as(client, "sub-claim2")
    _onboard(client, "X")
    r = client.post("/api/account/claim", json={"password": "anything"})
    assert r.status_code == 503


def test_the_unsigned_in_default_reader_cannot_claim_itself(client):
    r = client.post("/api/account/claim", json={"password": "x"})
    assert r.status_code == 409


def test_a_claimed_profile_cannot_be_claimed_again(monkeypatch, client):
    import primer.server as srv
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV, "secret")
    client.auth = ("primer", "secret")
    _onboard(client, "Legacy")

    _sign_in_as(client, "sub-first")
    assert client.post("/api/account/claim", json={"password": "secret"}).status_code == 200

    client.cookies.clear()
    _sign_in_as(client, "sub-second")
    _onboard(client, "Second")   # a second identity's own, separate profile
    again = client.post("/api/account/claim", json={"password": "secret"})
    assert again.status_code == 409, "reader_id=1 must already be claimed"
    assert client.get("/api/state").json()["profile"]["name"] == "Second", \
        "a refused claim must not disturb the claimant's own profile"

    client.cookies.clear()
    _sign_in_as(client, "sub-first")
    assert client.get("/api/state").json()["profile"]["name"] == "Legacy", \
        "the legacy profile must still belong to whoever claimed it first"


def test_claiming_moves_the_live_session_to_the_legacy_profile(monkeypatch, client):
    """The claim moves the identity's row to reader_id=1; the cookie already
    in hand must follow it without a fresh sign-in."""
    import primer.server as srv
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV, "secret")
    client.auth = ("primer", "secret")
    _sign_in_as(client, "sub-x")
    _onboard(client, "X")
    old_token = _reader_cookie(client, srv)
    client.post("/api/account/claim", json={"password": "secret"})
    new_token = _reader_cookie(client, srv)
    assert new_token and new_token != old_token
    assert srv.learner.reader_for_session(old_token) is None, \
        "the old session must be gone, not merely superseded"
    assert srv.learner.reader_for_session(new_token) == 1


# ---------------- the OAuth callback ----------------

class _FakeTokenResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class _FakeAsyncClient:
    """Stands in for httpx.AsyncClient so the token exchange never leaves
    the process. The callback's own logic — state check, verification,
    session creation — is what these tests are pinning, not Google's API."""

    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, data=None):
        return _FakeTokenResponse({"id_token": "fake-id-token"})


def _state_from_cookie(client, srv):
    """The state /auth/google/start just issued, unquoted.

    httpx's cookie jar keeps the RFC 6265 quoting a value containing "/"
    picks up (Starlette unquotes it again on the way back in, which is what
    the real callback sees — this is a test-side artifact of reading the
    cookie jar directly, not a production concern).
    """
    return client.cookies.get(srv._OAUTH_STATE_COOKIE).strip('"').split("|", 1)[0]


def _configure_google(monkeypatch, srv, verify=None):
    monkeypatch.setattr(srv, "GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(srv, "GOOGLE_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setattr(srv.httpx, "AsyncClient", _FakeAsyncClient)
    if verify is not None:
        monkeypatch.setattr(srv, "_verify_google_id_token", verify)


def test_google_start_is_unavailable_without_a_configured_client(client):
    import primer.server as srv
    assert srv.GOOGLE_CLIENT_ID is None, \
        "fixture assumes no real Google client is configured in test env"
    r = client.get("/auth/google/start")
    assert r.status_code == 503


def test_google_callback_happy_path_signs_in_and_sets_a_session(monkeypatch, client):
    import primer.server as srv
    _configure_google(monkeypatch, srv, verify=lambda raw: {
        "sub": "sub-happy", "email": "happy@example.com", "name": "Happy"})

    client.get("/auth/google/start", follow_redirects=False)
    state = _state_from_cookie(client, srv)
    cb = client.get("/auth/google/callback?code=abc&state=" + state,
                    follow_redirects=False)
    assert cb.status_code == 303
    assert _reader_cookie(client, srv)

    account = client.get("/api/account").json()
    assert account["signed_in"] is True
    assert account["email"] == "happy@example.com"
    assert account["reader_id"] != 1


def test_signing_in_again_with_the_same_identity_reaches_the_same_reader(monkeypatch, client):
    import primer.server as srv
    _configure_google(monkeypatch, srv, verify=lambda raw: {
        "sub": "same-sub", "email": "e@example.com", "name": "E"})

    def _go():
        client.get("/auth/google/start", follow_redirects=False)
        state = _state_from_cookie(client, srv)
        client.get("/auth/google/callback?code=abc&state=" + state, follow_redirects=False)
        return client.get("/api/account").json()["reader_id"]

    first = _go()
    client.cookies.delete(srv.READER_COOKIE)   # a new browser session
    second = _go()
    assert first == second


def test_google_callback_refuses_a_mismatched_state(monkeypatch, client):
    import primer.server as srv
    _configure_google(monkeypatch, srv, verify=lambda raw: {
        "sub": "sub-cs", "email": "e@example.com", "name": "E"})

    client.get("/auth/google/start", follow_redirects=False)
    cb = client.get("/auth/google/callback?code=abc&state=not-the-real-state",
                    follow_redirects=False)
    assert cb.status_code == 303
    assert srv.READER_COOKIE not in client.cookies


def test_google_callback_refuses_when_google_reports_an_error(monkeypatch, client):
    import primer.server as srv
    _configure_google(monkeypatch, srv)

    client.get("/auth/google/start", follow_redirects=False)
    state = _state_from_cookie(client, srv)
    cb = client.get("/auth/google/callback?error=access_denied&state=" + state,
                    follow_redirects=False)
    assert cb.status_code == 303
    assert srv.READER_COOKIE not in client.cookies


@pytest.mark.parametrize("exc", [
    ValueError("Token expired"),
    ValueError("Wrong recipient, payload audience != test-client-id"),
    ValueError("Could not verify signature"),
])
def test_google_callback_refuses_an_id_token_that_fails_verification(monkeypatch, client, exc):
    import primer.server as srv

    def _boom(raw):
        raise exc
    _configure_google(monkeypatch, srv, verify=_boom)

    client.get("/auth/google/start", follow_redirects=False)
    state = _state_from_cookie(client, srv)
    cb = client.get("/auth/google/callback?code=abc&state=" + state,
                    follow_redirects=False)
    assert cb.status_code == 303
    assert srv.READER_COOKIE not in client.cookies
    assert client.get("/api/account").json()["signed_in"] is False


def test_google_sign_out_ends_the_session(monkeypatch, client):
    import primer.server as srv
    _configure_google(monkeypatch, srv, verify=lambda raw: {
        "sub": "sub-out", "email": "e@example.com", "name": "E"})
    client.get("/auth/google/start", follow_redirects=False)
    state = _state_from_cookie(client, srv)
    client.get("/auth/google/callback?code=abc&state=" + state, follow_redirects=False)
    token = _reader_cookie(client, srv)
    assert srv.learner.reader_for_session(token) is not None

    out = client.post("/api/account/sign-out")
    assert out.status_code == 200 and out.json()["signed_out"] is True
    assert srv.learner.reader_for_session(token) is None
    assert client.get("/api/account").json()["reader_id"] == 1, \
        "signing out must fall back to the unsigned-in default, not an error"
