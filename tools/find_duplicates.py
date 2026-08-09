"""Find items within a node that ask the same question twice.

The last audit's defects were no longer strawmen — they were items too easy for
their stage, and each was also the *weaker duplicate* of a sibling in its own
node ("bond order of O2" with the definition and both electron counts supplied,
sitting next to "bond order of N2" which asks the same thing properly).

A bank of ten that contains three near-duplicates is a bank of eight, and the
weaker twin is what a reader is likely to meet.
"""

import collections
import glob
import json
import os
import re
import sys

STOP = set("""the a an and or but if then than that this these those with without for from into
onto of to in on at by as is are was were be been being it its their his her our your my we you
they have has had do does did not no so such very more most much many can could would should may
might will shall must one two both each other same when where which who what how why while during
after before over under about against between among through what is are does do""".split())


def shingles(text):
    words = [w.lower() for w in re.findall(r"[^\W\d_]{3,}", str(text)) if w.lower() not in STOP]
    return set(words), {tuple(words[i:i + 2]) for i in range(len(words) - 1)}


def jaccard(a, b):
    return len(a & b) / len(a | b) if (a | b) else 0.0


def _text(q):
    """Prompt plus what it is asking between — two items can share every word of
    their stem and still be different questions when the content sits in the
    options ("How many sides? 🔺" against "How many sides? 🟦")."""
    return " ".join([str(q.get("prompt", "")), str(q.get("answer", ""))]
                    + sorted(str(o) for o in (q.get("choices") or [])))


def scan(path, threshold=0.55):
    d = json.load(open(path))
    hits = []
    for n in d["nodes"]:
        if n.get("stage", 0) < 2:
            continue          # young prompts carry their content in emoji
        qs = n.get("quiz") or []
        for i in range(len(qs)):
            wi, bi = shingles(_text(qs[i]))
            if len(wi) < 6:
                continue      # too terse to judge by overlap
            for j in range(i + 1, len(qs)):
                wj, bj = shingles(_text(qs[j]))
                if len(wj) < 6:
                    continue
                word_sim = jaccard(wi, wj)
                bigram_sim = jaccard(bi, bj)
                same_answer = (str(qs[i].get("answer", "")).strip().lower()
                               == str(qs[j].get("answer", "")).strip().lower())
                score = max(word_sim, bigram_sim) + (0.15 if same_answer else 0)
                if score >= threshold:
                    hits.append({
                        "node": n["id"], "stage": n.get("stage", 0), "i": i, "j": j,
                        "sim": round(score, 2), "same_answer": same_answer,
                        "a": qs[i].get("prompt", "")[:74],
                        "b": qs[j].get("prompt", "")[:74],
                    })
    return hits


if __name__ == "__main__":
    argv = [a for a in sys.argv[1:] if not a.startswith("-")]
    targets = argv or sorted(glob.glob("data/curriculum/*.json"))
    total = 0
    for t in targets:
        hits = scan(t)
        total += len(hits)
        print("=== {} — {} near-duplicate pair(s) ===".format(os.path.basename(t), len(hits)))
        for h in hits[:12]:
            print("  [{} sim{}] {} #{} / #{}".format(
                "same answer" if h["same_answer"] else "  ", h["sim"], h["node"], h["i"], h["j"]))
            print("      a {!r}".format(h["a"]))
            print("      b {!r}".format(h["b"]))
    print("\n{} pair(s) across {} file(s)".format(total, len(targets)))
