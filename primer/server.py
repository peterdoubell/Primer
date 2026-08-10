"""The Primer server: one FastAPI app binding content, curriculum, learner,
practice, quizzes, tutor and pacing into a single interactive book.
"""

import contextvars
import datetime
import hashlib
import json
import logging
import os
import random
import secrets
import threading
import time
import uuid
from contextlib import asynccontextmanager
from typing import List, Literal, Optional

from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse, Response, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from . import library, practice, quiz, tutor
from . import sittings as sittings_mod
from . import story as story_mod
from .curriculum import Curriculum
from .learner import LearnerStore, STAGE_NAMES, STAGE_SPAN, STAGE_TITLES
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
            try:
                os.remove(os.path.join(dest_dir, f))
            except OSError:
                pass


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


def _maintenance_loop():
    """Back up the irreplaceable learner record and prune old logs — at
    startup and then daily. The whole multi-year history lives in one file."""
    while True:
        try:
            if learner.get_profile() is not None:
                # Retention is ours, not the store's flat "newest N": pass a
                # keep the rotation can never hit, then apply the tiered
                # policy in _prune_backups.
                dest = learner.backup(BACKUP_DIR, keep=10 ** 6)
                if os.path.isdir(BACKUP_DIR):
                    _prune_backups(BACKUP_DIR)
                learner.prune()
                if dest:
                    log.info("backed up learner record to %s", os.path.basename(dest))
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
    (log.warning if bk["off_disk"] is False else log.info)(
        "backups -> %s (%d kept) | %s", bk["dir"], bk["copies"], bk["advice"])
    threading.Thread(target=_maintenance_loop, daemon=True).start()
    yield
    # Let the maintenance thread finish its wait and return rather than being
    # killed mid-backup when the process exits.
    _shutdown.set()


app.router.lifespan_context = _lifespan


# Second line of defence behind the HTML sanitizer: even if untrusted article
# markup ever slipped through, it could not load or run code. Applied as
# middleware so it covers every route — including the static mount, which would
# otherwise serve an identical, unprotected copy of the app shell.
CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
    "base-uri 'none'; frame-ancestors 'none'; form-action 'none'"
)


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


def _public_node(node: dict) -> dict:
    """A node as the reader may see it. Anything that serialises a node goes
    through here — stripping the bank route by route is how keys leak."""
    out = {k: v for k, v in node.items() if k not in _NODE_PRIVATE}
    out["question_count"] = len(node.get("quiz") or [])
    return out


def _check_ascension(prof: dict) -> Optional[dict]:
    """If the reader has newly opened a higher stage in any domain, record a
    stage-ascension ceremony and return it once."""
    gates = learner.gate_map()
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
                             prof["domains"], settings)
        info = {"stage": rank, "name": STAGE_NAMES[min(rank, 5)],
                "title": STAGE_TITLES[min(rank, 5)]}
        learner.log_event("ascension", info)
        return info
    return None


def _book_title(name: str) -> str:
    return story_mod.book_title(STORY, name)


def _personalize(chapter: dict, name: str,
                 pronouns: str = story_mod.DEFAULT_PRONOUNS) -> dict:
    return story_mod.personalize(chapter, name, pronouns)


def _story_cursor(prof: dict, commit: bool = False):
    """The reader's chapter, whether it may turn, and what it wants — see
    primer.story for the cursor's invariants. commit=True only from a write
    endpoint: a GET must not persist."""
    return story_mod.cursor(STORY, curr, learner, prof, commit)


def _story_needs(chapter: Optional[dict]) -> Optional[dict]:
    return story_mod.needs(curr, learner, chapter)


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
    pronouns: Literal["she", "he", "they"] = story_mod.DEFAULT_PRONOUNS
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
    return out


@app.get("/api/state")
def state():
    profile = _profile_view(learner.get_profile())
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
def save_profile(p: ProfileIn):
    stage = LearnerStore.stage_for_age(p.age)
    existing = learner.get_profile()
    first_time = existing is None
    # Pronouns live in settings (that is where reader preferences live), so
    # they have to be merged rather than passed positionally — and merged onto
    # the existing settings, or re-saving a profile would wipe the reader's
    # theme and story position along with them.
    settings = dict((existing or {}).get("settings") or {})
    settings["pronouns"] = p.pronouns
    learner.save_profile(p.name, p.age, p.hours_per_week, p.breadth, stage,
                         p.domains, settings)
    # Meet the reader at their age: on first setup, credit the stages below
    # their placement as "assumed known" (not proven) so Today starts at their
    # level. A per-domain placement check can later verify or adjust this.
    if first_time and stage > 0:
        learner.seed_assumed(curr.seed_mastery_for_stage(stage))
    log.info("profile saved: %s age=%s stage=%s breadth=%s", p.name, p.age, stage, p.breadth)
    return _profile_view(learner.get_profile())


# Only the reader's own preferences are writable here — `placed`, `rank` and
# `story_progress` are the book's record of what happened, never client input,
# and no field is accepted that nothing reads back. Typed values; extras are
# tolerated at the parse step (extra="allow") only so they can be refused by
# name in the response — a bare 422 would hide *which* key was the problem.
class SettingsIn(BaseModel):
    model_config = {"extra": "allow"}
    theme: Optional[str] = None
    speak: Optional[bool] = None
    reduce_motion: Optional[bool] = None
    font_scale: Optional[float] = None
    name_pronunciation: Optional[str] = None
    # Reader-owned privacy switch: False keeps the tutor fully local even
    # when an ANTHROPIC_API_KEY is set (see _tutor_remote_allowed).
    tutor_remote_ok: Optional[bool] = None
    # Changeable after onboarding: a reader who was mis-set, or who changes
    # how they are addressed, must not have to rebuild their profile to fix
    # the story's pronouns.
    pronouns: Optional[Literal["she", "he", "they"]] = None


READER_SETTINGS = set(SettingsIn.model_fields)


@app.post("/api/profile/settings")
def save_settings(settings: SettingsIn):
    prof = learner.get_profile()
    if not prof:
        return JSONResponse({"error": "no profile"}, status_code=400)
    rejected = sorted((settings.model_extra or {}).keys())
    if rejected:
        log.warning("refused client write to server-owned settings: %s", rejected)
    merged = dict(prof.get("settings", {}))
    merged.update({k: getattr(settings, k) for k in settings.model_fields_set
                   if k in READER_SETTINGS})
    saved = learner.save_profile(prof["name"], prof["age"], prof["hours_per_week"],
                                 prof["breadth"], prof["stage"], prof["domains"], merged)
    saved = _profile_view(saved)
    if rejected:
        saved = dict(saved)
        saved["refused"] = rejected
    return saved


# ---------------- articles & search ----------------

@app.get("/api/article")
def article(title: str, simple: Optional[bool] = None, log_read: bool = True):
    prof = learner.get_profile()
    prefer_simple = simple if simple is not None else (prof and prof["stage"] <= 1)
    art = wiki.get_article(title, prefer_simple=bool(prefer_simple))
    if not art:
        return JSONResponse({"error": "not found", "title": title}, status_code=404)
    art["rendered"] = rewrite_article(art["html"], art.get("base", ""))
    del art["html"]
    if log_read:
        learner.log_reading(art["title"])
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
ASSET_HEADERS = {
    "Cache-Control": "public, max-age=604800",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "default-src 'none'; sandbox",
}


def _safe_asset_response(data: bytes, mime: str) -> Response:
    base = (mime or "").split(";")[0].strip().lower()
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
    return _safe_asset_response(data, mime)


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
def curriculum():
    graph = curr.annotated_graph(learner.gate_map())
    proven = learner.proven_set()
    ever = learner.ever_proven_set()
    credited = learner.credited_set()
    stale = learner.assumed_stale_set()
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


@app.get("/api/curriculum/node/{node_id}")
def curriculum_node(node_id: str):
    node = curr.node(node_id)
    if not node:
        return JSONResponse({"error": "no such node"}, status_code=404)
    gates = learner.gate_map()
    out = _public_node(node)
    out["mastery"] = round(learner.mastery_map().get(node_id, 0), 2)
    out["mastered"] = node_id in learner.mastered_set()
    out["proven"] = node_id in learner.proven_set()
    out["ever_proven"] = node_id in learner.ever_proven_set()
    out["faded"] = out["ever_proven"] and not out["proven"]
    out["assumed"] = (node_id in learner.credited_set() and not out["proven"]
                      and not out["ever_proven"])
    out["assumed_stale"] = node_id in learner.assumed_stale_set()
    out["mastery_detail"] = learner.mastery_detail(node_id)
    out["unlocked"] = curr.unlocked(node, gates)
    if not out["unlocked"] and not out["mastered"]:
        out["unlock_requirements"] = curr.unlock_requirements(node, gates)
    # Two-way tissue: a lesson should say which chapter it opens.
    prof = learner.get_profile()
    if prof:
        cur, progress, _ = _story_cursor(prof)
        if cur and cur.get("leads_to") == node_id:
            needs = _story_needs(cur) or {}
            out["opens_chapter"] = {"title": cur["title"], "number": progress + 1}
            out["passes_needed"] = needs.get("passes_needed")
    cards = []
    for title in node["articles"][:6]:
        s = wiki.get_summary(title)
        cards.append({"title": title, "summary": (s or {}).get("extract", "")[:280],
                      "thumb": (s or {}).get("thumbnail", "")})
    out["article_cards"] = cards
    return out


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


def _remember(questions: list, purpose: str, subject: str = "") -> str:
    """Remember a served paper, bound to what it was issued for.

    The binding matters: without it a token from a trivial counting drill can be
    redeemed as a graduate-level quiz, or as a stage-5 placement pass. A paper is
    only ever valid for the exact thing it was handed out for.
    """
    token = secrets.token_urlsafe(12)
    now = time.time()
    with _SERVED_LOCK:
        _SERVED[token] = {"questions": [dict(q) for q in questions], "at": now,
                          "purpose": purpose, "subject": subject, "committed": {},
                          "issued_at": now}
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


def _recall(token: str, purpose: str, subject: str = ""):
    """The server's own copy of a served paper, or None.

    There is deliberately NO fallback to a client-supplied copy: the token is
    caller-controlled, so any fallback can be forced simply by omitting it —
    which is exactly how an earlier version of this was defeated. Tokens are
    single-use, and are only honoured for the purpose and subject they were
    issued against.
    """
    with _SERVED_LOCK:
        entry = _live_paper(token)
        if entry is None:
            return None
        if entry["purpose"] != purpose or entry["subject"] != subject:
            log.warning("token issued for %s/%s redeemed as %s/%s — refused",
                        entry["purpose"], entry["subject"][:40], purpose, subject[:40])
            return None
        # Claim it inside the lock: two threads must not both walk away with it.
        _SERVED.pop(token, None)
    return entry


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


@app.get("/api/today")
def today():
    """The adaptive home: a stable daily quest — review first, then new
    lessons across the reader's domains, then mixed practice."""
    prof = learner.get_profile()
    if not prof:
        return JSONResponse({"error": "no profile"}, status_code=400)
    gates = learner.gate_map()
    domains = prof["domains"] or [d["id"] for d in curr.domains]
    lessons = [_public_node(n) for n in curr.next_lessons(gates, domains, per_domain=1)]
    # Stable order for the day (no reshuffle on refresh), but varied day to day.
    rng = random.Random(_daily_seed() + int(prof.get("created_at", 0)))
    rng.shuffle(lessons)
    lessons = lessons[:5]

    deck = learner.deck_stats()
    reading = learner.reading_stats()
    refresh = learner.nodes_needing_refresh(4)
    refresh_titles = [{"id": nid, "title": (curr.node(nid) or {}).get("title", nid)}
                      for nid in refresh]

    # The day's quest — completion reflects work actually done today. Every
    # step is built through this one function so the excusal rule cannot
    # diverge between steps: a step with nothing available to do (empty deck,
    # exhausted frontier) is excused, never left blocking the crown.
    def step(label, done, count, hint=None):
        return {"label": label, "done": done, "count": count,
                # Excused only when the reader has not already done it AND
                # there is genuinely nothing available to do.
                "excused": not done and count == 0,
                "hint": hint if not done and count == 0 else None}

    quest = {
        "review": step("Strengthen your memory", _events_today("review"), deck["due"],
                       "Deck is clear — nothing due" if deck["total"]
                       else "Pass a lesson quiz and the book will start your deck"),
        "learn": step("Learn something new", _events_today("attempt"), len(lessons),
                      "You are at the frontier of every subject you chose — "
                      "add another from your profile, or review to keep it solid"),
        # No count to exhaust: an article is always available to read, so this
        # step can never be excused. `None` is not zero.
        "read": step("Read one article", _events_today("read"), None),
    }
    quest_done = sum(1 for k in quest.values() if k["done"])
    quest_total = sum(1 for k in quest.values() if not k["excused"])

    story, progress, story_can_advance = _story_cursor(prof, commit=True)

    return {
        "profile": prof,
        "lessons": lessons,
        "deck": deck,
        "reading": reading,
        "refresh": refresh_titles,
        "mastered": learner.proven_count_current(),
        # Both sides of this subtraction now come from the same decay-aware
        # definition. Before, `mastered_count()` was decay-aware while
        # `proven_count()` counted every node ever earned regardless of
        # freshness — so a faded node counted on the proven side but not the
        # mastered side, and the difference went negative.
        "assumed": max(0, learner.mastered_count() - learner.proven_count_current()),
        "xp_today": learner.xp_today(),
        "streak": prof["streak"],
        "best_streak": learner.best_streak_days(),
        "streak_milestone": learner.streak_milestone(),
        "freezes_left": learner.freezes_left(),
        "active_today": learner.active_today(),
        "quest": quest,
        "quest_done": quest_done,
        "quest_total": quest_total,
        "story": story,
        "story_progress": progress,
        "story_can_advance": story_can_advance,
        "story_needs": None if story_can_advance else _story_needs(story),
        "story_title": _book_title(prof["name"]),
    }


def _events_today(kind: str) -> bool:
    """Whether this kind of event was logged today — the store's own question."""
    return bool(learner.events_today(kind))


# A graded paper is never one question long. A single item can be lucky, and a
# lone constructed-response item is worth a whole node's mastery only if the
# reader can be trusted not to want that — which is not a safe assumption to
# build an education on.
QUIZ_MIN_ITEMS = 4
QUIZ_MAX_ITEMS = 12


# ---------------- practice ----------------

@app.get("/api/practice/{gen_key}")
def practice_set(gen_key: str, n: int = 6, level: int = 1, node_id: str = ""):
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
    return {"generator": gen_key, "token": _remember(qs, "practice", node_id),
            "questions": _public(qs)}


class AttemptIn(BaseModel):
    node_id: str
    answers: List[str] = []
    token: str = ""


@app.post("/api/attempt")
def record_attempt(a: AttemptIn):
    # Practice is graded here, from the book's own copy of the paper. There is
    # no self-reported score to accept.
    entry = _recall(a.token, "practice", a.node_id)
    graded = entry["questions"] if entry else None
    if graded is None:
        return JSONResponse({"error": "this practice was not issued for this lesson"},
                            status_code=409)
    given = _final_answers(entry, a.answers)
    scorable, scorable_given, _spent = _drop_burned(graded, given, a.node_id, entry)
    if len(scorable) < min(QUIZ_MIN_ITEMS, len(graded)):
        return JSONResponse(
            {"error": "the book has already shown you the answers to most of "
                      "these. Come back to this one in a few days."}, status_code=409)
    score = quiz.score_quiz(scorable, scorable_given)["score"]
    # A drill can be run without a lesson behind it (/api/practice/{gen} with
    # no node_id mints a token bound to ""), and that is fine to *do* — but it
    # must not be recorded. Writing mastery and XP against the empty-string
    # node created a ledger row for a lesson that does not exist and paid for
    # it. Grade it, return the marks, record nothing.
    if not a.node_id or curr.node(a.node_id) is None:
        return {"score": score, "xp_gained": 0, "unlessoned": True,
                "cards_added": 0, "ascension": None}
    res = learner.record_attempt(a.node_id, score)
    # Practice is a study event too: whatever was missed should come back.
    cards_added = 0
    if graded and given:
        node = curr.node(a.node_id)
        article = node["articles"][0] if node and node["articles"] else ""
        missed = [q for q in quiz.cards_from_missed(graded, given, a.node_id, article)
                  if not _is_ephemeral(graded, q)]
        cards_added = learner.add_cards(missed)
    res["cards_added"] = cards_added
    res["ascension"] = _check_ascension(learner.get_profile()) if res.get("newly_mastered") else None
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
    keep = [q for q in questions if q.get("kind") in ("numeric", "short", "order")]
    drop = [q for q in questions if q not in keep]
    return (keep + drop)[:max(0, n - 1)] + extra


@app.get("/api/quiz/{node_id}")
def quiz_for_node(node_id: str, n: int = 6):
    """Draw a paper from the node's bank — assembled in ONE pass, deliberately;
    layered patches here have fought each other before.

    Order of business: draw from the bank, top up from the node's own drill,
    give the youngest an ordering item, then append the unmarked reflection
    item. Auto-generated cloze is deliberately absent — successive hand audits
    put its defect rate at 65%, then 90%, then 55% after the 2026-08 precision
    pass (tools/hand-audit-cloze-2026-08.md) — and as of that audit it is
    absent from the whole app: the self-check that served it is withdrawn.
    """
    node = curr.node(node_id)
    if not node:
        return JSONResponse({"error": "no such node"}, status_code=404)
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
            "token": _remember(questions, "quiz", node_id), "questions": _public(questions)}


class CheckIn(BaseModel):
    token: str
    id: int
    answer: str = ""


def _drop_burned(questions: list, given: list, node_id: str, entry: dict = None):
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
    burned = learner.burned_map(node_id)
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
def check_one(c: CheckIn):
    """Grade a single item so the reader gets immediate feedback.

    The answer is revealed only *after* they commit to one — which is what
    teaches — while the key itself never ships with the paper.
    """
    # Same liveness rule as the submit this sitting ends with — an expired
    # paper must not still be marking items (and burning them) here only to
    # be refused there. Looked up inside the lock, like every other read of
    # _SERVED: this entry is mutated below.
    with _SERVED_LOCK:
        entry = _live_paper(c.token)
    if not entry:
        return JSONResponse({"error": "unknown quiz token"}, status_code=409)
    if entry["purpose"] == "placement":
        # A placement check measures what the reader already knows; walking it
        # item by item for the answers turns it into a coaching session and then
        # a clean pass. Placement is sat once, in the dark.
        return JSONResponse({"error": "a placement check is marked at the end"},
                            status_code=409)
    questions = entry["questions"]
    q = next((x for x in questions if x.get("id") == c.id), None)
    if q is None:
        return JSONResponse({"error": "no such question"}, status_code=404)
    if not (c.answer or "").strip():
        return JSONResponse({"error": "answer first — then the book will tell you"},
                            status_code=400)
    # First commitment stands: seeing the key cannot retroactively improve it.
    # Re-read under the lock and write the whole map back: the store is
    # persistent, so a nested in-place mutation would only ever touch a copy.
    with _SERVED_LOCK:
        fresh = _SERVED.get(c.token) or entry
        committed = dict(fresh.get("committed") or {})
        committed.setdefault(c.id, {"answer": c.answer, "at": time.time()})
        fresh["committed"] = committed
        locked = committed[c.id]["answer"]
    correct = quiz.score_quiz([q], [locked])["score"] >= (0.6 if q.get("kind") == "short" else 1.0)
    # A wrong answer spends the item: the reader is about to be told, and for the
    # next week that item cannot be the evidence they know it — otherwise a paper
    # is read for its answers, discarded, and a clean one sat a moment later.
    # A *correct* answer spends nothing. Being shown the answer you already gave
    # teaches nothing and reveals nothing, and burning it refused an honest
    # reader their own pass on every sitting, permanently.
    node_for = q.get("node_id") or (entry["subject"] if entry["purpose"] in
                                    ("quiz", "practice") else "")
    if node_for and not correct:
        learner.burn_item(node_for, _fingerprint(q))
    return {"correct": correct, "answer": q.get("answer", ""),
            "explain": q.get("explain", ""), "keywords": q.get("keywords", []),
            "locked": locked}


# Deliberately NO `questions` field: the server grades from its own copy of
# the paper, so a client-supplied bank is never even parsed. (It used to be
# accepted and ignored, which reads like an input when it is not one.)
class QuizSubmitIn(BaseModel):
    node_id: str
    answers: List[str]
    make_cards: bool = True
    token: str = ""
    confidence: List[int] = []   # per-item self-rating, for calibration


@app.post("/api/quiz/submit")
def submit_quiz(s: QuizSubmitIn):
    entry = _recall(s.token, "quiz", s.node_id)
    if entry is None:
        return JSONResponse({"error": "this paper was not issued for this lesson"},
                            status_code=409)
    questions = entry["questions"]
    given = _final_answers(entry, s.answers)
    # Measurement drops the items whose keys were shown; the deck does not. An
    # item the reader got wrong and was then told the answer to is exactly what
    # should come back tomorrow, whether or not it still counts for anything.
    scorable, scorable_given, spent = _drop_burned(questions, given, s.node_id, entry)
    # The floor is on what is *scored*, not on what was served. Enforcing it only
    # at serve time let a burnt-out bank be graded on the one or two procedural
    # top-ups that were left — a thirteen-item paper marked `total: 1`, and
    # random guessing proved undergraduate calculus in seven sittings.
    if len(scorable) < QUIZ_MIN_ITEMS:
        return JSONResponse(
            {"error": "the book has already shown you the answers to most of "
                      "these. Come back to this one in a few days.",
             "spent": spent}, status_code=409)
    result = quiz.score_quiz(scorable, scorable_given)
    mastery = learner.record_attempt(s.node_id, result["score"])
    cards_added = 0
    if s.make_cards:
        node = curr.node(s.node_id)
        article = node["articles"][0] if node and node["articles"] else ""
        # Errors are exactly what should come back tomorrow — always build cards
        # from missed items, regardless of overall score.
        missed = quiz.cards_from_missed(questions, given, s.node_id, article)
        cards_added += learner.add_cards(missed)
        # Young lessons always yield concept cards: a child who failed needs the
        # review most, and their questions are procedural so misses mint nothing.
        if node and node["stage"] <= 1:
            cards_added += learner.add_cards(quiz.cards_from_lesson(
                node["title"], node.get("goal", ""), node.get("kid_text", ""), s.node_id))
        elif result["score"] >= 0.5 and node:
            if node["stage"] >= 2 and node["articles"]:
                # Older readers: durable cards drawn from the article itself.
                art = wiki.get_article(node["articles"][0])
                if art:
                    text = wiki.article_plaintext(art["html"], 4000)
                    cards_added += learner.add_cards(
                        quiz.cards_from_text(node["articles"][0], text, s.node_id))
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
        learner.log_event("calibration", {"node": s.node_id, **calibration})
    ascension = _check_ascension(learner.get_profile()) if mastery.get("newly_mastered") else None
    return {"result": result, "mastery": mastery, "cards_added": cards_added,
            "ascension": ascension, "calibration": calibration}


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

@app.get("/api/review/due")
def review_due(limit: int = 20):
    return {"cards": learner.due_cards(limit), "stats": learner.deck_stats()}


class ReviewIn(BaseModel):
    card_id: int
    quality: int


@app.post("/api/review")
def review(r: ReviewIn):
    return learner.review_card(r.card_id, max(0, min(5, r.quality)))


class CardIn(BaseModel):
    front: str
    back: str
    article: str = ""
    node_id: str = ""


@app.post("/api/review/add")
def add_card(c: CardIn):
    """A card the reader writes for themselves. Marked as theirs, so it can be
    studied like any other but cannot stand in as evidence of mastery."""
    card = c.model_dump() if hasattr(c, "model_dump") else c.dict()
    card["origin"] = "reader"
    return {"added": learner.add_cards([card])}


# ---------------- placement ----------------

def _placement_rung(domain: str, prof: Optional[dict]) -> Optional[int]:
    """The rung the book is willing to offer next for this domain.

    The staircase used to be entirely the client's to walk: it named the stage
    it wanted, so a reader could open at stage 5, pass one paper and settle
    there. The server now decides where the ladder starts and where it goes
    next, and refuses papers for any other rung.
    """
    state = learner.placement_state().get(domain, {})
    if state.get("done"):
        return None
    asked = state.get("asked") or []
    if not asked:
        # Start from where their age would put them, never above it.
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


def _placement_reopen(domain: str) -> bool:
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
        return bool(fn(domain))
    except Exception as exc:
        log.warning("placement reopen for %s failed: %s", domain, exc)
        return False


@app.get("/api/placement/next")
def placement_next(domain: str, stage: Optional[int] = None, n: int = 6,
                   recheck: bool = False):
    """Serve a short, server-scored placement check at the rung the book chooses.

    Prefers the expert-authored item bank (the most valid measure we have),
    topped up with the node's own practice generator. `recheck=true` asks to
    re-measure a settled domain; honoured only when the store supports
    reopening and its cooling period has passed.
    """
    prof = learner.get_profile()
    rung = _placement_rung(domain, prof)
    if rung is None and recheck and _placement_reopen(domain):
        rung = _placement_rung(domain, prof)
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
            "token": _remember(served, "placement", "{}:{}".format(domain, stage)),
            "questions": _public(served)}


class PlacementSubmitIn(BaseModel):
    domain: str
    stage: int
    # No `questions` field, same rule as QuizSubmitIn: the server's copy grades.
    answers: List[str]
    token: str = ""


@app.post("/api/placement/submit")
def placement_submit(s: PlacementSubmitIn):
    """Score placement answers *on the server* (never the client's word) and
    walk an adaptive staircase: pass → try the next stage up; fail → step down.
    When the staircase settles, the reader's stage is actually updated."""
    prof = learner.get_profile()
    expected = _placement_rung(s.domain, prof)
    if expected is None or int(s.stage) != expected:
        return JSONResponse({"error": "that is not the rung this check is on",
                             "expected_stage": expected}, status_code=409)
    entry = _recall(s.token, "placement", "{}:{}".format(s.domain, s.stage))
    questions = entry["questions"] if entry else None
    if questions is None:
        return JSONResponse({"error": "this paper was not issued for this check"},
                            status_code=409)
    given = _final_answers(entry, s.answers)
    result = quiz.score_quiz(questions, given)
    passed = result["score"] >= 0.7
    credited_through = -1
    state = learner.placement_state().get(s.domain, {})
    history = list(state.get("asked", []))
    history.append({"stage": s.stage, "score": round(result["score"], 2), "passed": passed})

    if passed:
        next_stage = s.stage + 1 if s.stage < 5 else None
    else:
        next_stage = s.stage - 1 if s.stage > 0 else None

    # The staircase stops when it reverses direction or runs off either end.
    tried = {h["stage"] for h in history}
    settled = next_stage is None or next_stage in tried
    if settled:
        placed = max([h["stage"] for h in history if h["passed"]], default=-1) + 1
        placed = max(0, min(placed, 5))
        # Credit is granted once, at settle time — not on every passing rung.
        credited_through = placed - 1
        if placed > 0:
            learner.seed_assumed(curr.seed_mastery_for_stage(placed, [s.domain]))
        # Placement can also place a reader *down*. Age-seeded credit above where
        # they actually landed is not evidence of anything and must not stand.
        stale = [nid for nid, nd in curr.nodes.items()
                 if nd["domain"] == s.domain and nd["stage"] >= placed]
        learner.revoke_assumed(stale)
        if prof:
            # Placement is evidence, so it may move the reader either way — but
            # a single domain's result must not overwrite their whole reading
            # level. The global stage is the median of what has been measured.
            settings = dict(prof.get("settings", {}))
            per_domain = dict(settings.get("placed", {}))
            per_domain[s.domain] = placed
            settings["placed"] = per_domain
            measured = sorted(per_domain.values())
            if len(measured) < 2:
                # One domain is not a reading level: keep the age placement
                # unless this single result is *lower*, which is safe.
                overall = min(int(prof["stage"] or 0), measured[0])
            else:
                overall = measured[(len(measured) - 1) // 2]   # lower median
            learner.save_profile(prof["name"], prof["age"], prof["hours_per_week"],
                                 prof["breadth"], overall, prof["domains"], settings)
        next_stage = None
        log.info("placement settled: %s at stage %d", s.domain, placed)
    learner.placement_update(s.domain, s.stage, history, settled)
    return {"domain": s.domain, "score": round(result["score"], 2), "passed": passed,
            "credited_through_stage": credited_through, "suggest_stage": next_stage,
            "settled": settled}


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


@app.post("/api/tutor")
def ask_tutor(t: TutorIn):
    prof = learner.get_profile()
    stage = prof["stage"] if prof else 2
    excerpt = t.excerpt
    if not excerpt and t.title:
        s = wiki.get_summary(t.title)
        excerpt = (s or {}).get("extract", "")
    messages = [m.model_dump() for m in t.messages]
    return tutor.ask(messages, t.title, excerpt, stage,
                     allow_remote=_tutor_remote_allowed(prof))


# ---------------- roadmap & journal ----------------

@app.get("/api/roadmap")
def roadmap_api():
    prof = learner.get_profile()
    if not prof:
        return JSONResponse({"error": "no profile"}, status_code=400)
    # Pace against what the reader can still be expected to need to learn.
    # Placement-assumed nodes are treated as covered for scheduling, but the
    # headline "mastered" count reports only what has actually been proven.
    r = roadmap(prof, curr.graph(), learner.gate_map(), proven=learner.proven_set())
    r["nodes_mastered"] = learner.proven_count_current()
    r["nodes_assumed"] = max(0, learner.mastered_count() - learner.proven_count_current())
    return r


@app.get("/api/journal")
def journal_api():
    items = learner.journal(60)
    for it in items:
        if it.get("kind") == "mastered":
            node = curr.node(it.get("node_id", ""))
            if node:
                it["title"] = node["title"]
                it["domain"] = node["domain"]
    # The Journey page is where a reader looks for durable proof of who they
    # are becoming — the natural home for a record that outlives any one
    # streak, not something buried in the daily-quest sidebar.
    return {"items": items, "best_streak": learner.best_streak_days()}


# ---------------- story ----------------

@app.get("/api/story")
def story():
    prof = learner.get_profile()
    if not prof:
        # Even the un-onboarded preview must be rendered: the source chapters
        # are tokenised, and raw {SUBJ}/{NAME} on the page is not a story.
        return {"title": STORY["title"], "about": STORY["about"],
                "chapters": [_personalize(ch, "") for ch in STORY["chapters"]],
                "progress": 0, "can_advance": False}
    cur, progress, can_advance = _story_cursor(prof)
    name = prof["name"]
    domains = prof.get("domains") or [d["id"] for d in curr.domains]
    chapters = []
    for i, ch in enumerate(STORY["chapters"]):
        c = _personalize(ch, name, story_mod.reader_pronouns(prof))
        node = curr.node(ch.get("leads_to", "") or "")
        # A chapter skipped because its field was never chosen was not "read".
        c["set_aside"] = bool(node) and node["domain"] not in domains
        c["read"] = i < progress and not c["set_aside"]
        c["current"] = i == progress
        chapters.append(c)
    return {"title": _book_title(name), "about": STORY["about"],
            "chapters": chapters, "progress": progress,
            "can_advance": can_advance, "needs": None if can_advance else _story_needs(cur)}


@app.post("/api/story/advance")
def story_advance():
    prof = learner.get_profile()
    if not prof:
        return JSONResponse({"error": "no profile"}, status_code=400)
    chapter, progress, can_advance = _story_cursor(prof, commit=True)
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
                         prof["breadth"], prof["stage"], prof["domains"], settings)
    learner.log_event("chapter", {"title": chapter.get("title", ""),
                                  "number": next_progress}, xp=15)
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
    """The shell, with the stylesheet and script stamped by content hash.

    Without this the browser happily runs today's JavaScript against last
    week's stylesheet: the URLs never changed and the static mount sends no
    Cache-Control. It is not a hypothetical — an accessibility audit measured
    contrast against a stale stylesheet and reported failures the served CSS
    did not have.
    """
    with open(os.path.join(WEB_DIR, "index.html")) as fh:
        html = fh.read()
    html = html.replace("/app/styles.css", "/app/styles.css?v=" + _asset_tag("styles.css"))
    html = html.replace("/app/app.js", "/app/app.js?v=" + _asset_tag("app.js"))
    return HTMLResponse(html, headers={"Cache-Control": "no-cache"})


@app.get("/")
def index():
    return app_shell()


@app.get("/healthz")
def healthz():
    return {"ok": True, "nodes": len(curr.nodes), "archives": len(wiki.archives)}




class _CachedStatic(StaticFiles):
    """Fingerprinted assets may be cached hard; everything else revalidates."""

    def file_response(self, *args, **kwargs):
        resp = super().file_response(*args, **kwargs)
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
