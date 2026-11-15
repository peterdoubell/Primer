from pathlib import Path
import hashlib,json,subprocess,sys
import pytest
from primer.curriculum import Curriculum
from tools.particle_runtime_compatibility import before_particle_bytes
R=Path(__file__).resolve().parents[1];D=R/'docs/physics-condensed-review-20261102'
def test_one_calibrated_activity_and_original_assessment_scope():
    n=Curriculum().nodes['phys.5.condensed'];m=[x for x in n['lesson_media']if x['kind']=='model']
    assert len(m)==1 and m[0]['renderer']=='spatial-3d'and m[0]['props']['family']=='type-i-field-geometry'
    assert m[0]['props']['scenario']=='module.phys.5.condensed'and m[0]['props']['mode']=='model'
def test_shipped_core_against_high_precision_independent_values(tmp_path):
    output=tmp_path/'core.json';r=subprocess.run([sys.executable,str(R/'tools/check_condensed_core.py'),'--output',str(output)],cwd=R,capture_output=True,text=True,timeout=60)
    assert r.returncode==0,r.stdout+r.stderr
    p=json.loads(output.read_bytes());assert p['allPassed']and p['states']==462 and p['decimalPrecision']==50
    assert p['coreSHA256']==hashlib.sha256((R/'web/physics-condensed-core.js').read_bytes()).hexdigest()
def test_authenticated_reader_and_field_geometry_evidence():
    b=json.loads((D/'reader/browser-proof.json').read_bytes());g=json.loads((D/'reader/geometry-proof.json').read_bytes());f=json.loads((D/'reader/rendered-field-proof.json').read_bytes())
    assert b['allPassed']and b['authenticatedSyntheticApp']and not b['productionLearnerWrites']and b['errors']==[]
    assert b['cases']==12 and b['fieldCases']==24 and b['routeReopenChecks']==2
    for name,digest in b['sourceSHA256'].items():assert hashlib.sha256(before_particle_bytes(name,(R/name).read_bytes())).hexdigest()==digest,name
    assert g['allPassed']and g['renderedBranchVertices']==992 and g['nonzeroFieldCoexistenceNoUniqueMarker']
    assert f['allPassed']and f['renderedNonzeroVectors']==852 and f['independentMagneticPhaseAndSheetCurrentValues']
def test_exact_inverse_rejects_foreign_source_bytes():
    from tools.condensed_runtime_compatibility import reviewed,before_condensed_bytes
    for name,row in reviewed()['files'].items():
        raw=(R/name).read_bytes();before=before_condensed_bytes(name,raw)
        assert hashlib.sha256(before).hexdigest()==row['before_sha256']
        with pytest.raises(ValueError):before_condensed_bytes(name,raw+b'foreign')
