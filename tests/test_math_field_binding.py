"""Preserve the tangent plane while binding the integral/flux activity locally."""
import copy
import hashlib
from pathlib import Path

import pytest

from primer.curriculum import Curriculum, _validate_lesson_media

ROOT = Path(__file__).resolve().parents[1]


def test_integral_flux_activity_supplements_tangent_plane():
    node = Curriculum().nodes["math.4.multivar"]
    assert any(m.get("renderer") == "spatial-3d" and m.get("props", {}).get("scenario") == node["id"]
               for m in node["lesson_media"])
    models = [m for m in node["lesson_media"] if m.get("renderer") == "math-field-lab"]
    assert len(models) == 1
    assert models[0]["props"] == {"scenario": "math.4.multivar.integral-flux"}
    _validate_lesson_media(node)


@pytest.mark.parametrize("alteration", ["lesson", "scenario", "extra-prop"])
def test_integral_flux_rejects_cross_lesson_or_unexpected_props(alteration):
    node = copy.deepcopy(Curriculum().nodes["math.4.multivar"])
    model = next(m for m in node["lesson_media"] if m.get("renderer") == "math-field-lab")
    node["lesson_media"] = [model]
    if alteration == "lesson":
        node["id"] = "math.4.diffeq"
    elif alteration == "scenario":
        model["props"]["scenario"] = "math.4.multivar"
    else:
        model["props"]["url"] = "https://example.org/field.js"
    with pytest.raises(ValueError, match="cross-lesson"):
        _validate_lesson_media(node)


def test_field_dependencies_and_current_asset_tags():
    from primer.server import app_shell
    html = app_shell().body.decode()
    assert html.index("/app/spatial-models.js") < html.index("/app/math-field-lab.js") < html.index("/app/lesson-models.js")
    for name in ("math-field-lab.js", "math-field-lab.css"):
        digest = hashlib.sha256((ROOT / "web" / name).read_bytes()).hexdigest()[:10]
        assert "/app/" + name + "?v=" + digest in html
