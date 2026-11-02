"""Computed particle audits, dimensional kinematics and actual-reader evidence."""
from pathlib import Path
import copy,hashlib,json,subprocess,sys
import pytest
from primer.curriculum import Curriculum,_validate_lesson_media
from tools.particle_runtime_compatibility import before_particle_bytes,reviewed
R=Path(__file__).resolve().parents[1];D=R/'docs/physics-particle-review-20261102'

def test_lesson_preserves_quiz_illustration_and_detector_context():
    current=json.loads((R/'data/curriculum/03-physics.json').read_bytes())
    prior=json.loads(before_particle_bytes('data/curriculum/03-physics.json',(R/'data/curriculum/03-physics.json').read_bytes()))
    node=next(n for n in current['nodes']if n['id']=='phys.4.particles')
    original=next(n for n in prior['nodes']if n['id']=='phys.4.particles')
    assert {k:v for k,v in node.items()if k!='lesson_media'}=={k:v for k,v in original.items()if k!='lesson_media'}
    assert node['lesson_media'][0]==original['lesson_media'][0]
    effective=Curriculum().nodes['phys.4.particles']['lesson_media']
    assert [m.get('renderer')for m in effective if m['kind']=='model']==['physics-particle-lab','spatial-3d']
    assert next(m for m in effective if m.get('renderer')=='spatial-3d')['props']['family']=='detector'
    assert node['lesson_media'][1]['props']=={'scenario':'phys.4.particles'}
    for change in [{'id':'phys.5.qft'},{'scenario':'phys.5.qft'},{'extra':True}]:
        changed=copy.deepcopy(node)
        if 'id'in change:changed['id']=change['id']
        else:changed['lesson_media'][1]['props'].update(change)
        with pytest.raises(ValueError):_validate_lesson_media(changed)

@pytest.mark.parametrize('script,name,key,count',[
 ('check_particle_core.py','four-momentum-proof.json','kinematicCases',120),
 ('check_particle_ledger.py','ledger-independent-proof.json','channels',516),
 ('check_particle_edges.py','angular-edge-proof.json','cases',252),
])
def test_shipped_computations_against_independent_numbers(tmp_path,script,name,key,count):
    out=tmp_path/name;r=subprocess.run([sys.executable,str(R/'tools'/script),'--output',str(out)],cwd=R,text=True,capture_output=True,timeout=30)
    assert r.returncode==0,r.stdout+r.stderr
    proof=json.loads(out.read_bytes());assert proof.get('allPassed',proof.get('allKinematicsChecksPassed'))and proof[key]==count


def test_actual_reader_source_geometry_and_lifecycle():
    browser=json.loads((D/'reader/browser-proof.json').read_bytes());geometry=json.loads((D/'reader/rendered-proof.json').read_bytes())
    assert browser['allPassed']and browser['authenticatedSyntheticApp']and not browser['productionLearnerWrites']and browser['errors']==[]
    assert browser['cases']==36 and browser['independentMounts']==4 and browser['routeReopenChecks']==2 and browser['staleResponseChecks']==4
    for name,digest in browser['sourceSHA256'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,name
    assert geometry['allPassed']and geometry['renderedNonzeroVectors']==94 and geometry['equalMomentumScaleVerified']


def test_historical_projection_is_exact_and_rejects_foreign_edits():
    for name,row in reviewed()['files'].items():
        raw=(R/name).read_bytes();assert hashlib.sha256(before_particle_bytes(name,raw)).hexdigest()==row['before_sha256']
        with pytest.raises(ValueError):before_particle_bytes(name,raw+b'foreign')
