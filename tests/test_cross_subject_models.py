"""Numerical, semantic, and curriculum boundaries for cross-subject models."""
import itertools
import shutil
import subprocess
from pathlib import Path

import pytest

from primer.curriculum import CONCEPT_MODEL_SCENARIOS, _validate_lesson_media
import json


ROOT = Path(__file__).resolve().parents[1]
CONCEPT_LESSONS = frozenset({
    "arts.1.beat", "lang.2.etymology", "lang.2.poetry", "lang.2.novels", "lang.2.research", "lang.2.speaking", "lang.2.grammar", "lang.2.paragraphs", "lang.0.phonics", "lang.1.handwriting", "lang.0.speaking", "lang.1.childrens-lit", "lang.1.writing-stories", "lang.1.dictionary", "lang.1.vocabulary", "lang.1.spelling", "lang.1.sentences", "lang.0.rhymes", "lang.0.stories", "earth.5.frontier", "earth.5.earth-systems", "earth.5.cosmology", "earth.5.astrobiology", "earth.4.planetary", "earth.4.climatology", "earth.4.oceanatmos", "earth.4.geophysics", "earth.4.astrophysics", "earth.3.astronomy", "earth.3.ecology-earth", "earth.3.climate-sci", "earth.3.space-exploration", "earth.2.geology", "earth.2.oceans", "earth.2.atmosphere", "earth.2.environment", "earth.2.planets", "earth.2.stars", "earth.0.weather", "earth.1.solar-system", "earth.0.land-water", "earth.1.water-cycle", "earth.1.rocks", "cs.4.security", "cs.4.systems", "cs.5.deep-learning", "cs.5.distributed", "cs.5.pl-theory", "cs.5.frontier", "cs.4.algorithms-adv", "cs.4.ml", "cs.4.theory", "cs.3.web", "cs.2.internet", "cs.4.os", "cs.4.databases-adv", "cs.3.versioncontrol", "cs.3.oop", "cs.3.hardware", "cs.2.bigo-intro", "cs.3.algorithms", "cs.1.blocks", "cs.2.programming", "cs.1.parts", "cs.3.databases", "cs.2.data-types", "cs.2.debugging", "cs.2.functions", "cs.0.sorting", "cs.0.patterns", "chem.3.bonding", "chem.4.inorganic", "chem.3.organic-intro", "chem.2.reactions-intro", "chem.3.reactions", "chem.2.periodic", "chem.2.acids", "chem.0.materials", "chem.1.materials-props", "chem.5.materials", "chem.1.changes", "chem.4.electrochem", "chem.5.biochem", "chem.5.frontier", "chem.4.analytical", "chem.5.compchem", "chem.2.mixtures", "chem.3.atomic-structure", "chem.3.gases", "chem.3.energy", "chem.4.physical", "chem.3.stoichiometry", "chem.0.mixing", "chem.0.water-states", "chem.1.matter", "bio.1.health", "bio.3.microbiology", "bio.5.immunology", "bio.5.frontier", "bio.4.neuro", "bio.4.physiology", "bio.4.ethology", "bio.4.genomics", "bio.5.comp-bio", "bio.5.systems-bio", "bio.3.ecology", "bio.3.botany", "bio.4.biochem", "bio.3.evolution", "bio.4.evo-bio", "bio.1.human-body", "bio.2.digestion", "bio.2.reproduction", "bio.0.animals", "bio.1.habitats", "bio.0.body", "bio.0.seasons", "bio.0.living", "bio.2.classification", "bio.2.ecosystems", "bio.2.microbes", "bio.0.plants", "bio.1.plants-parts", "bio.2.photosynthesis", "bio.1.food-chains", "math.5.diffgeo", "math.5.complex-analysis", "math.5.logic", "math.5.frontier", "math.5.abstract", "math.5.measure", "math.5.functional", "math.5.numerical", "math.4.diffeq", "math.4.discrete", "math.4.numtheory", "math.4.analysis", "math.4.prob-theory", "math.3.euclid", "math.4.complex", "math.4.diff-calc", "math.4.int-calc", "math.3.probability", "math.3.statistics", "math.3.precalc", "math.3.polynomials", "math.3.trig", "math.3.expo-logs", "math.3.sequences", "math.3.systems", "math.3.quadratics", "math.3.linear", "math.3.slope", "math.2.primes", "math.2.ratio", "math.2.exponents", "math.2.data", "math.2.prealgebra",
    "math.2.decimals", "math.2.order-ops",
    "math.2.percent", "math.2.coordinates",
    "math.1.measurement", "math.1.time", "math.1.fractions-intro",
    "math.1.multiplication", "math.1.division",
    "math.1.subtraction", "math.1.place-value",
    "math.0.compare", "math.0.patterns", "math.0.numbers20",
    "cs.1.binary",
    "hist.3.economics-intro", "lang.4.linguistics", "mind.5.logic-advanced",
})
CROSS_SUBJECT_LESSONS = CONCEPT_LESSONS | {
    "arts.2.color-theory", "cs.5.quantum",
}


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")
def test_cross_subject_model_invariants_and_interactions():
    result = subprocess.run(
        ["node", str(ROOT / "tools" / "check_cross_subject_models.js")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"Verified {len(CONCEPT_LESSONS) + 2} cross-subject models" in result.stdout
    assert {
        line.removeprefix("COVER ") for line in result.stdout.splitlines()
        if line.startswith("COVER ")
    } == CROSS_SUBJECT_LESSONS


def concept_node(node_id, props):
    return {
        "id": node_id,
        "lesson_media": [{
            "id": "cross-subject-concept",
            "kind": "model",
            "renderer": "concept-lab",
            "title": "Explore the concept",
            "instructions": "Change a parameter and compare the result.",
            "props": props,
        }],
    }


def test_concept_registry_matches_the_authored_lessons():
    assert CONCEPT_MODEL_SCENARIOS == CONCEPT_LESSONS


def test_real_curriculum_concept_entries_pass_the_production_schema():
    seen = set()
    for source in (ROOT / "data" / "curriculum").glob("[0-9]*.json"):
        for node in json.loads(source.read_text())["nodes"]:
            if node["id"] in CONCEPT_LESSONS:
                _validate_lesson_media(node)
                seen.add(node["id"])
    assert seen == CONCEPT_LESSONS


@pytest.mark.parametrize("node_id", sorted(CONCEPT_LESSONS))
def test_concept_scenario_is_valid_on_its_own_lesson(node_id):
    _validate_lesson_media(concept_node(node_id, {"scenario": node_id}))


@pytest.mark.parametrize("node_id,scenario", [
    pair for pair in itertools.product(sorted(CONCEPT_LESSONS), repeat=2)
    if pair[0] != pair[1]
])
def test_concept_scenario_cannot_be_attached_to_another_concept_lesson(node_id, scenario):
    with pytest.raises(ValueError, match="cross-lesson"):
        _validate_lesson_media(concept_node(node_id, {"scenario": scenario}))


@pytest.mark.parametrize("node_id", ["arts.2.color-theory", "cs.5.quantum", "math.2.geometry"])
def test_concept_renderer_cannot_be_used_on_a_spatial_lesson(node_id):
    with pytest.raises(ValueError):
        _validate_lesson_media(concept_node(node_id, {"scenario": node_id}))


@pytest.mark.parametrize("props", [
    {}, {"scenario": "unknown"}, {"scenario": "constructor"},
    {"scenario": "toString"}, {"scenario": "__proto__"},
    {"scenario": None}, {"scenario": True}, {"scenario": False},
    {"scenario": []}, {"scenario": {}}, {"scenario": 1},
    {"scenario": "hist.3.economics-intro", "url": "https://example.com/model.js"},
    {"scenario": "hist.3.economics-intro", "price": 25},
    {"scenario": "hist.3.economics-intro", "state": {"demandShift": 8}},
    {"scenario": "hist.3.economics-intro", "__proto__": {}},
    [], None, "hist.3.economics-intro",
])
def test_concept_model_rejects_unknown_and_malformed_props(props):
    with pytest.raises(ValueError):
        _validate_lesson_media(concept_node("hist.3.economics-intro", props))
