"""Every module must offer usable, correctly bound 3D and no generated scenery."""

import copy
import json
from pathlib import Path

import pytest

from primer.curriculum import Curriculum, _validate_lesson_media
from primer.module_media import model_bindings


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def curriculum():
    return Curriculum()


def test_every_module_has_a_spatial_model_and_no_photorealistic_scene(curriculum):
    assert len(curriculum.nodes) == 558
    assert len(curriculum.domains) == 19
    for node in curriculum.nodes.values():
        media = node["lesson_media"]
        assert {item["kind"] for item in media} <= {"illustration", "model"}, node["id"]
        assert any(item.get("renderer") in {"spatial-3d", "radiology-anatomy"}
                   for item in media), node["id"]
        assert len({item["id"] for item in media}) == len(media)


def test_generated_scene_assets_and_manifest_are_gone():
    # AI-generated contextual scenes were removed: they matched neither the
    # plates nor the source figures and taught nothing about the lesson.
    assert not (ROOT / "data/module-photographs.json").exists()
    assert not (ROOT / "web/illustrations/photoreal").exists()


def test_authored_teaching_media_is_preserved(curriculum):
    for source in (ROOT / "data/curriculum").glob("*.json"):
        for node in json.loads(source.read_text())["nodes"]:
            actual = curriculum.nodes[node["id"]]["lesson_media"]
            for original in node["lesson_media"]:
                assert original in actual, (node["id"], original["id"])
    assert set(model_bindings()) == {n["id"] for n in curriculum.nodes.values()
                                     if not n.get("radiology_reference")}


@pytest.mark.parametrize("field,value", [
    ("scenario", "module.cs.5.quantum"), ("family", "unknown"),
    ("context", "Unreviewed geometry"), ("mode", "simulation"),
    ("lesson", "A different lesson"), ("url", "https://example.com/model.js"),
])
def test_spatial_companions_reject_tampered_or_cross_lesson_props(curriculum, field, value):
    node = copy.deepcopy(curriculum.nodes["math.0.counting"])
    model = next(m for m in node["lesson_media"] if m.get("props", {}).get("scenario", "").startswith("module."))
    model["props"][field] = value
    with pytest.raises(ValueError, match="cross-lesson"):
        _validate_lesson_media(node)


def test_photorealistic_scene_media_is_rejected(curriculum):
    node = copy.deepcopy(curriculum.nodes["math.0.counting"])
    plate = next(m for m in node["lesson_media"] if m["kind"] == "illustration")
    node["lesson_media"].append(dict(plate, id="math-photograph-context", kind="photograph",
                                     credit="AI-generated", source_type="generated"))
    with pytest.raises(ValueError, match="unknown kind"):
        _validate_lesson_media(node)


def test_radiology_model_cannot_switch_to_another_module(curriculum):
    node = copy.deepcopy(curriculum.nodes["rad.5.shoulder"])
    model = next(m for m in node["lesson_media"] if m.get("renderer") == "radiology-anatomy")
    model["props"]["node_id"] = "rad.5.knee"
    with pytest.raises(ValueError, match="cross-lesson"):
        _validate_lesson_media(node)
