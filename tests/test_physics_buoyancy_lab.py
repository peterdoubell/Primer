"""Hydrostatic geometry must preserve displaced volume and actual force units."""
import copy
from pathlib import Path
import shutil
import subprocess

import pytest
from primer.curriculum import Curriculum, _validate_lesson_media

ROOT = Path(__file__).resolve().parents[1]

def test_buoyancy_binding_replaces_the_full_immersion_ratio_and_rejects_other_lessons():
    curr = Curriculum(); node = copy.deepcopy(curr.node('phys.0.float-sink'))
    model = next(m for m in node['lesson_media'] if m['kind'] == 'model')
    assert model['renderer'] == 'physics-buoyancy-lab'
    assert model['props'] == {'scenario': 'phys.0.float-sink.hydrostatics'}
    _validate_lesson_media(node)
    spatial = next(m for m in node['lesson_media'] if m.get('renderer') == 'spatial-3d')
    assert spatial['props']['family'] == 'buoyant-prism'
    retired = copy.deepcopy(node)
    old = next(m for m in retired['lesson_media'] if m.get('renderer') == 'physics-buoyancy-lab')
    old['renderer'] = 'physics-concept-lab'; old['props'] = {'scenario': 'phys.0.float-sink'}
    with pytest.raises(ValueError, match='physics concept'): _validate_lesson_media(retired)
    for field, value in [('id', 'phys.2.matter'), ('id', 'math.0.compare')]:
        bad = copy.deepcopy(node); bad[field] = value
        with pytest.raises(ValueError, match='buoyancy'): _validate_lesson_media(bad)
    model['props']['extra'] = True
    with pytest.raises(ValueError, match='buoyancy'): _validate_lesson_media(node)
    shell = (ROOT / 'web/index.html').read_text()
    assert shell.index('/app/physics-buoyancy-lab.js') < shell.index('/app/lesson-models.js')
    assert '/app/physics-buoyancy-lab.css' in shell

@pytest.mark.skipif(shutil.which('node') is None, reason='Node is required')
def test_hydrostatic_oracles_and_actual_mounted_geometry():
    result = subprocess.run(['node', 'tools/check_physics_buoyancy_lab.js'], cwd=ROOT,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'hydrostatic states' in result.stdout and 'mounted geometries' in result.stdout
