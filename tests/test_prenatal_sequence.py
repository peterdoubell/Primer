"""The prenatal sequence is a local supplement to the reproduction lesson."""

import copy
from pathlib import Path
import shutil
import subprocess

import pytest

from primer.curriculum import Curriculum, _validate_lesson_media


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def reproduction():
    return Curriculum().nodes["bio.2.reproduction"]


def test_sequence_supplements_existing_reproduction_media(reproduction):
    media = reproduction["lesson_media"]
    assert any(entry["id"] == "bio-2-reproduction-insight" for entry in media)
    assert any(entry["id"] == "bio-2-reproduction-sets" for entry in media)
    sequence = [entry for entry in media if entry.get("renderer") == "prenatal-sequence"]
    assert len(sequence) == 1
    assert sequence[0]["props"] == {}
    assert "first trimester" in sequence[0]["title"]
    _validate_lesson_media(reproduction)


@pytest.mark.parametrize("alteration", ["different_lesson", "external_manifest"])
def test_sequence_cannot_be_rebound_or_fetch_arbitrary_assets(reproduction, alteration):
    node = copy.deepcopy(reproduction)
    sequence = next(entry for entry in node["lesson_media"] if entry.get("renderer") == "prenatal-sequence")
    node["lesson_media"] = [sequence]
    if alteration == "different_lesson":
        node["id"] = "bio.2.cells"
    else:
        sequence["props"]["manifest"] = "https://example.org/sequence.json"
    with pytest.raises(ValueError, match="own reproduction lesson"):
        _validate_lesson_media(node)


def test_shell_loads_player_before_the_model_registry():
    html = (ROOT / "web/index.html").read_text()
    assert html.index('/app/prenatal-sequence.js') < html.index('/app/lesson-models.js')
    assert '/app/prenatal-sequence.css' in html


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")
def test_sequence_playback_loading_accessibility_and_cleanup():
    result = subprocess.run(
        ["node", "--test", str(ROOT / "tests/prenatal-sequence.test.cjs")],
        cwd=ROOT, capture_output=True, text=True, timeout=30, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
