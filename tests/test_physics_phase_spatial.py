"""Independent enthalpy, temperature and phase-fraction coordinates in 3D."""
import copy
from pathlib import Path
import shutil
import subprocess

import pytest

from primer.curriculum import Curriculum, _validate_lesson_media

ROOT = Path(__file__).resolve().parents[1]


def test_phase_spatial_graph_is_bound_to_the_actual_matter_lesson():
    node = copy.deepcopy(Curriculum().node('phys.2.matter'))
    graph = next(model for model in node['lesson_media']
                 if model.get('renderer') == 'spatial-3d')
    assert graph['props']['scenario'] == 'module.phys.2.matter'
    assert graph['props']['family'] == 'phase-enthalpy-path'
    assert graph['props']['mode'] == 'model'
    _validate_lesson_media(node)

    retired = copy.deepcopy(node)
    old = next(model for model in retired['lesson_media']
               if model.get('renderer') == 'spatial-3d')
    old['props']['family'] = 'molecular-chamber'
    with pytest.raises(ValueError, match='module spatial'):
        _validate_lesson_media(retired)

    wrong_lesson = {'id': 'phys.0.hot-cold', 'title': 'Hot and Cold',
                    'lesson_media': [copy.deepcopy(graph)]}
    with pytest.raises(ValueError, match='cross-lesson'):
        _validate_lesson_media(wrong_lesson)


@pytest.mark.skipif(shutil.which('node') is None, reason='Node is required')
def test_phase_spatial_coordinates_against_the_independent_enthalpy_oracle():
    result = subprocess.run(
        ['node', 'tools/check_physics_phase_spatial.js'], cwd=ROOT,
        capture_output=True, text=True, timeout=40, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'phase spatial states' in result.stdout
    assert 'liquid-fraction coordinates and control dependence' in result.stdout
