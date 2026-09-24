"""Every module must offer local photography and usable, correctly bound 3D."""

import copy
import json
from pathlib import Path

import pytest

from primer.curriculum import Curriculum, _validate_lesson_media, _webp_dimensions
from primer.module_media import model_bindings, photographs


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def curriculum():
    return Curriculum()


def test_every_module_has_photographic_context_and_a_spatial_model(curriculum):
    assert len(curriculum.nodes) == 558
    assert len(curriculum.domains) == 19
    used_photographs = set()
    for node in curriculum.nodes.values():
        media = node["lesson_media"]
        photos = [item for item in media if item["kind"] == "photograph"]
        assert len(photos) == 1, node["id"]
        assert any(item.get("renderer") in {"spatial-3d", "radiology-anatomy"}
                   for item in media), node["id"]
        assert len({item["id"] for item in media}) == len(media)
        assert photos[0]["source_type"] == "generated"
        assert "AI-generated" in photos[0]["credit"]
        used_photographs.add(photos[0]["src"])
    assert len(used_photographs) == 30
    foundation = curriculum.nodes["rad.2.modalities"]
    photo = next(item for item in foundation["lesson_media"] if item["kind"] == "photograph")
    assert photo["id"] == "radiology-photograph-context"


def test_local_photographs_have_true_responsive_dimensions_and_provenance():
    assert set(photographs()) == {"math", "language", "physics", "biology", "chemistry",
                                  "cs", "history", "earth", "arts", "mind", "radiology",
                                  "engineering", "health", "environment", "design",
                                  "business", "civics", "education", "media"}
    sources = set()
    for domain, entries in photographs().items():
        assert len(entries) == (1 if domain in {"engineering", "health", "environment", "design",
                                               "business", "civics", "education", "media"} else 2), domain
        for photo in entries:
            assert photo["src"] not in sources, domain
            sources.add(photo["src"])
            assert photo["alt"] != photo["caption"]
            assert len(photo["alt"].split()) >= 8
            for candidate in photo["srcset"].split(","):
                url, width = candidate.split()
                assert url.startswith("/app/illustrations/photoreal/")
                image = ROOT / "web" / url.removeprefix("/app/")
                w, h = _webp_dimensions(str(image))
                assert w == int(width[:-1])
                assert w * photo["height"] == h * photo["width"]
                assert image.stat().st_size < 600_000
    assert len(sources) == 30


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


@pytest.mark.parametrize("field,value", [
    ("src", "https://example.com/photo.webp"),
    ("src", "/app/illustrations/../../secret.webp"),
    ("source_type", "patient-scan"), ("credit", ""),
    ("srcset", "/app/illustrations/missing.webp 800w"),
])
def test_photographs_reject_unknown_sources_and_false_provenance(curriculum, field, value):
    node = copy.deepcopy(curriculum.nodes["math.0.counting"])
    photo = next(m for m in node["lesson_media"] if m["kind"] == "photograph")
    photo[field] = value
    with pytest.raises(ValueError):
        _validate_lesson_media(node)


def test_radiology_model_cannot_switch_to_another_module(curriculum):
    node = copy.deepcopy(curriculum.nodes["rad.5.shoulder"])
    model = next(m for m in node["lesson_media"] if m.get("renderer") == "radiology-anatomy")
    model["props"]["node_id"] = "rad.5.knee"
    with pytest.raises(ValueError, match="cross-lesson"):
        _validate_lesson_media(node)
