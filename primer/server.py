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
import sqlite3
import threading
import time
import uuid
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse, Response, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import library, practice, quiz, tutor
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

# Importing this module attaches to a real reader's record — their mastery,
# their streak, their story position. A throwaway script written to poke at
# one endpoint gets the live book unless it knows to rebind srv.learner and
# srv.wiki by hand (which is what tests/test_api.py does). PRIMER_DB makes
# isolation the easy thing to ask for instead of the thing you have to know
# about: set it and the whole process — store, wiki cache, backups — lands
# somewhere disposable.
DB_PATH = os.environ.get("PRIMER_DB") or os.path.join(ROOT, "content", "primer.db")
BACKUP_DIR = os.environ.get("PRIMER_BACKUP_DIR") or (
    os.path.join(os.path.dirname(DB_PATH), "backups")
    if os.environ.get("PRIMER_DB") else os.path.join(ROOT, "content", "backups"))
WEB_DIR = os.path.join(ROOT, "web")
STORY_PATH = os.path.join(ROOT, "data", "story", "frame.json")

app = FastAPI(title="The Primer")

wiki = WikiService(DB_PATH)
curr = Curriculum()
learner = LearnerStore(DB_PATH)
with open(STORY_PATH) as f:
    STORY = json.load(f)


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
        time.sleep(24 * 3600)


@asynccontextmanager
async def _lifespan(_app):
    threading.Thread(target=_maintenance_loop, daemon=True).start()
    yield


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
    """A node as the reader may see it.

    This exists because the bank was stripped route by route as each leak was
    noticed — `graph()` dropped it, `/api/curriculum/node` did not until it was
    caught, and `/api/today` still did afterwards, publishing the complete key
    for every frontier lesson on the endpoint the app fetches on every load.
    Anything that serialises a node goes through here now.
    """
    out = {k: v for k, v in node.items() if k not in _NODE_PRIVATE}
    out["question_count"] = len(node.get("quiz") or [])
    return out


def _check_ascension(prof: dict) -> Optional[dict]:
    """If the reader has newly opened a higher stage in any domain, record a
    stage-ascension ceremony and return it once."""
    gates = learner.gate_map()
    # The reader's level is what they can do across their fields, not their best
    # single one: take the lower median so one domain cannot promote them.
    #
    # "Their fields" means the ones they chose. Taking the median over all ten
    # counted seven subjects the reader never opted into as evidence against
    # them, and onboarding actively encourages choosing a few — so a focused
    # reader who mastered every node in both their domains, preschool through
    # graduate, still ranked 1: the median of {5, 5, 1, 1, 1, 1, 1, 1, 1, 1}.
    # The ceremony could never fire, and because stage drives quiz difficulty,
    # the story window and the read-aloud UI mode, all of it stayed frozen at
    # the level they started. The placement path already scopes to the
    # reader's own domains; this is the same rule, applied in the one place
    # that had been left global.
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
    """The frame story is titled for its heroine; give it to the reader."""
    if not name or name.strip().lower() == "nell":
        return STORY["title"]
    return STORY["title"].replace("Nell", name)


def _personalize(chapter: dict, name: str) -> dict:
    """The reader is the protagonist. The frame story is written about 'Nell';
    swap in the reader's own name so the book is about them."""
    if not name or name.strip().lower() in ("nell", ""):
        return chapter
    out = dict(chapter)
    out["text"] = [t.replace("Nell", name) for t in chapter.get("text", [])]
    out["prompt"] = (chapter.get("prompt") or "").replace("Nell", name)
    out["title"] = (chapter.get("title") or "").replace("Nell", name)
    return out


# The 4 chapters that round added for chemistry, earth-space, arts, and
# mind-society were inserted right before the epilogue, which used to sit at
# index 18 in a 19-chapter frame.json. A reader's `story_progress` was a raw
# array index, so inserting chapters mid-array silently retargeted anyone
# already sitting at that index onto whatever now occupies it — the one
# reader on index 18 would have opened a beginner chemistry chapter instead
# of the finale they had actually earned. `story_chapter_id` fixes the
# representation going forward (an id survives any future insertion); this
# constant identifies profiles saved before the fix. (A fixed-offset
# correction was tried first and rejected: several more chapters were added
# in the rounds since, each one reintroducing the exact same bug for any
# still-unmigrated reader — see _resolve_story_position below.)
_LEGACY_STORY_INSERT_AT = 18


def _resolve_story_position(settings: dict, chapters: List[dict]) -> int:
    """The reader's chapter index, from a stable id when we have one.

    Older profiles only have the pre-fix raw array index; those get the exact
    arithmetic shift undone once, then are re-saved as an id on the next
    commit so this branch never has to run for them again.
    """
    chapter_id = settings.get("story_chapter_id")
    if chapter_id:
        for i, ch in enumerate(chapters):
            if ch["id"] == chapter_id:
                return i
        return 0
    legacy = int(settings.get("story_progress", 0))
    if legacy >= _LEGACY_STORY_INSERT_AT:
        # legacy==18 meant "at the finale" in the original 19-chapter frame —
        # a fixed +4 offset only located the correct chapter once, right
        # after that one historical insertion. Every chapter added since
        # (and several rounds have added many) shifts what sits at index 22
        # again, silently reintroducing the exact bug this migration exists
        # to fix. A reader who had reached the end always means the CURRENT
        # end, not a fixed position that decays with every future edit.
        return len(chapters) - 1
    return legacy


def _story_cursor(prof: dict, commit: bool = False):
    """The chapter the reader is on, whether it may be turned, and what it wants.

    Turning a page requires real evidence for the lesson it leads to. For
    lessons at or below the reader's placed stage a single genuine pass is
    enough (the book already assumes that ground); for anything ahead of them it
    takes full proof — two passes, spaced. Chapters that are already earned, or
    that point into fields this reader never chose, are skipped rather than
    becoming dead ends.

    Pass commit=True only from a write endpoint: a GET must not persist.
    """
    settings = prof.get("settings", {})
    chapters = STORY["chapters"]
    start = _resolve_story_position(settings, chapters)
    progress = start
    proven = learner.proven_set()
    passed = learner.passed_set()
    standing = learner.mastered_set()
    domains = prof.get("domains") or [d["id"] for d in curr.domains]
    stage = int(prof.get("stage") or 0)

    def earned(node, target):
        if not target:
            return True
        if target in proven:
            return True
        # A lesson the reader was placed past needs one honest pass, not two —
        # or the standing credit the book itself gave them for it.
        #
        # That last clause is what makes the arc reachable at all. Onboarding
        # above stage 0 seeds every earlier lesson as `assumed` (level 0.85,
        # passes 0), and `next_lessons` then skips anything at or above 0.8 —
        # so the very lessons the early chapters are gated on are the ones the
        # book has decided never to teach this reader. Requiring a pass on
        # them left a twelve-year-old frozen on chapter 1 with no route
        # forward anywhere in the app: the gate node never appears in Today,
        # and the page never turns. Every other gate in the book already
        # honours assumed credit — `gate_map` opens successors on it — so the
        # story was the one place the book refused to stand behind its own
        # assumption. `mastered_set` is decay-aware and drops revoked credit,
        # so this accepts only credit that still stands today.
        return (bool(node) and node["stage"] < stage
                and (target in passed or target in standing))

    def skippable(ch):
        """Only a chapter in a field the reader never chose is skipped.

        A chapter that is merely *ahead* of them must wait, not vanish — the
        upper half of the arc was being silently discarded and, because the
        cursor is persisted, irreversibly so.
        """
        node = curr.node(ch.get("leads_to", "") or "")
        if node is None:
            return False
        return node["domain"] not in domains

    while progress < len(chapters):
        ch = chapters[progress]
        # Only a wrong-domain chapter is skipped automatically. A chapter whose
        # lesson happens to be proven is NOT — that used to auto-advance the
        # cursor silently, and because `commit=True` is passed from /api/today,
        # every page load walked the reader past pages they had never turned.
        # "Turn the page ✦" never fired on the honest path: 18 chapters earned
        # over an arc, 0 ceremonies, 0 chapter XP paid, 0 journal entries. A
        # page turns only through the explicit action in /api/story/advance,
        # which is the only place that logs the event and pays the reward.
        if skippable(ch):
            progress += 1
            continue
        break
    # Persist only the legacy-format migration, never the domain-skip walk
    # itself. Domain selection is not immutable — a reader can revisit
    # /api/profile and add a domain later — so baking the skip-forward
    # result into story_chapter_id stranded any chapter skipped for a domain
    # the reader had not yet chosen: once persisted, the walk never revisits
    # it even after the domain is added, silently losing its ceremony, its
    # text, and its XP. Recomputing the skip live on every call (cheap: a
    # single pass over ~35 chapters) means a domain change takes effect
    # immediately instead of being permanently foreclosed by an earlier read.
    stale_format = "story_chapter_id" not in settings
    if commit and stale_format:
        s = dict(settings)
        s["story_chapter_id"] = chapters[progress]["id"] if progress < len(chapters) else chapters[-1]["id"]
        s.pop("story_progress", None)
        learner.save_profile(prof["name"], prof["age"], prof["hours_per_week"],
                             prof["breadth"], prof["stage"], prof["domains"], s)
    if progress >= len(chapters):
        # The arc ends rather than disappearing: hold on the last page.
        last = _personalize(chapters[-1], prof.get("name", ""))
        return last, len(chapters) - 1, False
    chapter = chapters[progress]
    target = chapter.get("leads_to", "")
    node = curr.node(target)
    # The last chapter is an epilogue: it closes the arc and turns to nothing.
    can_advance = bool(target) and earned(node, target) and progress < len(chapters) - 1
    return _personalize(chapter, prof.get("name", "")), progress, can_advance


def _story_needs(chapter: Optional[dict]) -> Optional[dict]:
    """What the current chapter is waiting for, in plain terms."""
    if not chapter:
        return None
    target = chapter.get("leads_to", "")
    node = curr.node(target)
    if not node:
        return None
    info = learner.mastery_detail(target)
    # A lesson the reader was placed past opens on one honest pass; anything
    # ahead of them needs the full two, spaced. Say which.
    prof = learner.get_profile() or {}
    placed_past = node["stage"] < int(prof.get("stage") or 0)
    needed = 1 if placed_past else 2
    # A faded lesson's lifetime pass count is stale evidence — reporting it
    # verbatim reads as "2 of 2 passes, almost there" on a page that is in
    # fact shut until the reader proves it again.
    faded = info.get("faded", False)
    passes = 0 if faded else info.get("passes", 0)
    return {
        "node_id": target,
        "title": node["title"],
        "passes": min(passes, needed),
        "passes_needed": needed,
        "ready_at": None if placed_past else info.get("ready_at"),
        "faded": faded,
        "ever_proven": info.get("ever_proven", False),
    }


# ---------------- profile & onboarding ----------------

class ProfileIn(BaseModel):
    name: str = "Reader"
    age: float = 8
    hours_per_week: float = 6
    breadth: str = "balanced"
    domains: List[str] = []


@app.get("/api/state")
def state():
    profile = learner.get_profile()
    lib = wiki.library_status()
    return {
        "profile": profile,
        "onboarded": profile is not None,
        "library": lib,
        "tutor_engine": "claude" if tutor.have_api_key() else "book",
        # Machine-readable disclosure: when true, tutor messages and article
        # excerpts leave this machine for api.anthropic.com. The UI shows it;
        # the flag also rides on every /api/tutor reply (see tutor.ask).
        "tutor_remote": tutor.have_api_key(),
        "stages": [{"i": i, "name": STAGE_NAMES[i], "span": STAGE_SPAN[i],
                    "title": STAGE_TITLES[i]} for i in range(6)],
        "domains": curr.domains,
    }


@app.post("/api/profile")
def save_profile(p: ProfileIn):
    stage = LearnerStore.stage_for_age(p.age)
    first_time = learner.get_profile() is None
    learner.save_profile(p.name, p.age, p.hours_per_week, p.breadth, stage, p.domains)
    # Meet the reader at their age: on first setup, credit the stages below
    # their placement as "assumed known" (not proven) so Today starts at their
    # level. A per-domain placement check can later verify or adjust this.
    if first_time and stage > 0:
        learner.seed_assumed(curr.seed_mastery_for_stage(stage))
    log.info("profile saved: %s age=%s stage=%s breadth=%s", p.name, p.age, stage, p.breadth)
    return learner.get_profile()


# Only the reader's own preferences are writable here. `placed`, `rank` and
# `story_progress` are the book's record of what happened — accepting them
# from the client let a POST set a four-year-old to stage 5 and mark eleven
# chapters read, with no paper sat.
# `daily_goal` and `reminders` used to be accepted here and consumed
# nowhere — a client could set them and the API would silently agree, but
# nothing in the quest, streak or notification logic ever read them back.
# Promising a feature that does not exist is worse than not having it.
#
# Typed, not an open dict: an untyped Body accepted `font_scale: "huge"` and
# stored it verbatim, leaving the frontend to divide by a string. Extras are
# still tolerated at the parse step (extra="allow") because refusing them by
# name, loudly, is the endpoint's existing contract — a 422 would hide *which*
# key was the problem.
class SettingsIn(BaseModel):
    model_config = {"extra": "allow"}
    theme: Optional[str] = None
    speak: Optional[bool] = None
    reduce_motion: Optional[bool] = None
    font_scale: Optional[float] = None
    name_pronunciation: Optional[str] = None


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
    for n in graph["nodes"]:
        nid = n["id"]
        n["proven"] = nid in proven
        n["ever_proven"] = nid in ever
        # `assumed` means credited without ever being earned — age placement or a
        # placement check. A node the reader genuinely proved and has since let
        # fade is `faded`, and saying "assumed" about it erased the difference
        # between work they did and a guess about how old they are.
        n["faded"] = n["ever_proven"] and not n["proven"]
        n["assumed"] = n["mastered"] and not n["proven"] and not n["ever_proven"]
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


_SERVED_LIMIT = 200
_SERVED_TTL = 12 * 3600   # a paper is a sitting, not a standing offer
# Sync endpoints run in a threadpool, so two submissions of the same paper can
# be in flight at once. Claiming a paper must be one indivisible step or the
# single-use rule holds only by luck of scheduling.
_SERVED_LOCK = threading.Lock()


class _SittingProxy(dict):
    """A sitting as a mutable dict view. Top-level assignment writes through to
    the store, so a caller (or a test) that adjusts, say, `at` is adjusting the
    persistent record, not a copy that evaporates on the next read."""

    def __init__(self, store, token, data):
        super().__init__(data)
        self._store, self._token = store, token

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._store[self._token] = dict(self)


class _SittingStore:
    """Served papers, persisted in the learner DB.

    These used to live in an in-memory OrderedDict, which meant a server
    restart silently voided every open paper — the reader lost the sitting,
    and worse, lost the burn/commit record that keeps the single-use and
    reveal-order rules honest. A sitting is short-lived but it is still state
    the reader paid for; it goes in the same file as everything else they
    paid for. The connection is derived from `learner.db_path` at call time,
    not bound at import, so rebinding `srv.learner` (what tests do) rebinds
    this store with it. Dict-like on purpose: the callers and the tests keep
    the exact interface the in-memory version had.
    """

    def _conn(self):
        conn = sqlite3.connect(learner.db_path, timeout=15)
        conn.execute("PRAGMA busy_timeout=8000")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS sittings ("
            " token TEXT PRIMARY KEY, at REAL, data TEXT)")
        return conn

    @staticmethod
    def _decode(row):
        entry = json.loads(row[1])
        entry["at"] = row[0]
        # JSON object keys are strings; `committed` is keyed by question id,
        # which is an int everywhere else. Undo the round-trip.
        committed = entry.get("committed") or {}
        entry["committed"] = {int(k): v for k, v in committed.items()}
        return entry

    def get(self, token, default=None):
        with self._conn() as c:
            row = c.execute("SELECT at, data FROM sittings WHERE token=?",
                            (token,)).fetchone()
        if row is None:
            return default
        return _SittingProxy(self, token, self._decode(row))

    def __getitem__(self, token):
        entry = self.get(token)
        if entry is None:
            raise KeyError(token)
        return entry

    def __contains__(self, token):
        return self.get(token) is not None

    def __setitem__(self, token, entry):
        payload = {k: v for k, v in entry.items() if k != "at"}
        with self._conn() as c:
            c.execute("INSERT OR REPLACE INTO sittings(token, at, data) VALUES(?,?,?)",
                      (token, float(entry.get("at", time.time())), json.dumps(payload)))

    def pop(self, token, default=None):
        with self._conn() as c:
            row = c.execute("SELECT at, data FROM sittings WHERE token=?",
                            (token,)).fetchone()
            c.execute("DELETE FROM sittings WHERE token=?", (token,))
        if row is None:
            return default
        return self._decode(row)

    def sweep(self, now: float):
        """TTL sweep plus the size cap, oldest first — the same eviction the
        in-memory OrderedDict applied, now in one SQL breath."""
        with self._conn() as c:
            c.execute("DELETE FROM sittings WHERE at < ?", (now - _SERVED_TTL,))
            c.execute(
                "DELETE FROM sittings WHERE token IN ("
                " SELECT token FROM sittings ORDER BY at DESC"
                " LIMIT -1 OFFSET ?)", (_SERVED_LIMIT,))


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

    # The day's quest — completion reflects work actually done today, never a
    # merely empty deck.
    #
    # Every step is built through one function, deliberately. A step with
    # nothing to offer is not a task left undone: there is no action available
    # that could complete it, so it must not be the one thing standing between
    # the reader and the crown. That was first fixed for `review` alone — the
    # deck is built from quiz misses, so it is necessarily empty on day one and
    # empty again on every caught-up day — and `learn`, which has exactly the
    # same shape and exactly the same failure, was left behind in the same
    # round: a reader who has mastered their domains' current frontier gets no
    # lessons offered, and sat at 0/2 with the crown permanently unreachable.
    # Building all three the same way is what stops the next one diverging.
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
    # TODO(learner): LearnerStore has no public per-kind event query (its
    # nearest, active_today/xp_today, cannot filter by kind) — this belongs as
    # a method on the store; until it grows one, _conn() is the only interface
    # that can answer this. Read-only and brief.
    from .learner import _local_midnight
    start = _local_midnight(time.time())
    with learner._conn() as c:
        row = c.execute("SELECT 1 FROM events WHERE kind=? AND at>=? LIMIT 1",
                        (kind, start)).fetchone()
    return row is not None


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
    """Draw a paper from the node's bank.

    Assembled in one pass. It grew by patching once and the patches began to
    fight: a slot reserved for an authored produced item sat at index n-1, the
    generated reflection item then truncated the list to n-1, and a final
    `questions[:n]` cut the reflection item back off — so authored numeric items
    were selected and discarded in the same breath, and on one node three of
    them never once reached a paper.

    Order of business: draw from the bank, top up from the node's own drill,
    give the youngest an ordering item, then append the unmarked reflection
    item. Auto-generated cloze is deliberately absent — an audit put its defect
    rate at 65%, and it survives only at /api/selfcheck, labelled and never
    touching mastery.
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


class QuizSubmitIn(BaseModel):
    node_id: str
    questions: list = []
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
        overconfident = sum(1 for c, q, a in pairs if c >= 3 and not _right(q, a))
        underconfident = sum(1 for c, q, a in pairs if c <= 1 and _right(q, a))
        calibration = {"overconfident": overconfident, "underconfident": underconfident,
                       "total": len(pairs)}
        learner.log_event("calibration", {"node": s.node_id, **calibration})
    ascension = _check_ascension(learner.get_profile()) if mastery.get("newly_mastered") else None
    return {"result": result, "mastery": mastery, "cards_added": cards_added,
            "ascension": ascension, "calibration": calibration}


@app.get("/api/selfcheck")
def selfcheck(title: str, n: int = 4):
    """Practice questions for an article outside the curriculum.

    Explicitly NOT graded: these are machine-generated from prose and are a
    prompt to re-read, not a measure of anything. Nothing here touches mastery.

    Fill-in-the-blank on raw article prose is a text-reading task by
    construction — a pre-reader can't decode the prompt, let alone the
    blank. The frontend already hides the button that reaches this at
    stage<=1; refusing it here too means a stage-appropriate response even
    if this URL is ever hit directly.
    """
    prof = learner.get_profile()
    if prof and int(prof.get("stage") or 0) <= 1:
        return JSONResponse(
            {"error": "self-check is a text exercise; not offered at this stage"},
            status_code=403)
    art = wiki.get_article(title)
    if not art:
        return JSONResponse({"error": "not found"}, status_code=404)
    text = wiki.article_plaintext(art["html"], 6000)
    questions = quiz.cloze_from_text(text, n, topic=title)
    for i, q in enumerate(questions):
        q["id"] = i
    return {"title": title, "graded": False,
            "note": "Generated from the article — a nudge to re-read, not a test.",
            "token": _remember(questions, "selfcheck", title),
            "questions": _public(questions)}


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
# after a cooling period is how the book notices. The store side of this lives
# in learner.py (another agent's file, landing under a name like
# reopen_placement); resolve it by name at call time so the server runs — with
# the feature a graceful no-op — whichever spelling actually lands, or none.
_REOPEN_NAMES = ("reopen_placement", "placement_reopen", "reopen")
_REOPENABLE_NAMES = ("placement_reopenable", "reopenable_placement")


def _placement_reopen(domain: str) -> bool:
    """Ask the store to reopen a settled domain, if it can and cooling allows.

    True only when a reopen actually happened. Every call is defensive: the
    method may not exist yet, and its return convention is its author's.
    """
    fn = next((getattr(learner, n) for n in _REOPEN_NAMES
               if callable(getattr(learner, n, None))), None)
    if fn is None:
        return False
    gate = next((getattr(learner, n) for n in _REOPENABLE_NAMES
                 if callable(getattr(learner, n, None))), None)
    try:
        if gate is not None and not gate(domain):
            return False   # still cooling — the 7-day period is the store's call
        return bool(fn(domain)) or not learner.placement_state().get(domain, {}).get("done", False)
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
                             "reopen_supported": any(
                                 callable(getattr(learner, n, None))
                                 for n in _REOPEN_NAMES)}, status_code=409)
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
    questions: list = []
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

class TutorIn(BaseModel):
    messages: list
    title: str = ""
    excerpt: str = ""


@app.post("/api/tutor")
def ask_tutor(t: TutorIn):
    prof = learner.get_profile()
    stage = prof["stage"] if prof else 2
    excerpt = t.excerpt
    if not excerpt and t.title:
        s = wiki.get_summary(t.title)
        excerpt = (s or {}).get("extract", "")
    return tutor.ask(t.messages, t.title, excerpt, stage)


# ---------------- roadmap & journal ----------------

@app.get("/api/roadmap")
def roadmap_api():
    prof = learner.get_profile()
    if not prof:
        return JSONResponse({"error": "no profile"}, status_code=400)
    # Pace against what the reader can still be expected to need to learn.
    # Placement-assumed nodes are treated as covered for scheduling, but the
    # headline "mastered" count reports only what has actually been proven.
    r = roadmap(prof, curr.graph(), learner.gate_map())
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
        return {"title": STORY["title"], "about": STORY["about"],
                "chapters": STORY["chapters"], "progress": 0, "can_advance": False}
    cur, progress, can_advance = _story_cursor(prof)
    name = prof["name"]
    domains = prof.get("domains") or [d["id"] for d in curr.domains]
    chapters = []
    for i, ch in enumerate(STORY["chapters"]):
        c = _personalize(ch, name)
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
