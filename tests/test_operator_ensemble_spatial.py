"""Actual sparse-operator and statistical-ensemble graphs, with independent oracles."""
import copy
from pathlib import Path
import shutil
import subprocess

import pytest
from primer.curriculum import Curriculum, _validate_lesson_media

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('lesson,family', [('math.5.functional', 'operator-coordinate-graph'),
                                         ('phys.4.statmech', 'ensemble-state-graph')])
def test_exact_authored_graph_binding_and_cross_lesson_rejection(lesson, family):
    node = copy.deepcopy(Curriculum().node(lesson))
    graph = next(m for m in node['lesson_media'] if m.get('renderer') == 'spatial-3d')
    assert graph['props']['family'] == family
    assert graph['props']['mode'] == 'model'
    assert graph['props']['scenario'] == 'module.' + lesson
    _validate_lesson_media(node)
    authored = copy.deepcopy(graph)
    graph['props']['family'] = 'particles'
    with pytest.raises(ValueError, match='module spatial'):
        _validate_lesson_media(node)
    other = 'phys.4.statmech' if lesson == 'math.5.functional' else 'math.5.functional'
    wrong_lesson = {'id': other, 'title': 'Wrong lesson', 'lesson_media': [authored]}
    with pytest.raises(ValueError, match='cross-lesson'):
        _validate_lesson_media(wrong_lesson)


@pytest.mark.skipif(shutil.which('node') is None, reason='Node required')
def test_independent_rational_operator_and_counting_coordinates():
    result = subprocess.run(['node', 'tools/check_operator_ensemble_spatial.js'],
                            cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'independent rational operator spatial states' in result.stdout
    assert 'independent Pascal/Boltzmann spatial states' in result.stdout
