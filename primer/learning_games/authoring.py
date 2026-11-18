"""The authored activity model, and the plain-text format it is written in.

One file per field lives in ``data/learning-games/``.  The format is terse on
purpose — a sequence is a page of prose a subject reviewer can read and mark
up without a JSON editor — and strict on purpose: every line either parses to
exactly one meaning or stops the load with the file and line number.

    @ math.2.fractions                 a curriculum module
    ~ Fair Shares                      a sequence title (a module may hold several)
    goal: …                            the learning objective
    intro: …                           introduce the idea
      show: frac 3/4 5/8               an optional visual, here and on any step
    demo: …                            demonstrate it on a worked example
    P: Which is larger, 3/4 or 5/8?    a step: TYPE, then the prompt
      + 3/4 :: 3/4 is 6/8.             the right response and what to say about it
      - 5/8 :: [bigger-digits] …       a distractor, the reasoning error behind it,
                                       and the feedback aimed at that error
      hint: Rewrite both in eighths.
      why: Equal-sized pieces can be counted and compared.
    >P: …                              ``>`` marks the transfer task
    done: …                            how completion connects to the next step

Step types: P predict · S select all · C compare two structures · O order ·
M match · G group (classify) · F fill a missing value · E constrained edit ·
K minimum clues · X explore a parameter · B build (assemble) · R reflect.

``docs/learning-games.md`` documents every sub-line.  Nothing here is served
to a browser: the answer keys in these models stay on the server, and
``catalog.public_step`` decides what a reader may see before committing.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Dict, List, Optional

from . import exprs

STEP_TYPES = {
    "P": "predict", "S": "select", "C": "compare", "O": "order", "M": "match",
    "G": "group", "F": "fill", "E": "edit", "K": "clues", "X": "explore",
    "B": "build", "R": "reflect",
}
# What each type asks of the learner, in the vocabulary of the brief the
# system was built to: used by the coverage report and the validator alike.
INTERACTION_LABELS = {
    "predict": "prediction", "select": "select all that apply", "compare": "structural comparison",
    "order": "ordering", "match": "matching", "group": "classification",
    "fill": "missing value", "edit": "constrained edit", "clues": "minimum information",
    "explore": "parameter exploration", "build": "construction", "reflect": "explanation",
}
CHOICE_TYPES = ("predict", "select", "compare", "clues")
SHOW_KINDS = (
    "art", "text", "emoji", "digits", "tree", "cycle", "dots", "line", "bars", "table",
    "steps", "chips", "time", "frac", "plot", "balance", "pair", "flow", "grid", "clock",
    "shapes",
)
_HEADER = re.compile(r"^(>?)([PSCOMGFEKXBR]):\s*(.+)$")
_TAG = re.compile(r"^\[([a-z0-9][a-z0-9-]{1,39})\]\s*(.*)$")
_TOKEN_ALTS = re.compile(r"^(.*?)\{(.+)\}$")
_PARAM = re.compile(
    r"^(-?\d+(?:\.\d+)?)\s*\.\.\s*(-?\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)\s*@\s*(-?\d+(?:\.\d+)?)$")
_NAME = re.compile(r"^[a-z][a-z0-9_]{0,15}$")
MAX_TEXT = 600


class AuthoringError(ValueError):
    """An authored model that must not be loaded, with where and why."""

    def __init__(self, message: str, source: str = "", line: int = 0):
        where = ("%s:%d: " % (source, line)) if source and line else (source + ": " if source else "")
        super().__init__(where + message)
        self.source, self.line, self.detail = source, line, message


def split_bar(value: str) -> List[str]:
    """Split ``a | b | c`` at bars that stand between spaces.

    A bar written tight against its neighbours, as in ``|x|``, is part of the
    item; ``\\|`` keeps a spaced one literal.
    """
    parts = re.split(r"(?:^|\s)\|(?:\s|$)", value.replace("\\|", "\x00"))
    return [part.replace("\x00", "|").strip() for part in parts if part.strip() != ""]


def _number(text: str):
    value = float(text)
    return int(value) if value == int(value) else value


# ---------------------------------------------------------------- visuals

def parse_show(spec: str) -> Dict:
    """Parse one ``show:`` line into a visual the player knows how to draw."""
    spec = spec.strip()
    kind, _, rest = spec.partition(" ")
    rest = rest.strip()
    if kind not in SHOW_KINDS:
        raise AuthoringError("unknown visual '%s'" % kind)
    if kind == "art":
        return {"kind": "art"}
    if kind in ("text", "emoji"):
        if not rest:
            raise AuthoringError("'%s' needs content" % kind)
        return {"kind": kind, "text": rest}
    if kind == "pair":
        halves = [half.strip() for half in rest.split("||")]
        if len(halves) != 2 or not all(halves):
            raise AuthoringError("'pair' needs two visuals separated by ||")
        return {"kind": "pair", "items": [parse_panel(half) for half in halves]}
    if kind == "digits":
        words = rest.split()
        if not words or not re.fullmatch(r"[0-9?]{1,40}", words[0]):
            raise AuthoringError("'digits' needs a number of at most 40 digits")
        out = {"kind": "digits", "value": words[0]}
        for word in words[1:]:
            key, _, value = word.partition("=")
            if key in ("last", "hide") and value.isdigit():
                out[key] = int(value)
            elif key == "mark" and re.fullmatch(r"\d+(,\d+)*", value):
                out["mark"] = [int(v) for v in value.split(",")]
            elif key == "label" and value:
                out["label"] = value.replace("_", " ")
            else:
                raise AuthoringError("bad 'digits' option '%s'" % word)
        return out
    if kind == "tree":
        root, tail = _tree(rest.replace(" ", ""), 0)
        if tail != len(rest.replace(" ", "")):
            raise AuthoringError("'tree' has trailing text")
        return {"kind": "tree", "root": root}
    if kind == "cycle":
        values = rest.split()
        if not 2 <= len(values) <= 12:
            raise AuthoringError("'cycle' needs 2 to 12 values")
        return {"kind": "cycle", "values": values}
    if kind == "dots":
        grid = re.fullmatch(r"(\d+)x(\d+)", rest)
        grouped = re.fullmatch(r"(\d+)\s*/\s*(\d+)", rest)
        plain = re.fullmatch(r"(\d+)", rest)
        if grid:
            rows, cols = int(grid.group(1)), int(grid.group(2))
            if not (1 <= rows <= 12 and 1 <= cols <= 12):
                raise AuthoringError("'dots' grid is at most 12 by 12")
            return {"kind": "dots", "rows": rows, "cols": cols}
        if grouped or plain:
            count = int((grouped or plain).group(1))
            group = int(grouped.group(2)) if grouped else 0
            if not 1 <= count <= 60 or (grouped and not 1 <= group <= 12):
                raise AuthoringError("'dots' shows 1 to 60 dots in groups of 1 to 12")
            return {"kind": "dots", "count": count, "group": group}
        raise AuthoringError("'dots' is 'dots 12', 'dots 12 /3' or 'dots 3x4'")
    if kind == "line":
        words = rest.split()
        span = re.fullmatch(r"(-?\d+(?:\.\d+)?)\.\.(-?\d+(?:\.\d+)?)", words[0] if words else "")
        if not span or float(span.group(1)) >= float(span.group(2)):
            raise AuthoringError("'line' needs a range such as 0..10")
        out = {"kind": "line", "min": _number(span.group(1)), "max": _number(span.group(2))}
        for word in words[1:]:
            key, _, value = word.partition("=")
            try:
                if key == "mark":
                    out["mark"] = [_number(v) for v in value.split(",")]
                elif key == "step":
                    out["step"] = _number(value)
                elif key == "hop":
                    out["hops"] = [[_number(a), _number(b)] for a, b in
                                   (pair.split(">") for pair in value.split(","))]
                else:
                    raise ValueError(key)
            except ValueError:
                raise AuthoringError("bad 'line' option '%s'" % word)
        return out
    if kind == "bars":
        bars, unit = [], ""
        for word in rest.split():
            label, sep, value = word.rpartition("=")
            if not sep:
                raise AuthoringError("'bars' entries look like Label=3")
            if label == "unit":
                unit = value.replace("_", " ")
                continue
            try:
                bars.append({"label": label.replace("_", " "), "value": _number(value)})
            except ValueError:
                raise AuthoringError("'bars' value is not a number: %s" % word)
        if not 1 <= len(bars) <= 8:
            raise AuthoringError("'bars' shows 1 to 8 bars")
        return {"kind": "bars", "bars": bars, "unit": unit}
    if kind == "table":
        rows = [split_bar(row) for row in rest.split(";;")]
        if len(rows) < 2 or len({len(row) for row in rows}) != 1 or not rows[0]:
            raise AuthoringError("'table' needs a header and rows of equal width")
        if len(rows) > 9 or len(rows[0]) > 5:
            raise AuthoringError("'table' is at most 5 columns and 8 rows")
        return {"kind": "table", "head": rows[0], "rows": rows[1:]}
    if kind in ("steps", "chips", "flow"):
        items = ([part.strip() for part in rest.split(";;")] if kind == "steps"
                 else [part.strip() for part in rest.split(" > ")] if kind == "flow"
                 else split_bar(rest))
        items = [item for item in items if item]
        if not 2 <= len(items) <= 10:
            raise AuthoringError("'%s' needs 2 to 10 entries" % kind)
        return {"kind": kind, "items": items}
    if kind == "time":
        events = []
        for part in split_bar(rest):
            at, sep, label = part.partition("=")
            if not sep or not at.strip() or not label.strip():
                raise AuthoringError("'time' entries look like 1066=Hastings")
            events.append({"at": at.strip(), "label": label.strip()})
        if not 2 <= len(events) <= 8:
            raise AuthoringError("'time' needs 2 to 8 events")
        return {"kind": "time", "events": events}
    if kind == "frac":
        parts = []
        for word in rest.split():
            match = re.fullmatch(r"(\d+)/(\d+)", word)
            if not match or int(match.group(2)) == 0 or int(match.group(2)) > 24:
                raise AuthoringError("'frac' entries look like 3/4, denominators up to 24")
            parts.append([int(match.group(1)), int(match.group(2))])
        if not 1 <= len(parts) <= 4:
            raise AuthoringError("'frac' shows 1 to 4 fractions")
        return {"kind": "frac", "parts": parts}
    if kind == "plot":
        match = re.fullmatch(r"(.+?)\s+x=(-?\d+(?:\.\d+)?)\.\.(-?\d+(?:\.\d+)?)(\s+mark=[-\d.,]+)?", rest)
        if not match:
            raise AuthoringError("'plot' looks like 'plot 2*x+1 x=0..10'")
        try:
            unknown = exprs.names(match.group(1)) - {"x"}
        except exprs.ExpressionError as exc:
            raise AuthoringError(str(exc))
        if unknown:
            raise AuthoringError("'plot' may only use x, found %s" % sorted(unknown))
        out = {"kind": "plot", "expr": match.group(1).strip(),
               "x": [_number(match.group(2)), _number(match.group(3))]}
        if out["x"][0] >= out["x"][1]:
            raise AuthoringError("'plot' range must increase")
        if match.group(4):
            out["mark"] = [_number(v) for v in match.group(4).split("=")[1].split(",")]
        return out
    if kind == "balance":
        sides = split_bar(rest)
        if len(sides) != 2:
            raise AuthoringError("'balance' needs a left and a right side")
        return {"kind": "balance", "left": sides[0], "right": sides[1]}
    if kind == "grid":
        match = re.fullmatch(r"(\d+)x(\d+)(?:\s+on=([\d,]*))?", rest)
        if not match:
            raise AuthoringError("'grid' looks like 'grid 3x3 on=1,5,9'")
        rows, cols = int(match.group(1)), int(match.group(2))
        cells = [int(v) for v in (match.group(3) or "").split(",") if v]
        if not (1 <= rows <= 10 and 1 <= cols <= 10) or any(not 1 <= c <= rows * cols for c in cells):
            raise AuthoringError("'grid' is at most 10 by 10 and cells count from 1")
        return {"kind": "grid", "rows": rows, "cols": cols, "on": cells}
    if kind == "clock":
        match = re.fullmatch(r"(\d{1,2}):(\d{2})", rest)
        if not match or not (1 <= int(match.group(1)) <= 12 and int(match.group(2)) < 60):
            raise AuthoringError("'clock' needs a time such as 3:30")
        return {"kind": "clock", "hour": int(match.group(1)), "minute": int(match.group(2))}
    if kind == "shapes":
        allowed = {"circle", "square", "triangle", "rectangle", "pentagon", "hexagon", "oval", "star", "diamond"}
        items = rest.split()
        if not 1 <= len(items) <= 8 or any(item not in allowed for item in items):
            raise AuthoringError("'shapes' takes up to 8 of: %s" % ", ".join(sorted(allowed)))
        return {"kind": "shapes", "items": items}
    raise AuthoringError("visual '%s' is not implemented" % kind)  # pragma: no cover


def parse_panel(value: str) -> Dict:
    """A comparison panel: a visual when it names one, otherwise plain text."""
    head = value.strip().split(" ", 1)[0]
    if head in SHOW_KINDS and head != "text":
        return parse_show(value)
    return {"kind": "text", "text": value.strip()[5:].strip() if head == "text" else value.strip()}


def _tree(text: str, at: int):
    start = at
    while at < len(text) and text[at] not in "(),":
        at += 1
    label = text[start:at]
    if not re.fullmatch(r"\?|\d{1,12}", label):
        raise AuthoringError("'tree' nodes are whole numbers or ?")
    node = {"v": label}
    if at < len(text) and text[at] == "(":
        kids = []
        at += 1
        while True:
            kid, at = _tree(text, at)
            kids.append(kid)
            if at >= len(text):
                raise AuthoringError("'tree' is missing a closing bracket")
            if text[at] == ",":
                at += 1
                continue
            if text[at] == ")":
                at += 1
                break
        if len(kids) != 2:
            raise AuthoringError("each 'tree' split has exactly two branches")
        node["kids"] = kids
    return node, at


# ----------------------------------------------------------------- parser

def _feedback(text: str):
    """Split ``[error-tag] feedback`` into its two parts."""
    match = _TAG.match(text.strip())
    if match:
        return match.group(1), match.group(2).strip()
    return "", text.strip()


def _option(line: str, correct: bool) -> Dict:
    text, _, tail = line.partition("::")
    error, feedback = _feedback(tail)
    return {"text": text.strip(), "correct": correct, "feedback": feedback, "error": error}


def _edit_map(text: str) -> Dict[int, str]:
    out = {}
    for part in text.split("&"):
        position, sep, value = part.partition("=")
        if not sep or not position.strip().isdigit():
            raise AuthoringError("edits look like 2=word, joined by & when several are needed")
        out[int(position.strip())] = value.strip()
    return out


def parse(text: str, source: str = "") -> List[Dict]:
    """Parse one authored file into a list of sequences (unvalidated)."""
    sequences: List[Dict] = []
    node_id: Optional[str] = None
    seq: Optional[Dict] = None
    block: Optional[Dict] = None        # the intro, demo or step sub-lines attach to
    number = 0

    def fail(message):
        raise AuthoringError(message, source, number)

    def sequence():
        nonlocal seq, block
        if node_id is None:
            fail("a sequence needs a module line first (@ module.id)")
        if seq is None:
            seq = {"node_id": node_id, "title": "", "objective": "", "beats": [], "next": "",
                   "line": number, "source": source}
            sequences.append(seq)
            block = None
        return seq

    for number, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indented = raw[0] in " \t"
        line = raw.strip()
        try:
            if not indented:
                if line.startswith("@"):
                    node_id, seq, block = line[1:].strip(), None, None
                    if not re.fullmatch(r"[a-z]+\.[a-z0-9.\-]+", node_id):
                        fail("'%s' is not a module id" % node_id)
                    continue
                if line.startswith("~"):
                    seq = None
                    sequence()["title"] = line[1:].strip()
                    continue
                header = _HEADER.match(line)
                if header:
                    kind = STEP_TYPES[header.group(2)]
                    block = {"kind": "step", "type": kind, "prompt": header.group(3).strip(),
                             "transfer": bool(header.group(1)), "hints": [], "why": "", "miss": "",
                             "line": number}
                    sequence()["beats"].append(block)
                    continue
                key, sep, value = line.partition(":")
                value = value.strip()
                if not sep:
                    fail("unrecognised line")
                if key == "goal":
                    sequence()["objective"] = value
                    block = None
                elif key in ("intro", "demo"):
                    block = {"kind": key, "text": value, "line": number}
                    sequence()["beats"].append(block)
                elif key == "done":
                    sequence()["next"] = value
                    block = None
                elif key == "level":
                    if not value.isdigit() or not 0 <= int(value) <= 5:
                        fail("level is a stage from 0 to 5")
                    sequence()["level"] = int(value)
                elif key == "from":
                    sequence()["from"] = value
                elif key == "review":
                    # Names the specialist who must check the content before it
                    # can be called reviewed, e.g. "review: radiologist".
                    if not 3 <= len(value) <= 60:
                        fail("review names a specialist in 3 to 60 characters")
                    sequence()["review"] = value
                elif key == "reviewed":
                    # A reviewer's sign-off, e.g. "reviewed: 2026-12-01, consultant radiologist".
                    if not re.match(r"\d{4}-\d{2}-\d{2}, \S", value) or len(value) > 160:
                        fail("reviewed is 'YYYY-MM-DD, who reviewed it'")
                    sequence()["reviewed"] = value
                else:
                    fail("unknown key '%s'" % key)
                continue
            if block is None:
                fail("an indented line needs an intro, demo or step above it")
            _subline(block, line)
        except AuthoringError as exc:
            if exc.line:
                raise
            raise AuthoringError(exc.detail, source, number)
    return sequences


def _subline(block: Dict, line: str) -> None:
    if line.startswith("+ ") or line.startswith("- "):
        if block.get("kind") != "step" or block["type"] not in CHOICE_TYPES:
            raise AuthoringError("options belong to P, S, C and K steps")
        block.setdefault("options", []).append(_option(line[2:], line[0] == "+"))
        return
    if line.startswith("x "):
        if block.get("kind") != "step" or block["type"] not in ("fill", "edit", "build"):
            raise AuthoringError("anticipated wrong responses belong to F, E and B steps")
        value, _, tail = line[2:].partition("::")
        error, feedback = _feedback(tail)
        if not feedback:
            raise AuthoringError("an anticipated wrong response needs feedback after ::")
        entry = {"feedback": feedback, "error": error}
        if block["type"] == "edit":
            entry["edit"] = _edit_map(value)
        else:
            entry["value"] = value.strip()
        block.setdefault("wrong", []).append(entry)
        return
    if line.startswith("note "):
        # Written with ``::`` because the item itself may contain a colon (6 : 3).
        item, sep, reason = line[5:].partition("::")
        if block.get("kind") != "step" or block["type"] != "group" or not sep or not reason.strip():
            raise AuthoringError("a note belongs to a G step: 'note item :: reason'")
        block.setdefault("notes", {})[item.strip()] = reason.strip()
        return
    if line in ("keep", "any-order"):
        block["keep" if line == "keep" else "unordered"] = True
        return
    head, sep, value = line.partition(":")
    value = value.strip()
    if not sep:
        raise AuthoringError("unrecognised line '%s'" % line[:40])
    words = head.split(" ", 1)
    key = words[0]
    if key == "show":
        block["visual"] = parse_show(value)
    elif key == "say":
        block["say"] = value
    elif block.get("kind") != "step":
        raise AuthoringError("'%s' is not allowed under %s" % (key, block.get("kind")))
    elif key == "hint":
        block["hints"].append(value)
    elif key in ("why", "miss", "skill", "aim", "frame", "model", "target"):
        block[key] = value
    elif key == "card":
        front, arrow, back = value.partition("=>")
        if not arrow or not front.strip() or not back.strip():
            raise AuthoringError("a card is written 'front => back'")
        block["card"] = {"front": front.strip(), "back": back.strip()}
    elif key in ("left", "right"):
        block.setdefault("panels", {})[key] = parse_panel(value)
    elif key == "items":
        block["items"] = split_bar(value)
    elif key == "ends":
        block["ends"] = split_bar(value)
    elif key == "pairs":
        pairs = []
        for part in split_bar(value):
            left, arrow, right = part.partition("=>")
            if not arrow or not left.strip() or not right.strip():
                raise AuthoringError("pairs are written 'left => right'")
            pairs.append([left.strip(), right.strip()])
        block["pairs"] = pairs
    elif key == "bin":
        if len(words) < 2:
            raise AuthoringError("a bin needs a name: 'bin Name: a | b'")
        block.setdefault("bins", []).append({"name": words[1].strip(), "items": split_bar(value)})
    elif key == "answer":
        block.setdefault("answers", []).append(split_bar(value))
    elif key == "taps":
        block["choices"] = split_bar(value)
    elif key == "tokens":
        tokens = []
        for part in split_bar(value):
            match = _TOKEN_ALTS.match(part)
            if match:
                alts = [alt.strip() for alt in match.group(2).split(",") if alt.strip()]
                tokens.append({"text": match.group(1).strip(), "alts": alts})
            else:
                tokens.append({"text": part, "alts": []})
        block["tokens"] = tokens
    elif key == "limit":
        if not value.isdigit() or int(value) < 1:
            raise AuthoringError("limit is a whole number of allowed changes")
        block["limit"] = int(value)
    elif key == "accept":
        block.setdefault("accept", []).extend(_edit_map(part) for part in split_bar(value))
    elif key == "eval":
        name, _, arguments = value.partition(" ")
        options = {}
        for word in arguments.split():
            option, eq, setting = word.partition("=")
            if not eq:
                raise AuthoringError("evaluator options look like key=value")
            options[option] = setting
        block["computed"] = {"name": name, "args": options}
    elif key == "clue":
        if len(words) < 2:
            raise AuthoringError("a clue needs a label: 'clue Label: text'")
        block.setdefault("clues", []).append({"label": words[1].strip(), "text": value})
    elif key == "need":
        try:
            block["sufficient"] = [sorted(int(v) for v in part.split(",")) for part in split_bar(value)]
        except ValueError:
            raise AuthoringError("need lists clue numbers: '1,3 | 2'")
    elif key == "param":
        fields = split_bar(value)
        match = _PARAM.match(fields[0]) if fields else None
        if len(words) < 2 or not _NAME.match(words[1]) or not match or len(fields) < 2:
            raise AuthoringError("param looks like 'param v: 0..20 /1 @5 | Speed | m/s'")
        block.setdefault("params", []).append({
            "id": words[1], "min": _number(match.group(1)), "max": _number(match.group(2)),
            "step": _number(match.group(3)), "start": _number(match.group(4)),
            "label": fields[1], "unit": fields[2] if len(fields) > 2 else ""})
    elif key == "out":
        fields = split_bar(value)
        if len(words) < 2 or not _NAME.match(words[1]) or len(fields) < 2:
            raise AuthoringError("out looks like 'out d: v*t | Distance | m'")
        block.setdefault("outputs", []).append({
            "id": words[1], "expr": fields[0], "label": fields[1],
            "unit": fields[2] if len(fields) > 2 else ""})
    elif key == "view":
        block["view"] = value
    elif key == "bank":
        block["bank"] = split_bar(value)
    else:
        raise AuthoringError("unknown step line '%s'" % key)


# -------------------------------------------------------------- validation

def _text(value, what, low=1, high=MAX_TEXT):
    if not isinstance(value, str) or not low <= len(value.strip()) <= high:
        raise AuthoringError("%s must be %d to %d characters" % (what, low, high))


def _unique(values, what, fold=True):
    seen = set()
    for value in values:
        # Options keep their case: F(b) and f(b) are different things to offer.
        key = " ".join((str(value).casefold() if fold else str(value)).split())
        if key in seen:
            raise AuthoringError("%s repeats '%s'" % (what, value))
        seen.add(key)


def validate_step(step: Dict, level: int, strict: bool = True) -> None:
    kind = step["type"]
    _text(step["prompt"], "a prompt", 3, 400)
    if strict:
        if not step["hints"]:
            raise AuthoringError("every step offers at least one hint")
        _text(step["why"], "the explanation (why:)", 8)
    for hint in step["hints"]:
        _text(hint, "a hint", 3, 300)
    if kind in CHOICE_TYPES:
        options = step.get("options") or []
        right = [o for o in options if o["correct"]]
        wrong = [o for o in options if not o["correct"]]
        if kind == "select" or (kind == "compare" and len(right) > 1):
            step["multi"] = True
            if not right or not wrong:
                raise AuthoringError("a select-all step needs right and wrong statements")
        elif len(right) != 1 or not wrong:
            raise AuthoringError("a %s step needs exactly one right option and at least one distractor" % kind)
        if not 2 <= len(options) <= 6:
            raise AuthoringError("offer 2 to 6 options")
        _unique([o["text"] for o in options], "the option list", fold=False)
        for option in options:
            _text(option["text"], "an option", 1, 160)
            if not option["correct"]:
                if not option["feedback"]:
                    raise AuthoringError("distractor '%s' needs feedback aimed at its error" % option["text"])
                if strict and not option["error"]:
                    raise AuthoringError("distractor '%s' needs its reasoning error in [brackets]" % option["text"])
    if kind == "compare":
        panels = step.get("panels") or {}
        if set(panels) != {"left", "right"}:
            raise AuthoringError("a compare step shows a left: and a right: structure")
    elif kind == "order":
        items = step.get("items") or []
        if not 3 <= len(items) <= 7:
            raise AuthoringError("order 3 to 7 items")
        _unique(items, "the order list")
        if step.get("ends") and len(step["ends"]) != 2:
            raise AuthoringError("ends: names the first and the last position")
    elif kind == "match":
        pairs = step.get("pairs") or []
        if not 3 <= len(pairs) <= 6:
            raise AuthoringError("match 3 to 6 pairs")
        _unique([p[0] for p in pairs], "the left side")
        _unique([p[1] for p in pairs], "the right side")
    elif kind == "group":
        bins = step.get("bins") or []
        items = [item for b in bins for item in b["items"]]
        if not 2 <= len(bins) <= 4 or not 4 <= len(items) <= 10:
            raise AuthoringError("sort 4 to 10 items into 2 to 4 groups")
        if any(not b["items"] for b in bins):
            raise AuthoringError("every group needs at least one item")
        _unique([b["name"] for b in bins], "the group names")
        _unique(items, "the items to sort")
        for name in step.get("notes") or {}:
            if name not in items:
                raise AuthoringError("note '%s' matches no item" % name)
    elif kind == "fill":
        frame = step.get("frame") or ""
        blanks = frame.count("__")
        answers = step.get("answers") or []
        if not 1 <= blanks <= 3 or blanks != len(answers) or any(not a for a in answers):
            raise AuthoringError("a fill step needs a frame with 1 to 3 __ blanks and one answer: line for each")
        if step.get("choices"):
            if blanks != 1 or not 2 <= len(step["choices"]) <= 6:
                raise AuthoringError("taps: offers 2 to 6 choices for a single blank")
            _unique(step["choices"], "the tap choices")
            if not any(_same(choice, accepted) for choice in step["choices"] for accepted in answers[0]):
                raise AuthoringError("the tap choices do not include the answer")
        elif strict and level <= 1:
            raise AuthoringError("readers at stages 0 and 1 answer by tapping: add taps:")
    elif kind == "edit":
        tokens = step.get("tokens") or []
        limit = step.setdefault("limit", 1)
        computed = step.get("computed")
        if not 2 <= len(tokens) <= 14:
            raise AuthoringError("an edit step shows 2 to 14 tokens")
        if not any(t["alts"] for t in tokens):
            raise AuthoringError("at least one token must offer a replacement in {braces}")
        if not step.get("aim"):
            raise AuthoringError("an edit step states its aim:")
        accept = step.get("accept") or []
        if not accept and not computed:
            raise AuthoringError("an edit step lists accept: edits or names an eval:")
        for edit in accept + [w["edit"] for w in step.get("wrong") or []]:
            if not 1 <= len(edit) <= limit:
                raise AuthoringError("an edit changes between 1 and limit tokens")
            for position, value in edit.items():
                if not 1 <= position <= len(tokens) or value not in tokens[position - 1]["alts"]:
                    raise AuthoringError("edit %d=%s is not an offered replacement" % (position, value))
    elif kind == "clues":
        clues = step.get("clues") or []
        need = step.get("sufficient") or []
        if not 2 <= len(clues) <= 5 or not need:
            raise AuthoringError("a clues step hides 2 to 5 clues and lists need:")
        for group in need:
            if not group or any(not 1 <= n <= len(clues) for n in group):
                raise AuthoringError("need: refers to a clue that does not exist")
        _unique([c["label"] for c in clues], "the clue labels")
    elif kind == "explore":
        params, outputs = step.get("params") or [], step.get("outputs") or []
        if not 1 <= len(params) <= 3 or not 1 <= len(outputs) <= 3:
            raise AuthoringError("explore 1 to 3 parameters and show 1 to 3 results")
        if not step.get("aim") or not step.get("target"):
            raise AuthoringError("an explore step states its aim: and a checkable target:")
        ids = [p["id"] for p in params] + [o["id"] for o in outputs]
        _unique(ids, "parameter and result names")
        known = {p["id"] for p in params}
        start = {p["id"]: p["start"] for p in params}
        for p in params:
            if not p["min"] < p["max"] or p["step"] <= 0 or not p["min"] <= p["start"] <= p["max"]:
                raise AuthoringError("parameter '%s' has an impossible range" % p["id"])
            if (p["max"] - p["min"]) / p["step"] > 400:
                raise AuthoringError("parameter '%s' has too many positions" % p["id"])
        values = dict(start)
        try:
            for o in outputs:
                if exprs.names(o["expr"]) - known - {x["id"] for x in outputs}:
                    raise AuthoringError("result '%s' reads an unknown name" % o["id"])
                values[o["id"]] = exprs.evaluate(o["expr"], values)
            if exprs.names(step["target"]) - set(values):
                raise AuthoringError("the target reads an unknown name")
            met = exprs.evaluate(step["target"], values)
        except exprs.ExpressionError as exc:
            raise AuthoringError(str(exc))
        if not isinstance(met, bool):
            raise AuthoringError("the target must be a comparison")
        if met:
            raise AuthoringError("the target is already met at the starting position")
        if not _reachable(step):
            raise AuthoringError("no parameter position meets the target")
        _check_view(step, values)
    elif kind == "build":
        bank, answers = step.get("bank") or [], step.get("answers") or []
        if not 3 <= len(bank) <= 12 or not answers:
            raise AuthoringError("a build step offers a bank of 3 to 12 pieces and at least one answer:")
        for answer in answers:
            if not 2 <= len(answer) <= 8:
                raise AuthoringError("an assembled answer uses 2 to 8 pieces")
            pool = list(bank)
            for piece in answer:
                if piece not in pool:
                    raise AuthoringError("piece '%s' is not in the bank (or is used too often)" % piece)
                pool.remove(piece)
    elif kind == "reflect":
        _text(step.get("model") or "", "the model answer", 20)
    if step.get("card"):
        _text(step["card"]["front"], "a card front", 5, 300)
        _text(step["card"]["back"], "a card back", 1, 400)


_VIEW_SERIES = re.compile(r"^(bars|plot)\s+(\w+)\s+over\s+(\w+)$")
_VIEW_GRAPH = re.compile(r"^graph\s+(.+?)\s+x=(-?\d+(?:\.\d+)?)\.\.(-?\d+(?:\.\d+)?)$")


def _check_view(step: Dict, values: Dict) -> None:
    """An exploration's picture: a result across one control, or a curve in x."""
    view = step.get("view") or ""
    if not view:
        return
    series, graph = _VIEW_SERIES.match(view), _VIEW_GRAPH.match(view)
    if series:
        if (series.group(2) not in {o["id"] for o in step["outputs"]}
                or series.group(3) not in {p["id"] for p in step["params"]}):
            raise AuthoringError("view: names a result and a parameter of this step")
    elif graph:
        try:
            unknown = exprs.names(graph.group(1)) - set(values) - {"x"}
            exprs.evaluate(graph.group(1), dict(values, x=float(graph.group(2))))
        except exprs.ExpressionError as exc:
            raise AuthoringError("view: %s" % exc)
        if unknown or float(graph.group(2)) >= float(graph.group(3)):
            raise AuthoringError("view: graph uses x and this step's names over an increasing range")
    else:
        raise AuthoringError("view: is 'bars r over p', 'plot r over p' or 'graph <expression> x=a..b'")


def _same(given: str, expected: str) -> bool:
    if exprs.number(given) is not None and exprs.number(expected) is not None:
        return exprs.same_number(given, expected)
    return " ".join(given.casefold().split()) == " ".join(expected.casefold().split())


def _reachable(step: Dict) -> bool:
    """Whether some combination of parameter positions satisfies the target."""
    grids = []
    for p in step["params"]:
        count = int(round((p["max"] - p["min"]) / p["step"]))
        grids.append([round(p["min"] + i * p["step"], 6) for i in range(count + 1)])
    total = 1
    for grid in grids:
        total *= len(grid)
    if total > 30000:
        return True          # too large to enumerate at load; the playthrough tests cover it

    def walk(index, values):
        if index == len(grids):
            scope = dict(values)
            try:
                for o in step["outputs"]:
                    scope[o["id"]] = exprs.evaluate(o["expr"], scope)
                return exprs.evaluate(step["target"], scope) is True
            except exprs.ExpressionError:
                return False
        for value in grids[index]:
            values[step["params"][index]["id"]] = value
            if walk(index + 1, values):
                return True
        return False

    return walk(0, {})


def validate(seq: Dict, level: int, strict: bool = True) -> Dict:
    """Check one sequence and settle its derived fields.  Raises AuthoringError."""
    source, line = seq.get("source", ""), seq.get("line", 0)
    try:
        _text(seq.get("objective"), "the learning objective (goal:)", 12, 320)
        beats = seq.get("beats") or []
        steps = [b for b in beats if b["kind"] == "step"]
        shows = [b for b in beats if b["kind"] != "step"]
        if strict:
            if [b["kind"] for b in beats[:2]] != ["intro", "demo"] or len(shows) != 2:
                raise AuthoringError("a sequence opens with one intro: and one demo:, then its steps")
            if len(steps) < 3:
                raise AuthoringError("a sequence has at least three checked steps")
            if len({s["type"] for s in steps}) < 2:
                raise AuthoringError("a sequence uses at least two interaction types")
            transfers = [s for s in steps if s["transfer"]]
            if len(transfers) != 1 or not steps[-1]["transfer"]:
                raise AuthoringError("a sequence ends with exactly one transfer task (>)")
        elif not steps:
            raise AuthoringError("a sequence has at least one checked step")
        for show in shows:
            _text(show["text"], "the %s text" % show["kind"], 12)
        seq["level"] = level = int(seq.get("level", level))
        prompts = []
        for index, beat in enumerate(beats):
            line = beat.get("line", line)
            if beat["kind"] == "step":
                validate_step(beat, level, strict)
                prompts.append(beat["prompt"])
        _unique(prompts, "the sequence's prompts")
    except AuthoringError as exc:
        if exc.line:
            raise
        raise AuthoringError(exc.detail, source, line)
    # Stable identities: a checkpoint names a step by position within its
    # sequence and is only honoured while the step's own content is unchanged.
    counter = 0
    for beat in beats:
        if beat["kind"] == "step":
            counter += 1
            beat["id"] = "s%d" % counter
        else:
            beat["id"] = beat["kind"]
        beat["fingerprint"] = fingerprint(beat)
    seq["fingerprint"] = fingerprint([b["fingerprint"] for b in beats] + [seq["objective"]])
    return seq


def fingerprint(value) -> str:
    def clean(item):
        if isinstance(item, dict):
            return {k: clean(v) for k, v in sorted(item.items())
                    if k not in ("line", "fingerprint", "id")}
        if isinstance(item, (list, tuple)):
            return [clean(v) for v in item]
        return item
    packed = json.dumps(clean(value), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(packed.encode("utf-8")).hexdigest()[:16]


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-")[:48] or "sequence"
