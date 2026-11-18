"""HTTP surface for learning sequences.

Every response to a step is marked here, against the server's copy of the
authored model, and the reader is told about *their* response only after they
have committed to it — the same order of events the quiz endpoints enforce,
for the same reason: being shown an answer is not the same as producing one.

The routes read the server's services at request time (``primer.server`` binds
them in ``init_services`` and tests rebind them), and apply the server's own
lock rule, so a sequence opens exactly when its lesson's questions do.
"""
from __future__ import annotations

import hashlib
import os
from typing import Dict, List, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import authoring, catalog as catalog_module, evaluators
from .catalog import BadResponse
from .progress import ProgressStore, REVEAL_AFTER, SEQUENCE_XP, response_key

router = APIRouter(prefix="/api/learning-games")

STUDY_NOTE = ("This is a study activity. Finishing it records that you studied; "
              "it is the module quiz, passed on spaced days, that proves mastery.")
SCRIPTS = ("learning-games/visuals.js", "learning-games/play.js")
STYLE = "learning-games/play.css"


def _host():
    from .. import server
    return server


def _catalog():
    return catalog_module.for_curriculum(_host().curr)


def _asset_url(name: str) -> str:
    """A static file's URL, stamped with its content hash so it can be cached hard."""
    try:
        with open(os.path.join(catalog_module.WEB_DIR, name), "rb") as handle:
            tag = hashlib.sha256(handle.read()).hexdigest()[:10]
    except OSError:
        tag = "0"
    return "/app/%s?v=%s" % (name, tag)


def _asset_urls() -> Dict:
    return {"scripts": [_asset_url(name) for name in SCRIPTS], "style": _asset_url(STYLE)}


def _art(node: Dict) -> Optional[Dict]:
    """The module's own illustration, for a sequence to open on."""
    for media in node.get("lesson_media") or []:
        if media.get("kind") == "illustration" and media.get("src"):
            return {"src": media["src"], "alt": media.get("alt", ""), "caption": media.get("caption", "")}
    return None


def _error(message: str, status: int, **extra) -> JSONResponse:
    return JSONResponse(dict({"error": message}, **extra), status_code=status)


class _Target(BaseModel):
    sequence: str = Field("", max_length=64)
    step: str = Field("", max_length=16)


class CheckIn(_Target):
    response: Dict = Field(default_factory=dict)


class ClueIn(_Target):
    clue: str = Field("", max_length=24)


class CursorIn(BaseModel):
    sequence: str = Field("", max_length=64)
    beat: str = Field("", max_length=16)


class RestartIn(BaseModel):
    sequence: str = Field("", max_length=64)


# ------------------------------------------------------------- projection

def _steps(seq: Dict) -> List[Dict]:
    return [beat for beat in seq["beats"] if beat["kind"] == "step"]


def _valid(rows: Dict[str, Dict], step: Dict) -> Optional[Dict]:
    """A checkpoint row, honoured only while the step it was earned on is unchanged."""
    row = rows.get(step["id"])
    return row if row and row.get("fingerprint") == step["fingerprint"] else None


def _settled(row: Optional[Dict]) -> bool:
    return bool(row) and row["status"] in ("solved", "revealed")


def _step_state(step: Dict, row: Optional[Dict]) -> Dict:
    state = {"status": (row or {}).get("status", "open"), "attempts": (row or {}).get("attempts", 0),
             "hints_shown": list((step.get("hints") or [])[:(row or {}).get("hints", 0)]),
             "can_reveal": bool(row) and row["status"] == "open" and row["attempts"] >= REVEAL_AFTER}
    if step["type"] == "clues":
        shown = set((row or {}).get("detail", {}).get("revealed") or [])
        ids = catalog_module._ids(step, "clue", len(step["clues"]))
        state["clues"] = [{"id": ids[i], "label": clue["label"], "text": clue["text"]}
                          for i, clue in enumerate(step["clues"]) if (i + 1) in shown]
    if _settled(row):
        state["solution"] = catalog_module.public_solution(step)
        state["why"] = step.get("why", "")
        state["first_try"] = bool(row.get("first_try"))
    return state


def _public_sequence(seq: Dict, rows: Dict[str, Dict], seq_row: Optional[Dict], reader_id: int,
                     locked: bool) -> Dict:
    plays = (seq_row or {}).get("plays", 0) or 0
    seed = "%s|%s|%s" % (reader_id, seq["id"], plays)
    beats, done = [], 0
    steps = _steps(seq)
    for beat in seq["beats"]:
        if beat["kind"] != "step":
            beats.append(catalog_module.public_show(beat))
            continue
        if locked:
            continue
        row = _valid(rows, beat)
        public = catalog_module.public_step(beat, seed)
        public["state"] = _step_state(beat, row)
        done += int(_settled(row))
        beats.append(public)
    finished = bool(steps) and done == len(steps)
    saved = (seq_row or {}).get("cursor") or ""
    cursor = ""
    if not locked and not finished and steps:
        # Resume at the first step still open: a checkpoint is a place to
        # carry on from, not a record of where the browser happened to be.
        # A reader who has answered nothing yet returns to the page of the
        # introduction they had reached.
        first_open = next(s["id"] for s in steps if not _settled(_valid(rows, s)))
        reading = saved in ("intro", "demo") and not done
        cursor = saved if reading else (first_open if (done or saved) else "")
    return {
        "slug": seq["slug"], "title": seq["title"], "objective": seq["objective"],
        "level": seq["level"], "origin": {"kind": seq["origin"]["kind"], "review": seq["origin"]["review"],
                   "review_by": seq["origin"].get("review_by", "")},
        "beats": beats, "steps": len(steps), "done": done, "cursor": cursor,
        "status": "completed" if (seq_row or {}).get("completed_at") else ("started" if done else "new"),
        "finished_run": finished, "plays": plays,
        "types": sorted({authoring.INTERACTION_LABELS[s["type"]] for s in steps}),
    }


def _completion(seq: Dict, node: Dict, result: Dict, cards: int, sequences: List[Dict]) -> Dict:
    index = next(i for i, s in enumerate(sequences) if s["slug"] == seq["slug"])
    following = sequences[index + 1] if index + 1 < len(sequences) else None
    helped = result["steps"] - result["unaided"]
    return {
        "first": result["first"], "xp_gained": result["xp_gained"], "cards_added": cards,
        "steps": result["steps"], "first_try": result["first_try"], "with_help": helped,
        "plays": result["plays"],
        "message": seq.get("next") or ("You have worked through “%s”." % seq["title"]),
        "study_note": STUDY_NOTE,
        "next_sequence": ({"slug": following["slug"], "title": following["title"]} if following else None),
        "has_quiz": bool(node.get("quiz")), "practice": node.get("practice") or "",
    }


def _cards_for(seq: Dict, node: Dict, rows: Dict[str, Dict]) -> List[Dict]:
    """Review cards for the steps a reader needed more than one try at."""
    cards = []
    article = (node.get("articles") or [""])[0]
    for step in _steps(seq):
        row = _valid(rows, step)
        if not row or step["type"] == "reflect":
            continue
        if not (row["attempts"] or row["status"] == "revealed"):
            continue
        authored = step.get("card")
        front = authored["front"] if authored else _card_front(step)
        back = authored["back"] if authored else _card_back(step)
        # ``origin`` keeps these out of mastery evidence: a card minted from
        # study is a memory aid, graded by the reader, and cannot certify.
        cards.append({"front": front, "back": back, "node_id": seq["node_id"],
                      "article": article, "origin": "activity"})
    return cards


def _card_front(step: Dict) -> str:
    prompt = step["prompt"]
    if step["type"] == "fill":
        return "%s\n\n%s" % (prompt, step["frame"])
    if step["type"] == "order":
        return "%s\n\n%s" % (prompt, " · ".join(sorted(step["items"], key=str.casefold)))
    if step["type"] == "edit":
        return "%s\n\n%s\n\n%s" % (prompt, " ".join(t["text"] for t in step["tokens"]), step["aim"])
    return prompt


def _card_back(step: Dict) -> str:
    answer = catalog_module.answer_text(step)
    why = step.get("why", "")
    back = answer if not why else "%s\n\n%s" % (answer, why)
    return back[:700]


def _resolve(node_id: str, slug: str, step_id: str = ""):
    host = _host()
    node = host.curr.node(node_id)
    if not node:
        return None, None, None, _error("no such node", 404)
    seq = _catalog().sequence(node_id, slug)
    if seq is None:
        return node, None, None, _error("no such sequence", 404)
    step = None
    if step_id:
        step = next((s for s in _steps(seq) if s["id"] == step_id), None)
        if step is None:
            return node, seq, None, _error("no such step", 404)
    return node, seq, step, None


def _progress() -> ProgressStore:
    return ProgressStore(_host().learner)


def _finish_if_done(seq: Dict, node: Dict, reader_id: int) -> Optional[Dict]:
    """Close the run when every step is settled.  Safe to call again."""
    store = _progress()
    seq_row, rows = store.load(reader_id, seq["node_id"], seq["slug"])
    steps = _steps(seq)
    valid = {s["id"]: _valid(rows, s) for s in steps}
    if not steps or not all(_settled(valid[s["id"]]) for s in steps):
        return None
    result = store.complete(reader_id, seq["node_id"], seq["slug"], steps, valid)
    cards = 0
    if not result["repeat"]:
        cards = _host().learner.add_cards(_cards_for(seq, node, valid), reader_id=reader_id)
    return _completion(seq, node, result, cards, _catalog().sequences(seq["node_id"]))


# ------------------------------------------------------------------ routes

@router.get("/{node_id}")
def describe(node_id: str, request: Request, sequence: str = ""):
    """A module's sequences, and the reader's place in the one they are on."""
    host = _host()
    reader_id = host.current_reader(request)
    node = host.curr.node(node_id)
    if not node:
        return _error("no such node", 404)
    cat = _catalog()
    sequences = cat.sequences(node_id)
    locked_response = host._locked_lesson_response(node, reader_id)
    locked = locked_response is not None
    out = {
        "node_id": node_id, "title": node["title"], "stage": node["stage"],
        "locked": locked, "study_note": STUDY_NOTE,
        "policy": {"xp": SEQUENCE_XP, "reveal_after": REVEAL_AFTER},
        "assets": _asset_urls(), "activities": cat.existing_activities(node), "art": _art(node),
        "sequences": [], "current": None,
    }
    if locked:
        gates = host.learner.gate_map(reader_id=reader_id)
        out["unlock_requirements"] = host.curr.unlock_requirements(node, gates)
    if not sequences:
        return out
    store = _progress()
    overview = store.overview(reader_id, node_id)
    chosen = None
    for seq in sequences:
        entry = overview.get(seq["slug"]) or {}
        live = {s["id"]: s["fingerprint"] for s in _steps(seq)}
        done = sum(1 for d in entry.get("done", []) if live.get(d["step_id"]) == d["fingerprint"])
        status = ("completed" if entry.get("completed_at") else "started" if done else "new")
        out["sequences"].append({"slug": seq["slug"], "title": seq["title"], "objective": seq["objective"],
                                 "steps": len(live), "done": done, "status": status,
                                 "plays": entry.get("plays", 0) or 0})
        if sequence and seq["slug"] == sequence:
            chosen = seq
    if sequence and chosen is None:
        return _error("no such sequence", 404)
    if chosen is None:
        # Carry on where the reader left off; otherwise the first unfinished
        # sequence; otherwise the first, for a replay.
        started = [s for s, e in zip(sequences, out["sequences"]) if e["status"] == "started"]
        fresh = [s for s, e in zip(sequences, out["sequences"]) if e["status"] == "new"]
        chosen = (started or fresh or sequences)[0]
    seq_row, rows = store.load(reader_id, node_id, chosen["slug"])
    out["current"] = _public_sequence(chosen, rows, seq_row, reader_id, locked)
    if out["current"]["finished_run"]:
        valid = {s["id"]: _valid(rows, s) for s in _steps(chosen)}
        result = {"first": False, "repeat": True, "xp_gained": 0,
                  "plays": (seq_row or {}).get("plays", 0) or 0, "steps": len(valid),
                  "unaided": sum(1 for r in valid.values() if r["status"] == "solved"),
                  "first_try": sum(1 for r in valid.values() if r.get("first_try"))}
        out["current"]["completed"] = _completion(chosen, node, result, 0, sequences)
    return out


@router.post("/{node_id}/check")
def check(node_id: str, body: CheckIn, request: Request):
    """Mark one response.  A step already settled answers as it was settled."""
    host = _host()
    reader_id = host.current_reader(request)
    node, seq, step, problem = _resolve(node_id, body.sequence, body.step)
    if problem is not None:
        return problem
    locked = host._locked_lesson_response(node, reader_id)
    if locked is not None:
        return locked
    store = _progress()
    row = store.step(reader_id, node_id, seq["slug"], step)
    if _settled(row):
        return {"correct": True if row["status"] == "solved" else None, "already": True,
                "feedback": "", "marks": {}, "state": _step_state(step, row),
                "completed": _finish_if_done(seq, node, reader_id)}
    try:
        response = catalog_module.canonical_response(step, body.response)
    except BadResponse as exc:
        return _error(str(exc), 400)
    verdict = evaluators.evaluate(step, response, row.get("detail") or {})
    if verdict["error"] == "no-response":
        return {"correct": False, "incomplete": True, "feedback": verdict["feedback"],
                "marks": {}, "state": _step_state(step, row), "completed": None}
    if verdict["correct"] is False:
        row = store.wrong(reader_id, node_id, seq["slug"], step, response_key(response))
        return {"correct": False, "feedback": verdict["feedback"], "marks": _public_marks(step, verdict),
                "state": _step_state(step, row), "completed": None}
    row, changed = store.settle(reader_id, node_id, seq["slug"], step, "solved")
    if changed:
        store.studied_today(reader_id, node_id, seq["slug"])
    return {"correct": verdict["correct"], "feedback": verdict["feedback"],
            "marks": _public_marks(step, verdict), "state": _step_state(step, row),
            "completed": _finish_if_done(seq, node, reader_id)}


def _public_marks(step: Dict, verdict: Dict) -> Dict:
    """Per-part detail, re-expressed in the ids the browser holds."""
    marks = dict(verdict.get("marks") or {})
    kind = step["type"]
    if "wrong" in marks:
        if kind in authoring.CHOICE_TYPES:
            ids = catalog_module._ids(step, "option", len(step["options"]))
        elif kind == "match":
            ids = catalog_module._ids(step, "left", len(step["pairs"]))
        else:
            ids = catalog_module._ids(step, "item", len(evaluators.group_items(step)))
        marks["wrong"] = [ids[i] for i in marks["wrong"]]
    marks.pop("chosen", None)
    marks.pop("edits", None)
    return marks


@router.post("/{node_id}/hint")
def hint(node_id: str, body: _Target, request: Request):
    host = _host()
    reader_id = host.current_reader(request)
    node, seq, step, problem = _resolve(node_id, body.sequence, body.step)
    if problem is not None:
        return problem
    locked = host._locked_lesson_response(node, reader_id)
    if locked is not None:
        return locked
    row = _progress().hint(reader_id, node_id, seq["slug"], step)
    return {"state": _step_state(step, row), "more": row["hints"] < len(step.get("hints") or [])}


@router.post("/{node_id}/clue")
def clue(node_id: str, body: ClueIn, request: Request):
    """Turn one clue over.  What was turned over is remembered and counted."""
    host = _host()
    reader_id = host.current_reader(request)
    node, seq, step, problem = _resolve(node_id, body.sequence, body.step)
    if problem is not None:
        return problem
    locked = host._locked_lesson_response(node, reader_id)
    if locked is not None:
        return locked
    if step["type"] != "clues":
        return _error("this step has no clues", 400)
    try:
        number = catalog_module.clue_index(step, body.clue)
    except BadResponse as exc:
        return _error(str(exc), 400)
    row = _progress().clue(reader_id, node_id, seq["slug"], step, number)
    return {"state": _step_state(step, row)}


@router.post("/{node_id}/reveal")
def reveal(node_id: str, body: _Target, request: Request):
    """Show the answer to a step the reader has genuinely tried.

    A study step should never be a wall.  After two different wrong responses
    the book will show the answer and its reasoning; the step is then recorded
    as *shown*, not solved, and earns nothing.
    """
    host = _host()
    reader_id = host.current_reader(request)
    node, seq, step, problem = _resolve(node_id, body.sequence, body.step)
    if problem is not None:
        return problem
    locked = host._locked_lesson_response(node, reader_id)
    if locked is not None:
        return locked
    store = _progress()
    row = store.step(reader_id, node_id, seq["slug"], step)
    if row["status"] == "open" and row["attempts"] < REVEAL_AFTER:
        return _error("try it %s first" % ("once more" if row["attempts"] else "twice"), 409,
                      attempts=row["attempts"])
    row, changed = store.settle(reader_id, node_id, seq["slug"], step, "revealed")
    if changed:
        store.studied_today(reader_id, node_id, seq["slug"])
    return {"state": _step_state(step, row), "completed": _finish_if_done(seq, node, reader_id)}


@router.post("/{node_id}/cursor")
def cursor(node_id: str, body: CursorIn, request: Request):
    """Remember which beat the reader is on, so the page can reopen there."""
    host = _host()
    reader_id = host.current_reader(request)
    node, seq, _step, problem = _resolve(node_id, body.sequence)
    if problem is not None:
        return problem
    if body.beat not in {beat["id"] for beat in seq["beats"]}:
        return _error("no such step", 404)
    if host._locked_lesson_response(node, reader_id) is None:
        _progress().cursor(reader_id, node_id, seq["slug"], body.beat)
    return {"ok": True}


@router.post("/{node_id}/restart")
def restart(node_id: str, body: RestartIn, request: Request):
    host = _host()
    reader_id = host.current_reader(request)
    node, seq, _step, problem = _resolve(node_id, body.sequence)
    if problem is not None:
        return problem
    locked = host._locked_lesson_response(node, reader_id)
    if locked is not None:
        return locked
    _progress().restart(reader_id, node_id, seq["slug"])
    return {"ok": True}
