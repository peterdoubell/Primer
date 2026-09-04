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


def test_a_knowledge_drill_is_worth_a_review_card():
    """Recall of a fact belongs on a card; the ordering items do not, and are
    excluded by kind the same way every other generator's are."""
    assert practice.is_durable_item("know:bio.0.animals", 0, "Which one is a bird?")


def test_missing_material_yields_no_items_rather_than_noise():
    gen = practice.make_knowledge_generator("no.such.node")
    assert gen(0) is None
    practice.GENERATORS["know:no.such.node"] = gen
    try:
        assert practice.generate_set("know:no.such.node", 6) == []
    finally:
        del practice.GENERATORS["know:no.such.node"]
