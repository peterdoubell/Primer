"""Actual thermo binding and independently integrated gas-cycle balances."""
import copy
from pathlib import Path
import shutil
import subprocess
import pytest
from primer.curriculum import Curriculum, _validate_lesson_media

ROOT = Path(__file__).resolve().parents[1]


def test_thermo_cycle_binding_rejects_cross_lesson_and_extra_props():
    node = copy.deepcopy(Curriculum().node('phys.3.thermo'))
    model = next(m for m in node['lesson_media'] if m.get('renderer') == 'physics-cycle-lab')
    assert model['props'] == {'scenario': 'phys.3.thermo.cycle-entropy'}
    _validate_lesson_media(node)
    model['props']['extra'] = True
    with pytest.raises(ValueError, match='cycle'):
        _validate_lesson_media(node)
    model['props'] = {'scenario': 'phys.2.heat.transport'}
    with pytest.raises(ValueError, match='cycle'):
        _validate_lesson_media(node)


@pytest.mark.skipif(shutil.which('node') is None, reason='Node required')
def test_independent_work_integrals_gas_reservoir_and_rendered_ledgers():
    result = subprocess.run(['node', 'tools/check_physics_cycle_lab.js'], cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'independent pressure-work integrals' in result.stdout
    assert 'mounted physical-coordinate states' in result.stdout


def test_cycle_shell_loads_dependency_before_registry():
    shell = (ROOT / 'web/index.html').read_text()
    assert shell.index('/app/physics-cycle-lab.js') < shell.index('/app/lesson-models.js')
    assert '/app/physics-cycle-lab.css' in shell
