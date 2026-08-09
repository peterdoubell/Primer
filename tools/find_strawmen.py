"""Surface likely strawman distractors — options no learner would ever pick.

An audit found this class dominant (7 of 8 defects) and invisible to the other
checkers: every option is grammatical, plausible-looking prose, and only one is
a real answer. There is no exact test for "nobody would choose this", so this
ranks candidates by three signals and leaves the judgement to a reader:

  short      the distractor is far terser than the key — the classic shape of
             a real answer padded with qualifiers against throwaway wrong ones
  absolute   it leans on all/never/only/cannot, which flags itself as wrong
  detached   it shares no content word with the stem or with any other option,
             so it is not about the same thing as the question

Usage:  .venv/bin/python tools/find_strawmen.py [file ...] [--top N]
"""

import glob
import json
import os
import re
import sys

ABS = re.compile(r"\b(all|every|never|only|cannot|always|none|impossible|no one)\b", re.I)
STOP = set("""the a an and or but if then than that this these those with without for from
into onto of to in on at by as is are was were be been being it its their his her our your
my we you they have has had do does did not no so such very more most much many can could
would should may might will shall must one two both each other same when where which who
what how why while during after before over under about against between among through""".split())


def words(text):
    return {w.lower() for w in re.findall(r"[^\W\d_]{4,}", str(text))} - STOP


def score(stem, key, other, siblings):
    reasons = []
    if len(key) >= 18 and len(other) * 1.7 < len(key):
        reasons.append("short")
    if ABS.search(other) and not ABS.search(key):
        reasons.append("absolute")
    ow = words(other)
    if ow and not (ow & (words(stem) | words(key) | siblings)):
        reasons.append("detached")
    return reasons


def scan(path):
    d = json.load(open(path))
    out = []
    for n in d["nodes"]:
        if n.get("stage", 0) < 2:
            continue
        for q in n.get("quiz") or []:
            ch, key, stem = q.get("choices") or [], str(q.get("answer", "")), q.get("prompt", "")
            if len(ch) < 3 or key not in ch:
                continue
            for other in ch:
                if other == key:
                    continue
                siblings = set()
                for s in ch:
                    if s not in (key, other):
                        siblings |= words(s)
                r = score(stem, key, str(other), siblings)
                if len(r) >= 2:
                    out.append({"node": n["id"], "stage": n["stage"], "stem": stem[:66],
                                "key": key[:56], "suspect": str(other)[:56], "why": "+".join(r)})
    return out


if __name__ == "__main__":
    argv = sys.argv[1:]
    top = 25
    if "--top" in argv:
        i = argv.index("--top")
        top = int(argv[i + 1])
        del argv[i:i + 2]          # ...and don't then treat "10" as a filename
    args = [a for a in argv if not a.startswith("--")]
    targets = args or sorted(glob.glob("data/curriculum/*.json"))
    grand = 0
    for t in targets:
        hits = scan(t)
        grand += len(hits)
        print("=== {} — {} candidate(s) ===".format(os.path.basename(t), len(hits)))
        for h in hits[:top]:
            print("  [{}] {:22} {}".format(h["why"], h["node"], h["stem"]))
            print("        key     {!r}".format(h["key"]))
            print("        suspect {!r}".format(h["suspect"]))
    print("\n{} candidate(s) across {} file(s)".format(grand, len(targets)))
