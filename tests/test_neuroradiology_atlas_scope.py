import json
from pathlib import Path
import pytest
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve

ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('identifier,index,terms', [
 ('ra.brain-anatomy',1,['deep grey','internal capsule','corpus callosum']),
 ('ra.mri-ms',1,['spinal cord','optic nerves']),
 ('ra.mri-ms',3,['Central veins','rims']),
 ('ra.venous-sinus-thrombosis',0,['dural venous sinuses']),
 ('ra.venous-sinus-thrombosis',1,['Deep and cortical veins']),
 ('ra.intracranial-hypotension',3,['pituitary']),
 ('ra.intracranial-hypotension',4,['spinal anatomy']),
])
def test_unavailable_structures_do_not_highlight_unrelated_meshes(identifier,index,terms):
 ref=detail(Curriculum(),resolve(identifier))['radiology_reference']
 step=ref['walkthrough']['steps'][index]
 assert step['parts']==[]
 assert all(t in step['anatomy_note'] for t in terms)
 assert step['sections'] and step['findings'] and step['look']


def test_ventricle_reference_remains_available_for_the_actual_ventricular_step():
 step=detail(Curriculum(),resolve('ra.brain-anatomy'))['radiology_reference']['walkthrough']['steps'][3]
 manifest=json.loads((ROOT/'web/anatomy/bodyparts3d/manifest.json').read_text())
 assert len(step['parts'])==4
 assert all('ventricle' in manifest['parts'][i]['name'] for i in step['parts'])
