"""The new ODE activity remains bound to its own lesson and current assets."""
import copy
import hashlib
from pathlib import Path

import pytest

from primer.curriculum import Curriculum, _validate_lesson_media

ROOT = Path(__file__).resolve().parents[1]


def test_second_order_activity_supplements_first_order_activity():
    node = Curriculum().nodes["math.4.diffeq"]
    assert any(m.get("renderer") == "concept-lab" for m in node["lesson_media"])
    models = [m for m in node["lesson_media"] if m.get("renderer") == "math-ode-lab"]
    assert len(models) == 1
    assert models[0]["props"] == {"scenario": "math.4.diffeq.second-order"}
    _validate_lesson_media(node)


@pytest.mark.parametrize("alteration", ["lesson", "scenario", "extra-prop"])
def test_ode_activity_rejects_cross_lesson_or_unexpected_parameters(alteration):
    node = copy.deepcopy(Curriculum().nodes["math.4.diffeq"])
    model = next(m for m in node["lesson_media"] if m.get("renderer") == "math-ode-lab")
    node["lesson_media"] = [model]
    if alteration == "lesson":
        node["id"] = "math.4.int-calc"
    elif alteration == "scenario":
        model["props"]["scenario"] = "math.4.diffeq"
    else:
        model["props"]["url"] = "https://example.org/model.js"
    with pytest.raises(ValueError, match="cross-lesson"):
        _validate_lesson_media(node)


def test_ode_loader_order_and_content_hashes():
    from primer.server import app_shell
    html = app_shell().body.decode()
    assert html.index("/app/math-ode-lab.js") < html.index("/app/lesson-models.js")
    for name in ("math-ode-lab.js", "math-ode-lab.css"):
        digest = hashlib.sha256((ROOT / "web" / name).read_bytes()).hexdigest()[:10]
        assert "/app/" + name + "?v=" + digest in html
