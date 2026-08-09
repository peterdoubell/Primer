"""Audit the curriculum item banks against the board's standards.

Kept in the repo rather than a scratch directory because the previous copy lived
in /tmp and was rewritten — by the very agents whose work it was judging. A
verification tool that the thing under test can edit is not a verification tool.
Run it from the repo root:

    .venv/bin/python tools/check_banks.py            # every domain
    .venv/bin/python tools/check_banks.py data/curriculum/03-physics.json
"""

import collections
import glob
import json
import os
import re
import sys

MIN_DEPTH = 10          # a bank must be bigger than the paper drawn from it
MIN_YOUNG = 5
MAX_BINARY_SHARE = 0.15
MAX_LENGTH_EDGE = 0.08   # what picking by length may gain over guessing
# Below the hard threshold there was silence: banks drifting at +4.8 to
# +6.1pp all printed "ok" and nobody saw the trend until one crossed the
# line. The WARN tier names the margin per bank without failing CLEAN —
# visibility, not a new gate.
WARN_LENGTH_EDGE = 0.045
MAX_NAMING_SHARE = 0.25   # stems that demonstrably only ask for a term

ABS = re.compile(r"\b(all|every|never|only|cannot|always|none)\b", re.I)
DEFINITIONAL = re.compile(r"\b(refers to|is best described as|is defined as)\b", re.I)

# Asking the reader to NAME the thing, however much scenery surrounds it. An
# audit hand-classified one file at 59% application-or-transfer where this tool
# reported 81%: the old test required the stem to end in "?", so every recall
# item ending in ":" was counted as a novel situation. It was measuring
# punctuation. This is still a heuristic — the output says so — but it looks at
# what the reader is asked to produce.
NAMING = re.compile(
    r"\b(is called|are called|is known as|known as|the term for|term is|name for|"
    r"this (?:pattern|phenomenon|effect|process|fallacy|principle|law|error) is|"
    r"which (?:term|word|name|concept|theory|school|movement|period|genre)\b|"
    r"what (?:is|are) (?:the )?(?:term|name|word)\b|best describes|"
    r"this is an example of|this illustrates|would be classified as|"
    r"the (?:name|term) (?:given|used) )", re.I)
#
# There is deliberately no matching "APPLYING" pattern and no percentage in the
# output. Two attempts to estimate the application share were both wrong in the
# project's favour — the first counted any stem ending in ":" as a novel
# situation and reported 81% where a hand audit found 59%; the second still put
# two files at 100%. A regex cannot tell whether a reader is reasoning or
# recognising, and a number that looks measured is worse than no number. What
# this can honestly report is a *lower bound*: items whose stem asks, in so many
# words, for a name.


def audit(path):
    d = json.load(open(path))
    name = os.path.basename(path)
    problems = []
    rank = collections.Counter()   # keyed by strategy, not by rank
    abs_key = abs_dis = n_key = n_dis = 0
    novel = defn = 0
    naming_examples = []
    binary = young_choice = 0

    for n in d["nodes"]:
        stage = n.get("stage", 0)
        qs = n.get("quiz") or []
        older = stage >= 2

        if older and len(qs) < MIN_DEPTH:
            problems.append(("shallow", n["id"], "{} items".format(len(qs))))
        if not older and len(qs) < MIN_YOUNG:
            problems.append(("thin", n["id"], "{} items".format(len(qs))))
        if older and not any(q.get("kind") in ("numeric", "short") for q in qs):
            problems.append(("no produced item", n["id"], ""))

        prompts = [q.get("prompt", "") for q in qs]
        if len(set(prompts)) != len(prompts):
            problems.append(("duplicate prompt", n["id"], ""))

        for q in qs:
            stem, ans = q.get("prompt", ""), str(q.get("answer", ""))
            ch = q.get("choices") or []

            if q.get("kind") == "short" and len(q.get("keywords") or []) < 3:
                problems.append(("thin keywords", n["id"], stem[:40]))

            if ch:
                if ans not in ch:
                    problems.append(("answer not an option", n["id"], stem[:40]))
                if len(set(ch)) != len(ch):
                    problems.append(("duplicate options", n["id"], stem[:40]))
                shown = [o for o in ch if str(o) and str(o) in stem]
                if shown == [ans]:
                    problems.append(("stem shows only the key", n["id"], stem[:40]))
                if not older:
                    young_choice += 1
                    binary += len(ch) == 2
                if older and len(ch) >= 3 and ans in ch:
                    # What matters is not where the key sits in a length ranking
                    # but whether picking by length beats guessing. Chasing the
                    # ranking directly produced longest-key, then first-position,
                    # then shortest-key over three rounds — each fix overshooting
                    # into the opposite tell. Measure the exploit, not the proxy.
                    lens = sorted(len(str(o)) for o in ch)
                    flat = lens[-1] - lens[0] <= max(6, 0.25 * lens[-1])
                    rank["n"] += 1
                    rank["chance"] += 1.0 / len(ch)
                    if not flat:
                        rank["shortest"] += min(ch, key=len) == ans
                        rank["longest"] += max(ch, key=len) == ans
                    else:
                        # No length signal to read: a picker is guessing here.
                        rank["shortest"] += 1.0 / len(ch)
                        rank["longest"] += 1.0 / len(ch)
                for o in ch:
                    if o == ans:
                        n_key += 1
                        abs_key += bool(ABS.search(str(o)))
                    else:
                        n_dis += 1
                        abs_dis += bool(ABS.search(str(o)))

            if stage >= 4:
                if DEFINITIONAL.search(stem):
                    problems.append(("definitional stem", n["id"], stem[:50]))
                    defn += 1
                elif NAMING.search(stem):
                    defn += 1
                    naming_examples.append((n["id"], stem[:56]))
                else:
                    novel += 1

    print("=== {} ===".format(name))
    if rank["n"]:
        n = rank["n"]
        chance = rank["chance"] / n
        best = max(rank["shortest"], rank["longest"]) / n
        which = "shortest" if rank["shortest"] >= rank["longest"] else "longest"
        edge = best - chance
        verdict = ("EXPLOITABLE" if edge > MAX_LENGTH_EDGE
                   else "WARN (drifting)" if edge > WARN_LENGTH_EDGE else "ok")
        print("  pick-by-length: {} scores {:.1%} vs {:.1%} chance ({:+.1f}pp)  {}".format(
            which, best, chance, edge * 100, verdict))
        if WARN_LENGTH_EDGE < edge <= MAX_LENGTH_EDGE:
            # Visible margin to the hard limit, but not a problem: stays CLEAN.
            print("     margin to limit: {:.1f}pp of {:.1f}pp used".format(
                edge * 100, MAX_LENGTH_EDGE * 100))
        if edge > MAX_LENGTH_EDGE:
            problems.append(("length is a tell", name, "{:+.1f}pp".format(edge * 100)))
    if young_choice:
        b = binary / young_choice
        print("  stage 0-1 two-option: {}/{} = {:.0%}  {}".format(
            binary, young_choice, b, "ok" if b <= MAX_BINARY_SHARE else "TOO MANY"))
        if b > MAX_BINARY_SHARE:
            problems.append(("binary share", name, "{:.0%}".format(b)))
    if novel + defn:
        # A floor, not an estimate: these stems ask for a name in so many words.
        # The true recall share is higher and only a reader can say how much.
        share = defn / (novel + defn)
        print("  stage 4-5 stems that ask only for a name: {} of {} ({:.0%}, a lower bound)  {}".format(
            defn, novel + defn, share, "ok" if share <= MAX_NAMING_SHARE else "TOO MANY"))
        for ex in naming_examples[:3]:
            print("     {:24} {!r}".format(*ex))
        if share > MAX_NAMING_SHARE:
            problems.append(("names rather than applies", name, "{:.0%}".format(share)))
    if n_key and n_dis:
        gap = abs(abs_key / n_key - abs_dis / n_dis)
        print("  absolute language: keys {:.1%} vs distractors {:.1%}  {}".format(
            abs_key / n_key, abs_dis / n_dis, "ok" if gap < 0.08 else "SKEWED"))
        if gap >= 0.08:
            problems.append(("absolute-language skew", name, "{:.1%}".format(gap)))

    kinds = collections.Counter(p[0] for p in problems)
    if problems:
        print("  PROBLEMS: {}".format(dict(kinds)))
        for p in problems[:10]:
            print("     {:24} {:22} {}".format(*p))
    print("  {}".format("CLEAN" if not problems else "NEEDS WORK"))
    return problems


if __name__ == "__main__":
    targets = sys.argv[1:] or sorted(glob.glob("data/curriculum/*.json"))
    allp = []
    for t in targets:
        allp += audit(t)
    print("\n{} problem(s) across {} file(s)".format(len(allp), len(targets)))
    sys.exit(1 if allp else 0)
