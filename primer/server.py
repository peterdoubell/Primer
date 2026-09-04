"""The Primer server: one FastAPI app binding content, curriculum, learner,
practice, quizzes, tutor and pacing into a single interactive book.
"""

import base64
import binascii
import contextvars
import datetime
import hashlib
import hmac
import json
import logging
import os
import random
import re
import secrets
import threading
import time
import urllib.parse
import uuid
from contextlib import asynccontextmanager
from html import escape as _escape
from typing import Dict, List, Literal, Optional

import httpx
from fastapi import FastAPI, Body, Request
from fastapi.responses import (JSONResponse, Response, FileResponse, HTMLResponse,
                               RedirectResponse)
from fastapi.staticfiles import StaticFiles
from google.oauth2 import id_token as google_id_token
from pydantic import BaseModel, Field, field_validator

from . import library, practice, quiz, store, tutor
from . import sittings as sittings_mod
from . import story as story_mod
from .curriculum import Curriculum
from .learner import (LearnerStore, STAGE_NAMES, STAGE_SPAN, STAGE_TITLES,
                      _end_of_tomorrow, _local_day, _remove_backup)
from .pacing import roadmap
from .render import rewrite_article
from .wiki import WikiService, ROOT

# A single-user app rarely needs to untangle interleaved requests, but this
# one runs under asyncio with more than one browser tab open at once being
# the normal case (roadmap open in one, quiz in another) — two requests'
# logs can and do interleave. A short id carried through every log line let
# in one request separates from every other without threading it through
# each call site by hand.
_request_id_var = contextvars.ContextVar("request_id", default="-")


class _RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = _request_id_var.get()
        return True


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s [%(request_id)s]: %(message)s",
    handlers=[logging.StreamHandler()],
)
for _h in logging.getLogger().handlers:
    _h.addFilter(_RequestIdFilter())
log = logging.getLogger("primer.server")

# Importing this module attaches to a real reader's record. PRIMER_DB makes
# isolation the easy thing to ask for: set it and the whole process — store,
# wiki cache, backups — lands somewhere disposable.
DB_PATH = os.environ.get("PRIMER_DB") or os.path.join(ROOT, "content", "primer.db")
BACKUP_DIR = os.environ.get("PRIMER_BACKUP_DIR") or (
    os.path.join(os.path.dirname(DB_PATH), "backups")
    if os.environ.get("PRIMER_DB") else os.path.join(ROOT, "content", "backups"))
WEB_DIR = os.path.join(ROOT, "web")
STORY_PATH = os.path.join(ROOT, "data", "story", "frame.json")

app = FastAPI(title="The Primer")


def init_services(db_path: str = None):
    """(Re)build the module's service graph against one database path.

    The factory exists so isolation is structural rather than conventional:
    tests (and any embedder) call `init_services(tmp_db)` instead of knowing
    to rebind `srv.learner` and `srv.wiki` by hand. Module-level singletons
    remain — every route reads them — but they are only ever assigned here.
    """
    global wiki, learner, curr, STORY
    db_path = db_path or DB_PATH
    wiki = WikiService(db_path)
    curr = Curriculum()
    learner = LearnerStore(db_path)
    with open(STORY_PATH) as f:
        STORY = json.load(f)
    return wiki, curr, learner, STORY


wiki, curr, learner, STORY = init_services()


# ---------------- maintenance (backup + retention) ----------------

def _prune_backups(dest_dir: str):
    """Long-horizon retention: ~5 daily, 4 weekly, 12 monthly generations.

    Five same-week dailies protect against yesterday's mistake but not against
    a corruption noticed a month later — by then every surviving copy had
    inherited it. Grandfathered tiers keep the horizon long while the count
    stays small. This is still same-disk retention by default: a dead drive
    takes the backups with the record, and the off-disk answer remains the
    reader's own PRIMER_BACKUP_DIR choice (point it at removable or synced
    storage) — deliberately theirs to make, not the book's.
    """
    files = sorted((f for f in os.listdir(dest_dir)
                    if f.startswith("primer-") and f.endswith(".db")), reverse=True)
    # Newest copy per calendar day; same-day extras are pure redundancy.
    by_day = {}
    for f in files:
        by_day.setdefault(f[7:15], f)          # "YYYYMMDD" from primer-YYYYMMDD-HHMMSS.db
    days = sorted(by_day, reverse=True)
    keep = set(by_day[d] for d in days[:5])    # daily tier
    weekly, monthly = {}, {}
    for d in days[5:]:
        try:
            iso = time.strptime(d, "%Y%m%d")
        except ValueError:
            keep.add(by_day[d])                # unparseable: never delete blind
            continue
        week = "{}-{:02d}".format(*datetime.date(
            iso.tm_year, iso.tm_mon, iso.tm_mday).isocalendar()[:2])
        month = d[:6]
        # Newest day wins each bucket — days iterate newest-first, so first in.
        weekly.setdefault(week, by_day[d])
        monthly.setdefault(month, by_day[d])
    keep.update(list(weekly.values())[:4])
    keep.update(list(monthly.values())[:12])
    for f in files:
        if f not in keep:
            # Sidecar-aware: this removed only the `.db` and left the -wal/-shm
            # beside it, so every rotated-out generation leaked two files that
            # nothing would ever collect.
            _remove_backup(os.path.join(dest_dir, f))


def backup_status() -> dict:
    """Where the backups are, and whether they would survive this disk dying.

    The retention policy above is careful and the off-disk escape hatch exists,
    but PRIMER_BACKUP_DIR only helps a reader who already knows to look for it
    — which is nobody who has not read the source. So the same-disk fact is
    reported: once in the startup log, and as a field on /api/state that a UI
    can surface without asking the server anything new.

    "Off-disk" is decided by comparing filesystem device ids, not by whether
    the env var is set. Pointing PRIMER_BACKUP_DIR at another folder on the
    same drive is exactly the move that feels like safety and is not, and a
    check that congratulated it would be worse than no check.
    """
    if store.using_turso():
        return {
            "dir": None,
            "copies": 0,
            "configured_by_env": bool(os.environ.get("PRIMER_BACKUP_DIR")),
            "off_disk": True,
            "env_var": "PRIMER_BACKUP_DIR",
            "mode": "managed_remote",
            "advice": (
                "The learner record is stored remotely in Turso; local file "
                "backups do not apply. Use Turso recovery or exports for an "
                "independent copy."
            ),
        }

    dest = os.path.abspath(BACKUP_DIR)
    configured = bool(os.environ.get("PRIMER_BACKUP_DIR"))
    off_disk = None                      # unknown until both paths exist
    try:
        db_dev = os.stat(os.path.dirname(os.path.abspath(DB_PATH)) or ".").st_dev
        probe = dest if os.path.isdir(dest) else (os.path.dirname(dest) or ".")
        off_disk = os.stat(probe).st_dev != db_dev
    except OSError:
        pass
    try:
        copies = len([f for f in os.listdir(dest)
                      if f.startswith("primer-") and f.endswith(".db")])
    except OSError:
        copies = 0
    return {
        "dir": dest,
        "copies": copies,
        "configured_by_env": configured,
        "off_disk": off_disk,
        "env_var": "PRIMER_BACKUP_DIR",
        "mode": "local_file",
        # Plain sentence, written once, so the log line, the API and any UI
        # that renders it all say the same thing.
        "advice": (
            "Backups are on the same drive as the learner record — a failed "
            "drive loses both. Set PRIMER_BACKUP_DIR to a path on removable "
            "or synced storage to keep a copy off this disk."
            if off_disk is False else
            "Backups are on a different drive from the learner record."
            if off_disk else
            "Backup location could not be checked against the record's drive."
        ),
    }


_shutdown = threading.Event()


def _run_maintenance_once():
    """Run one retention pass, using only operations the backend supports."""
    if learner.get_profile() is None:
        return
    dest = None
    if not store.using_turso():
        # Retention is ours, not the store's flat "newest N": pass a keep the
        # rotation can never hit, then apply the tiered policy in
        # _prune_backups. Remote Turso databases cannot use sqlite's local
        # online-backup API.
        dest = learner.backup(BACKUP_DIR, keep=10 ** 6)
        if os.path.isdir(BACKUP_DIR):
            _prune_backups(BACKUP_DIR)
    learner.prune()
    if dest:
        log.info("backed up learner record to %s", os.path.basename(dest))


def _maintenance_loop():
    """Back up the irreplaceable learner record and prune old logs — at
    startup and then daily. The whole multi-year history lives in one file."""
    while True:
        try:
            _run_maintenance_once()
        except Exception as exc:  # never let maintenance crash the app
            log.warning("maintenance failed: %s", exc)
        # Wait on an Event rather than sleeping: a bare sleep(24h) cannot be
        # interrupted at shutdown, and a laptop suspended overnight wakes with
        # the timer still counting down the hours it slept through, silently
        # skipping a backup day. Waking hourly and checking the clock means a
        # missed day is noticed as soon as the machine is awake again.
        target = time.time() + 24 * 3600
        while not _shutdown.is_set() and time.time() < target:
            if _shutdown.wait(min(3600.0, max(1.0, target - time.time()))):
                return


@asynccontextmanager
async def _lifespan(_app):
    # First-run nudge. Logged at startup rather than on the first backup so a
    # reader who has not onboarded yet — the one who can still choose where the
    # record will live — sees it too. WARNING when same-disk: this is the one
    # thing in the maintenance story that the book cannot fix for them.
    bk = backup_status()
    if bk["mode"] == "managed_remote":
        log.info("learner record -> Turso | %s", bk["advice"])
    else:
        (log.warning if bk["off_disk"] is False else log.info)(
            "backups -> %s (%d kept) | %s",
            bk["dir"], bk["copies"], bk["advice"])
    threading.Thread(target=_maintenance_loop, daemon=True).start()
    yield
    # Let the maintenance thread finish its wait and return rather than being
    # killed mid-backup when the process exits.
    _shutdown.set()


app.router.lifespan_context = _lifespan


# The data model is deliberately one-reader: every table belongs to profile
# id 1. A local process is private by topology, but a hosted deployment is not.
# Vercel Authentication does not cover production aliases on every plan, so a
# small application-level boundary protects both the HTML and every API route.
# Health remains public for deployment monitoring and contains no reader data.
ACCESS_PASSWORD_ENV = "PRIMER_ACCESS_PASSWORD"
ACCESS_USERNAME_ENV = "PRIMER_ACCESS_USERNAME"


ACCESS_COOKIE = "primer_access"
ACCESS_MAX_AGE = 60 * 60 * 24 * 30       # a month of reading between sign-ins
SIGN_IN_PATH = "/sign-in"
PUBLIC_ASSET_PATHS = frozenset({
    "/app/apple-touch-icon.png",
    "/app/favicon-32x32.png",
    "/app/favicon.ico",
    "/app/icon-192.png",
    "/app/icon-512.png",
    "/app/icon-1024.png",
    "/app/manifest.webmanifest",
})


def _access_token(username: str, password: str) -> str:
    """The cookie's value: an HMAC over the username, keyed by the password.

    No new secret to configure, and no session table to keep — changing
    PRIMER_ACCESS_PASSWORD invalidates every cookie ever issued, which is
    exactly what changing the password should mean.
    """
    return hmac.new(password.encode("utf-8"),
                    b"primer-access-v1:" + username.encode("utf-8"),
                    hashlib.sha256).hexdigest()


def _safe_next(raw: Optional[str]) -> str:
    """Only ever bounce back to a path on this same book.

    A `next` that starts with `//` or carries a scheme is an open redirect
    dressed as a convenience, and control characters are header smuggling.
    """
    if not raw or not raw.startswith("/") or raw.startswith("//"):
        return "/"
    if len(raw) > 512:
        return "/"
    # Rebuilt character by character from an allowlist, and REFUSED — not
    # laundered — if anything was lost in the rebuild: a target that arrives
    # carrying a quote, an angle bracket, a CR/LF or a backslash is an attack
    # to send home with "/", not an address to tidy up and honour. What is
    # returned on success is the constructed copy, not the input, so the value
    # provably contains nothing but path characters in every context it is
    # later pasted into (the hidden form field, the Location header) — and no
    # analyser has to take html.escape on faith.
    kept = "".join(c for c in raw[1:]
                   if c.isalnum() or c in "/?=&#%-._~+,@")
    if kept != raw[1:] or kept.startswith("/"):
        return "/"
    return "/" + kept


def _wants_html(request) -> bool:
    """A person navigating, as opposed to the app's own fetch() calls."""
    return "text/html" in request.headers.get("accept", "")


def _no_store(headers: Optional[dict] = None) -> dict:
    out = {
        "Cache-Control": "no-store",
        "Content-Security-Policy": CSP,
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "Vary": "Authorization, Cookie",
    }
    out.update(headers or {})
    return out


def _access_challenge(status_code: int = 401) -> JSONResponse:
    """The answer for a request that is not a person: the app's own fetch().

    Deliberately no WWW-Authenticate. That header is what made the browser
    draw its own grey credential box over the book — a dialog no stylesheet
    can reach, naming a host and a port to a reader who came for a book.
    People are sent to /sign-in instead; scripts still get honest JSON, and
    a Basic header is still accepted for curl and CI.
    """
    detail = ("Authentication required" if status_code == 401
              else "Hosted access is not configured")
    return JSONResponse({"detail": detail}, status_code=status_code,
                        headers=_no_store())


# Second line of defence behind the HTML sanitizer: even if untrusted article
# markup ever slipped through, it could not load or run code. Applied as
# middleware so it covers every route — including the static mount, which would
# otherwise serve an identical, unprotected copy of the app shell.
CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
    "base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
)


@app.middleware("http")
async def _hosted_access_guard(request, call_next):
    """Keep the single-reader store private whenever the app is hosted.

    Local installs need no password. A Vercel deployment fails closed when its
    password is missing, preventing a configuration mistake from silently
    publishing the shared profile and cost-bearing tutor endpoints.
    """
    # Starlette builds ``request.url`` from the untrusted Host header.  On
    # affected releases, a Host value containing a path can make
    # ``request.url.path`` differ from the path that ASGI actually routed.
    # Authorisation exemptions must therefore use the raw ASGI scope path.
    path = request.scope.get("path")
    # Health monitoring and inert brand/install assets disclose no reader data.
    # Keep the allowlist exact: the rest of /app contains the private client.
    if path == "/healthz" or path in PUBLIC_ASSET_PATHS:
        return await call_next(request)

    password = os.environ.get(ACCESS_PASSWORD_ENV)
    hosted = bool(os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"))
    if not password:
        return _access_challenge(503) if hosted else await call_next(request)

    username = os.environ.get(ACCESS_USERNAME_ENV) or "primer"
    if _is_signed_in(request, username, password):
        response = await call_next(request)
        response.headers.setdefault("Vary", "Authorization, Cookie")
        return response
    # The sign-in page is the one door that must open while locked out.
    if path == SIGN_IN_PATH:
        return await call_next(request)
    if _wants_html(request) and request.method == "GET":
        # Carry the whole target across, query and all: a reader deep-linked to
        # #atlas or /api-less path should land back where they were aiming.
        query = (request.scope.get("query_string") or b"").decode("latin-1")
        wanted = path + ("?" + query if query else "")
        target = SIGN_IN_PATH + "?next=" + urllib.parse.quote(
            _safe_next(wanted), safe="/")
        return RedirectResponse(target, status_code=303, headers=_no_store())
    return _access_challenge()


def _is_signed_in(request, username: str, password: str) -> bool:
    """Either the cookie the sign-in page set, or a Basic header.

    Basic stays accepted — unadvertised — because the deployment's own health
    checks, curl and CI authenticate that way and should not have to hold a
    cookie jar to do it.
    """
    expected_token = _access_token(username, password)
    cookie = request.cookies.get(ACCESS_COOKIE, "")
    if cookie and secrets.compare_digest(cookie, expected_token):
        return True
    try:
        scheme, encoded = request.headers.get("Authorization", "").split(" ", 1)
        if scheme.lower() != "basic" or len(encoded) > 8192:
            raise ValueError
        supplied_user, supplied_password = base64.b64decode(
            encoded, validate=True).split(b":", 1)
        expected_user = username.encode("utf-8")
        expected_password = password.encode("utf-8")
    except (ValueError, UnicodeEncodeError, binascii.Error):
        return False
    return (secrets.compare_digest(supplied_user, expected_user)
            and secrets.compare_digest(supplied_password, expected_password))


# ---------------- google identity (inner layer) ----------------

# The password gate above is the outer door: it protects the hosted URL from
# strangers finding it at all, and asks nothing of a young reader opening the
# book on the family's own machine. Google sign-in is an inner layer that
# decides *whose* profile is behind that door once inside. Every route below
# still runs unauthenticated-by-Google by default — no cookie resolves to
# reader_id=1, the one profile every database had before this feature
# existed — so nothing about the single-tenant flow, or the tests written
# against it, requires a Google account to keep working exactly as before.
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

READER_COOKIE = "primer_reader"
READER_MAX_AGE = 60 * 60 * 24 * 180      # half a year between Google sign-ins
_OAUTH_STATE_COOKIE = "primer_oauth_state"
_OAUTH_STATE_MAX_AGE = 600               # the round trip to Google and back


def current_reader(request: Request) -> int:
    """The reader whose profile this request reads and writes.

    No session cookie — today's default, and every caller that predates
    Google sign-in — resolves to reader_id=1. A cookie that no longer matches
    a live session (expired, signed out) falls back the same way rather than
    erroring: losing the Google session should read as "not signed in", never
    as a broken app.
    """
    token = request.cookies.get(READER_COOKIE, "")
    if not token:
        return 1
    reader_id = learner.reader_for_session(token)
    return reader_id if reader_id is not None else 1


def _set_reader_cookie(response, token: str):
    response.set_cookie(
        READER_COOKIE, token, max_age=READER_MAX_AGE, httponly=True,
        samesite="lax",
        secure=bool(os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV")),
        path="/")
    return response


class _HttpxAuthTransport:
    """The google.auth.transport.Request shape, over the httpx this book
    already depends on elsewhere — sparing a second HTTP client (`requests`,
    the default transport's own dependency) for the one certificate fetch
    signature verification needs.
    """

    def __call__(self, url, method="GET", body=None, headers=None,
                 timeout=None, **kwargs):
        resp = httpx.request(method, url, content=body, headers=headers,
                             timeout=timeout or 10.0)
        return _HttpxAuthResponse(resp)


class _HttpxAuthResponse:
    def __init__(self, resp):
        self.status = resp.status_code
        self.data = resp.content
        self.headers = resp.headers


def _verify_google_id_token(raw: str) -> dict:
    """Verify a Google ID token's signature, issuer, audience and expiry.

    Raises on anything wrong. An unverified token is not an identity, and the
    only safe response to a bad one is to refuse the sign-in — never to fall
    back to trusting its claims unchecked.
    """
    return google_id_token.verify_oauth2_token(
        raw, _HttpxAuthTransport(), GOOGLE_CLIENT_ID)


def _google_redirect_uri(request: Request) -> str:
    """Built from the request rather than a fixed env var, so one client id
    serves both local dev and the hosted deployment — Google just needs every
    value this can produce pre-registered on the OAuth client. TLS is decided
    the same way the access cookie's Secure flag is (env, not request scheme):
    Vercel terminates TLS in front of the app, so the request the app sees is
    plain http even when the reader's browser spoke https to Vercel.
    """
    hosted = bool(os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"))
    scheme = "https" if hosted else request.url.scheme
    host = request.headers.get("host") or request.url.netloc
    return "{}://{}/auth/google/callback".format(scheme, host)


@app.get("/auth/google/start")
def google_start(request: Request, next: str = "/"):
    if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET):
        return JSONResponse({"error": "Google sign-in is not configured"},
                            status_code=503, headers=_no_store())
    state = secrets.token_urlsafe(24)
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": _google_redirect_uri(request),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
    }
    url = GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(params)
    response = RedirectResponse(url, status_code=303, headers=_no_store())
    # State and the return path travel together in one short-lived cookie —
    # the callback has nothing else linking it back to this specific request.
    # _safe_next() guarantees a safe PATH (no scheme, no CR/LF); a cookie
    # value has its own, stricter grammar (RFC 6265 cookie-octet excludes
    # the comma that a path may legally contain), so the path is
    # percent-encoded before it rides in the cookie rather than trusted to
    # already be cookie-safe — CodeQL flags exactly this class of gap.
    response.set_cookie(
        _OAUTH_STATE_COOKIE,
        state + "|" + urllib.parse.quote(_safe_next(next), safe=""),
        max_age=_OAUTH_STATE_MAX_AGE, httponly=True, samesite="lax",
        secure=bool(os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV")),
        path="/auth/google")
    return response


@app.get("/auth/google/callback")
async def google_callback(request: Request, code: str = "", state: str = "",
                          error: str = ""):
    cookie_val = request.cookies.get(_OAUTH_STATE_COOKIE, "")
    expected_state, _, next_encoded = cookie_val.partition("|")
    try:
        next_path = urllib.parse.unquote(next_encoded, errors="strict")
    except (UnicodeDecodeError, ValueError):
        next_path = "/"
    # Decoded, then re-validated — the cookie is the book's own and the
    # encoding round-trips cleanly, but this is the one call that turns the
    # value into a redirect target, and that call trusts nothing it has not
    # just checked itself.
    next_path = _safe_next(next_path or "/")
    response = RedirectResponse(next_path, status_code=303, headers=_no_store())
    response.delete_cookie(_OAUTH_STATE_COOKIE, path="/auth/google")
    state_ok = bool(state and expected_state
                    and secrets.compare_digest(state, expected_state))
    if error or not code or not state_ok:
        log.warning("google sign-in refused: error=%r state_ok=%s", error, state_ok)
        return response
    if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET):
        return response
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            token_resp = await client.post(GOOGLE_TOKEN_URL, data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": _google_redirect_uri(request),
                "grant_type": "authorization_code",
            })
        token_resp.raise_for_status()
        claims = _verify_google_id_token(token_resp.json()["id_token"])
    except Exception as exc:
        log.warning("google sign-in token exchange failed: %s: %s",
                    exc.__class__.__name__, exc)
        return response
    google_sub = claims.get("sub")
    if not google_sub:
        return response
    reader_id = learner.upsert_google_reader(
        google_sub, claims.get("email", ""),
        claims.get("name") or claims.get("given_name") or "")
    session_token = learner.create_session(reader_id)
    log.info("google sign-in: reader_id=%s", reader_id)
    return _set_reader_cookie(response, session_token)


@app.post("/api/account/sign-out")
def google_sign_out(request: Request):
    token = request.cookies.get(READER_COOKIE, "")
    if token:
        learner.delete_session(token)
    response = JSONResponse({"signed_out": True}, headers=_no_store())
    response.delete_cookie(READER_COOKIE, path="/")
    return response


@app.get("/api/account")
def account(request: Request):
    reader_id = current_reader(request)
    reader = learner.get_reader(reader_id)
    legacy = reader if reader_id == 1 else learner.get_reader(1)
    return {
        "reader_id": reader_id,
        "signed_in": bool(reader and reader.get("google_sub")),
        "email": (reader or {}).get("email") or None,
        "name": (reader or {}).get("name") or None,
        # Offered only to a reader who has actually signed in with Google
        # AND whose sign-in is not already the one behind reader_id=1 —
        # reader_id=1 unclaimed is the one thing that makes the button do
        # something.
        "claimable": bool(
            reader_id != 1 and reader and reader.get("google_sub")
            and legacy and not legacy.get("google_sub")),
    }


class ClaimIn(BaseModel):
    password: str = Field(..., max_length=1024)


@app.post("/api/account/claim")
def claim_profile(body: ClaimIn, request: Request):
    """Re-entering the access password proves possession, one way, only while
    reader_id=1 is unclaimed — not a new secret, since anyone reaching this
    screen already passed the same password gate to get in at all."""
    reader_id = current_reader(request)
    if reader_id == 1:
        return JSONResponse({"error": "you are already reading this profile"},
                            status_code=409)
    password = os.environ.get(ACCESS_PASSWORD_ENV)
    if not password:
        return JSONResponse({"error": "claiming is not available"}, status_code=503)
    if not secrets.compare_digest(body.password.encode("utf-8"), password.encode("utf-8")):
        return JSONResponse({"error": "that is not the word this copy knows"},
                            status_code=401)
    reader = learner.get_reader(reader_id)
    if not reader or not reader.get("google_sub"):
        return JSONResponse({"error": "sign in with Google first"}, status_code=400)
    claimed = learner.claim_legacy_reader(
        reader_id, reader["google_sub"], reader.get("email", ""), reader.get("name", ""))
    if not claimed:
        return JSONResponse({"error": "this profile has already been claimed"},
                            status_code=409)
    # The claim just moved this identity's row to reader_id=1; the live
    # session must follow it, or the reader lands right back on the empty
    # profile they were trying to leave.
    old_token = request.cookies.get(READER_COOKIE, "")
    if old_token:
        learner.delete_session(old_token)
    new_token = learner.create_session(1)
    return _set_reader_cookie(JSONResponse({"claimed": True}), new_token)


@app.middleware("http")
async def _request_id(request, call_next):
    rid = uuid.uuid4().hex[:8]
    token = _request_id_var.set(rid)
    started = time.monotonic()
    try:
        response = await call_next(request)
        # Logged before the reset below so this line, like every log call a
        # route handler makes during the request, carries the same id.
        log.info("%s %s -> %d (%.0fms)", request.method, request.url.path,
                  response.status_code, (time.monotonic() - started) * 1000)
        response.headers["X-Request-Id"] = rid
        return response
    finally:
        _request_id_var.reset(token)


# A browser tells the server where a request came from, and the book had never
# looked. Every state-changing route is a plain same-site call with no token,
# which is exactly right for a local book — and means any page the reader has
# open in another tab could drive this API through their own browser: read the
# whole profile from GET /api/state, re-open a settled placement through
# GET /api/placement/next?recheck=true, write reading history, spend quiz
# items. On a machine bound to 127.0.0.1 the classic route in is DNS
# rebinding; on the hosted copy it is an ordinary cross-origin page.
#
# `Sec-Fetch-Site` closes the class in one place, which is why it is preferred
# here over patching individual routes: fixing the reading-log write on one
# GET leaves every other state-changing GET exactly as it was.
#
# Only `same-origin` and `none` (a typed URL, a bookmark) are the book talking
# to itself. `cross-site` is obvious; `same-site` is refused too, because for
# a book served from 127.0.0.1 another port on the same host is somebody else.
# An ABSENT header is allowed: curl, the test client, and older browsers send
# nothing, and a guard that cannot tell those from an attacker must not
# pretend it can — this raises the floor for real browsers rather than
# claiming an authentication story the book does not have.
_SAME_ORIGIN_FETCH_SITES = {"same-origin", "none"}


@app.middleware("http")
async def _cross_origin_guard(request, call_next):
    site = (request.headers.get("sec-fetch-site") or "").lower()
    if site and site not in _SAME_ORIGIN_FETCH_SITES and request.url.path.startswith("/api/"):
        log.warning("refused %s request to %s from another origin",
                    site, request.url.path)
        return JSONResponse(
            {"error": "this book answers only to its own pages"}, status_code=403)
    return await call_next(request)


@app.middleware("http")
async def _security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("Content-Security-Policy", CSP)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    return response


# ---------------- helpers ----------------

# Fields of a curriculum node that must never leave the server. `quiz` carries
# every `answer` and `explain` in the bank.
_NODE_PRIVATE = ("quiz",)
_NODE_DETAIL_ONLY = ("lesson_media",)


def _public_node(node: dict, include_detail: bool = False) -> dict:
    """A node as the reader may see it. Anything that serialises a node goes
    through here — stripping the bank route by route is how keys leak. Large
    lesson plates and model copy travel only with the one opened lesson, not
    every Today card."""
    hidden = _NODE_PRIVATE if include_detail else _NODE_PRIVATE + _NODE_DETAIL_ONLY
    out = {k: v for k, v in node.items() if k not in hidden}
    out["question_count"] = len(node.get("quiz") or [])
    return out


def _check_ascension(prof: dict, reader_id: int) -> Optional[dict]:
    """If the reader has newly opened a higher stage in any domain, record a
    stage-ascension ceremony and return it once."""
    gates = learner.gate_map(reader_id=reader_id)
    # The reader's level is the lower median over the domains they CHOSE —
    # one strong domain cannot promote them, and domains they never opted
    # into are not evidence against them.
    domains = prof.get("domains") or [d["id"] for d in curr.domains]
    per_domain = sorted(curr.domain_stage_estimate(d, gates) for d in domains)
    rank = per_domain[(len(per_domain) - 1) // 2] if per_domain else 0
    prev = int(prof.get("settings", {}).get("rank", prof.get("stage", 0)))
    if rank > prev:
        settings = dict(prof.get("settings", {}))
        settings["rank"] = rank
        # Actually promote the reader: the ceremony announced a new stage, so
        # the sidebar, the UI mode and the story window must all move with it.
        learner.save_profile(prof["name"], prof["age"], prof["hours_per_week"],
                             prof["breadth"], max(int(prof["stage"] or 0), rank),
                             prof["domains"], settings, reader_id=reader_id)
        info = {"stage": rank, "name": STAGE_NAMES[min(rank, 5)],
                "title": STAGE_TITLES[min(rank, 5)]}
        learner.log_event("ascension", info, reader_id=reader_id)
        return info
    return None


def _book_title(name: str) -> str:
    return story_mod.book_title(STORY, name)


def _personalize(chapter: dict, name: str,
                 pronouns: str = story_mod.DEFAULT_PRONOUNS) -> dict:
    return story_mod.personalize(chapter, name, pronouns)


def _story_cursor(prof: dict, reader_id: int, commit: bool = False):
    """The reader's chapter, whether it may turn, and what it wants — see
    primer.story for the cursor's invariants. commit=True only from a write
    endpoint: a GET must not persist."""
    return story_mod.cursor(STORY, curr, learner, prof, reader_id, commit)


def _story_needs(chapter: Optional[dict], reader_id: int) -> Optional[dict]:
    return story_mod.needs(curr, learner, chapter, reader_id)


# ---------------- profile & onboarding ----------------

class ProfileIn(BaseModel):
    # stage_for_age clamps the derived stage, but the raw numbers are written
    # to the profile as given: an age of -4 or 900 hours a week would be
    # persisted and then shown back to the reader as fact. Bound them at the
    # door, where the bad value is still just a request.
    name: str = Field("Reader", min_length=1, max_length=60)
    # 3 is the youngest reader the stage-0 material is written for; 120 is the
    # far side of plausible. The onboarding slider offers exactly this range.
    age: float = Field(8, ge=3, le=120)
    hours_per_week: float = Field(6, gt=0, le=80)
    # `breadth` was a free string written straight to the profile and read back
    # by the pacing code, which understands exactly these three words: anything
    # else was persisted verbatim and then silently treated as "balanced".
    breadth: Literal["focused", "balanced", "polymath"] = "balanced"
    # A name never tells you someone's pronouns, so the story does not guess:
    # the neutral set is the default, and the reader says otherwise if they
    # wish. Rendered by primer.story.personalize into every chapter.
    pronouns: Literal["she", "he"] = story_mod.DEFAULT_PRONOUNS
    domains: List[str] = []

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("a name cannot be only spaces")
        return v


def _profile_view(prof: Optional[dict]) -> Optional[dict]:
    """The profile as the client sees it.

    `pronouns` is stored in settings but lifted to the top level here: it is a
    fact about the reader that the story renders with, not a UI preference the
    client can take or leave, and every client reads the profile — not the
    settings blob — to find out who the reader is.
    """
    if not prof:
        return prof
    out = dict(prof)
    out["pronouns"] = story_mod.reader_pronouns(prof)
    # Renders-with versus chose: a reader carrying a retired set, or none at
    # all, is rendered with the fallback but must still be asked. Without this
    # the client cannot tell a deliberate "she" from a defaulted one.
    out["pronouns_set"] = story_mod.pronouns_are_set(prof)
    return out


@app.get("/api/state")
def state(request: Request):
    reader_id = current_reader(request)
    profile = _profile_view(learner.get_profile(reader_id=reader_id))
    lib = wiki.library_status()
    tutor_remote = tutor.have_api_key() and _tutor_remote_allowed(profile)
    return {
        "profile": profile,
        "onboarded": profile is not None,
        "library": lib,
        "tutor_engine": "claude" if tutor_remote else "book",
        # Machine-readable disclosure: when true, tutor messages and article
        # excerpts leave this machine for api.anthropic.com. The UI shows it;
        # the flag also rides on every /api/tutor reply (see tutor.ask). The
        # reader can turn it off in-app via the tutor_remote_ok setting.
        "tutor_remote": tutor_remote,
        # Where the record is copied to, and whether those copies would
        # survive this drive failing. Carried on the state every client
        # already fetches so surfacing it costs the UI one field, not a round
        # trip — see backup_status() for why off_disk is a device comparison.
        "backup": backup_status(),
        "stages": [{"i": i, "name": STAGE_NAMES[i], "span": STAGE_SPAN[i],
                    "title": STAGE_TITLES[i]} for i in range(6)],
        "domains": curr.domains,
    }


@app.post("/api/profile")
def save_profile(p: ProfileIn, request: Request):
    reader_id = current_reader(request)
    existing = learner.get_profile(reader_id=reader_id)
    # A new reader starts at the beginning. Age says how old they are, not what
    # they have been taught: placement is what moves stage above zero. Re-saving
    # an existing profile, however, is an edit to name/age/domains — it must not
    # erase the stage that placement and later progress already established.
    stage = existing["stage"] if existing else 0
    # Pronouns live in settings (that is where reader preferences live), so
    # they have to be merged rather than passed positionally — and merged onto
    # the existing settings, or re-saving a profile would wipe the reader's
    # theme and story position along with them.
    settings = dict((existing or {}).get("settings") or {})
    settings["pronouns"] = p.pronouns
    learner.save_profile(p.name, p.age, p.hours_per_week, p.breadth, stage,
                         p.domains, settings, reader_id=reader_id)
    # No assumed credit is seeded here any more, for the same reason: nothing
    # has been measured yet. Placement seeds it (see _settle), where there is
    # evidence behind it.
    log.info("profile saved: %s age=%s stage=%s breadth=%s", p.name, p.age, stage, p.breadth)
    return _profile_view(learner.get_profile(reader_id=reader_id))


# Only the reader's own preferences are writable here — `placed`, `rank` and
# `story_progress` are the book's record of what happened, never client input,
# and no field is accepted that nothing reads back. Typed values; extras are
# tolerated at the parse step (extra="allow") only so they can be refused by
# name in the response — a bare 422 would hide *which* key was the problem.
class SettingsIn(BaseModel):
    model_config = {"extra": "allow"}
    # Bounded like every other client-writable string in this file
    # (ProfileIn.name 60, TutorIn.title 300, CheckIn.answer 2000). These
    # three were the only ones without a ceiling, and they are persisted
    # into the profile, so an 8 MB string was an 8 MB row for ever.
    theme: Optional[str] = Field(None, max_length=40)
    speak: Optional[bool] = None
    reduce_motion: Optional[bool] = None
    font_scale: Optional[float] = None
    name_pronunciation: Optional[str] = Field(None, max_length=120)
    # Reader-owned privacy switch: False keeps the tutor fully local even
    # when an ANTHROPIC_API_KEY is set (see _tutor_remote_allowed).
    tutor_remote_ok: Optional[bool] = None
    # Changeable after onboarding: a reader who was mis-set, or who changes
    # how they are addressed, must not have to rebuild their profile to fix
    # the story's pronouns.
    pronouns: Optional[Literal["she", "he"]] = None
    # Per-domain override of the reader's effective level, keyed by domain
    # id. `profile.stage` remains the fallback for any domain not present
    # here, and the only value story.py and pacing.py ever fall back to when
    # this is absent entirely — see _display_stage / roadmap()'s per-domain
    # weighting.
    domain_stage: Optional[Dict[str, int]] = None

    @field_validator("domain_stage")
    @classmethod
    def _domain_stage_in_range(cls, v):
        if v is None:
            return v
        if any(not (0 <= s <= 5) for s in v.values()):
            raise ValueError("each domain's stage must be 0..5, matching STAGE_NAMES")
        # Keys are checked against the real fields, which bounds this far better
        # than a length cap would: a cap on the number of keys still admits
        # thirty-two keys of a megabyte each, whereas a domain id is a domain id.
        known = {d["id"] for d in curr.domains}
        unknown = sorted(k for k in v if k not in known)
        if unknown:
            raise ValueError("no such field: %s" % ", ".join(unknown[:3]))
        return v


READER_SETTINGS = set(SettingsIn.model_fields)


@app.post("/api/profile/settings")
def save_settings(settings: SettingsIn, request: Request):
    reader_id = current_reader(request)
    prof = learner.get_profile(reader_id=reader_id)
    if not prof:
        return JSONResponse({"error": "no profile"}, status_code=400)
    rejected = sorted((settings.model_extra or {}).keys())
    if rejected:
        log.warning("refused client write to server-owned settings: %s", rejected)
    merged = dict(prof.get("settings", {}))
    merged.update({k: getattr(settings, k) for k in settings.model_fields_set
                   if k in READER_SETTINGS})
    saved = learner.save_profile(prof["name"], prof["age"], prof["hours_per_week"],
                                 prof["breadth"], prof["stage"], prof["domains"], merged,
                                 reader_id=reader_id)
    saved = _profile_view(saved)
    if rejected:
        saved = dict(saved)
        saved["refused"] = rejected
    return saved


# ---------------- articles & search ----------------

@app.get("/api/article")
def article(request: Request, title: str, simple: Optional[bool] = None,
           log_read: bool = True):
    reader_id = current_reader(request)
    prof = learner.get_profile(reader_id=reader_id)
    stage = None
    if prof:
        domain = curr.domain_for_article(title)
        domain_stage = (prof.get("settings") or {}).get("domain_stage") or {}
        stage = domain_stage.get(domain, prof["stage"]) if domain else prof["stage"]
    prefer_simple = simple if simple is not None else (stage is not None and stage <= 1)
    art = wiki.get_article(title, prefer_simple=bool(prefer_simple))
    if not art:
        return JSONResponse({"error": "not found", "title": title}, status_code=404)
    art["rendered"] = rewrite_article(art["html"], art.get("base", ""))
    del art["html"]
    if log_read:
        learner.log_reading(art["title"], reader_id=reader_id)
    return art


@app.get("/api/summary")
def summary(title: str):
    s = wiki.get_summary(title)
    if not s:
        return JSONResponse({"error": "not found"}, status_code=404)
    return s


@app.get("/api/search")
def search(q: str, limit: int = 14, live: bool = False):
    """`live=true` is sent only when the reader submits, not on every keystroke."""
    return {"query": q, "results": wiki.search(q, limit, live=live)}


@app.get("/api/random")
def random_article():
    return {"title": wiki.random_article()}


# Only these render inline on our own origin. Notably NOT image/svg+xml:
# Wikimedia hosts user-uploaded SVGs, which are documents that can run script.
SAFE_INLINE_MIME = {
    "image/png", "image/jpeg", "image/gif", "image/webp", "image/avif",
    "image/x-icon", "image/bmp",
}
# SVG stays out of the set above on purpose: Commons hosts user-uploaded SVG,
# and an SVG is a document that can carry script. But Wikipedia also draws
# every equation as an SVG, from a different place — the MediaWiki maths
# renderer, whose output is generated from the article's own LaTeX and is not
# user-supplied markup. Excluding that too cost the reader every formula in
# every maths article: a column of broken-image boxes.
#
# So the exception is granted by SOURCE, not by type. Only this one endpoint
# path qualifies, and the response still carries `default-src 'none'; sandbox`
# with nosniff, so even a direct visit to the proxy URL cannot run a script.
_MATH_RENDER_URL = re.compile(
    r"^https://wikimedia\.org/api/rest_v1/media/math/render/svg/[0-9a-f]+$",
    re.IGNORECASE)


def _is_math_render(url: str) -> bool:
    return bool(_MATH_RENDER_URL.match((url or "").strip()))
ASSET_HEADERS = {
    "Cache-Control": "public, max-age=604800",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "default-src 'none'; sandbox",
}


def _safe_asset_response(data: bytes, mime: str, allow_svg: bool = False) -> Response:
    base = (mime or "").split(";")[0].strip().lower()
    if allow_svg and base == "image/svg+xml":
        return Response(content=data, media_type=base, headers=ASSET_HEADERS)
    if base in SAFE_INLINE_MIME:
        return Response(content=data, media_type=base, headers=ASSET_HEADERS)
    # Anything else (SVG, HTML, unknown) is never rendered inline on our origin.
    headers = dict(ASSET_HEADERS)
    headers["Content-Disposition"] = "attachment"
    return Response(content=data, media_type="application/octet-stream", headers=headers)


@app.get("/api/image")
def image(url: str):
    got = wiki.proxy_image(url)
    if not got:
        return Response(status_code=404)
    data, mime = got
    return _safe_asset_response(data, mime, allow_svg=_is_math_render(url))


@app.get("/zim/{archive_id}/{path:path}")
def zim_asset(archive_id: str, path: str):
    arc = wiki.archive_by_id(archive_id)
    if not arc:
        return Response(status_code=404)
    got = arc.get_entry_raw(path)
    if not got:
        return Response(status_code=404)
    data, mime = got
    base = (mime or "").split(";")[0].strip().lower()
    if base in ("text/css",):  # ZIM stylesheets are safe and needed for layout
        return Response(content=data, media_type=base, headers=ASSET_HEADERS)
    return _safe_asset_response(data, mime)


# ---------------- curriculum ----------------

@app.get("/api/curriculum")
def curriculum(request: Request):
    reader_id = current_reader(request)
    graph = curr.annotated_graph(learner.gate_map(reader_id=reader_id))
    proven = learner.proven_set(reader_id=reader_id)
    ever = learner.ever_proven_set(reader_id=reader_id)
    credited = learner.credited_set(reader_id=reader_id)
    stale = learner.assumed_stale_set(reader_id=reader_id)
    for n in graph["nodes"]:
        nid = n["id"]
        n["proven"] = nid in proven
        n["ever_proven"] = nid in ever
        # `assumed` means credited without ever being earned — age placement or a
        # placement check. A node the reader genuinely proved and has since let
        # fade is `faded`, and saying "assumed" about it erased the difference
        # between work they did and a guess about how old they are.
        n["faded"] = n["ever_proven"] and not n["proven"]
        # Read from `credited` rather than `mastered`: the latter is freshness-
        # gated, so expired placement credit stopped being *any* of the four
        # words instead of becoming the fifth one. `assumed_stale` is what the
        # book says out loud when it re-locks a lesson the reader was placed
        # past — "your placement credit has expired", not silence.
        n["assumed"] = nid in credited and not n["proven"] and not n["ever_proven"]
        n["assumed_stale"] = nid in stale
    return graph


@app.get("/api/curriculum/mathematics/illustrations")
def mathematics_illustrations():
    """The complete, deliberately small catalogue behind the image dashboard.

    Lesson detail is intentionally not reused here: a node contains its quiz
    bank, reading list and interactive-model instructions as well as its plate.
    Projecting an explicit record keeps this browse-all surface useful without
    turning it into a second, much larger curriculum graph (or another place an
    answer key could escape).
    """
    ranked = []
    for authored_order, node in enumerate(curr.nodes.values()):
        if node["domain"] != "math":
            continue
        plates = [entry for entry in node.get("lesson_media", [])
                  if entry.get("kind") == "illustration"]
        # The dashboard promises one explanatory plate for every mathematics
        # lesson.  Failing closed makes a future missing or duplicate plate a
        # content error, not a quietly misleading coverage number.
        if len(plates) != 1:
            raise RuntimeError("{} has {} mathematics illustrations; expected 1".format(
                node["id"], len(plates)))
        plate = plates[0]
        ranked.append((node["stage"], authored_order, {
            "lesson_id": node["id"],
            "title": node["title"],
            "stage": node["stage"],
            "stage_name": STAGE_NAMES[node["stage"]],
            "goal": node["goal"],
            "media_id": plate["id"],
            "src": plate["src"],
            "srcset": plate["srcset"],
            "alt": plate["alt"],
            "caption": plate["caption"],
            "width": plate["width"],
            "height": plate["height"],
        }))
    illustrations = [record for _, _, record in sorted(
        ranked, key=lambda item: (item[0], item[1]))]
    return {"domain": "math", "count": len(illustrations),
            "illustrations": illustrations}


@app.get("/api/curriculum/node/{node_id}")
def curriculum_node(node_id: str, request: Request):
    reader_id = current_reader(request)
    node = curr.node(node_id)
    if not node:
        return JSONResponse({"error": "no such node"}, status_code=404)
    gates = learner.gate_map(reader_id=reader_id)
    out = _public_node(node, include_detail=True)
    out["mastery"] = round(learner.mastery_map(reader_id=reader_id).get(node_id, 0), 2)
    out["mastered"] = node_id in learner.mastered_set(reader_id=reader_id)
    out["proven"] = node_id in learner.proven_set(reader_id=reader_id)
    out["ever_proven"] = node_id in learner.ever_proven_set(reader_id=reader_id)
    out["faded"] = out["ever_proven"] and not out["proven"]
    out["assumed"] = (node_id in learner.credited_set(reader_id=reader_id) and not out["proven"]
                      and not out["ever_proven"])
    out["assumed_stale"] = node_id in learner.assumed_stale_set(reader_id=reader_id)
    out["mastery_detail"] = learner.mastery_detail(node_id, reader_id=reader_id)
    out["unlocked"] = curr.unlocked(node, gates)
    if not out["unlocked"] and not out["mastered"]:
        out["unlock_requirements"] = curr.unlock_requirements(node, gates)
    # Two-way tissue: a lesson should say which chapter it opens.
    prof = learner.get_profile(reader_id=reader_id)
    if prof:
        cur, progress, _ = _story_cursor(prof, reader_id)
        if cur and cur.get("leads_to") == node_id:
            needs = _story_needs(cur, reader_id) or {}
            out["opens_chapter"] = {"title": cur["title"], "number": progress + 1}
            out["passes_needed"] = needs.get("passes_needed")
    cards = []
    for title in node["articles"][:6]:
        s = wiki.get_summary(title)
        cards.append({"title": title, "summary": (s or {}).get("extract", "")[:280],
                      "thumb": (s or {}).get("thumbnail", "")})
    out["article_cards"] = cards
    return out


@app.get("/api/curriculum/node/{node_id}/navigation")
def curriculum_node_navigation(node_id: str, request: Request):
    """The small, explicit projection used by the reader's lesson navigator.

    An article title cannot identify its lesson: more than a hundred readings
    belong to multiple nodes, occasionally in different fields.  The route's
    node id is authoritative, and this endpoint turns it into enough context to
    orient and navigate without shipping the full curriculum graph, lesson
    media, practice instructions, or any answer-bank material.
    """
    reader_id = current_reader(request)
    node = curr.node(node_id)
    if not node:
        return JSONResponse({"error": "no such node"}, status_code=404)
    domain = next((d for d in curr.domains if d["id"] == node["domain"]), None)
    if not domain:  # The loader guarantees this; keep the HTTP boundary total.
        return JSONResponse({"error": "no such domain"}, status_code=404)

    gates = learner.gate_map(reader_id=reader_id)
    mastered = learner.mastered_set(reader_id=reader_id)
    lessons = []
    for sibling in curr.nodes.values():
        if sibling["domain"] != node["domain"]:
            continue
        lessons.append({
            "id": sibling["id"],
            "title": sibling["title"],
            "stage": sibling["stage"],
            "stage_name": STAGE_NAMES[sibling["stage"]],
            "section": sibling.get("section", ""),
            "unlocked": curr.unlocked(sibling, gates),
            "mastered": sibling["id"] in mastered,
        })
    return {
        "domain": {"id": domain["id"], "name": domain["name"],
                   "icon": domain.get("icon", "")},
        "current": {
            "id": node["id"], "title": node["title"], "goal": node.get("goal", ""),
            "stage": node["stage"], "stage_name": STAGE_NAMES[node["stage"]],
            "section": node.get("section", ""), "articles": node.get("articles", []),
        },
        "lessons": lessons,
    }


def _shuffled(question: dict) -> dict:
    """Return a copy with its options reordered.

    Authored items are written answer-first, so serving them verbatim lets a
    test-wise reader score by always picking A. Order is randomised on every
    serve — the answer is matched by value, never by position.
    """
    q = dict(question)
    choices = list(q.get("choices") or [])
    if len(choices) > 1:
        random.shuffle(choices)
        q["choices"] = choices
    # The same reasoning reaches an order item's `items`, and it had been left
    # out. An author writes the steps down in the order they happen — that is
    # the only sane way to write them — so serving them verbatim lets the
    # reader tap left to right and score full marks without knowing the
    # sequence at all. The corpus carried no authored order items when this
    # was found, so nothing was exploitable yet; it would have become
    # exploitable with the first one written. Shuffled here rather than
    # trusted to every future author remembering to scramble by hand.
    items = list(q.get("items") or [])
    if len(items) > 1 and q.get("kind") == "order":
        shuffled = items[:]
        # An order item with two steps has a 50% chance of shuffling to itself,
        # and a fair shuffle may return the identity for any length. Reroll a
        # few times rather than shipping the answer as the starting position.
        for _ in range(8):
            random.shuffle(shuffled)
            if shuffled != items:
                break
        q["items"] = shuffled
    return q


# The sitting store lives in primer.sittings; see that module for the rules a
# sitting obeys (persistence across restarts, single use, TTL). The aliases
# keep this module's historical names, which the tests use.
_SERVED_LIMIT = sittings_mod.SERVED_LIMIT
_SERVED_TTL = sittings_mod.SERVED_TTL
# Sync endpoints run in a threadpool, so two submissions of the same paper can
# be in flight at once. Claiming a paper must be one indivisible step or the
# single-use rule holds only by luck of scheduling.
_SERVED_LOCK = threading.Lock()


def _SittingStore():
    """A sitting store bound to whatever learner store the module holds NOW —
    rebinding `learner` (init_services, tests) rebinds the sittings with it."""
    return sittings_mod.SittingStore(lambda: learner.db_path)


# Served quizzes are remembered here so scoring never trusts a client-supplied
# answer key. Bounded, short-lived, and — since a restart must not void an
# open paper — persisted alongside the rest of the learner record.
_SERVED = _SittingStore()


def _fingerprint(q: dict) -> str:
    """A stable identity for an item across servings.

    Options are shuffled at serve time and ids are per-paper, so the prompt plus
    the key is what actually identifies the question.
    """
    raw = (str(q.get("prompt", "")) + "\x00" + str(q.get("answer", ""))).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def _remember(questions: list, purpose: str, subject: str, reader_id: int) -> str:
    """Remember a served paper, bound to what it was issued for and to who it
    was issued to.

    The purpose/subject binding matters: without it a token from a trivial
    counting drill can be redeemed as a graduate-level quiz, or as a stage-5
    placement pass — a paper is only ever valid for the exact thing it was
    handed out for. The reader binding matters the same way across readers: a
    token is unguessable (128 bits), but this is the check that makes that a
    defence in depth rather than the only thing standing between one reader's
    open sitting and another's.
    """
    token = secrets.token_urlsafe(12)
    now = time.time()
    with _SERVED_LOCK:
        _SERVED[token] = {"questions": [dict(q) for q in questions], "at": now,
                          "purpose": purpose, "subject": subject, "committed": {},
                          "issued_at": now, "reader_id": reader_id}
        # Papers were only ever evicted by the size cap, so a token minted months
        # ago stayed redeemable as long as the book had been quiet. A paper is a
        # sitting, and a sitting does not last a day.
        _SERVED.sweep(now)
    return token


def _final_answers(entry: dict, submitted: list) -> list:
    """The answers that count.

    Immediate feedback teaches, but it also shows the key — so whatever the
    reader committed to at feedback time is what gets graded, no matter what
    they send at submit time. Without this, a reader (or a script) can walk the
    paper with blank answers, collect every key, and hand in a perfect sheet.
    """
    committed = entry.get("committed") or {}
    if not committed:
        return submitted
    out = list(submitted)
    for i, q in enumerate(entry["questions"]):
        if q.get("id") in committed:
            first = committed[q["id"]]["answer"]
            while len(out) <= i:
                out.append("")
            out[i] = first
    return out


def _public(questions: list) -> list:
    """The copy that goes over the wire. The answer key never leaves the book —
    otherwise the reader's device holds the marking scheme."""
    out = []
    for q in questions:
        pub = {k: v for k, v in q.items()
               if k not in ("answer", "keywords", "ephemeral", "explain")}
        out.append(pub)
    return out


def _live_paper(token: str):
    """The served paper behind this token if it is still a live sitting.

    Expiry lives here, in one place, because two entry points consult the
    same papers and only one of them used to check: `_recall` (redeeming a
    finished paper) enforced the TTL, while `/api/quiz/check` (marking one
    item mid-sitting) read `_SERVED` directly and enforced nothing. Since
    papers are only swept when a new one is minted or one is recalled, a
    quiet book let an expired paper keep marking items — revealing each
    answer and burning each missed item for a week — right up until the
    submit its sibling then refused with a 409. The sitting was lost and
    the node's bank was spent for it.

    Callers still differ in what they do next: `_recall` claims the paper
    (single use), a mid-sitting check leaves it in place.
    """
    entry = _SERVED.get(token or "")
    if entry is None:
        return None
    if time.time() - entry["at"] > _SERVED_TTL:
        _SERVED.pop(token, None)
        log.info("paper %s expired unredeemed", (token or "")[:6])
        return None
    return entry


def _recall(token: str, purpose: str, subject: str, reader_id: int):
    """The server's own copy of a served paper, or None.

    There is deliberately NO fallback to a client-supplied copy: the token is
    caller-controlled, so any fallback can be forced simply by omitting it —
    which is exactly how an earlier version of this was defeated. Tokens are
    single-use, and are only honoured for the purpose, subject and reader they
    were issued against. A paper minted before this reader check existed
    carries no "reader_id" key at all; it defaults to reader 1 rather than
    None so it stays redeemable by the one reader every such paper was ever
    actually issued to.
    """
    with _SERVED_LOCK:
        entry = _live_paper(token)
        if entry is None:
            return None
        if (entry["purpose"] != purpose or entry["subject"] != subject
                or entry.get("reader_id", 1) != reader_id):
            log.warning("token issued for %s/%s/%s redeemed as %s/%s/%s — refused",
                        entry["purpose"], entry["subject"][:40], entry.get("reader_id", 1),
                        purpose, subject[:40], reader_id)
            return None
        # The pop itself is an atomic DELETE ... RETURNING claim. The process
        # lock covers threads here; its return value is what prevents a second
        # serverless instance from walking away with the stale pre-delete read.
        claimed = _SERVED.pop(token, None)
    return claimed


# Which ordering drill suits each domain's early lessons.
_ORDER_FOR_YOUNG = {
    "math": "order-numbers",
    "language": "order-letters",
    "biology": "order-lifecycle",
    "earth": "order-time",
    "history": "order-time",
    "cs": "order-numbers",
    "physics": "order-numbers",
    "chemistry": "order-lifecycle",
    "arts": "order-time",
    "mind": "order-time",
}


def _daily_seed() -> int:
    lt = time.localtime()
    return lt.tm_year * 1000 + lt.tm_yday


# How many of today's five lessons may be ones already started. Two is the
# whole safety margin: uncapped, a reader with six half-proved lessons opens
# the book to a day made entirely of debt, which is the opposite of the point.
RESUME_MAX = 2
TODAY_LESSONS = 5
# Appointments not shown among today's five. Bounded for the same reason the
# refresh list is: this is a row of chips on a page, not a report.
PENDING_SHOWN = 6
# Mirrors learner.streak_milestone's ladder. Duplicated deliberately rather
# than imported: that function answers "did one land today", this one answers
# "which is next", and the two must be readable side by side to stay in step.
STREAK_MILESTONES = (3, 7, 30, 100, 365)

# The day's review ask, and the smaller one a returning reader meets.
REVIEW_GOAL = 12
REVIEW_GOAL_RETURNING = 5

# ---------------- how long tonight will take ----------------
# The book had never once told a reader what it was asking of them: not for a
# card, not for a quiz, not for the day. These are the numbers it uses BEFORE
# it has watched this particular reader do anything — stated here rather than
# buried, so they can be argued with, and superseded the moment there is a
# real measurement (learner.pace). The book says "about" either way, and says
# which of the two it is using.
DEFAULT_CARD_SECONDS = 25.0
DEFAULT_QUESTION_SECONDS = 55.0
# What `startQuiz` actually asks the server for. If that cap ever moves, the
# estimate moves with it or the book starts lying about its own quiz.
QUIZ_QUESTIONS = 5
# An article is the one step with no natural unit, and the reader chooses how
# deep to go. A deliberately modest figure: the step asks for one article
# read, not one article exhausted.
ARTICLE_MINUTES = 6


def _round_minutes(mins: float) -> int:
    """Minutes as a person would say them. Never zero: a step the reader has
    to actually do is never "about 0 minutes", and rounding it there would be
    the one kind of dishonesty this whole block exists to remove."""
    return max(1, int(round(mins)))


def _review_goal(deck: dict, days_away: Optional[int] = None,
                 done_today: int = 0) -> int:
    """How many cards the book asks for today.

    A module function because the quest tile and the deck itself must name the
    same number — a tile reading "of 12" over a deck that never stops is worse
    than no number at all.

    Never more than the deck actually holds: a goal above what is available is
    a task the reader cannot finish, which is precisely what `step()`'s excusal
    rule exists to prevent, and `goal == 0` is how that rule now recognises it.

    `done_today` is added back in so the ask cannot shrink under the reader as
    they work. Pricing the goal against the cards still due would re-read "five
    of twenty done" as "five of fifteen", and the day would recede exactly as
    fast as it was met.

    A reader three days away meets a smaller day. The backlog is not a debt to
    be collected on the first afternoon back.
    """
    cap = REVIEW_GOAL_RETURNING if (days_away or 0) >= 3 else REVIEW_GOAL
    return max(0, min(int(done_today) + int(deck.get("due") or 0), cap))


# Beyond this the events log has been thinned to one representative row per
# day (learner.prune), so "when were you last here" stops being a measurement.
# Unknown is the honest answer, and the ordinary greeting stands.
ABSENCE_HORIZON_DAYS = 400


def _elapsed_days(last_seen: Optional[float]) -> Optional[int]:
    """Whole local days between the reader's last visit and today, or None.

    None has one meaning and it is not "long ago": either the reader's whole
    history is today's (a first afternoon, which must never be greeted as a
    lapse) or it is older than the retention window can vouch for. Counted in
    calendar days rather than by dividing seconds, because a day is not always
    86400 seconds long and a DST transition must not invent or erase one.
    """
    if last_seen is None:
        return None
    days = _local_day(time.time()) - _local_day(last_seen)
    if days < 0 or days > ABSENCE_HORIZON_DAYS:
        return None
    return days


@app.get("/api/today")
def today(request: Request):
    """The adaptive home: a stable daily quest — review first, then new
    lessons across the reader's domains, then mixed practice."""
    reader_id = current_reader(request)
    prof = learner.get_profile(reader_id=reader_id)
    if not prof:
        return JSONResponse({"error": "no profile"}, status_code=400)
    gates = learner.gate_map(reader_id=reader_id)
    domains = prof["domains"] or [d["id"] for d in curr.domains]
    lessons = [_public_node(n) for n in curr.next_lessons(gates, domains, per_domain=1)]
    # Stable order for the day (no reshuffle on refresh), but varied day to day.
    rng = random.Random(_daily_seed() + int(prof.get("created_at", 0)))
    rng.shuffle(lessons)

    # An open loop outranks a new one. A lesson standing one earned pass short
    # of mastery already has a dated appointment — `_apply_attempt` refuses to
    # master it until the proving gap has elapsed — and until now the book
    # never mentioned it, leaving it a coin flip whether the reader met that
    # lesson again at all.
    #
    # The shuffle above runs ONCE, over the whole candidate list, and the
    # partition is read off its result. Shuffling the two halves separately
    # would make the draw sequence depend on how many lessons are pending, so
    # passing one lesson would silently re-order the rest of the day — the
    # reshuffle-on-refresh bug the seeded rng exists to prevent, wearing a
    # different hat.
    now = time.time()
    pend = {p["node_id"]: p for p in learner.pending_proofs(reader_id=reader_id)}
    for n in lessons:
        appointment = pend.get(n["id"])
        if appointment:
            n["passes"] = appointment["passes"]
            n["ready_at"] = appointment["ready_at"]
            n["resume"] = True
    resume = [n for n in lessons if n.get("resume")]
    fresh = [n for n in lessons if not n.get("resume")]
    # Ready now ahead of ready later; the seeded order holds within each group
    # because sort is stable. An elapsed ready_at is an invitation, never a
    # date the reader appears to have missed.
    resume.sort(key=lambda n: n["ready_at"] > now)
    lessons = (resume[:RESUME_MAX] + fresh)[:TODAY_LESSONS]
    shown = {n["id"] for n in lessons}
    # The appointments that did not fit. Named rather than dropped: the cap
    # protects the shape of the day, and it should not cost the reader the
    # knowledge that the work is still there and still theirs.
    # An appointment can be RE-LOCKED between sittings: one failed attempt nulls
    # `mastered_at`, gate_map caps the node at 0.79, and every dependent — and
    # the node itself, if a prereq of its own faded — closes behind it. This
    # list was built with no gate check at all, so the chip went on saying
    # "ready now" for a lesson the reader could not open, and the lesson page
    # met them with a lock. The chip stays either way (it is the reader's only
    # reminder that half-proved work is still theirs), but it now says which of
    # the two states it is in, and what stands in the way. `curr.node` can
    # return None for a retired id, which is why the title lookup guards — the
    # gate check needs the same guard rather than throwing on it.
    pending = []
    for nid, p in pend.items():
        if nid in shown:
            continue
        node = curr.node(nid)
        entry = {"id": nid, "title": (node or {}).get("title", nid),
                 "ready_at": p["ready_at"],
                 "open": bool(node) and curr.unlocked(node, gates)}
        if node is not None and not entry["open"]:
            needs = curr.unlock_requirements(node, gates)
            if needs:
                entry["blocked_by"] = needs[0]
        pending.append(entry)
        if len(pending) >= PENDING_SHOWN:
            break

    deck = learner.deck_stats(reader_id=reader_id)
    # How long the reader has been away, read before the quest is built
    # because a returning day asks for less.
    last_seen = learner.last_active_before_today(reader_id=reader_id)
    days_away = _elapsed_days(last_seen)
    reading = learner.reading_stats(reader_id=reader_id)
    refresh = learner.nodes_needing_refresh(4, reader_id=reader_id)
    refresh_titles = [{"id": nid, "title": (curr.node(nid) or {}).get("title", nid)}
                      for nid in refresh]

    # The day's quest — completion reflects work actually done today. Every
    # step is built through this one function so the excusal rule cannot
    # diverge between steps: a step with nothing available to do (empty deck,
    # exhausted frontier) is excused, never left blocking the crown.
    attempts_today = learner.attempts_today(reader_id=reader_id)

    def step(label, done_count, goal, count, hint=None):
        # `goal` is what the book asks for today; `count` stays exactly what it
        # always was — what is available — because pacing and the current
        # client read it, and this round may only add.
        #
        # `max(goal, 1)` keeps the old yes/no meaning of `done` wherever the
        # goal is zero: with nothing to do, having done nothing is not done.
        # Without it, `0 >= 0` would quietly hand the reader the crown for an
        # empty deck instead of excusing the step, which is a different claim.
        done = done_count >= max(goal, 1)
        return {"label": label, "done": done, "count": count,
                # What the day asks for and how much of it is behind them.
                "done_count": done_count, "goal": goal,
                # Excused only when the reader has not already done it AND
                # there is genuinely nothing available to do. `goal == 0` is
                # the same condition `count == 0` used to state: every goal
                # below is bounded by what is available.
                "excused": not done and goal == 0,
                "hint": hint if not done and goal == 0 else None}

    reviewed_today = learner.events_today_count("review", reader_id=reader_id)
    quest = {
        "review": step("Strengthen your memory", reviewed_today,
                       _review_goal(deck, days_away, reviewed_today), deck["due"],
                       "Deck is clear — nothing due" if deck["total"]
                       else "Pass a lesson quiz and the book will start your deck"),
        # Counted by what LANDED, not by what was sat. An attempt event is
        # written whatever the score, so a paper at 17% used to tick the day's
        # learning off and collect the crown — while the same paper earned no
        # growth, so the tile and the ledger disagreed about the same sitting.
        "learn": step("Learn something new",
                      attempts_today["landed"],
                      min(len(lessons), 1), len(lessons),
                      "You are at the frontier of every subject you chose — "
                      "add another from your profile, or review to keep it solid"),
        # No count to exhaust: an article is always available to read, so this
        # step can never be excused. `None` is not zero.
        "read": step("Read one article",
                     learner.events_today_count("read", reader_id=reader_id), 1, None),
    }
    # A paper sat that did not land is neither "not started" nor "done", and the
    # reader should be told which of the two they are in. The tile carries the
    # fact; the client turns it into a sentence and a route to the drill.
    if not quest["learn"]["done"] and attempts_today["sat"]:
        quest["learn"]["sat"] = attempts_today["sat"]
    quest_done = sum(1 for k in quest.values() if k["done"])
    quest_total = sum(1 for k in quest.values() if not k["excused"])

    # What the day costs, in minutes, priced per step. Only steps the reader
    # still has to do are counted: a day two-thirds finished should say what is
    # LEFT, which is the number a reader deciding whether to sit down needs.
    card_s = learner.pace("review", reader_id=reader_id)
    quiz_s = learner.pace("attempt", reader_id=reader_id)
    # Two independent clocks, and the label has to speak for the numbers
    # actually on the bill. A single `or` here meant six graded cards made
    # the *quiz* estimate wear the "timed from you" label — the exact
    # estimate-presented-as-measurement the label exists to prevent.
    card_measured = card_s is not None
    quiz_measured = quiz_s is not None
    card_s = card_s or DEFAULT_CARD_SECONDS
    quiz_s = quiz_s or DEFAULT_QUESTION_SECONDS
    step_minutes = {}
    for key, q in quest.items():
        if q["done"] or q["excused"]:
            step_minutes[key] = 0
            continue
        left = max(0, (q["goal"] or 0) - (q["done_count"] or 0))
        if key == "review":
            step_minutes[key] = _round_minutes(left * card_s / 60.0)
        elif key == "learn":
            step_minutes[key] = _round_minutes(QUIZ_QUESTIONS * quiz_s / 60.0)
        else:
            step_minutes[key] = ARTICLE_MINUTES
    # `measured` is true only when every kind still being priced is priced
    # from the reader's own record; `partly` says the honest middle out loud.
    flags = {"review": card_measured, "learn": quiz_measured}
    relevant = [k for k, q in quest.items()
                if not q["done"] and not q["excused"] and k in flags]
    measured = bool(relevant) and all(flags[k] for k in relevant)
    partly = (bool(relevant) and any(flags[k] for k in relevant)
              and not measured)
    # The smallest honest sitting. Which door it opens is read off what the day
    # still OWES — never off the deck alone. `"review" if deck["due"] else
    # "learn"` had no idea whether either step was still on the bill, so a
    # reader who had sat their lesson that morning and whose deck was clear was
    # offered "One lesson quiz, about 5 minutes" — a five-minute door into the
    # only room they had already left — while the one step still owed went
    # unnamed. An empty `short_kind` is a real answer: there is no smaller
    # honest sitting than what is left, and the client draws no door for it.
    # `short_cards` is the number a short sitting would ACTUALLY be, not the
    # cap: promising five when two are due is the same class of small lie as
    # rounding 0.4 GB up to "about a gigabyte".
    owed = [k for k, q in quest.items() if not q["done"] and not q["excused"]]
    short_cards = min(SHORT_DOSE_CARDS, max(0, deck["due"]))
    if "review" in owed and short_cards:
        short_kind = "review"
        short_minutes = _round_minutes(short_cards * card_s / 60.0)
    elif "learn" in owed:
        short_kind = "learn"
        short_minutes = _round_minutes(QUIZ_QUESTIONS * quiz_s / 60.0)
    else:
        # Only the article is left (or nothing is). There is no shorter version
        # of "read one article" than reading one article, so no door is drawn.
        short_kind, short_minutes = "", 0
    pace = {
        "measured": measured,
        "partly": partly,
        "card_seconds": round(card_s, 1),
        "question_seconds": round(quiz_s, 1),
        "steps": step_minutes,
        "minutes_left": sum(step_minutes.values()),
        "short_cards": short_cards,
        "short_minutes": short_minutes,
        "short_kind": short_kind,
    }

    story, progress, story_can_advance = _story_cursor(prof, reader_id, commit=True)

    best_streak = learner.best_streak_days(reader_id=reader_id)
    standing = learner.proven_count_current(reader_id=reader_id)

    # A day with a tomorrow. Every clause is something waiting, never
    # something forfeited by not returning — the reader may be five.
    streak = int(prof["streak"] or 0)
    milestone = next((m for m in STREAK_MILESTONES if m > streak), None)
    horizon = _end_of_tomorrow(now)
    ready_soon = [p["ready_at"] for p in pend.values() if p["ready_at"] < horizon]
    tomorrow = {
        "due_tomorrow": deck.get("due_tomorrow", 0),
        "next_due": deck.get("next_due"),
        # May already be in the past, which means ready now — pending_proofs
        # never nulls an elapsed appointment, and neither does this.
        "next_ready": min(ready_soon) if ready_soon else None,
        "streak_next": streak + 1,
        "milestone": ({"days": milestone, "away": milestone - streak}
                      if milestone else None),
    }

    # Where the reader was, and what the book kept while they were gone.
    # Omitted entirely when there is nothing honest to say.
    absence = None if days_away is None else {
        "days_away": days_away,
        "last_seen": last_seen,
        "best_streak": best_streak,
        "standing": standing,
        "chapter_title": (story or {}).get("title"),
    }

    return {
        "profile": prof,
        "lessons": lessons,
        "pending": pending,
        "tomorrow": tomorrow,
        "absence": absence,
        "deck": deck,
        "reading": reading,
        "refresh": refresh_titles,
        "mastered": standing,
        # Both sides of this subtraction now come from the same decay-aware
        # definition. Before, `mastered_count()` was decay-aware while
        # `proven_count()` counted every node ever earned regardless of
        # freshness — so a faded node counted on the proven side but not the
        # mastered side, and the difference went negative.
        "assumed": max(0, learner.mastered_count(reader_id=reader_id)
                       - learner.proven_count_current(reader_id=reader_id)),
        "xp_today": learner.xp_today(reader_id=reader_id),
        "streak": prof["streak"],
        "best_streak": best_streak,
        "streak_milestone": learner.streak_milestone(reader_id=reader_id),
        "freezes_left": learner.freezes_left(reader_id=reader_id),
        "active_today": learner.active_today(reader_id=reader_id),
        "quest": quest,
        "pace": pace,
        "quest_done": quest_done,
        "quest_total": quest_total,
        "story": story,
        "story_progress": progress,
        "story_can_advance": story_can_advance,
        "story_needs": None if story_can_advance else _story_needs(story, reader_id),
        "story_title": _book_title(prof["name"]),
    }


# A graded paper is never one question long. A single item can be lucky, and a
# lone constructed-response item is worth a whole node's mastery only if the
# reader can be trusted not to want that — which is not a safe assumption to
# build an education on.
QUIZ_MIN_ITEMS = 4
QUIZ_MAX_ITEMS = 12


def _locked_lesson_response(node: dict, reader_id: int) -> Optional[JSONResponse]:
    """Return a conflict response when this lesson is not currently open.

    Standing mastery remains revisitable even if a prerequisite later fades;
    that matches the Atlas, which allows both open and mastered tiles. Everything
    else must satisfy the same decay-aware curriculum gates shown by the UI.
    """
    gates = learner.gate_map(reader_id=reader_id)
    if gates.get(node["id"], 0) >= 0.8 or curr.unlocked(node, gates):
        return None
    return JSONResponse({
        "error": "this lesson is still locked",
        "node_id": node["id"],
        "unlock_requirements": curr.unlock_requirements(node, gates),
    }, status_code=409)


# ---------------- practice ----------------

@app.get("/api/practice/{gen_key}")
def practice_set(gen_key: str, request: Request, n: int = 6, level: int = 1,
                 node_id: str = ""):
    reader_id = current_reader(request)
    # Binding the token to a *caller-supplied* subject repeats the mistake it was
    # meant to fix. If this paper is to count towards a lesson, the drill must be
    # that lesson's own drill, at that lesson's own level — otherwise six ducks
    # would be a sitting for quantum field theory.
    if node_id:
        node = curr.node(node_id)
        if not node:
            return JSONResponse({"error": "no such node"}, status_code=404)
        if node.get("practice") != gen_key:
            return JSONResponse(
                {"error": "that drill does not belong to that lesson"}, status_code=409)
        locked = _locked_lesson_response(node, reader_id)
        if locked is not None:
            return locked
        level = node["stage"]
    # The same floor as a quiz. Without it `?n=1` served a single item, and a
    # single item scores 0 or 1 against a 0.8 pass mark — so one lucky click was
    # a full pass, retryable without limit, feeding mastery exactly as a quiz
    # does. Guessing alone proved undergraduate differential calculus.
    n = max(QUIZ_MIN_ITEMS, min(int(n), QUIZ_MAX_ITEMS)) if node_id else max(1, min(int(n), 20))
    qs = practice.generate_set(gen_key, n, level)
    if not qs:
        return JSONResponse({"error": "unknown generator", "available": practice.list_generators()},
                            status_code=404)
    # Bound to the lesson it will be recorded against, so a trivial drill's
    # token cannot be spent as a graduate-level attempt.
    return {"generator": gen_key, "token": _remember(qs, "practice", node_id, reader_id),
            "questions": _public(qs)}


class AttemptIn(BaseModel):
    node_id: str
    answers: List[str] = Field(default_factory=list, max_length=24)
    token: str = ""
    # How long the paper took, by the reader's own clock. Untrusted and
    # non-load-bearing: see learner._per_item_seconds. Nothing about grading,
    # mastery or XP reads it; it exists only so the book can answer "how long
    # will this take me" with the reader's own number instead of a guess.
    seconds: Optional[float] = None

    @field_validator("answers")
    @classmethod
    def _bounded_answers(cls, values: List[str]) -> List[str]:
        if any(len(value) > 2000 for value in values):
            raise ValueError("each answer must be at most 2000 characters")
        return values


@app.post("/api/attempt")
def record_attempt(a: AttemptIn, request: Request):
    reader_id = current_reader(request)
    # Practice is graded here, from the book's own copy of the paper. There is
    # no self-reported score to accept.
    entry = _recall(a.token, "practice", a.node_id, reader_id)
    graded = entry["questions"] if entry else None
    if graded is None:
        return JSONResponse({"error": "this practice was not issued for this lesson"},
                            status_code=409)
    node = curr.node(a.node_id) if a.node_id else None
    if node is not None:
        locked = _locked_lesson_response(node, reader_id)
        if locked is not None:
            return locked
    given = _final_answers(entry, a.answers)
    scorable, scorable_given, _spent = _drop_burned(graded, given, a.node_id, reader_id, entry)
    if len(scorable) < min(QUIZ_MIN_ITEMS, len(graded)):
        return JSONResponse(
            {"error": "the book has already shown you the answers to most of "
                      "these. Come back to this one in a few days.",
             # A stable tag beside the prose. The client used to have to match
             # the sentence itself to know what had happened, which couples its
             # copy to this file's wording character for character; the reader
             # got the generic offline card instead, and was told a refusal the
             # book had made on purpose was probably their network.
             "reason": "bank_spent"}, status_code=409)
    score = quiz.score_quiz(scorable, scorable_given)["score"]
    # A drill can be run without a lesson behind it (/api/practice/{gen} with
    # no node_id mints a token bound to ""), and that is fine to *do* — but it
    # must not be recorded. Writing mastery and XP against the empty-string
    # node created a ledger row for a lesson that does not exist and paid for
    # it. Grade it, return the marks, record nothing.
    if not a.node_id or node is None:
        return {"score": score, "xp_gained": 0, "unlessoned": True,
                "cards_added": 0, "ascension": None}
    res = learner.record_attempt(a.node_id, score, seconds=a.seconds,
                                 items=len(a.answers), reader_id=reader_id)
    # Practice is a study event too: whatever was missed should come back.
    cards_added = 0
    if graded and given:
        article = node["articles"][0] if node and node["articles"] else ""
        missed = [q for q in quiz.cards_from_missed(graded, given, a.node_id, article)
                  if not _is_ephemeral(graded, q)]
        cards_added = learner.add_cards(missed, reader_id=reader_id)
    res["cards_added"] = cards_added
    res["ascension"] = (_check_ascension(learner.get_profile(reader_id=reader_id), reader_id)
                        if res.get("newly_mastered") else None)
    return res


def _is_ephemeral(questions: list, card: dict) -> bool:
    """Whether this card would drill a one-off instance rather than a fact.

    Every practice generator stamps `ephemeral: True` on every item it makes.
    That is right for "5 + 3 = ?" and wrong for "Which shape has 8 sides?" or
    "Is 53 a prime number?" — durable facts that happen to come from a
    generator. Trusting the blanket flag meant the 41 nodes assessed through
    practice could never contribute a single review card, however badly the
    reader did, which flatly contradicts building cards from every error.

    The prompt is the better judge, and `is_ephemeral_prompt` already reads it.
    """
    front = card.get("front", "")
    for q in questions:
        prompt = (q.get("prompt") or "").strip()
        if prompt and prompt in front:
            return quiz.is_ephemeral_prompt(prompt, q.get("kind", ""),
                                            q.get("ephemeral"), q.get("gen", ""),
                                            q.get("level", 0))
    return False


# ---------------- quizzes ----------------

def _draw_from_bank(bank, n, rng):
    """Choose n authored items, guaranteeing one that must be produced.

    Two-option items go last because those can be passed by luck. Everything
    else competes on equal footing: listing the choice items first meant a
    node's *other* produced items were never drawn at all, so a guaranteed slot
    for one had quietly become a cap of one.

    Membership is by identity, not equality — comparing whole dicts is quadratic
    and would drop both copies of a genuinely duplicated bank item.
    """
    produced = [q for q in bank if q.get("kind") in ("numeric", "short")]
    chosen, taken = [], set()
    if produced:
        keep = rng.choice(produced)
        chosen.append(keep)
        taken.add(id(keep))
    rest = [q for q in bank if id(q) not in taken]
    rng.shuffle(rest)
    rest.sort(key=lambda q: len(q.get("choices") or []) == 2)
    chosen.extend(rest[:max(0, n - len(chosen))])
    rng.shuffle(chosen)                      # no positional tell
    return chosen


def _add_young_ordering(questions, node, n, stage):
    """Give the youngest readers something to put in order.

    Recognition only ever asks "which of these?"; ordering asks a child to
    produce a sequence. Room is made by dropping a *recognition* item, never the
    guaranteed produced one — the old splice took whatever sat last.
    """
    gen = _ORDER_FOR_YOUNG.get(node["domain"])
    if not gen:
        return questions
    extra = practice.generate_set(gen, 1, level=stage)
    if not extra:
        return questions
    # `tally` belongs here with the other produced answers: it asks the child
    # to count and hand back a number. Left out, the one question shape built
    # for these readers is classified as droppable recognition and dropped —
    # for exactly the readers it was built for.
    keep = [q for q in questions
            if q.get("kind") in ("numeric", "short", "order", "tally")]
    drop = [q for q in questions if q not in keep]
    return (keep + drop)[:max(0, n - 1)] + extra


def _add_young_production(questions, node, n, stage):
    """Guarantee the youngest readers something to PRODUCE, not just recognise.

    From Sapling up every paper closes with a written reflection, so a produced
    answer is guaranteed. Below that there was no equivalent: all 622 authored
    items at stages 0-1 are multiple choice, and a paper is drawn from the
    authored bank first, so the generators never got a look in. The reader's
    first years — priced in years, not weeks — asked them to recognise an
    answer and never once to produce one.

    The instrument for this already existed and was simply never minted onto a
    paper: `g_count_tally` scores counting AS counting (touch each object, the
    book counting along), so a child who counts five apples but cannot yet read
    the numeral 5 is marked right rather than wrong. It has a touch UI, a
    validator in check_banks, and its own tests.

    Written against the node's own generator rather than against a hard-coded
    list, so any young generator that later grows a produced form arrives on
    the paper for free. A recognition item makes room; the ordering item added
    beside it is never the one dropped.
    """
    gen = node.get("practice")
    if not gen:
        return questions
    extra = [q for q in practice.generate_set(gen, 2, level=stage)
             if q.get("kind") in ("tally", "numeric", "short", "order")]
    if not extra:
        return questions
    if any(q.get("kind") in ("tally", "numeric", "short") for q in questions):
        return questions          # this paper already asks for something produced
    keep = [q for q in questions
            if q.get("kind") in ("numeric", "short", "order", "tally")]
    drop = [q for q in questions if q not in keep]
    return (keep + drop)[:max(0, n - 1)] + extra[:1]


@app.get("/api/quiz/{node_id}")
def quiz_for_node(node_id: str, request: Request, n: int = 6):
    """Draw a paper from the node's bank — assembled in ONE pass, deliberately;
    layered patches here have fought each other before.

    Order of business: draw from the bank, top up from the node's own drill,
    give the youngest an ordering item, then append the unmarked reflection
    item. Auto-generated cloze is deliberately absent — successive hand audits
    put its defect rate at 65%, then 90%, then 55% after the 2026-08 precision
    pass (tools/hand-audit-cloze-2026-08.md) — and as of that audit it is
    absent from the whole app: the self-check that served it is withdrawn.
    """
    reader_id = current_reader(request)
    node = curr.node(node_id)
    if not node:
        return JSONResponse({"error": "no such node"}, status_code=404)
    locked = _locked_lesson_response(node, reader_id)
    if locked is not None:
        return locked
    n = max(QUIZ_MIN_ITEMS, min(int(n), QUIZ_MAX_ITEMS))
    stage = node["stage"]

    bank = list(node.get("quiz", []))
    random.shuffle(bank)
    questions = [_shuffled(q) for q in _draw_from_bank(bank, n, random)]

    # Top up from the node's own drill so a quiz exercises skill, not only
    # recall — and so stage 0-1 has a real, non-reading assessment.
    if node.get("practice") and len(questions) < n:
        questions.extend(practice.generate_set(node["practice"], n - len(questions), level=stage))

    if stage <= 1:
        questions = _add_young_ordering(questions, node, n, stage)
        questions = _add_young_production(questions, node, n, stage)

    questions = questions[:n]

    # From middle school up, close with something to write. It is not marked —
    # its key is the node's published goal — but it is worth writing, and it is
    # *added* to the paper rather than displacing a graded item.
    if stage >= 2:
        sa = quiz.short_answer_from_node(node["title"], node.get("goal", ""), node["articles"])
        if sa:
            questions.append(sa)

    # The paper is already the right length: n graded items plus the unmarked
    # reflection item. A blanket `questions[:n]` here was silently cutting that
    # reflection item straight back off again.
    for i, q in enumerate(questions):
        q["id"] = i
    return {"node_id": node_id, "title": node["title"], "stage": stage,
            "token": _remember(questions, "quiz", node_id, reader_id),
            "questions": _public(questions)}


class CheckIn(BaseModel):
    token: str
    id: int
    answer: str = Field("", max_length=2000)


def _drop_burned(questions: list, given: list, node_id: str, reader_id: int,
                 entry: dict = None):
    """Keep only the items this reader answered without having been told.

    The rule is per item, and it is about order: an item counts if the reader
    committed an answer to it *before* its key was ever shown. That is exactly
    what honest use looks like — the app checks every answer as it is given, so
    the commitment always precedes the reveal — and it is exactly what harvesting
    is not.

    Keying this to the *paper's* issue time instead was defeated by asking for
    the paper first: fetch a clean paper, burn the bank through a second one,
    then submit the first. Every burn postdated its issue, so nothing was
    dropped and a 0.83 was scored from no knowledge. A paper is free to request;
    a commitment is not.
    """
    if not node_id:
        return questions, given, 0
    burned = learner.burned_map(node_id, reader_id=reader_id)
    if not burned:
        return questions, given, 0
    committed = (entry or {}).get("committed") or {}
    keep_q, keep_a = [], []
    for i, q in enumerate(questions):
        burn_at = burned.get(_fingerprint(q))
        if burn_at is not None:
            mine = committed.get(q.get("id"))
            # No commitment on this paper, or one made after the reveal: the
            # reader had the answer in hand either way.
            if not mine or mine.get("at", 0) > burn_at:
                continue
        keep_q.append(q)
        keep_a.append(given[i] if i < len(given) else "")
    return keep_q, keep_a, len(questions) - len(keep_q)


@app.post("/api/quiz/check")
def check_one(c: CheckIn, request: Request):
    """Grade a single item so the reader gets immediate feedback.

    The answer is revealed only *after* they commit to one — which is what
    teaches — while the key itself never ships with the paper.
    """
    reader_id = current_reader(request)
    # Same liveness rule as the submit this sitting ends with — an expired
    # paper must not still be marking items (and burning them) here only to
    # be refused there. Looked up inside the lock, like every other read of
    # _SERVED: this entry is mutated below.
    with _SERVED_LOCK:
        entry = _live_paper(c.token)
    # A foreign-owned token reads identically to an unknown one — otherwise
    # the distinct error would confirm another reader has a paper open.
    if not entry or entry.get("reader_id", 1) != reader_id:
        return JSONResponse({"error": "unknown quiz token"}, status_code=409)
    if entry["purpose"] == "placement":
        # A placement check measures what the reader already knows; walking it
        # item by item for the answers turns it into a coaching session and then
        # a clean pass. Placement is sat once, in the dark.
        return JSONResponse({"error": "a placement check is marked at the end"},
                            status_code=409)
    if entry["purpose"] in ("quiz", "practice") and entry.get("subject"):
        node = curr.node(entry["subject"])
        if node is not None:
            locked = _locked_lesson_response(node, reader_id)
            if locked is not None:
                return locked
    questions = entry["questions"]
    q = next((x for x in questions if x.get("id") == c.id), None)
    if q is None:
        return JSONResponse({"error": "no such question"}, status_code=404)
    if not (c.answer or "").strip():
        return JSONResponse({"error": "answer first — then the book will tell you"},
                            status_code=400)
    # First commitment stands: seeing the key cannot retroactively improve it.
    # The store performs a compare-and-swap update, so this remains true across
    # serverless instances and cannot recreate a token that submit just claimed.
    with _SERVED_LOCK:
        committed = _SERVED.commit_answer(c.token, c.id, c.answer)
    if committed is None:
        return JSONResponse({"error": "this quiz token was already submitted"},
                            status_code=409)
    locked = committed["answer"]
    # The closing reflection item every paper from Sapling up carries is
    # `ungraded` by construction (quiz.py:934): its key is the node's published
    # goal, which the reader can read on the lesson page, so it is worth writing
    # and worth comparing against a model answer, but it is not worth marks.
    # `score_quiz` skips ungraded items and then floors the denominator at 1, so
    # asking it to mark one returns 0.0 — and this endpoint duly told the reader
    # they were wrong, on every paper, whatever they wrote, capping every lesson
    # quiz at five out of six. It then burned the item for a week for having
    # been "missed". An item the book has declined to grade cannot be graded
    # wrong, and cannot be spent as evidence either. `correct` is null here
    # rather than false: there is no verdict to report.
    ungraded = bool(q.get("ungraded"))
    correct = None if ungraded else (
        quiz.score_quiz([q], [locked])["score"] >= (0.6 if q.get("kind") == "short" else 1.0))
    # A wrong answer spends the item: the reader is about to be told, and for the
    # next week that item cannot be the evidence they know it — otherwise a paper
    # is read for its answers, discarded, and a clean one sat a moment later.
    # A *correct* answer spends nothing. Being shown the answer you already gave
    # teaches nothing and reveals nothing, and burning it refused an honest
    # reader their own pass on every sitting, permanently.
    node_for = q.get("node_id") or (entry["subject"] if entry["purpose"] in
                                    ("quiz", "practice") else "")
    if node_for and correct is False:
        learner.burn_item(node_for, _fingerprint(q), reader_id=reader_id)
    return {"correct": correct, "ungraded": ungraded, "answer": q.get("answer", ""),
            "explain": q.get("explain", ""), "keywords": q.get("keywords", []),
            "locked": locked}


# Deliberately NO `questions` field: the server grades from its own copy of
# the paper, so a client-supplied bank is never even parsed. (It used to be
# accepted and ignored, which reads like an input when it is not one.)
class QuizSubmitIn(BaseModel):
    node_id: str
    answers: List[str] = Field(..., max_length=24)
    make_cards: bool = True
    token: str = ""
    confidence: List[int] = Field(default_factory=list, max_length=24)
    seconds: Optional[float] = None

    @field_validator("answers")
    @classmethod
    def _bounded_answers(cls, values: List[str]) -> List[str]:
        if any(len(value) > 2000 for value in values):
            raise ValueError("each answer must be at most 2000 characters")
        return values


@app.post("/api/quiz/submit")
def submit_quiz(s: QuizSubmitIn, request: Request):
    reader_id = current_reader(request)
    entry = _recall(s.token, "quiz", s.node_id, reader_id)
    if entry is None:
        return JSONResponse({"error": "this paper was not issued for this lesson"},
                            status_code=409)
    node = curr.node(s.node_id)
    if node is not None:
        locked = _locked_lesson_response(node, reader_id)
        if locked is not None:
            return locked
    questions = entry["questions"]
    given = _final_answers(entry, s.answers)
    # Measurement drops the items whose keys were shown; the deck does not. An
    # item the reader got wrong and was then told the answer to is exactly what
    # should come back tomorrow, whether or not it still counts for anything.
    scorable, scorable_given, spent = _drop_burned(questions, given, s.node_id, reader_id, entry)
    # The floor is on what is *scored*, not on what was served. Enforcing it only
    # at serve time let a burnt-out bank be graded on the one or two procedural
    # top-ups that were left — a thirteen-item paper marked `total: 1`, and
    # random guessing proved undergraduate calculus in seven sittings.
    if len(scorable) < QUIZ_MIN_ITEMS:
        return JSONResponse(
            {"error": "the book has already shown you the answers to most of "
                      "these. Come back to this one in a few days.",
             "reason": "bank_spent", "spent": spent}, status_code=409)
    result = quiz.score_quiz(scorable, scorable_given)
    mastery = learner.record_attempt(s.node_id, result["score"],
                                     seconds=s.seconds, items=len(s.answers),
                                     reader_id=reader_id)
    cards_added = 0
    if s.make_cards:
        article = node["articles"][0] if node and node["articles"] else ""
        # Errors are exactly what should come back tomorrow — always build cards
        # from missed items, regardless of overall score.
        missed = quiz.cards_from_missed(questions, given, s.node_id, article)
        cards_added += learner.add_cards(missed, reader_id=reader_id)
        # Young lessons always yield concept cards: a child who failed needs the
        # review most, and their questions are procedural so misses mint nothing.
        if node and node["stage"] <= 1:
            cards_added += learner.add_cards(quiz.cards_from_lesson(
                node["title"], node.get("goal", ""), node.get("kid_text", ""), s.node_id),
                reader_id=reader_id)
        elif result["score"] >= 0.5 and node:
            if node["stage"] >= 2 and node["articles"]:
                # Older readers: durable cards drawn from the article itself.
                art = wiki.get_article(node["articles"][0])
                if art:
                    text = wiki.article_plaintext(art["html"], 4000)
                    cards_added += learner.add_cards(
                        quiz.cards_from_text(node["articles"][0], text, s.node_id),
                        reader_id=reader_id)
    calibration = None
    if any(s.confidence):
        # Knowing how well you know something is itself a skill worth tracking.
        def _right(q, a):
            expected = str(q.get("answer", "")).strip()
            num = quiz._numeric_equal(str(a), expected)
            return num is True or (num is None and str(a).strip().lower() == expected.lower())
        pairs = [(c, q, a) for c, q, a in zip(s.confidence, questions, s.answers) if c]
        # Each direction is counted over its OWN population. Overconfidence is
        # "of the answers you were confident about, how many were wrong" — so
        # its denominator is the confident answers, not every rated answer.
        # Sharing len(pairs) between the two made each figure a rate over a
        # population neither of them was about: a reader who rates most answers
        # mid-confidence (c==2, in neither direction) diluted both denominators
        # with answers that could not contribute to either numerator, and so
        # was systematically under-flagged against the 1/3 limit.
        confident = [p for p in pairs if p[0] >= 3]
        hesitant = [p for p in pairs if p[0] <= 1]
        overconfident = sum(1 for c, q, a in confident if not _right(q, a))
        underconfident = sum(1 for c, q, a in hesitant if _right(q, a))
        calibration = {"overconfident": overconfident, "underconfident": underconfident,
                       "confident_total": len(confident), "hesitant_total": len(hesitant),
                       # `total` stays: it is the sitting's rated-answer count,
                       # which is the honest sample size for the minimum-sample
                       # floor, and older stored events carry only this field.
                       "total": len(pairs)}
        learner.log_event("calibration", {"node": s.node_id, **calibration}, reader_id=reader_id)
    ascension = (_check_ascension(learner.get_profile(reader_id=reader_id), reader_id)
                if mastery.get("newly_mastered") else None)
    # The page turns where it was earned. This is a READ of the story cursor
    # and nothing else: /api/story/advance stays the only writer, or a splash
    # re-opened from history would grant the chapter's 15 XP a second time.
    # Read after the ascension, which may have moved the reader's stage and so
    # the window the cursor walks, and from the profile that ascension saved.
    story_unlocked = None
    if mastery.get("newly_mastered"):
        chapter, progress, can_advance = _story_cursor(
            learner.get_profile(reader_id=reader_id), reader_id, commit=False)
        # Only when this very lesson is the one the open chapter was waiting
        # for. A reader who masters something unrelated has not turned a page.
        if can_advance and (chapter or {}).get("leads_to") == s.node_id:
            story_unlocked = {"number": progress + 1,
                              "title": chapter.get("title", ""),
                              "chapter": chapter}
    return {"result": result, "mastery": mastery, "cards_added": cards_added,
            "ascension": ascension, "calibration": calibration,
            "story_unlocked": story_unlocked}


# The self-check that used to live here — machine-generated fill-in-the-blank
# over raw article prose, at GET /api/selfcheck — is withdrawn. The 2026-08
# hand audit (tools/hand-audit-cloze-2026-08.md) measured 22 of 40 items
# defective (55%, Wilson 40-69%) after the precision pass that had already
# halved it from 90%: roughly a quarter of items had a second defensible
# answer, and a quarter carried a distractor that could not be the answer. A
# feature that is wrong half the time teaches the wrong thing half the time,
# and a "provisional" label is a disclaimer, not a fix. Retired rather than
# shipped behind a warning.


# ---------------- spaced repetition ----------------

# The smallest sitting the book will admit to being worth doing. Named here
# because the quest tile, the deck and the copy that offers it must all quote
# the same number.
SHORT_DOSE_CARDS = 5


@app.get("/api/review/due")
def review_due(request: Request, limit: int = 20, dose: str = ""):
    reader_id = current_reader(request)
    # The deck ships the day's ask with the cards, from the same function the
    # quest tile is priced by — a deck that stops at a different number from
    # the one the tile promised would be worse than a deck that never stops.
    stats = learner.deck_stats(reader_id=reader_id)
    goal = _review_goal(stats, _elapsed_days(learner.last_active_before_today(reader_id=reader_id)),
                        learner.events_today_count("review", reader_id=reader_id))
    # A reader who asked for a short sitting gets a short sitting. The ask is
    # lowered, never the deck: the cards behind it are untouched and the full
    # day is one tap away, so this is a smaller door into the same room rather
    # than a different, lesser deck.
    if dose == "short" and goal > 0:
        goal = min(goal, SHORT_DOSE_CARDS)
    return {"cards": learner.due_cards(limit, reader_id=reader_id), "stats": stats, "goal": goal,
            "dose": dose or "full", "short_goal": SHORT_DOSE_CARDS}


class ReviewIn(BaseModel):
    card_id: int
    quality: int
    seconds: Optional[float] = None


@app.post("/api/review")
def review(r: ReviewIn, request: Request):
    reader_id = current_reader(request)
    return learner.review_card(r.card_id, max(0, min(5, r.quality)),
                               seconds=r.seconds, reader_id=reader_id)


class CardIn(BaseModel):
    front: str
    back: str
    article: str = ""
    node_id: str = ""


@app.post("/api/review/add")
def add_card(c: CardIn, request: Request):
    """A card the reader writes for themselves. Marked as theirs, so it can be
    studied like any other but cannot stand in as evidence of mastery."""
    reader_id = current_reader(request)
    card = c.model_dump() if hasattr(c, "model_dump") else c.dict()
    card["origin"] = "reader"
    return {"added": learner.add_cards([card], reader_id=reader_id)}


# ---------------- placement ----------------

def _placement_run(asked: list) -> list:
    """The rungs belonging to the CURRENT staircase.

    `reopen_placement` keeps the whole asked-history so a re-measurement does
    not repeat items the reader has already seen, and drops a marker where the
    new run starts. Everything that reasons about the staircase — which rung is
    next, whether the neighbours are exhausted, where it settles — has to read
    only the current run, or the previous run's passes go on holding the floor
    and a reader who has forgotten can be re-measured upward but never
    downward.
    """
    run = []
    for entry in asked or []:
        if not isinstance(entry, dict):
            continue          # legacy rows stored bare strings here
        if entry.get("reopened"):
            run = []
        elif "stage" in entry:
            run.append(entry)
    return run


def _placement_rung(domain: str, prof: Optional[dict], reader_id: int) -> Optional[int]:
    """The rung the book is willing to offer next for this domain.

    The staircase used to be entirely the client's to walk: it named the stage
    it wanted, so a reader could open at stage 5, pass one paper and settle
    there. The server now decides where the ladder starts and where it goes
    next, and refuses papers for any other rung.
    """
    state = learner.placement_state(reader_id=reader_id).get(domain, {})
    if state.get("done"):
        return None
    history = state.get("asked") or []
    asked = _placement_run(history)
    if not asked:
        # A RE-measurement resumes at the frontier the LAST run reached — that
        # is where growth or forgetting since would show — computed from the
        # previous run's own passes rather than from the `stage` column, which
        # records the last rung asked and not where the reader landed. Only the
        # starting rung is inherited: the new run settles on its own answers,
        # which is what stops a re-check ratcheting upward for ever.
        prior = [h for h in history if isinstance(h, dict) and "stage" in h]
        if prior:
            frontier = max([h["stage"] for h in prior if h.get("passed")],
                           default=-1) + 1
            return max(0, min(frontier, 5))
        # A first placement starts from where their age would put them.
        return learner.stage_for_age(float((prof or {}).get("age") or 6))
    last = asked[-1]
    nxt = last["stage"] + 1 if last["passed"] else last["stage"] - 1
    if nxt < 0 or nxt > 5 or any(h["stage"] == nxt for h in asked):
        # A staircase with every neighbouring rung already tried normally
        # means settled — but a *re-opened* placement (reopen_placement
        # clears `done` while keeping the history, so the next sitting need
        # not repeat items) arrives here unsettled. Re-measure at the rung
        # the reader settled on: the frontier is exactly where growth since
        # the last sitting would show.
        placed = max([h["stage"] for h in asked if h.get("passed")], default=-1) + 1
        return max(0, min(placed, 5))
    return nxt


# A settled placement is not settled forever: a reader grows, and re-measuring
# after a cooling period is how the book notices.


def _placement_reopen(domain: str, reader_id: int) -> bool:
    """Ask the store to reopen a settled domain; True only when it happened.

    The interface is fixed: `LearnerStore.reopen_placement(domain)` owns the
    whole decision — settled-or-not and the cooling period alike — and
    returns True only when the domain actually reopened. (This used to probe
    a tuple of candidate method names while the store method was still being
    written; now that it has landed, guessing would only hide a typo.)
    """
    fn = getattr(learner, "reopen_placement", None)
    if not callable(fn):
        return False   # a stub store without the feature: a graceful no-op
    try:
        return bool(fn(domain, reader_id=reader_id))
    except Exception as exc:
        log.warning("placement reopen for %s failed: %s", domain, exc)
        return False


@app.get("/api/placement/next")
def placement_next(domain: str, request: Request, stage: Optional[int] = None,
                   n: int = 6, recheck: bool = False):
    """Serve a short, server-scored placement check at the rung the book chooses.

    Prefers the expert-authored item bank (the most valid measure we have),
    topped up with the node's own practice generator. `recheck=true` asks to
    re-measure a settled domain; honoured only when the store supports
    reopening and its cooling period has passed.
    """
    reader_id = current_reader(request)
    prof = learner.get_profile(reader_id=reader_id)
    rung = _placement_rung(domain, prof, reader_id)
    if rung is None and recheck and _placement_reopen(domain, reader_id):
        rung = _placement_rung(domain, prof, reader_id)
    if rung is None:
        return JSONResponse({"error": "placement for this field is already settled",
                             "domain": domain,
                             "reopen_supported": callable(
                                 getattr(learner, "reopen_placement", None))},
                            status_code=409)
    if stage is not None and int(stage) != rung:
        # Not an error the reader can cause, but worth being loud about.
        log.warning("placement rung %s requested for %s; serving %s", stage, domain, rung)
    stage = rung
    n = max(4, min(int(n), 12))
    nodes = [nd for nd in curr.nodes.values()
             if nd["domain"] == domain and nd["stage"] == stage]
    random.shuffle(nodes)
    questions = []
    for node in nodes:
        if len(questions) >= n:
            break
        for q in (node.get("quiz") or [])[:2]:
            q = _shuffled(q)
            q["node_id"] = node["id"]
            questions.append(q)
    for node in nodes:
        if len(questions) >= n:
            break
        if node.get("practice"):
            for q in practice.generate_set(node["practice"], 2, level=stage):
                q["node_id"] = node["id"]
                questions.append(q)
    for i, q in enumerate(questions):
        q["id"] = i
    served = questions[:n]
    return {"domain": domain, "stage": stage,
            "token": _remember(served, "placement", "{}:{}".format(domain, stage), reader_id),
            "questions": _public(served)}


class PlacementSubmitIn(BaseModel):
    domain: str
    stage: int
    # No `questions` field, same rule as QuizSubmitIn: the server's copy grades.
    answers: List[str] = Field(..., max_length=24)
    token: str = ""

    @field_validator("answers")
    @classmethod
    def _bounded_answers(cls, values: List[str]) -> List[str]:
        if any(len(value) > 2000 for value in values):
            raise ValueError("each answer must be at most 2000 characters")
        return values


@app.post("/api/placement/submit")
def placement_submit(s: PlacementSubmitIn, request: Request):
    """Score placement answers *on the server* (never the client's word) and
    walk an adaptive staircase: pass → try the next stage up; fail → step down.
    When the staircase settles, the reader's stage is actually updated."""
    reader_id = current_reader(request)
    prof = learner.get_profile(reader_id=reader_id)
    expected = _placement_rung(s.domain, prof, reader_id)
    if expected is None or int(s.stage) != expected:
        return JSONResponse({"error": "that is not the rung this check is on",
                             "expected_stage": expected}, status_code=409)
    entry = _recall(s.token, "placement", "{}:{}".format(s.domain, s.stage), reader_id)
    questions = entry["questions"] if entry else None
    if questions is None:
        return JSONResponse({"error": "this paper was not issued for this check"},
                            status_code=409)
    if len(s.answers) != len(questions):
        return JSONResponse({
            "error": "answer count does not match the issued paper",
            "expected": len(questions),
            "received": len(s.answers),
        }, status_code=400)
    given = _final_answers(entry, s.answers)
    result = quiz.score_quiz(questions, given)
    passed = result["score"] >= 0.7
    credited_through = -1
    state = learner.placement_state(reader_id=reader_id).get(s.domain, {})
    history = list(state.get("asked", []))
    history.append({"stage": s.stage, "score": round(result["score"], 2), "passed": passed})
    # The whole history is stored (it is what keeps a re-measurement from
    # repeating items), but only the CURRENT run decides where this staircase
    # goes and where it lands. Reading the lot meant a previous run's passes
    # went on holding the floor, so a re-check could raise a reader and never
    # lower one — and "can place a reader down" is half of what makes it a
    # measurement rather than a ceremony.
    run = _placement_run(history)

    if passed:
        next_stage = s.stage + 1 if s.stage < 5 else None
    else:
        next_stage = s.stage - 1 if s.stage > 0 else None

    # The staircase stops when it reverses direction or runs off either end.
    tried = {h["stage"] for h in run}
    settled = next_stage is None or next_stage in tried
    if settled:
        placed = max([h["stage"] for h in run if h["passed"]], default=-1) + 1
        placed = max(0, min(placed, 5))
        # Credit is granted once, at settle time — not on every passing rung.
        credited_through = placed - 1
        if placed > 0:
            learner.seed_assumed(curr.seed_mastery_for_stage(placed, [s.domain]),
                                 reader_id=reader_id)
        # Placement can also place a reader *down*. Age-seeded credit above where
        # they actually landed is not evidence of anything and must not stand.
        stale = [nid for nid, nd in curr.nodes.items()
                 if nd["domain"] == s.domain and nd["stage"] >= placed]
        learner.revoke_assumed(stale, reader_id=reader_id)
        if prof:
            # Placement is evidence, so it may move the reader either way — but
            # a single domain's result must not overwrite their whole reading
            # level. The global stage is the median of what has been measured.
            settings = dict(prof.get("settings", {}))
            per_domain = dict(settings.get("placed", {}))
            # Whether the book had measured ANY field before this sitting. It
            # decides which of the two rules below applies, so it must be read
            # before this result joins the map.
            had_prior_measurement = bool(per_domain)
            per_domain[s.domain] = placed
            settings["placed"] = per_domain
            measured = sorted(per_domain.values())
            if len(measured) >= 2:
                overall = measured[(len(measured) - 1) // 2]   # lower median
            elif had_prior_measurement:
                # A re-measurement of the only field measured so far may lower
                # the reading level but not raise it — Round 5's rule, that one
                # domain must not promote a reader past what other evidence
                # supports.
                overall = min(int(prof["stage"] or 0), measured[0])
            else:
                # The first measurement the book has ever taken. Round 5's rule
                # was written when setup seeded a stage from age, so `min()`
                # meant "your age says Sapling; one strong result will not push
                # you to Grove". A later round made setup start EVERY reader at
                # 0 on principle ("age says how old a reader is, not what they
                # have been taught") — and that quietly turned this branch into
                # min(0, anything), so a settled placement could never raise
                # anyone. A reader measured at Grove was still served the
                # pre-reader UI, Simple English, and a story frozen at page one.
                # With nothing else measured, 0 is not neutrality; it is a claim
                # that the reader is a preschooler, and it is the one claim we
                # have evidence against. Take the measurement — the lower-median
                # rule above resumes the moment a second field is measured.
                overall = measured[0]
            learner.save_profile(prof["name"], prof["age"], prof["hours_per_week"],
                                 prof["breadth"], overall, prof["domains"], settings,
                                 reader_id=reader_id)
        next_stage = None
        log.info("placement settled: %s at stage %d", s.domain, placed)
    learner.placement_update(s.domain, s.stage, history, settled, reader_id=reader_id)
    return {"domain": s.domain, "score": round(result["score"], 2), "passed": passed,
            "credited_through_stage": credited_through, "suggest_stage": next_stage,
            "settled": settled}


# ---------------- opening a specialist field ----------------

class DomainOpenIn(BaseModel):
    domain: str


@app.post("/api/domain/open")
def domain_open(s: DomainOpenIn, request: Request):
    """Let a reader who already has the grounding open a specialist field.

    The ten general fields are a journey: they start at preschool and every
    lesson is earned from the one before it. A specialist field is not that.
    Radiology begins where the general spine ends, and the reader who wants it
    is a clinician, not a child working upward — they arrive already holding
    the anatomy and the physics its modules are gated on. Making them prove
    Systems Physiology to the book before it will show them PI-RADS is a ritual
    that teaches nobody anything.

    So the reader may say so, once, and the book takes them at their word — and
    then says so out loud. The grounding is credited as ASSUMED, which is the
    same standing placement gives and which every surface already renders as
    "assumed, not yet proved". Nothing here is recorded as mastery earned, no
    growth is paid, and the reader can prove any of it later, at which point the
    assumption is replaced by the real thing.

    Only a field that declares an `entry_stage` above zero can be opened this
    way. The general spine has no door of this kind, by design: a reader cannot
    skip their own education by asserting it.
    """
    domain = next((d for d in curr.domains if d["id"] == s.domain), None)
    if domain is None:
        return JSONResponse({"error": "no such field"}, status_code=404)
    if int(domain.get("entry_stage", 0)) <= 0:
        return JSONResponse(
            {"error": "this field is travelled from the beginning, not opened"},
            status_code=409)

    own = [n for n in curr.nodes.values() if n["domain"] == s.domain]
    # Only what stands OUTSIDE the field: crediting its own nodes would be
    # crediting the very thing the reader came to learn.
    outside = sorted({p for n in own for p in n["prereqs"]
                      if curr.nodes.get(p, {}).get("domain") != s.domain})
    if not outside:
        return JSONResponse({"error": "this field has nothing to open"},
                            status_code=409)

    # Every write and read here belongs to the reader who asked, not to the
    # default profile. This endpoint predates Google sign-in by a few hours and
    # was written when reader_id=1 was the only reader there was; left alone
    # through the rebase it would have credited a signed-in reader's grounding
    # to the legacy profile, reported "66 modules opened" off that profile's
    # gates, and left the actual reader's field still locked.
    reader_id = current_reader(request)
    learner.seed_assumed(outside, reader_id=reader_id)
    learner.log_event("domain_opened", {"domain": s.domain, "credited": outside},
                      reader_id=reader_id)
    gates = learner.gate_map(reader_id=reader_id)
    return {"domain": s.domain,
            "credited": [{"id": p, "title": curr.nodes[p]["title"]} for p in outside],
            "opened": sum(1 for n in own if curr.unlocked(n, gates)),
            "total": len(own)}


# ---------------- tutor ----------------

# A tutor turn is relayed — to the local rule engine, or (once switched on) to
# api.anthropic.com. Both ends expect a chat transcript, so both fields are
# bounded at the door: an unconstrained `role` reaches the remote API as an
# invalid message, and an unconstrained `content` makes POST /api/tutor a relay
# for arbitrarily large payloads at this machine's expense. 8000 characters is
# far more than any reader types and far less than a paste of a whole article.
MAX_TUTOR_CHARS = 8000
MAX_TUTOR_MESSAGES = 60


class TutorMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=MAX_TUTOR_CHARS)


class TutorIn(BaseModel):
    messages: List[TutorMessage] = Field(..., max_length=MAX_TUTOR_MESSAGES)
    title: str = Field("", max_length=300)
    excerpt: str = Field("", max_length=MAX_TUTOR_CHARS)


def _tutor_remote_allowed(prof: Optional[dict]) -> bool:
    """Whether the reader has switched the remote (Claude) tutor ON.

    Opt-in, and deliberately so. An API key in the environment says the
    installation *could* answer remotely; it is not a child's consent to send
    their questions — and the article excerpt they are reading — to
    api.anthropic.com. Until someone deliberately turns this on from inside the
    app (POST /api/profile/settings {"tutor_remote_ok": true}), the local
    rule-based engine answers and nothing leaves the machine, exactly as if no
    key were configured. The switch works in both directions.
    """
    settings = (prof or {}).get("settings") or {}
    return bool(settings.get("tutor_remote_ok", False))


@app.post("/api/tutor", response_class=JSONResponse)
def ask_tutor(t: TutorIn, request: Request) -> JSONResponse:
    reader_id = current_reader(request)
    prof = learner.get_profile(reader_id=reader_id)
    stage = prof["stage"] if prof else 2
    if prof and t.title:
        domain = curr.domain_for_article(t.title)
        if domain:
            domain_stage = (prof.get("settings") or {}).get("domain_stage") or {}
            stage = domain_stage.get(domain, stage)
    excerpt = t.excerpt
    if not excerpt and t.title:
        s = wiki.get_summary(t.title)
        excerpt = (s or {}).get("extract", "")
    messages = [m.model_dump() for m in t.messages]
    # State the response type explicitly.  Tutor text is untrusted (it may
    # include user input or a remote model's reply), and must never be inferred
    # or served as HTML by a framework/analyser.
    # The name travels only now that the disclosure the reader is shown says so.
    # It named the conversation, the passage and the reading level but not the
    # name, and it could not be wired until that sentence was true — which it
    # now is (see the tutor-disclosure line in web/app.js).
    return JSONResponse(tutor.ask(
        messages, t.title, excerpt, stage,
        allow_remote=_tutor_remote_allowed(prof),
        reader=(prof or {}).get("name") or "",
    ))


# ---------------- roadmap & journal ----------------

@app.get("/api/roadmap")
def roadmap_api(request: Request):
    reader_id = current_reader(request)
    prof = learner.get_profile(reader_id=reader_id)
    if not prof:
        return JSONResponse({"error": "no profile"}, status_code=400)
    # Pace against what the reader can still be expected to need to learn.
    # Placement-assumed nodes are treated as covered for scheduling, but the
    # headline "mastered" count reports only what has actually been proven.
    r = roadmap(prof, curr.graph(), learner.gate_map(reader_id=reader_id),
               proven=learner.proven_set(reader_id=reader_id))
    r["nodes_mastered"] = learner.proven_count_current(reader_id=reader_id)
    r["nodes_assumed"] = max(0, learner.mastered_count(reader_id=reader_id)
                             - learner.proven_count_current(reader_id=reader_id))
    return r


@app.get("/api/journal")
def journal_api(request: Request):
    reader_id = current_reader(request)
    items = learner.journal(60, reader_id=reader_id)
    for it in items:
        if it.get("kind") == "mastered":
            node = curr.node(it.get("node_id", ""))
            if node:
                it["title"] = node["title"]
                it["domain"] = node["domain"]
    # The Journey page is where a reader looks for durable proof of who they
    # are becoming — the natural home for a record that outlives any one
    # streak, not something buried in the daily-quest sidebar.
    return {"items": items, "best_streak": learner.best_streak_days(reader_id=reader_id)}


# ---------------- story ----------------

@app.get("/api/story")
def story(request: Request):
    reader_id = current_reader(request)
    prof = learner.get_profile(reader_id=reader_id)
    if not prof:
        # Even the un-onboarded preview must be rendered: the source chapters
        # are tokenised, and raw {SUBJ}/{NAME} on the page is not a story.
        # Nothing is set aside before a reader has chosen fields, so the preview
        # numbers straight through — but it must carry `number` like the real
        # thing, or the page falls back to a different scheme for this one case.
        preview = []
        for i, ch in enumerate(STORY["chapters"]):
            c = _personalize(ch, "")
            c["set_aside"], c["read"], c["number"] = False, False, i + 1
            preview.append(c)
        return {"title": STORY["title"], "about": STORY["about"],
                "chapters": preview, "progress": 0, "can_advance": False}
    cur, progress, can_advance = _story_cursor(prof, reader_id)
    name = prof["name"]
    domains = prof.get("domains") or [d["id"] for d in curr.domains]
    chapters = []
    number = 0
    for i, ch in enumerate(STORY["chapters"]):
        c = _personalize(ch, name, story_mod.reader_pronouns(prof))
        node = curr.node(ch.get("leads_to", "") or "")
        # A chapter skipped because its field was never chosen was not "read".
        c["set_aside"] = bool(node) and node["domain"] not in domains
        c["read"] = i < progress and not c["set_aside"]
        c["current"] = i == progress
        # The reader's own numbering, counted over the reader's own story. The
        # page took its total from the chapters that are NOT set aside while
        # numbering every card from the raw array index, so the same screen
        # could say "11 of 15 chapters earned" and head a card "Chapter 19".
        # A chapter belonging to a field this reader never chose is not their
        # chapter number seven; it has no number in their story at all.
        if not c["set_aside"]:
            number += 1
            c["number"] = number
        else:
            c["number"] = None
        chapters.append(c)
    return {"title": _book_title(name), "about": STORY["about"],
            "chapters": chapters, "progress": progress,
            "can_advance": can_advance,
            "needs": None if can_advance else _story_needs(cur, reader_id)}


@app.post("/api/story/advance")
def story_advance(request: Request):
    reader_id = current_reader(request)
    prof = learner.get_profile(reader_id=reader_id)
    if not prof:
        return JSONResponse({"error": "no profile"}, status_code=400)
    chapter, progress, can_advance = _story_cursor(prof, reader_id, commit=True)
    if not can_advance:
        # The next page opens only once its lesson is mastered.
        return {"progress": progress, "advanced": False,
                "needs": chapter.get("leads_to") if chapter else None}
    settings = dict(prof.get("settings", {}))
    next_progress = progress + 1
    chapters = STORY["chapters"]
    settings["story_chapter_id"] = (chapters[next_progress]["id"]
                                     if next_progress < len(chapters) else chapters[-1]["id"])
    settings.pop("story_progress", None)
    learner.save_profile(prof["name"], prof["age"], prof["hours_per_week"],
                         prof["breadth"], prof["stage"], prof["domains"], settings,
                         reader_id=reader_id)
    learner.log_event("chapter", {"title": chapter.get("title", ""),
                                  "number": next_progress}, xp=15, reader_id=reader_id)
    return {"progress": next_progress, "advanced": True, "xp_gained": 15}


# ---------------- library management ----------------

@app.get("/api/library")
def library_catalog():
    return {"status": wiki.library_status(),
            "catalog": library.catalog_with_status(),
            "downloads": library.downloads_status()}


@app.post("/api/library/download")
def library_download(key: str = Body(..., embed=True)):
    return library.start_download(key)


@app.post("/api/library/rescan")
def library_rescan():
    wiki.rescan()
    return wiki.library_status()


# ---------------- static frontend ----------------

def _asset_tag(name: str) -> str:
    """A short fingerprint of a static file, for cache-busting its URL."""
    try:
        with open(os.path.join(WEB_DIR, name), "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()[:10]
    except OSError:
        return "0"


@app.get("/app/", include_in_schema=False)
@app.get("/app/index.html", include_in_schema=False)
def app_shell():
    """The shell, with the stylesheet and scripts stamped by content hash.

    Without this the browser happily runs today's JavaScript against last
    week's stylesheet: the URLs never changed and the static mount sends no
    Cache-Control. It is not a hypothetical — an accessibility audit measured
    contrast against a stale stylesheet and reported failures the served CSS
    did not have.
    """
    with open(os.path.join(WEB_DIR, "index.html")) as fh:
        html = fh.read()
    html = html.replace("/app/styles.css", "/app/styles.css?v=" + _asset_tag("styles.css"))
    html = html.replace("/app/lesson-models.js", "/app/lesson-models.js?v=" + _asset_tag("lesson-models.js"))
    html = html.replace("/app/app.js", "/app/app.js?v=" + _asset_tag("app.js"))
    return HTMLResponse(html, headers={"Cache-Control": "no-cache"})


@app.get("/")
def index():
    return app_shell()


# ---------------- the door ----------------

# A hosted book still has to ask who is knocking, but it should ask in its own
# voice. The browser's Basic-auth dialog is a grey system box that names a host
# and a port, cannot be styled, cannot be branded, and offers no way back — the
# first thing a reader met was the least book-like surface in the product. The
# page below is the same question asked by the book: its paper, its gold, its
# register. Basic credentials are still accepted on the wire (see
# _is_signed_in) for curl and CI; they are simply never demanded of a person.

def _sign_in_page(error: str = "", status_code: int = 200):
    """The door, rendered without a byte of user input in it.

    The bounce target used to be templated into a hidden field, escaped and
    allowlisted — defensible, but the stronger property is available for
    free: the form posts back to its own URL, so ?next= rides the query
    string and never touches the page. The only slot left is the error
    banner, which carries the server's own sentence and nothing else.
    """
    with open(os.path.join(WEB_DIR, "sign-in.html")) as fh:
        page = fh.read()
    banner = ('<p class="err" role="alert">' + _escape(error) + "</p>") if error else ""
    page = page.replace("{{ERROR}}", banner)
    return HTMLResponse(page, status_code=status_code, headers=_no_store())


@app.get(SIGN_IN_PATH)
def sign_in_form(next: str = "/"):
    username = os.environ.get(ACCESS_USERNAME_ENV) or "primer"
    password = os.environ.get(ACCESS_PASSWORD_ENV)
    if not password:
        # Nothing to sign in to: locally there is no gate, and a hosted
        # deployment without a password has already failed closed upstream.
        return RedirectResponse(_safe_next(next), status_code=303,
                                headers=_no_store())
    return _sign_in_page()


@app.post(SIGN_IN_PATH)
async def sign_in(request: Request):
    password = os.environ.get(ACCESS_PASSWORD_ENV)
    if not password:
        return RedirectResponse("/", status_code=303, headers=_no_store())
    # Parsed here rather than through request.form(): the form is urlencoded
    # and this keeps the multipart parser — and its dependency — out of the
    # one route an unauthenticated stranger can reach.
    body = (await request.body())[:8192].decode("utf-8", "replace")
    form = dict(urllib.parse.parse_qsl(body, keep_blank_values=True))
    # The target arrives on the query string the form posted back to, not in
    # the body: the page carries no user data, so there is no hidden field.
    next_path = _safe_next(request.query_params.get("next") or "/")
    supplied_user = (form.get("username") or "")[:512]
    supplied_password = (form.get("password") or "")[:1024]
    username = os.environ.get(ACCESS_USERNAME_ENV) or "primer"
    ok = (secrets.compare_digest(supplied_user.encode("utf-8"),
                                 username.encode("utf-8"))
          and secrets.compare_digest(supplied_password.encode("utf-8"),
                                     password.encode("utf-8")))
    if not ok:
        # One message for a wrong reader and a wrong word alike: naming which
        # half was wrong tells an intruder which half to keep.
        log.info("sign-in refused")
        return _sign_in_page(
            "That is not the word this copy knows. Try again.", 401)
    response = RedirectResponse(next_path, status_code=303, headers=_no_store())
    response.set_cookie(
        ACCESS_COOKIE, _access_token(username, password),
        max_age=ACCESS_MAX_AGE, httponly=True, samesite="lax",
        # Secure only where there is TLS to be had: a Secure cookie is dropped
        # silently over plain http, which would lock out a local run behind a
        # password without ever saying why.
        secure=bool(os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV")),
        path="/")
    return response


@app.post("/sign-out")
def sign_out():
    response = RedirectResponse(SIGN_IN_PATH, status_code=303,
                                headers=_no_store())
    response.delete_cookie(ACCESS_COOKIE, path="/")
    return response


@app.get("/healthz")
def healthz():
    return {"ok": True, "nodes": len(curr.nodes), "archives": len(wiki.archives)}




class _CachedStatic(StaticFiles):
    """Fingerprinted assets may be cached hard; everything else revalidates."""

    def file_response(self, *args, **kwargs):
        resp = super().file_response(*args, **kwargs)
        full_path = kwargs.get("full_path") or (args[0] if args else None)
        # Some slim serverless Python images do not ship an OS MIME database
        # entry for WebP, so Starlette falls back to text/plain.  The app also
        # sends nosniff; make the raster contract explicit and portable rather
        # than relying on the host's /etc/mime.types.
        if full_path is not None and os.fspath(full_path).lower().endswith(".webp"):
            resp.headers["Content-Type"] = "image/webp"
        scope = kwargs.get("scope") or (args[2] if len(args) > 2 else None)
        query = ""
        if isinstance(scope, dict):
            query = (scope.get("query_string") or b"").decode("latin-1")
        if "v=" in query:
            resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        else:
            resp.headers["Cache-Control"] = "no-cache"
        return resp


if os.path.isdir(WEB_DIR):
    app.mount("/app", _CachedStatic(directory=WEB_DIR, html=True), name="static")
