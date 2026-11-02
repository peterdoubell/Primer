from pathlib import Path
import hashlib,json,subprocess,sys,copy
import pytest
from primer.curriculum import Curriculum,_validate_lesson_media
R=Path(__file__).resolve().parents[1];D=R/'docs/physics-rotation-review-20261102'

def test_frontier_has_one_calibrated_spatial_activity():
    n=Curriculum().nodes['phys.5.frontier'];models=[m for m in n['lesson_media']if m['kind']=='model']
    assert len(models)==1 and models[0]['renderer']=='spatial-3d'
    assert models[0]['props']['family']=='rotation-density-geometry'and models[0]['props']['mode']=='model'
    assert 'quantum' in n['goal'].lower()
    _validate_lesson_media(n)
    changed=copy.deepcopy(n);changed['lesson_media']=[copy.deepcopy(models[0])];changed['lesson_media'][0]['props']['scenario']='module.phys.4.particles'
    with pytest.raises(ValueError):_validate_lesson_media(changed)

def test_shipped_core_matches_independent_density_integrals_and_potential_gradients(tmp_path):
    output=tmp_path/'proof.json';r=subprocess.run([sys.executable,str(R/'tools/check_rotation_core.py'),'--output',str(output)],cwd=R,capture_output=True,text=True,timeout=90)
    assert r.returncode==0,r.stdout+r.stderr
    p=json.loads(output.read_bytes());assert p['allPassed']and p['radiusCases']==1620 and p['potentialGradientChecks']==972
    assert p['coreSHA256']==hashlib.sha256((R/'web/physics-rotation-core.js').read_bytes()).hexdigest()

def test_actual_reader_evidence_matches_shipped_files_and_preserves_scope():
    p=json.loads((D/'reader/browser-proof.json').read_bytes());assert p['allPassed']and p['authenticatedSyntheticApp']and not p['productionLearnerWrites']and not p['wholeGoalComplete']
    assert p['cases']==8 and p['routeReopenChecks']==2 and p['errors']==[]
    from tools.condensed_runtime_compatibility import before_condensed_bytes
    for name,digest in p['sourceSHA256'].items():assert hashlib.sha256(before_condensed_bytes(name,(R/name).read_bytes())).hexdigest()==digest,name
    g=json.loads((D/'reader/geometry-proof.json').read_bytes());assert g['allPassed']and g['renderedCurveVertices']==3864 and g['selectedMarkers']==8
    c=json.loads((D/'reader/comparison-proof.json').read_bytes());assert c['allPassed']and c['syntheticObservationsVerified']==96 and c['renderedUncertaintyEndpointsVerified']==192
    gpu=json.loads((D/'reader/gpu-proof.json').read_bytes());assert gpu['allPassed']and gpu['authenticatedGPUReadbacks']==8 and gpu['sourceBuffersExact']and gpu['allSourceVerticesInFrustum']

def test_exact_inverse_does_not_allow_unreviewed_source_changes():
    from tools.rotation_runtime_compatibility import reviewed,before_rotation_bytes
    for name,row in reviewed()['files'].items():
        raw=(R/name).read_bytes();restored=before_rotation_bytes(name,raw)
        assert hashlib.sha256(restored).hexdigest()==row['before_sha256']
        assert before_rotation_bytes(name,restored)==restored
        with pytest.raises(ValueError):before_rotation_bytes(name,raw+b'unreviewed')
