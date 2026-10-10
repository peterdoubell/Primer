"""Constant-pressure phase energetics, independent geometry, and strict bindings."""
import copy
from pathlib import Path
import shutil
import subprocess

import pytest
from primer.curriculum import Curriculum, _validate_lesson_media

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('lesson,scenario', [
    ('phys.0.hot-cold', 'phys.0.hot-cold.melting-ice'),
    ('phys.2.matter', 'phys.2.matter.phase-change'),
])
def test_phase_binding_and_cross_lesson_rejection(lesson, scenario):
    node = copy.deepcopy(Curriculum().node(lesson))
    model = next(m for m in node['lesson_media'] if m.get('renderer') == 'physics-phase-lab')
    assert model['props'] == {'scenario': scenario}
    _validate_lesson_media(node)
    model['props']['extra'] = True
    with pytest.raises(ValueError, match='phase'):
        _validate_lesson_media(node)
    model['props'] = {'scenario': 'phys.2.matter.phase-change' if lesson == 'phys.0.hot-cold' else 'phys.0.hot-cold.melting-ice'}
    with pytest.raises(ValueError, match='phase'):
        _validate_lesson_media(node)


@pytest.mark.skipif(shutil.which('node') is None, reason='Node required')
def test_independent_phase_balances_and_mounted_coordinates():
    result = subprocess.run(['node', 'tools/check_physics_phase_lab.js'], cwd=ROOT, capture_output=True, text=True, timeout=40)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'independent phase balances' in result.stdout
    assert 'mounted enthalpy-coordinate/fraction/ledger states' in result.stdout


def test_phase_shell_loads_dependency_before_registry():
    shell = (ROOT / 'web/index.html').read_text()
    assert shell.index('/app/physics-phase-lab.js') < shell.index('/app/lesson-models.js')
    assert '/app/physics-phase-lab.css' in shell
