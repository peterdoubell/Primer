"""Marking one response to one step, and saying something useful about it.

Each interaction type has one evaluator.  They work on canonical values —
option and item *indices* into the authored model, never the shuffled ids a
browser holds — so the catalog is the only place that knows how a step was
presented.  An evaluator returns a verdict:

    correct   True, False, or None for a step the book declines to mark
    feedback  what to tell the reader about *this* response
    error     the authored reasoning-error tag behind a chosen distractor
    marks     per-part detail the player may show (which pairs, which places)

A subject may also supply its own evaluation method: ``eval: name key=value``
on a step hands marking to a registered function (see ``computed``), which is
how exact number theory and expression repair are checked without listing
every acceptable answer by hand.
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional

from . import exprs

REFLECT_MIN_CHARS = 20


def norm(text) -> str:
    return " ".join(str(text).casefold().replace("’", "'").split())


def same_value(given: str, accepted: str) -> bool:
    if exprs.number(given) is not None and exprs.number(accepted) is not None:
        return exprs.same_number(given, accepted)
    return norm(given) == norm(accepted)


def _verdict(correct, feedback="", error="", **marks) -> Dict:
    return {"correct": correct, "feedback": feedback.strip(), "error": error,
            "marks": {k: v for k, v in marks.items() if v is not None}}


def _join(*parts) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


# ------------------------------------------------------------ computed

_COMPUTED: Dict[str, Dict[str, Callable]] = {}


def computed(name: str):
    """Register a subject-supplied evaluation method under ``name``.

    The decorated class provides ``expand(step)`` (run once at load, before
    validation, to fill in anything derivable from the options), ``check(step,
    response)`` returning a verdict, and ``solution(step)`` returning one
    canonical right response.
    """
    def register(cls):
        _COMPUTED[name] = {"expand": cls.expand, "check": cls.check, "solution": cls.solution}
        return cls
    return register


def expand(step: Dict) -> None:
    spec = step.get("computed")
    if not spec:
        return
    if spec["name"] not in _COMPUTED:
        raise ValueError("unknown evaluator '%s'" % spec["name"])
    _COMPUTED[spec["name"]]["expand"](step)


def _digits_of(step: Dict, edits: Dict[int, str]) -> str:
    return "".join(edits.get(index + 1, token["text"]) for index, token in enumerate(step["tokens"]))


@computed("nt.repair")
class _RepairDigit:
    """Change digits of a decimal numeral so the number becomes a multiple.

    ``eval: nt.repair by=8``.  Every position may take any other digit, except
    that the leading digit may not become zero.  The marking is exact integer
    arithmetic, so a five-digit puzzle and a forty-digit one are equally safe.
    """

    @staticmethod
    def expand(step):
        divisor = int(step["computed"]["args"].get("by", "0"))
        if divisor < 2:
            raise ValueError("nt.repair needs by=<divisor of at least 2>")
        tokens = step.get("tokens") or []
        if not tokens or any(not (len(t["text"]) == 1 and t["text"].isdigit()) for t in tokens):
            raise ValueError("nt.repair edits single decimal digits")
        for index, token in enumerate(tokens):
            token["alts"] = [d for d in "0123456789"
                             if d != token["text"] and not (index == 0 and d == "0" and len(tokens) > 1)]

    @staticmethod
    def check(step, edits):
        divisor = int(step["computed"]["args"]["by"])
        value = int(_digits_of(step, edits))
        remainder = value % divisor
        if remainder == 0:
            return _verdict(True, "%d = %d × %d, so it is a multiple of %d."
                            % (value, divisor, value // divisor, divisor))
        return _verdict(False, "%d leaves remainder %d when divided by %d."
                        % (value, remainder, divisor), "remainder-not-zero")

    @staticmethod
    def solution(step):
        divisor = int(step["computed"]["args"]["by"])
        tokens = step["tokens"]
        for position in range(len(tokens), 0, -1):          # prefer the units end
            for digit in tokens[position - 1]["alts"]:
                if int(_digits_of(step, {position: digit})) % divisor == 0:
                    return {position: digit}
        return {}

    @staticmethod
    def repairable_positions(number: str, divisor: int) -> List[int]:
        """Positions, counted from the right, where one new digit makes a multiple."""
        found = []
        for index in range(len(number)):
            for digit in "0123456789":
                if digit == number[index] or (index == 0 and digit == "0" and len(number) > 1):
                    continue
                if int(number[:index] + digit + number[index + 1:]) % divisor == 0:
                    found.append(len(number) - index)
                    break
        return found


@computed("expr.equals")
class _RepairExpression:
    """Edit the tokens of an arithmetic expression until it has a target value.

    ``eval: expr.equals value=24``.  The tokens are joined and evaluated by the
    restricted arithmetic language in ``exprs``; any edit within the limit that
    reaches the value is accepted, so the author does not have to enumerate
    every repair a reader might find.
    """

    @staticmethod
    def expand(step):
        target = step["computed"]["args"].get("value")
        if target is None or exprs.number(target) is None:
            raise ValueError("expr.equals needs value=<number>")
        text = " ".join(token["text"] for token in step.get("tokens") or [])
        try:
            start = exprs.evaluate(text)
        except exprs.ExpressionError as exc:
            raise ValueError("expr.equals tokens are not an expression: %s" % exc)
        if exprs.same_number(str(start), target):
            raise ValueError("expr.equals already has its target value")
        if not _RepairExpression.solution(step):
            raise ValueError("expr.equals has no repair within the limit")

    @staticmethod
    def _value(step, edits):
        text = " ".join(edits.get(index + 1, token["text"]) for index, token in enumerate(step["tokens"]))
        return exprs.evaluate(text)

    @staticmethod
    def check(step, edits):
        target = step["computed"]["args"]["value"]
        try:
            value = _RepairExpression._value(step, edits)
        except exprs.ExpressionError:
            return _verdict(False, "That is no longer an expression that can be worked out.", "malformed")
        shown = ("%g" % value) if not isinstance(value, bool) else str(value)
        if not isinstance(value, bool) and exprs.same_number(str(value), target):
            return _verdict(True, "That now works out to %s." % shown)
        return _verdict(False, "That works out to %s, not %s." % (shown, target), "wrong-value")

    @staticmethod
    def solution(step):
        limit = step.get("limit", 1)
        tokens = step["tokens"]
        editable = [(i + 1, alt) for i, token in enumerate(tokens) for alt in token["alts"]]

        def search(start, chosen):
            if chosen:
                try:
                    value = _RepairExpression._value(step, chosen)
                    if not isinstance(value, bool) and exprs.same_number(
                            str(value), step["computed"]["args"]["value"]):
                        return dict(chosen)
                except exprs.ExpressionError:
                    pass
            if len(chosen) >= limit:
                return None
            for index in range(start, len(editable)):
                position, alt = editable[index]
                if position in chosen:
                    continue
                chosen[position] = alt
                found = search(index + 1, chosen)
                del chosen[position]
                if found:
                    return found
            return None

        return search(0, {}) or {}


# ------------------------------------------------------------ per type

def _choice(step: Dict, response: Dict, state: Dict) -> Dict:
    options = step["options"]
    if step.get("multi"):
        chosen = sorted(set(response.get("choices") or []))
        if not chosen:
            return _verdict(False, "Choose at least one statement first.", "no-response")
        right = [i for i, o in enumerate(options) if o["correct"]]
        extra = [i for i in chosen if i not in right]
        missing = [i for i in right if i not in chosen]
        if not extra and not missing:
            return _verdict(True)
        if extra:
            option = options[extra[0]]
            return _verdict(False, _join("“%s”:" % option["text"], option["feedback"]),
                            option["error"], wrong=extra)
        return _verdict(False, _join(
            "Everything you chose holds, and there is more: %d of %d found." % (len(chosen), len(right)),
            step.get("miss")), "incomplete-selection", wrong=[])
    choice = response.get("choice")
    if not isinstance(choice, int) or not 0 <= choice < len(options):
        return _verdict(False, "Choose an answer first.", "no-response")
    option = options[choice]
    if step["type"] == "clues":
        return _clues(step, option, state)
    return _verdict(option["correct"], option["feedback"], "" if option["correct"] else option["error"],
                    chosen=choice)


def _clues(step: Dict, option: Dict, state: Dict) -> Dict:
    revealed = sorted(set(state.get("revealed") or []))
    minimal = step["sufficient"]
    if not option["correct"]:
        return _verdict(False, option["feedback"], option["error"])
    covering = [group for group in minimal if set(group) <= set(revealed)]
    labels = lambda group: " and ".join("“%s”" % step["clues"][n - 1]["label"] for n in group)
    if not covering:
        return _verdict(False, _join(
            "That is the right outcome, but nothing you have turned over settles it yet: "
            "what you can see still fits more than one answer.",
            "Turn over what you need, then decide again."), "decided-without-evidence", unsupported=True)
    efficient = any(sorted(group) == revealed for group in minimal)
    if efficient:
        return _verdict(True, _join(option["feedback"], "You used the fewest clues that could settle it."),
                        efficient=True)
    best = min(minimal, key=len)
    return _verdict(True, _join(option["feedback"],
                                "It could be settled with less: %s would have been enough." % labels(best)),
                    efficient=False)


def _order(step: Dict, response: Dict, state: Dict) -> Dict:
    order = response.get("order") or []
    count = len(step["items"])
    if sorted(order) != list(range(count)):
        return _verdict(False, "Place every item first.", "no-response")
    placed = [given == index for index, given in enumerate(order)]
    if all(placed):
        return _verdict(True, placed=placed)
    first = placed.index(False)
    return _verdict(False, _join(
        "%d of %d are in the right place." % (sum(placed), count),
        "Look again at position %d." % (first + 1), step.get("miss")),
        "sequence-error", placed=placed)


def _match(step: Dict, response: Dict, state: Dict) -> Dict:
    pairs = response.get("pairs") or {}
    count = len(step["pairs"])
    if sorted(pairs) != list(range(count)) or sorted(pairs.values()) != list(range(count)):
        return _verdict(False, "Pair every item first.", "no-response")
    wrong = [left for left, right in pairs.items() if left != right]
    if not wrong:
        return _verdict(True, wrong=[])
    return _verdict(False, _join(
        "%d of %d pairs are right." % (count - len(wrong), count),
        "Look again at “%s”." % step["pairs"][wrong[0]][0], step.get("miss")),
        "pairing-error", wrong=wrong)


def group_items(step: Dict) -> List[Dict]:
    return [{"text": item, "bin": index} for index, group in enumerate(step["bins"])
            for item in group["items"]]


def _group(step: Dict, response: Dict, state: Dict) -> Dict:
    items = group_items(step)
    bins = response.get("bins") or {}
    if sorted(bins) != list(range(len(items))) or any(
            not isinstance(b, int) or not 0 <= b < len(step["bins"]) for b in bins.values()):
        return _verdict(False, "Sort every item first.", "no-response")
    wrong = [index for index, item in enumerate(items) if bins[index] != item["bin"]]
    if not wrong:
        return _verdict(True, wrong=[])
    item = items[wrong[0]]
    note = (step.get("notes") or {}).get(item["text"], "")
    return _verdict(False, _join(
        "%d of %d are in the right group." % (len(items) - len(wrong), len(items)),
        ("“%s”: %s" % (item["text"], note)) if note else "Look again at “%s”." % item["text"],
        step.get("miss")), "classification-error", wrong=wrong)


def _fill(step: Dict, response: Dict, state: Dict) -> Dict:
    values = [str(v).strip()[:120] for v in (response.get("values") or [])]
    answers = step["answers"]
    if len(values) != len(answers) or any(not v for v in values):
        return _verdict(False, "Fill in every blank first.", "no-response")
    right = [any(same_value(value, accepted) for accepted in accepted_list)
             for value, accepted_list in zip(values, answers)]
    if all(right):
        return _verdict(True, right=right)
    for anticipated in step.get("wrong") or []:
        if any(same_value(value, anticipated["value"]) for value in values):
            return _verdict(False, anticipated["feedback"], anticipated["error"], right=right)
    direction = ""
    if len(answers) == 1:
        given, wanted = exprs.number(values[0]), exprs.number(answers[0][0])
        if given is not None and wanted is not None:
            direction = "Too high." if given > wanted else "Too low."
    return _verdict(False, _join(direction or ("Not yet." if len(answers) == 1 else
                                               "%d of %d blanks are right." % (sum(right), len(right))),
                                 step.get("miss")), "wrong-value", right=right)


def _edit(step: Dict, response: Dict, state: Dict) -> Dict:
    tokens = step["tokens"]
    edits = {}
    for position, value in (response.get("edits") or {}).items():
        if (not isinstance(position, int) or not 1 <= position <= len(tokens)
                or value not in tokens[position - 1]["alts"]):
            return _verdict(False, "That replacement is not on offer.", "no-response")
        edits[position] = value
    limit = step.get("limit", 1)
    if not edits:
        return _verdict(False, "Change something first: tap a part to see what it may become.", "no-response")
    if len(edits) > limit:
        # Outside the rules of the step rather than a wrong answer: not an attempt.
        return _verdict(False, "Too many changes: you may change %s. Put one back first." % (
            "one part only" if limit == 1 else "at most %d parts" % limit), "no-response")
    if any(edits == accepted for accepted in step.get("accept") or []):
        return _verdict(True, edits=edits)
    if step.get("computed"):
        return _COMPUTED[step["computed"]["name"]]["check"](step, edits)
    for anticipated in step.get("wrong") or []:
        if anticipated["edit"] == edits:
            return _verdict(False, anticipated["feedback"], anticipated["error"])
    return _verdict(False, _join("That change does not meet the aim yet.", step.get("miss")), "wrong-edit")


def explore_values(step: Dict, given: Dict) -> Optional[Dict]:
    """Snap a reader's parameter values to the authored grid; None if unusable."""
    values = {}
    for p in step["params"]:
        raw = given.get(p["id"])
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            return None
        clamped = min(max(float(raw), p["min"]), p["max"])
        snapped = p["min"] + round((clamped - p["min"]) / p["step"]) * p["step"]
        values[p["id"]] = round(min(snapped, p["max"]), 6)
    for o in step["outputs"]:
        values[o["id"]] = exprs.evaluate(o["expr"], values)
    return values


def _explore(step: Dict, response: Dict, state: Dict) -> Dict:
    try:
        values = explore_values(step, response.get("values") or {})
    except exprs.ExpressionError:
        values = None
    if values is None:
        return _verdict(False, "Set every control first.", "no-response")
    readout = "; ".join("%s = %s%s" % (o["label"], _shown(values[o["id"]]),
                                       (" " + o["unit"]) if o["unit"] else "")
                        for o in step["outputs"])
    if exprs.evaluate(step["target"], values) is True:
        return _verdict(True, "You have it: %s." % readout)
    return _verdict(False, _join("Not there yet: %s." % readout, step.get("miss")), "target-not-met")


def _shown(value) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    return "%g" % round(float(value), 4)


def _build(step: Dict, response: Dict, state: Dict) -> Dict:
    bank = step["bank"]
    picked = response.get("tokens") or []
    if (not picked or len(set(picked)) != len(picked)
            or any(not isinstance(i, int) or not 0 <= i < len(bank) for i in picked)):
        return _verdict(False, "Place the pieces first.", "no-response")
    texts = [bank[i] for i in picked]
    answers = step["answers"]
    unordered = bool(step.get("unordered"))
    key = (lambda seq: sorted(norm(t) for t in seq)) if unordered else (lambda seq: [norm(t) for t in seq])
    if any(key(texts) == key(answer) for answer in answers):
        return _verdict(True)
    for anticipated in step.get("wrong") or []:
        if any(norm(text) == norm(anticipated["value"]) for text in texts):
            return _verdict(False, _join("“%s”:" % anticipated["value"], anticipated["feedback"]),
                            anticipated["error"])
    closest = max(answers, key=lambda answer: sum(1 for a, b in zip(answer, texts) if norm(a) == norm(b)))
    placed = None if unordered else [index < len(closest) and norm(closest[index]) == norm(text)
                                     for index, text in enumerate(texts)]
    count = ("%d of %d pieces belong." % (len([t for t in texts if norm(t) in [norm(a) for a in closest]]),
                                           len(closest))
             if unordered else "%d of %d pieces are in place." % (sum(placed), len(closest)))
    return _verdict(False, _join(count, step.get("miss")), "assembly-error", placed=placed)


def _reflect(step: Dict, response: Dict, state: Dict) -> Dict:
    text = str(response.get("text") or "").strip()
    if len(text) < REFLECT_MIN_CHARS:
        return _verdict(False, "Write a sentence or two of your own first; then compare it with the model answer.",
                        "no-response")
    # Not marked: a reader's own explanation is worth writing and worth
    # comparing, and a keyword match would only teach them to echo.
    return _verdict(None, "Not marked. Compare what you wrote with the model answer below.")


_EVALUATORS = {
    "predict": _choice, "select": _choice, "compare": _choice, "clues": _choice,
    "order": _order, "match": _match, "group": _group, "fill": _fill, "edit": _edit,
    "explore": _explore, "build": _build, "reflect": _reflect,
}


def evaluate(step: Dict, response: Dict, state: Dict = None) -> Dict:
    """Mark one canonical response.  Never raises on reader input."""
    try:
        return _EVALUATORS[step["type"]](step, response or {}, state or {})
    except (TypeError, ValueError, KeyError, AttributeError, exprs.ExpressionError):
        return _verdict(False, "That response could not be read. Try again.", "no-response")


def solution(step: Dict) -> Dict:
    """One canonical right response, in the same shape ``evaluate`` accepts."""
    kind = step["type"]
    if kind in ("predict", "compare", "clues", "select"):
        right = [i for i, o in enumerate(step["options"]) if o["correct"]]
        out = {"choices": right} if step.get("multi") else {"choice": right[0]}
        if kind == "clues":
            out["revealed"] = list(min(step["sufficient"], key=len))
        return out
    if kind == "order":
        return {"order": list(range(len(step["items"])))}
    if kind == "match":
        return {"pairs": {i: i for i in range(len(step["pairs"]))}}
    if kind == "group":
        return {"bins": {i: item["bin"] for i, item in enumerate(group_items(step))}}
    if kind == "fill":
        return {"values": [accepted[0] for accepted in step["answers"]]}
    if kind == "edit":
        if step.get("accept"):
            return {"edits": dict(step["accept"][0])}
        return {"edits": _COMPUTED[step["computed"]["name"]]["solution"](step)}
    if kind == "explore":
        return {"values": _solve_explore(step)}
    if kind == "build":
        pool = list(enumerate(step["bank"]))
        picked = []
        for piece in step["answers"][0]:
            index = next(i for i, text in pool if text == piece)
            pool.remove((index, piece))
            picked.append(index)
        return {"tokens": picked}
    return {"text": step.get("model", "")}


def _solve_explore(step: Dict) -> Dict:
    """The parameter position meeting the target that is nearest the start."""
    best, best_cost = None, None
    grids = []
    for p in step["params"]:
        count = int(round((p["max"] - p["min"]) / p["step"]))
        grids.append([round(p["min"] + i * p["step"], 6) for i in range(count + 1)])

    def walk(index, values):
        nonlocal best, best_cost
        if index == len(grids):
            try:
                scope = dict(values)
                for o in step["outputs"]:
                    scope[o["id"]] = exprs.evaluate(o["expr"], scope)
                if exprs.evaluate(step["target"], scope) is not True:
                    return
            except exprs.ExpressionError:
                return
            cost = sum(abs(values[p["id"]] - p["start"]) / p["step"] for p in step["params"])
            if best_cost is None or cost < best_cost:
                best, best_cost = dict(values), cost
            return
        for value in grids[index]:
            values[step["params"][index]["id"]] = value
            walk(index + 1, values)

    walk(0, {})
    return best or {p["id"]: p["start"] for p in step["params"]}
