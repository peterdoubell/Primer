"""No surface strategy may beat guessing on a generated item.

`tools/check_banks.py` has audited the authored banks in `data/curriculum/*.json`
since Round 5, and it is why those banks are position-, length- and
absolute-language balanced. It reads nothing else — and the other half of the
graded surface is minted at request time by the ~50 generators in
`primer/practice.py`, which top up quiz papers and supply the whole of a
practice drill. Nobody had ever measured them.

When they were finally measured, the most-drilled generators in the book turned
out to be trivially exploitable, and had been all along:

  * addition, subtraction, division and times-tables built their distractors
    from a delta pool that was four-sevenths positive and then dropped negative
    candidates, so the key piled up at the low end. "Always pick the second
    smallest" scored 49-56% against a 25% chance rate.
  * g_counting offered {n-2, n-1, n, n+1}: the key was permanently the second
    largest, and "pick the third smallest" scored 87%.
  * g_patterns offered {nxt-step, nxt, nxt+1, nxt+step}: for any step > 1 the
    key was permanently the second smallest — 90%.
  * g_primes drew a number and asked whether it happened to be prime. Seventeen
    primes below 60 against forty-two composites made "always answer no" worth
    72% and passed 48% of six-item papers outright.

None of it was visible to the audits the project already had, because those
measured the order options are DISPLAYED in — and `_mc` does shuffle that.
What was fixed was the key's rank once a reader sorts the numbers by size, and
sorting undoes a shuffle. A drill that can be passed by a reader who cannot
count is not an assessment, and mastery earned on one is not mastery.

This runs the same measurement as `tools/check_generators.py`, so the tool and
the suite cannot disagree about what fair means.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))

from primer import practice  # noqa: E402
import check_generators  # noqa: E402


@pytest.mark.parametrize("gen_key", practice.list_generators())
def test_no_surface_strategy_beats_guessing(gen_key):
    """For each generator: rank, key and length must all sit near chance.

    Seeded per generator, so a failure is reproducible rather than a coin toss
    somebody has to re-run to believe.
    """
    problems = check_generators.audit(gen_key, verbose=False)
    assert not problems, "\n".join(
        "%s: %s" % (kind, detail) for kind, _, detail in problems)


def test_a_counting_drill_never_offers_a_negative_number():
    """Preschool counting had minus one among its answers.

    The generator's own distractors were guarded (`max(1, n - 1)`), but when the
    option space was too cramped to fill four — n = 1 dedupes to two — `_mc`'s
    padding loop invented the rest and could go below zero. A four-year-old
    being asked how many apples they can see should not be offered −2.
    """
    practice.R.seed("counting-negatives")
    for _ in range(60):
        for q in practice.generate_set("counting", 12, level=0):
            for choice in q.get("choices") or []:
                assert not str(choice).startswith("-"), (
                    "counting offered %r among %s" % (choice, q.get("choices")))


def test_a_short_item_cannot_be_passed_by_parroting_its_own_question():
    """Answering with the question must score materially worse than answering it.

    Short answers are marked on keyword coverage at 0.6. Where the keywords are
    words the STEM already prints, pasting the question back scores them — 34 of
    447 authored items reached a pass that way, and because `/api/quiz/check`
    burns an item only when the answer is wrong, that pass also handed back the
    full key with the item unspent, ready to be scored a clean 1.0 next sitting.

    The rule is a GAP, not a ceiling on the stem score: some items cannot avoid
    their own nouns (a question about bounded functionals on a normed space has
    to say "norm"), and a bare threshold would flag those forever. What must not
    happen is that parroting scores as well as answering.
    """
    import glob
    import json as _json

    from primer import quiz

    offenders = []
    for path in sorted(glob.glob("data/curriculum/*.json")):
        for node in _json.load(open(path, encoding="utf-8"))["nodes"]:
            for item in node.get("quiz") or []:
                if item.get("kind") != "short":
                    continue
                keywords = item.get("keywords") or []
                if len(keywords) < 3:
                    continue          # a separate rule, enforced by check_banks
                stem = quiz.score_short_answer(item.get("prompt", ""), keywords)
                model = quiz.score_short_answer(item.get("answer", ""), keywords)
                if stem >= 0.6 and (model - stem) < 0.25:
                    offenders.append("%s: stem %.2f vs model %.2f"
                                     % (node["id"], stem, model))
    assert not offenders, (
        "%d short item(s) can be passed by pasting the question:\n  %s"
        % (len(offenders), "\n  ".join(offenders[:8])))
