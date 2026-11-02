from pathlib import Path
import copy,hashlib,json,subprocess,sys
import pytest
from primer import cavernous_photo_reference as source
R=Path(__file__).resolve().parents[1]
def test_original_figures_and_discrepancies_remain_explicit():
    refs=source.references();assert set(refs)=={'ra.mri-sella'}
    item=refs['ra.mri-sella'][0];assert all(item[k]is False for k in source.FLAGS)
    meta=json.loads(source.validate_file('figure-review.json').read_bytes())
    assert len(meta['authors'])==8 and len(meta['figures'])==5
    assert all(meta['figures'][i]['captionDiscrepancy']for i in [1,2])
    assert not meta['raw3DCoordinatesOrMeshesProvided']and not meta['sourceMRIOrCTVolumesProvided']

def test_private_delivery_and_single_module_binding():
    r=subprocess.run([sys.executable,str(R/'tools/check_cavernous_photo_routes.py')],cwd=R,capture_output=True,text=True,timeout=180)
    assert r.returncode==0,r.stdout+r.stderr

def test_exact_historical_projection_rejects_unreviewed_changes():
    from tools.cavernous_photo_runtime_compatibility import reviewed,before_cavernous_bytes,before_cavernous_fields
    proof=reviewed()
    for name,row in proof['files'].items():
        raw=(R/name).read_bytes();restored=before_cavernous_bytes(name,raw)
        assert hashlib.sha256(restored).hexdigest()==row['before_sha256']
        with pytest.raises(ValueError):before_cavernous_bytes(name,raw+b'foreign')
    fields={'source_native_inspectors':[proof['inspector']]}
    assert before_cavernous_fields('ra.mri-sella',fields)=={'source_native_inspectors':[]}
    for key in [*source.FLAGS,'caption']:
        changed=copy.deepcopy(fields);changed['source_native_inspectors'][0][key]=True
        with pytest.raises(ValueError):before_cavernous_fields('ra.mri-sella',changed)
    with pytest.raises(ValueError):before_cavernous_fields('ra.brain-anatomy',fields)

def test_authenticated_phone_and_desktop_figures_reopen():
    d=R/'docs/cavernous-source-review-20261102';proof=json.loads((d/'reader/browser-proof.json').read_bytes());lifecycle=json.loads((d/'prototype/proof.json').read_bytes())
    assert proof['allPassed']and proof['authenticatedSyntheticApp']and not proof['productionVerified']and not proof['productionLearnerWrites']and proof['errors']==[]
    assert len(proof['cases'])==10 and len(proof['mounts'])==2 and all(r['reopened']for r in proof['mounts'])
    assert lifecycle['checksumMismatchRejected']and lifecycle['httpFailureRetryRecovered']
    for name,digest in proof['sourceSHA256'].items():assert hashlib.sha256((R/'web/anatomy'/source.ATLAS/name).read_bytes()).hexdigest()==digest
