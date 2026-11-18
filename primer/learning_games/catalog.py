"""Which sequences a module has, and what a reader may see of them.

The catalog is the single reader of ``data/learning-games/``.  It also holds
the one rule that matters most here: **the authored model never leaves the
server**.  ``public_step`` is the projection a browser receives before the
reader has committed to anything — prompts, options and controls, with every
answer key, feedback line, hint and explanation removed — and option order is
shuffled per reader so that neither position nor an id can give a key away.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import random
import threading
import time
from typing import Dict, List, Optional

from . import authoring, derived, evaluators
from .authoring import AuthoringError

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(ROOT, "data", "learning-games")
READER_LINKS = os.path.join(DATA_DIR, "reader-links.json")
WEB_DIR = os.path.join(ROOT, "web")
_lock = threading.Lock()


def _tag(*parts) -> str:
    return hashlib.sha256("\x1f".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:10]


class Catalog:
    """Every module's sequences, loaded once and validated before first use."""

    def __init__(self, nodes: Dict[str, Dict], data_dir: str = DATA_DIR, web_dir: str = WEB_DIR):
        self.nodes = nodes
        self.data_dir = data_dir
        self.web_dir = web_dir
        self.problems: List[str] = []
        self._by_node: Dict[str, List[Dict]] = {}
        self._load()

    # ------------------------------------------------------------ loading

    def _load(self) -> None:
        by_node: Dict[str, List[Dict]] = {}
        for path in sorted(glob.glob(os.path.join(self.data_dir, "*.lg"))):
            name = os.path.relpath(path, ROOT)
            try:
                with open(path, encoding="utf-8") as handle:
                    parsed = authoring.parse(handle.read(), name)
            except AuthoringError as exc:
                self.problems.append(str(exc))
                continue
            for seq in parsed:
                node = self.nodes.get(seq["node_id"])
                if node is None:
                    self.problems.append("%s:%d: unknown module '%s'" % (name, seq["line"], seq["node_id"]))
                    continue
                try:
                    for beat in seq["beats"]:
                        if beat["kind"] == "step":
                            try:
                                evaluators.expand(beat)
                            except ValueError as exc:
                                raise AuthoringError(str(exc), name, beat["line"])
                    authoring.validate(seq, int(node.get("stage", 0) or 0))
                except AuthoringError as exc:
                    self.problems.append(str(exc))
                    continue
                origin = {"kind": "authored", "review": "unreviewed",
                          "source": seq.get("from", "")}
                if seq.get("reviewed"):
                    origin["review"] = "reviewed"
                    origin["reviewed"] = seq["reviewed"]
                elif seq.get("review"):
                    origin["review"] = "awaiting specialist review"
                    origin["review_by"] = seq["review"]
                seq.setdefault("origin", origin)
                by_node.setdefault(seq["node_id"], []).append(seq)
        # A module without an authored sequence falls back to one derived from
        # its own reviewed reference, where it has one.
        for node_id, node in self.nodes.items():
            if node_id in by_node:
                continue
            seq = derived.sequence_from_reference(node)
            if seq is None:
                continue
            try:
                authoring.validate(seq, int(node.get("stage", 0) or 0), strict=False)
            except AuthoringError as exc:
                self.problems.append(str(exc))
                continue
            by_node[node_id] = [seq]
        for node_id, sequences in by_node.items():
            used = set()
            for seq in sequences:
                seq["title"] = seq["title"] or self.nodes[node_id]["title"]
                base = authoring.slug(seq["title"])
                slug, n = base, 2
                while slug in used:
                    slug, n = "%s-%d" % (base, n), n + 1
                used.add(slug)
                seq["slug"] = slug
                seq["id"] = node_id + "#" + slug
        self._by_node = by_node

    # ------------------------------------------------------------ lookup

    def sequences(self, node_id: str) -> List[Dict]:
        return self._by_node.get(node_id, [])

    def sequence(self, node_id: str, slug: str = "") -> Optional[Dict]:
        sequences = self.sequences(node_id)
        if not slug:
            return sequences[0] if sequences else None
        return next((s for s in sequences if s["slug"] == slug), None)

    def covered(self) -> List[str]:
        return sorted(self._by_node)

    def missing(self) -> List[str]:
        return sorted(node_id for node_id in self.nodes if node_id not in self._by_node)

    # ------------------------------------------------- existing activities

    def existing_activities(self, node: Dict) -> List[Dict]:
        """What a module already offered before sequences, so each can contribute."""
        found: List[Dict] = []
        if (node.get("lesson") or {}).get("overview"):
            found.append({"kind": "lesson", "label": "Step-by-step lesson"})
        elif node.get("kid_text"):
            found.append({"kind": "lesson", "label": "Read-aloud mini-lesson"})
        for media in node.get("lesson_media") or []:
            if media.get("kind") == "model":
                found.append({"kind": "model", "label": media.get("title") or "Interactive model",
                              "renderer": media.get("renderer", "")})
        for link in _reader_links().get(node["id"], []):
            found.append({"kind": "activity", "label": link["label"], "href": link["href"]})
        if node.get("music_study"):
            found.append({"kind": "music", "label": "Notation and listening study"})
        if node.get("reference"):
            found.append({"kind": "reference", "label": "Reporting reference"})
        if node.get("practice"):
            found.append({"kind": "practice", "label": "Unlimited practice", "generator": node["practice"]})
        if node.get("quiz"):
            found.append({"kind": "quiz", "label": "Module quiz", "questions": len(node["quiz"])})
        found.append({"kind": "review", "label": "Memory Garden review"})
        return found


def _reader_links() -> Dict[str, List[Dict]]:
    """Stand-alone activities the reader already links from a lesson page.

    Two sources: the registry the reader fetches (``web/activities``), and the
    links written directly into the reader, recorded in ``reader-links.json``
    by ``tools/learning_games_inventory.py`` (a test keeps that file honest).
    """
    with _lock:
        cached = getattr(_reader_links, "_cache", None)
        if cached is not None:
            return cached
        links: Dict[str, List[Dict]] = {}
        for path in (os.path.join(WEB_DIR, "activities", "registry.json"), READER_LINKS):
            try:
                with open(path, encoding="utf-8") as handle:
                    data = json.load(handle)
            except (OSError, ValueError):
                continue
            for node_id, entries in data.items():
                for entry in entries:
                    if str(entry.get("href", "")).startswith("/app/") and entry.get("label"):
                        bucket = links.setdefault(node_id, [])
                        if all(existing["href"] != entry["href"] for existing in bucket):
                            bucket.append({"href": entry["href"], "label": entry["label"]})
        _reader_links._cache = links
        return links


# ------------------------------------------------------------- identities

def _ids(step: Dict, group: str, count: int) -> List[str]:
    """Opaque ids for a step's options or items.

    Derived from the step's content hash, so they are stable for as long as
    the step is unchanged, differ between steps, and say nothing about which
    option is right.
    """
    return [group[0] + _tag(step["fingerprint"], group, index) for index in range(count)]


def _shuffled(indices: List[int], seed: str, avoid_identity: bool = False) -> List[int]:
    order = list(indices)
    rng = random.Random(seed)
    for _ in range(8):
        rng.shuffle(order)
        if not avoid_identity or order != list(indices) or len(order) < 2:
            break
    return order


def _option_order(step: Dict, seed: str) -> List[int]:
    indices = list(range(len(step["options"])))
    if step.get("keep"):
        return indices
    texts = [o["text"] for o in step["options"]]
    if all(evaluators.exprs.number(t) is not None for t in texts):
        return sorted(indices, key=lambda i: evaluators.exprs.number(texts[i]))
    return _shuffled(indices, seed)


def public_visual(visual: Optional[Dict]) -> Optional[Dict]:
    return json.loads(json.dumps(visual)) if visual else None


def public_step(step: Dict, seed: str) -> Dict:
    """What a reader may see of one step before answering it."""
    kind = step["type"]
    out = {"id": step["id"], "kind": "step", "type": kind, "prompt": step["prompt"],
           "label": authoring.INTERACTION_LABELS[kind], "transfer": bool(step.get("transfer")),
           "hints": len(step.get("hints") or []), "say": step.get("say", ""),
           "skill": step.get("skill", ""), "visual": public_visual(step.get("visual"))}
    seed = seed + "|" + step["id"]
    if kind in authoring.CHOICE_TYPES:
        ids = _ids(step, "option", len(step["options"]))
        out["options"] = [{"id": ids[i], "text": step["options"][i]["text"]}
                          for i in _option_order(step, seed)]
        out["multi"] = bool(step.get("multi"))
    if kind == "compare":
        out["panels"] = [dict(public_visual(step["panels"][side]), side=side) for side in ("left", "right")]
    elif kind == "clues":
        ids = _ids(step, "clue", len(step["clues"]))
        out["clues"] = [{"id": ids[i], "label": clue["label"]} for i, clue in enumerate(step["clues"])]
    elif kind == "order":
        ids = _ids(step, "item", len(step["items"]))
        out["items"] = [{"id": ids[i], "text": step["items"][i]}
                        for i in _shuffled(list(range(len(ids))), seed, avoid_identity=True)]
        out["ends"] = step.get("ends") or []
    elif kind == "match":
        lefts, rights = _ids(step, "left", len(step["pairs"])), _ids(step, "right", len(step["pairs"]))
        out["lefts"] = [{"id": lefts[i], "text": pair[0]} for i, pair in enumerate(step["pairs"])]
        out["rights"] = [{"id": rights[i], "text": step["pairs"][i][1]}
                         for i in _shuffled(list(range(len(rights))), seed, avoid_identity=True)]
    elif kind == "group":
        items = evaluators.group_items(step)
        ids, bins = _ids(step, "item", len(items)), _ids(step, "bin", len(step["bins"]))
        out["bins"] = [{"id": bins[i], "text": group["name"]} for i, group in enumerate(step["bins"])]
        out["items"] = [{"id": ids[i], "text": items[i]["text"]}
                        for i in _shuffled(list(range(len(ids))), seed)]
    elif kind == "fill":
        out["frame"] = step["frame"]
        out["blanks"] = len(step["answers"])
        out["numeric"] = all(evaluators.exprs.number(a) is not None for accepted in step["answers"] for a in accepted)
        if step.get("choices"):
            choices = list(step["choices"])
            if all(evaluators.exprs.number(c) is not None for c in choices):
                choices.sort(key=evaluators.exprs.number)
            else:
                choices = [choices[i] for i in _shuffled(list(range(len(choices))), seed)]
            out["choices"] = choices
    elif kind == "edit":
        out["tokens"] = [{"text": t["text"], "alts": list(t["alts"])} for t in step["tokens"]]
        out["limit"] = step.get("limit", 1)
        out["aim"] = step["aim"]
    elif kind == "explore":
        out["params"] = [dict(p) for p in step["params"]]
        out["outputs"] = [dict(o) for o in step["outputs"]]
        out["aim"] = step["aim"]
        out["view"] = step.get("view", "")
    elif kind == "build":
        ids = _ids(step, "piece", len(step["bank"]))
        out["bank"] = [{"id": ids[i], "text": step["bank"][i]}
                       for i in _shuffled(list(range(len(ids))), seed)]
        lengths = sorted({len(answer) for answer in step["answers"]})
        out["slots"] = lengths[0] if len(lengths) == 1 else 0
        out["max_slots"] = lengths[-1]
        out["unordered"] = bool(step.get("unordered"))
    elif kind == "reflect":
        out["min_chars"] = evaluators.REFLECT_MIN_CHARS
    return out


def public_show(beat: Dict) -> Dict:
    return {"id": beat["id"], "kind": beat["kind"], "text": beat["text"],
            "say": beat.get("say", ""), "visual": public_visual(beat.get("visual"))}


# ------------------------------------------------- responses and solutions

class BadResponse(ValueError):
    """A response that does not name things this step actually offered."""


def canonical_response(step: Dict, raw: Dict) -> Dict:
    """Translate a browser's ids into the indices the evaluators mark."""
    if not isinstance(raw, dict):
        raise BadResponse("response must be an object")
    kind = step["type"]

    def index_of(ids, value):
        if value not in ids:
            raise BadResponse("unknown id")
        return ids.index(value)

    if kind in authoring.CHOICE_TYPES:
        ids = _ids(step, "option", len(step["options"]))
        if step.get("multi"):
            return {"choices": [index_of(ids, v) for v in list(raw.get("choices") or [])[:12]]}
        if raw.get("choice") in (None, ""):
            return {}
        return {"choice": index_of(ids, raw.get("choice"))}
    if kind == "order":
        ids = _ids(step, "item", len(step["items"]))
        return {"order": [index_of(ids, v) for v in list(raw.get("order") or [])[:12]]}
    if kind == "match":
        lefts, rights = _ids(step, "left", len(step["pairs"])), _ids(step, "right", len(step["pairs"]))
        pairs = raw.get("pairs") or {}
        if not isinstance(pairs, dict):
            raise BadResponse("pairs must be an object")
        return {"pairs": {index_of(lefts, l): index_of(rights, r) for l, r in list(pairs.items())[:12]}}
    if kind == "group":
        items = evaluators.group_items(step)
        ids, bins = _ids(step, "item", len(items)), _ids(step, "bin", len(step["bins"]))
        chosen = raw.get("bins") or {}
        if not isinstance(chosen, dict):
            raise BadResponse("bins must be an object")
        return {"bins": {index_of(ids, i): index_of(bins, b) for i, b in list(chosen.items())[:16]}}
    if kind == "fill":
        values = raw.get("values")
        if not isinstance(values, list):
            raise BadResponse("values must be a list")
        return {"values": [str(v)[:120] for v in values[:4]]}
    if kind == "edit":
        edits = raw.get("edits") or {}
        if not isinstance(edits, dict):
            raise BadResponse("edits must be an object")
        try:
            return {"edits": {int(position): str(value)[:80] for position, value in list(edits.items())[:16]}}
        except (TypeError, ValueError):
            raise BadResponse("edit positions are numbers")
    if kind == "explore":
        values = raw.get("values") or {}
        if not isinstance(values, dict):
            raise BadResponse("values must be an object")
        return {"values": {str(k)[:16]: v for k, v in list(values.items())[:6]}}
    if kind == "build":
        ids = _ids(step, "piece", len(step["bank"]))
        return {"tokens": [index_of(ids, v) for v in list(raw.get("tokens") or [])[:16]]}
    return {"text": str(raw.get("text") or "")[:4000]}


def clue_index(step: Dict, clue_id: str) -> int:
    ids = _ids(step, "clue", len(step["clues"]))
    if clue_id not in ids:
        raise BadResponse("unknown clue")
    return ids.index(clue_id) + 1


def public_solution(step: Dict) -> Dict:
    """The right response in the browser's own ids, shown once a step is done."""
    kind = step["type"]
    answer = evaluators.solution(step)
    if kind in authoring.CHOICE_TYPES:
        ids = _ids(step, "option", len(step["options"]))
        out = ({"choices": [ids[i] for i in answer["choices"]]} if step.get("multi")
               else {"choice": ids[answer["choice"]]})
        if kind == "clues":
            clue_ids = _ids(step, "clue", len(step["clues"]))
            out["clues"] = [{"id": clue_ids[i], "label": c["label"], "text": c["text"]}
                            for i, c in enumerate(step["clues"])]
            out["enough"] = [clue_ids[n - 1] for n in min(step["sufficient"], key=len)]
        return out
    if kind == "order":
        ids = _ids(step, "item", len(step["items"]))
        return {"order": ids}
    if kind == "match":
        lefts, rights = _ids(step, "left", len(step["pairs"])), _ids(step, "right", len(step["pairs"]))
        return {"pairs": dict(zip(lefts, rights))}
    if kind == "group":
        items = evaluators.group_items(step)
        ids, bins = _ids(step, "item", len(items)), _ids(step, "bin", len(step["bins"]))
        return {"bins": {ids[i]: bins[item["bin"]] for i, item in enumerate(items)}}
    if kind == "fill":
        return {"values": answer["values"]}
    if kind == "edit":
        return {"edits": {str(position): value for position, value in answer["edits"].items()}}
    if kind == "explore":
        values = evaluators.explore_values(step, answer["values"])
        return {"values": {p["id"]: values[p["id"]] for p in step["params"]}}
    if kind == "build":
        ids = _ids(step, "piece", len(step["bank"]))
        return {"tokens": [ids[i] for i in answer["tokens"]]}
    return {"model": step.get("model", "")}


def answer_text(step: Dict) -> str:
    """The right answer as a sentence fragment, for a review card's back."""
    kind = step["type"]
    if kind in authoring.CHOICE_TYPES:
        return "; ".join(o["text"] for o in step["options"] if o["correct"])
    if kind == "order":
        return " → ".join(step["items"])
    if kind == "match":
        return "; ".join("%s — %s" % (left, right) for left, right in step["pairs"])
    if kind == "group":
        return "; ".join("%s: %s" % (group["name"], ", ".join(group["items"])) for group in step["bins"])
    if kind == "fill":
        frame = step["frame"]
        for accepted in step["answers"]:
            frame = frame.replace("__", accepted[0], 1)
        return frame
    if kind == "edit":
        edits = evaluators.solution(step)["edits"]
        return " ".join(edits.get(i + 1, t["text"]) for i, t in enumerate(step["tokens"]))
    if kind == "build":
        return (" + " if step.get("unordered") else " ").join(step["answers"][0])
    if kind == "explore":
        values = evaluators.solution(step)["values"]
        return ", ".join("%s = %g" % (p["label"], values[p["id"]]) for p in step["params"])
    return step.get("model", "")


# ---------------------------------------------------------------- cache

_cache_lock = threading.Lock()
_cached: Dict = {}


def for_curriculum(curriculum) -> Catalog:
    """The catalog for a curriculum object, rebuilt when its files change."""
    signature = tuple(sorted((path, os.path.getmtime(path), os.path.getsize(path))
                             for path in glob.glob(os.path.join(DATA_DIR, "*.lg"))))
    key = (id(curriculum), signature)
    with _cache_lock:
        if _cached.get("key") != key:
            _cached["key"] = key
            _cached["catalog"] = Catalog(curriculum.nodes)
            _cached["at"] = time.time()
        return _cached["catalog"]
