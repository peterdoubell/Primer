"""Audit the procedural generators the way check_banks.py audits the authored banks.

`tools/check_banks.py` reads `data/curriculum/*.json` and nothing else. That is
half the graded surface: the other half is minted at request time by the ~50
generators in `primer/practice.py`, which top up quiz papers and supply the
whole of a practice drill. Nobody had ever measured them, and three exploitable
defects had been sitting in them the entire time:

  * `g_counting` offered {n-2, n-1, n, n+1}, so the key was permanently the
    second largest of four. "Always pick the third smallest" scored 87% against
    a 25% chance rate and cleared the 0.8 mastery gate.
  * `g_patterns` offered {nxt-step, nxt, nxt+1, nxt+step}: for any step > 1 the
    key was permanently the second smallest. That strategy scored 90%.
  * `g_primes` drew a number and asked whether it happened to be prime. There
    are 17 primes below 60 and 42 composites, so "always answer no" scored 72%
    against 50% and passed 48% of six-item papers outright.

None of it was visible to a position audit, because the options ARE shuffled —
what is fixed is the key's rank once the reader sorts the numbers by size, and
shuffling does not disturb a sort. This tool measures the thing that was
actually exploitable.

    python3 tools/check_generators.py            # every generator
    python3 tools/check_generators.py counting patterns

The same checks run as a test (tests/test_generator_fairness.py) so a
regression fails the suite rather than waiting for someone to run this.
"""

import collections
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from primer import practice  # noqa: E402

SAMPLES = 600           # per generator, per level
LEVELS = (0, 2, 4)
# How far the best surface strategy may beat blind guessing before it counts as
# a way through. Some slack is unavoidable: near a floor, a key of 1 has only
# one distinct non-negative number below it, so counting to ten genuinely
# cannot spread its key evenly over four ranks.
RANK_TOLERANCE = 0.09
KEY_TOLERANCE = 0.09
MIN_FOR_VERDICT = 40    # below this many samples the percentages are noise


def profile(gen_key, samples=SAMPLES, seed=None):
    """Draw a lot of items and record what a surface strategy could exploit.

    Seeded, and deliberately so. An unseeded audit re-samples on every run, so a
    generator sitting near the tolerance drifts in and out of the problem list
    and "0 problems" can be luck — which is the same trap check_banks.py avoids
    by seeding its hand-audit draw. One seed per generator keeps each one's
    verdict stable while still giving them different streams.
    """
    practice.R.seed("%s/%s" % (gen_key, seed if seed is not None else "primer-audit"))
    # ...and put the knowledge drills' shape rotation back to the start, or a
    # generator's verdict depends on how many items the process drew before it.
    if hasattr(practice, "reset_rotation"):
        practice.reset_rotation()
    ranks = collections.Counter()
    len_ranks = collections.Counter()
    n_len_ranked = 0
    keys = collections.Counter()
    lengths = collections.Counter()
    n_ranked = n_keyed = n_len = 0
    negatives = []
    drawn = 0
    for level in LEVELS:
        while drawn < samples * (LEVELS.index(level) + 1) / len(LEVELS) * len(LEVELS):
            batch = practice.generate_set(gen_key, 12, level=level)
            if not batch:
                return None
            for q in batch:
                drawn += 1
                choices = [str(c) for c in (q.get("choices") or [])]
                answer = str(q.get("answer", ""))
                if not choices:
                    continue
                keys[answer] += 1
                n_keyed += 1
                # Length as a tell — scored the way check_banks.py scores it, so
                # the two auditors agree about what counts as a signal. What
                # matters is whether picking by length beats guessing, which
                # means the baseline is 1/len(choices), not a fixed quarter: a
                # two-option item where the key is the shorter half the time is
                # exactly chance. A trivial spread carries no readable signal
                # either ("9" beside "10" is not a tell a five-year-old reads),
                # so those items are counted as guesses, as check_banks does.
                lens = sorted(len(c) for c in choices)
                flat = lens[-1] - lens[0] <= max(6, 0.25 * lens[-1])
                n_len += 1
                lengths["chance"] += 1.0 / len(choices)
                if flat:
                    lengths["longest"] += 1.0 / len(choices)
                    lengths["shortest"] += 1.0 / len(choices)
                else:
                    lengths["longest"] += int(answer == max(choices, key=len))
                    lengths["shortest"] += int(answer == min(choices, key=len))
                # The same rank test, but by LENGTH — which is the only axis a
                # text-answer generator has. The numeric test below skips every
                # item whose options are words, and that is most of the
                # knowledge drills: the tool reported them clean while
                # "always take the third shortest" beat chance by 35 points on
                # one of them. Ties are shared rather than broken arbitrarily,
                # so a set of equal-length options reads as no signal at all.
                # Only where the options are WORDS. When they are numbers the
                # numeric rank check below is the right instrument and this one
                # measures the same thing badly — for numerals length is mostly
                # magnitude, so a generator whose key is honestly spread over
                # the numeric ranks fails a length test that is really the
                # numeric test with ties broken by digit count.
                try:
                    for c in choices:
                        float(c)
                    numeric = True
                except (TypeError, ValueError):
                    numeric = False
                lens_only = [len(c) for c in choices]
                if not numeric and len(set(lens_only)) > 1:
                    by_len = sorted(choices, key=lambda c: (len(c), c))
                    n_len_ranked += 1
                    same = [c for c in choices if len(c) == len(answer)]
                    if len(same) > 1:
                        # A shared length is not a readable position. Spread the
                        # item evenly over the ranks its ties occupy.
                        for c in same:
                            len_ranks[by_len.index(c) + 1] += 1.0 / len(same)
                    else:
                        len_ranks[by_len.index(answer) + 1] += 1
                try:
                    nums = sorted(float(c) for c in choices)
                    key_val = float(answer)
                except (TypeError, ValueError):
                    continue
                if any(c.startswith("-") for c in choices) and key_val >= 0:
                    negatives.append((q.get("prompt", "")[:48], choices))
                try:
                    ranks[nums.index(key_val) + 1] += 1
                    n_ranked += 1
                except ValueError:
                    pass
            if drawn >= samples:
                break
        if drawn >= samples:
            break
    return {"ranks": ranks, "keys": keys, "lengths": lengths, "negatives": negatives,
            "len_ranks": len_ranks, "n_len_ranked": n_len_ranked,
            "n_ranked": n_ranked, "n_keyed": n_keyed, "n_len": n_len, "drawn": drawn}


def audit(gen_key, verbose=True):
    """Return a list of problems for one generator (empty means clean)."""
    p = profile(gen_key)
    problems = []
    if p is None:
        return [("generator produced nothing", gen_key, "")]

    if p["n_ranked"] >= MIN_FOR_VERDICT:
        n = p["n_ranked"]
        share = {r: p["ranks"][r] / n for r in sorted(p["ranks"])}
        best_rank, best = max(share.items(), key=lambda kv: kv[1])
        chance = 1.0 / max(1, len(share))
        edge = best - chance
        if verbose:
            print("  key rank among sorted options: %s  best=rank %d at %.0f%% vs %.0f%% chance (%+.0fpp)  %s"
                  % ({r: "%.0f%%" % (v * 100) for r, v in share.items()},
                     best_rank, best * 100, chance * 100, edge * 100,
                     "ok" if edge <= RANK_TOLERANCE else "EXPLOITABLE"))
        if edge > RANK_TOLERANCE:
            problems.append(("key sits at a fixed rank", gen_key,
                             "rank %d at %.0f%% (%+.0fpp)" % (best_rank, best * 100, edge * 100)))

    if p["n_keyed"] >= MIN_FOR_VERDICT and len(p["keys"]) <= 8:
        n = p["n_keyed"]
        top, count = p["keys"].most_common(1)[0]
        share = count / n
        chance = 1.0 / len(p["keys"])
        edge = share - chance
        if verbose:
            print("  most common key: %-12r %.0f%% of %d vs %.0f%% chance (%+.0fpp)  %s"
                  % (top[:12], share * 100, n, chance * 100, edge * 100,
                     "ok" if edge <= KEY_TOLERANCE else "PREDICTABLE"))
        if edge > KEY_TOLERANCE:
            problems.append(("one key dominates", gen_key,
                             "%r %.0f%% (%+.0fpp)" % (top[:12], share * 100, edge * 100)))

    if p["n_len_ranked"] >= MIN_FOR_VERDICT:
        n = p["n_len_ranked"]
        share = {r: p["len_ranks"][r] / n for r in sorted(p["len_ranks"])}
        best_rank, best = max(share.items(), key=lambda kv: kv[1])
        chance = 1.0 / max(1, len(share))
        edge = best - chance
        if verbose:
            print("  key rank by length:            %s  best=rank %d at %.0f%% vs %.0f%% chance (%+.0fpp)  %s"
                  % ({r: "%.0f%%" % (v * 100) for r, v in share.items()},
                     best_rank, best * 100, chance * 100, edge * 100,
                     "ok" if edge <= RANK_TOLERANCE else "EXPLOITABLE"))
        if edge > RANK_TOLERANCE:
            problems.append(("key sits at a fixed rank by length", gen_key,
                             "rank %d at %.0f%% (%+.0fpp)" % (best_rank, best * 100, edge * 100)))

    if p["n_len"] >= MIN_FOR_VERDICT:
        chance = p["lengths"]["chance"] / p["n_len"]
        best = max(p["lengths"]["longest"], p["lengths"]["shortest"]) / p["n_len"]
        which = ("shortest" if p["lengths"]["shortest"] >= p["lengths"]["longest"]
                 else "longest")
        edge = best - chance
        if verbose:
            print("  pick-by-length: %s scores %.0f%% vs %.0f%% chance (%+.0fpp)  %s"
                  % (which, best * 100, chance * 100, edge * 100,
                     "ok" if edge <= RANK_TOLERANCE else "EXPLOITABLE"))
        if edge > RANK_TOLERANCE:
            problems.append(("length is a tell", gen_key,
                             "%s scores %.0f%% (%+.0fpp)" % (which, best * 100, edge * 100)))

    if p["negatives"]:
        problems.append(("negative option beside a non-negative key", gen_key,
                         "%d of %d, e.g. %s" % (len(p["negatives"]), p["drawn"],
                                                p["negatives"][0][1])))
    return problems


if __name__ == "__main__":
    targets = sys.argv[1:] or practice.list_generators()
    allp = []
    for key in targets:
        print("=== %s ===" % key)
        problems = audit(key)
        if problems:
            for kind, where, detail in problems:
                print("     %-42s %s" % (kind, detail))
        print("  %s" % ("CLEAN" if not problems else "NEEDS WORK"))
        allp += problems
    print("\n%d problem(s) across %d generator(s)" % (len(allp), len(targets)))
    sys.exit(1 if allp else 0)
