"""Physical balances and actual coordinates, rather than qualitative heat motifs."""
import copy
from pathlib import Path
import shutil
import subprocess
import pytest
from primer.curriculum import Curriculum, _validate_lesson_media
ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('lesson,scenario',[('phys.0.hot-cold','phys.0.hot-cold.energy-balance'),('phys.2.heat','phys.2.heat.transport')])
def test_thermal_binding_and_cross_lesson_rejection(lesson,scenario):
 node=copy.deepcopy(Curriculum().node(lesson))
 model=next(m for m in node['lesson_media'] if m.get('renderer')=='physics-thermal-lab')
 assert model['props']=={'scenario':scenario}
 _validate_lesson_media(node)
 model['props']['extra']=True
 with pytest.raises(ValueError,match='thermal model'):_validate_lesson_media(node)
 model['props']={'scenario':'phys.4.fluids'}
 with pytest.raises(ValueError,match='thermal model'):_validate_lesson_media(node)

@pytest.mark.skipif(shutil.which('node') is None,reason='Node required')
def test_independent_thermal_balances_and_mounted_coordinates():
 result=subprocess.run(['node','tools/check_physics_thermal_lab.js'],cwd=ROOT,capture_output=True,text=True,timeout=40)
 assert result.returncode==0,result.stdout+result.stderr
 assert 'thermal balances' in result.stdout and 'dimensioned 3D slabs' in result.stdout

def test_thermal_shell_loads_dependency_before_registry_and_spatial_builder():
 shell=(ROOT/'web/index.html').read_text()
 assert shell.index('/app/physics-thermal-lab.js')<shell.index('/app/lesson-models.js')
 assert '/app/physics-thermal-lab.css' in shell
 model=next(m for m in Curriculum().node('phys.2.heat')['lesson_media'] if m.get('renderer')=='spatial-3d')
 assert model['props']['family']=='thermal-slab' and model['props']['mode']=='model'
