"""Sequences built from a module's own reviewed reporting reference.

Most specialist radiology modules carry a structured reference — an ordered
approach, a table of measurements with their thresholds, a classification
table, a list of pitfalls — that has already been through source review.
Writing fresh clinical statements for an activity would put unreviewed claims
beside reviewed ones, so these sequences do not: every option, pair and
explanation below is the module's own wording, rearranged into a question.
A response is right exactly when it agrees with the reference.

What that buys is honesty about scope.  The activity practises *recalling and
navigating the reference* (sequencing the approach, pairing a measurement with
its threshold, reading a classification row both ways).  It does not present
a case, and it says so.  Modules whose reference is too thin to support a
step simply get fewer steps; the coverage report lists each one.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

# Long cells make poor options on a phone; rows beyond this are left to the
# reference itself rather than squeezed into a button.
MAX_CELL = 160
MAX_PAIR = 150


def _clean(text) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _sentence(text: str) -> str:
    text = _clean(text)
    return text if not text or text[-1] in ".?!" else text + "."


def _clip(text: str, limit: int) -> str:
    text = _clean(text)
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",;:—-")
    return cut + "…"


def _distinct(rows: List[List[str]], column: int) -> bool:
    cells = [_clean(row[column]).casefold() for row in rows]
    return len(set(cells)) == len(cells)


def _usable_rows(classify: Dict, width: int) -> List[List[str]]:
    rows = []
    for row in classify.get("rows") or []:
        if len(row) >= width and all(_clean(cell) and len(_clean(cell)) <= MAX_CELL for cell in row[:width]):
            rows.append([_clean(cell) for cell in row[:width]])
    return rows


def _row_text(columns: List[str], row: List[str]) -> str:
    return " ".join("%s: %s" % (_clean(name), _sentence(cell)) for name, cell in zip(columns, row))


def _choice_step(prompt, rows, ask, tell, target, hint, why, transfer=False):
    """One classification row read from column ``ask`` to column ``tell``."""
    options = []
    for index, row in enumerate(rows):
        if index == target:
            options.append({"text": row[tell], "correct": True, "feedback": "", "error": ""})
        else:
            options.append({"text": row[tell], "correct": False, "error": "neighbouring-row",
                            "feedback": "In the module's table that entry belongs with “%s”." % _clip(row[ask], 120)})
    return {"kind": "step", "type": "predict", "prompt": prompt, "transfer": transfer,
            "options": options, "hints": [hint], "why": why, "miss": ""}


def sequence_from_reference(node: Dict) -> Optional[Dict]:
    """Build the reporting-pathway sequence for one module, or None."""
    reference = node.get("reference")
    if not isinstance(reference, dict):
        return None
    approach = [step for step in reference.get("approach") or []
                if _clean(step.get("step")) and _clean(step.get("detail"))]
    if len(approach) < 3:
        return None
    title = _clean(node.get("title"))
    names = [_clean(step["step"]) for step in approach]
    beats: List[Dict] = [
        {"kind": "intro",
         "text": "%s has a reporting reference built from reviewed sources. It sets out an approach in %d steps. "
                 "This activity practises finding your way around that reference; it does not present a patient."
                 % (title, len(approach))},
        {"kind": "demo",
         "text": "The approach opens with “%s”. %s" % (names[0], _sentence(_clip(approach[0]["detail"], 420))),
         "visual": {"kind": "steps", "items": [_clip(name, 90) for name in names[:3]] + (["…"] if len(names) > 3 else [])}},
    ]
    shown = names[:6]
    beats.append({
        "kind": "step", "type": "order", "transfer": False, "miss": "",
        "prompt": ("Put the first six steps of the approach in the order the reference gives them."
                   if len(names) > 6 else "Put the steps of the approach in the order the reference gives them."),
        "items": shown, "ends": ["First", "Last"],
        "hints": ["The approach begins with “%s”." % shown[0],
                  "It ends, among these, with “%s”." % shown[-1]],
        "why": "The reference's order: " + " → ".join(shown) + ".",
    })

    measures = [m for m in reference.get("measure") or []
                if _clean(m.get("what")) and _clean(m.get("cutoff"))
                and len(_clean(m["what"])) <= MAX_PAIR and len(_clean(m["cutoff"])) <= MAX_PAIR]
    pairs = []
    for measure in measures:
        what, cutoff = _clean(measure["what"]), _clean(measure["cutoff"])
        if what.casefold() in {p[0].casefold() for p in pairs} or cutoff.casefold() in {p[1].casefold() for p in pairs}:
            continue
        pairs.append([what, cutoff])
        if len(pairs) == 4:
            break
    if len(pairs) >= 3:
        beats.append({
            "kind": "step", "type": "match", "transfer": False, "miss": "", "pairs": pairs,
            "prompt": "Match each measurement to the threshold or reading the reference gives for it.",
            "hints": ["Begin with the measurement you know best; the others narrow by elimination."],
            "why": " ".join("%s: %s" % (what, _sentence(cutoff)) for what, cutoff in pairs),
        })

    classify = reference.get("classify") if isinstance(reference.get("classify"), dict) else None
    columns = [_clean(c) for c in (classify or {}).get("columns") or []]
    note = _sentence(classify.get("note")) if classify and classify.get("note") else ""
    table = _clip((classify or {}).get("name"), 90)
    transfer_made = False
    if classify and len(columns) >= 2:
        rows = _usable_rows(classify, 2)[:4]
        if len(rows) >= 3 and _distinct(rows, 0) and _distinct(rows, 1):
            beats.append(_choice_step(
                "In the module's table “%s”, which entry under “%s” goes with: %s?" % (table, columns[1], rows[0][0]),
                rows, 0, 1, 0,
                "Find the row of the table that names this finding under “%s”." % columns[0],
                _join(_row_text(columns[:2], rows[0]), note)))
            wide = _usable_rows(classify, 3)[:4]
            if len(columns) >= 3 and len(wide) >= 3 and _distinct(wide, 0) and _distinct(wide, 2):
                target = len(wide) - 1
                beats.append(_choice_step(
                    "Carry the same table one column further. For “%s”, what does the reference give under “%s”?"
                    % (wide[target][0], columns[2]),
                    wide, 0, 2, target,
                    "Read along the row: “%s”, then “%s”, then “%s”." % tuple(columns[:3]),
                    _join(_row_text(columns[:3], wide[target]), note), transfer=True))
                transfer_made = True
            else:
                target = len(rows) - 1
                beats.append(_choice_step(
                    "Now read the table the other way. A report states “%s”. Which entry under “%s” supports it?"
                    % (rows[target][1], columns[0]),
                    rows, 1, 0, target,
                    "Each entry under “%s” belongs to exactly one row." % columns[1],
                    _join(_row_text(columns[:2], rows[target]), note), transfer=True))
                transfer_made = True
    if not transfer_made:
        # No table to read both ways: carry the approach itself to its detail.
        described = [(name, _clip(step["detail"], MAX_PAIR)) for name, step in zip(names, approach)][:4]
        if len(described) >= 3 and len({d[1] for d in described}) == len(described):
            beats.append({
                "kind": "step", "type": "match", "transfer": True, "miss": "",
                "pairs": [[name, detail] for name, detail in described],
                "prompt": "Match each step of the approach to what the reference asks you to do at that step.",
                "hints": ["Read each description for the action it names; the step titles summarise those actions."],
                "why": " ".join("%s: %s" % (name, _sentence(detail)) for name, detail in described),
            })
    pitfalls = [_sentence(p) for p in reference.get("pitfalls") or [] if _clean(p)]
    source = reference.get("source") if isinstance(reference.get("source"), dict) else {}
    return {
        "node_id": node["id"], "title": "Reporting pathway", "objective": _clip(node.get("goal"), 310),
        "beats": beats,
        "next": _join("Open the reporting reference to use the approach on a study.",
                      ("A pitfall the reference names: " + pitfalls[0]) if pitfalls else ""),
        "origin": {"kind": "derived", "review": "reference-reviewed",
                   "source": _clean(source.get("title")) or "module reporting reference",
                   "note": "Every statement is the module's own reviewed reference text; "
                           "the activity framing has not had a separate specialist review."},
        "source": "derived:" + node["id"], "line": 0,
    }


def _join(*parts) -> str:
    return " ".join(part for part in parts if part)
