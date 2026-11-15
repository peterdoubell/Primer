import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'docs/epilepsy-structure-coverage-20261030'

def test_standalone_comparison_is_bound_to_current_source_pixels_and_meshes():
    p=json.loads((D/'live-comparison/standalone-proof.json').read_bytes())
    assert p['allPassed'] and not p['errors'] and len(p['pixels'])==264
    assert all(r['pairedStateVerified'] and len(r['unmarkedSHA256'])==64 for r in p['pixels'])
    for name,digest in p['sourcePins'].items():
        assert hashlib.sha256((ROOT/'web/anatomy/spl-nac-limbic'/name).read_bytes()).hexdigest()==digest

def test_actual_authenticated_comparison_covers_all_bound_entry_points():
    p=json.loads((D/'authenticated-comparison/reader-proof.json').read_bytes())
    assert p['allPassed'] and not p['errors'] and len(p['cases'])==24
    assert {c['width']for c in p['cases']}=={390,1440}
    assert {c['investigation']for c in p['cases']}=={'ra.brain-anatomy','ra.mri-epilepsy','ra.mri-dementia'}
    assert sum(sum(bool(r.get('pairedStateVerified'))for r in c['pixels'])for c in p['cases'])==144
    assert len(p['payloads'])==27 and all(c['gpuMeshes']==24 for c in p['cases'])
    assert hashlib.sha256((ROOT/'data/radiology/spl-limbic-reference.json').read_bytes()).hexdigest()==p['registrySHA256']
    for name,digest in p['sourcePins'].items():
        assert hashlib.sha256((ROOT/'web/anatomy/spl-nac-limbic'/name).read_bytes()).hexdigest()==digest

def test_exact_comparison_inverse_rejects_source_and_approval_drift():
    import copy,pytest
    from tools.spl_unmarked_runtime_compatibility import reviewed,before_unmarked_bytes,before_unmarked_reference_fields
    p=reviewed()
    for name,row in p['files'].items():
        raw=(ROOT/name).read_bytes();before=before_unmarked_bytes(name,raw)
        assert hashlib.sha256(before).hexdigest()==row['before_sha256']
        assert before_unmarked_bytes(name,before)==before
        with pytest.raises(ValueError):before_unmarked_bytes(name,raw+b'foreign change')
    for identifier in p['bindings']:
        fields={'source_native_inspectors':[p['descriptor']['after']]}
        assert before_unmarked_reference_fields(identifier,fields)=={'source_native_inspectors':[p['descriptor']['before']]}
        bad=copy.deepcopy(fields);bad['source_native_inspectors'][0]['clinical_approval']=True
        with pytest.raises(ValueError):before_unmarked_reference_fields(identifier,bad)
