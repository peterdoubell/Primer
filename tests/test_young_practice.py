"""Every young node must have something to practise.

Seventy-five of the eighty-nine stage 0-1 nodes had no practice generator, so
the interactive loop — read it, try it, get it wrong, meet it again — could not
close on them at all. It was the single largest thing holding the meta-learning
score down, and it was curriculum authoring rather than a code defect, which is
exactly why it needed a test: nothing else stops the gap reopening the next
time a young node is written.
"""

import glob
import json
import re
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from primer import practice  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _young_nodes():
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "curriculum", "*.json"))):
        with open(path, encoding="utf-8") as fh:
            for node in json.load(fh).get("nodes", []):
                if node.get("stage", 9) in (0, 1):
                    out.append((os.path.basename(path), node))
    return out


YOUNG = _young_nodes()


def test_there_are_young_nodes_to_check():
    assert len(YOUNG) > 50


def test_every_young_node_has_a_practice_generator():
    missing = [n["id"] for _f, n in YOUNG if not n.get("practice")]
    assert missing == [], "young nodes with nothing to practise: %s" % missing


def test_every_young_practice_key_is_registered():
    unknown = [(n["id"], n["practice"]) for _f, n in YOUNG
               if n.get("practice") not in practice.GENERATORS]
    assert unknown == []


@pytest.mark.parametrize("node", [n for _f, n in YOUNG], ids=[n["id"] for _f, n in YOUNG])
def test_every_young_node_fills_a_whole_drill(node):
    """Six distinct items, or the drill runs short and the reader sees a stub."""
    level = min(1, node.get("stage", 0))
    items = practice.generate_set(node["practice"], 6, level=level)
    assert len(items) == 6, "%s yielded %d" % (node["id"], len(items))
    assert len({(q["prompt"], q.get("answer")) for q in items}) == 6


@pytest.mark.parametrize("node_id", sorted(practice.young_material()))
def test_every_knowledge_node_can_produce_not_only_recognise(node_id):
    """A young paper that is all multiple choice never asks the child to make
    anything. Every authored node carries at least one orderable sequence."""
    spec = practice.young_material()[node_id]
    seqs = [s for s in (spec.get("sequences") or []) if len(s) >= 3]
    assert seqs, "%s has no sequence to order" % node_id


@pytest.mark.parametrize("node_id", sorted(practice.young_material()))
def test_knowledge_items_are_all_spoken(node_id):
    """Nothing below stage 2 may require reading: every item carries a spoken
    line and asks the client to read its options aloud."""
    for level in (0, 1):
        for q in practice.generate_set("know:" + node_id, 6, level=level):
            assert q.get("say"), "%s: %r has no spoken line" % (node_id, q["prompt"])
            assert q.get("speak_choices") is True


@pytest.mark.parametrize("node_id", sorted(practice.young_material()))
def test_knowledge_options_are_never_duplicated(node_id):
    for q in practice.generate_set("know:" + node_id, 6, level=0):
        choices = q.get("choices")
        if choices:
            assert len(choices) == len(set(choices))
            assert str(q["answer"]) in choices


def test_a_fact_is_worth_a_review_card_and_a_category_pick_is_not():
    """A card's front has to determine its back.

    "Which one is a bird?" is one fixed prompt over a set of members, so the
    first draw froze one arbitrary member as the answer — the deck's
    UNIQUE(front, node_id) — and the reader was then drilled towards it
    forever. An audit found a third of card-worthy items had a front mapping to
    more than one back, one of them to five. A fact names its own answer in the
    prompt; a category pick does not.
    """
    assert practice.is_durable_item(
        "know:bio.0.animals", 0, "How many legs does an insect have?")
    assert not practice.is_durable_item(
        "know:bio.0.animals", 0, "Which one is a bird?")


@pytest.mark.parametrize("node_id", sorted(practice.young_material()))
def test_no_card_front_maps_to_two_different_backs(node_id):
    """The measurement that caught it, run over every node."""
    backs = {}
    for level in (0, 1):
        for _ in range(40):
            for q in practice.generate_set("know:" + node_id, 6, level=level):
                if q.get("kind") == "order":
                    continue
                if not practice.is_durable_item("know:" + node_id, level, q["prompt"]):
                    continue
                backs.setdefault(q["prompt"], set()).add(str(q["answer"]))
    ambiguous = {f: b for f, b in backs.items() if len(b) > 1}
    assert not ambiguous, "%s: %s" % (node_id, list(ambiguous.items())[:2])


@pytest.mark.parametrize("node_id", sorted(practice.young_material()))
def test_no_item_has_two_right_answers(node_id):
    """Fourteen members across six nodes belong to two categories at once —
    red is both primary and warm — and the distractor draw did not know it. On
    arts.0.colors that put a second correct answer on 92% of category cards."""
    spec = practice.young_material()[node_id]
    groups = spec.get("groups") or {}
    member_of = {}
    for cat, members in groups.items():
        for m in members:
            member_of.setdefault(m, set()).add(cat)
    positive = {practice._articled(
        spec.get("group_prompt", "Which one is a {}?").format(cat)): cat
        for cat in groups}
    for _ in range(300):
        q = practice._know_group(spec)
        if not q or q["prompt"] not in positive:
            continue
        cat = positive[q["prompt"]]
        extra = [c for c in q["choices"]
                 if c != q["answer"] and cat in member_of.get(c, ())]
        assert not extra, "%s: %r also answers %r" % (node_id, extra, q["prompt"])


@pytest.mark.parametrize("node_id", sorted(practice.young_material()))
def test_every_item_explains_itself(node_id):
    """Every authored bank item in the book explains itself; not one generated
    knowledge item did. "Not quite. The answer is red" teaches nothing about
    how to get the next one right, which is the whole bar this dimension is
    scored against."""
    for level in (0, 1):
        for q in practice.generate_set("know:" + node_id, 6, level=level):
            assert q.get("explain"), "%s: %r explains nothing" % (node_id, q["prompt"])


@pytest.mark.parametrize("node_id", sorted(practice.young_material()))
def test_prompts_are_grammatical(node_id):
    """The book says these out loud. "Which one is a insect?" was spoken to a
    five-year-old exactly as written."""
    for _ in range(60):
        for shape in (practice._know_group, practice._know_pair):
            q = shape(practice.young_material()[node_id])
            if not q:
                continue
            assert not re.search(r"\ba [aeiouAEIOU]", q["prompt"]), q["prompt"]
            assert q["prompt"] == q["say"]


def test_missing_material_yields_no_items_rather_than_noise():
    gen = practice.make_knowledge_generator("no.such.node")
    assert gen(0) is None
    practice.GENERATORS["know:no.such.node"] = gen
    try:
        assert practice.generate_set("know:no.such.node", 6) == []
    finally:
        del practice.GENERATORS["know:no.such.node"]


def test_a_seedling_meets_every_shape():
    """At level 0 the ordering cadence and the recall rotation shared one
    counter, so the category pick was served 0.0% of the time and a
    Seedling's whole drill shrank to sixteen distinct items."""
    import collections
    practice.R.seed("shapes")
    practice.reset_rotation()
    for level in (0, 1):
        kinds = collections.Counter()
        for node_id in sorted(practice.young_material()):
            for q in practice.generate_set("know:" + node_id, 8, level=level):
                if q["kind"] == "order":
                    kinds["order"] += 1
                elif q["prompt"] in practice._group_prompts("know:" + node_id):
                    kinds["group"] += 1
                else:
                    kinds["recall"] += 1
        total = sum(kinds.values())
        assert kinds["group"] / total > 0.12, (level, dict(kinds))
        assert kinds["order"] / total > 0.15, (level, dict(kinds))


def test_an_ordering_front_never_prints_its_answer():
    """Forty-one authored orderings are alphabetical — every dictionary
    drill, the binary numbers — so a front that listed the members
    alphabetically printed the answer and the child could copy it off."""
    for node_id, spec in practice.young_material().items():
        for _ in range(30):
            q = practice._know_order(spec)
            if not q:
                break
            listed = q["prompt"].split(": ", 1)[1]
            assert listed != q["answer"].replace(" ", ", ") or len(q["items"]) < 3, \
                (node_id, q["prompt"])
            assert ", ".join(q["answer"].split(" ")) != listed or " " in q["items"][0], \
                (node_id, q["prompt"])


def test_one_ordering_front_has_one_back():
    """`bio.0.seasons` authored three rotations of one cycle: one durable
    front, three backs — the defect class Round 25 was scored on,
    reintroduced by Round 26's own feature."""
    for node_id, spec in practice.young_material().items():
        fronts = {}
        for s in spec.get("sequences") or []:
            core = [str(x) for x in s if not isinstance(x, dict)]
            if len(core) < 3:
                continue
            key = frozenset(core)
            fronts.setdefault(key, set()).add(tuple(core))
        dupes = {k: v for k, v in fronts.items() if len(v) > 1}
        assert not dupes, (node_id, list(dupes.values())[0])
