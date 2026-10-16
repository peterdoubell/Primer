"""Source identities, bounded historical views and protected reader delivery."""
from pathlib import Path
import copy,hashlib,json,os,subprocess,sys
import pytest
from primer import spl_reporting_reference as reference
from tools import spl_reporting_runtime_compatibility as bridge
ROOT=Path(__file__).resolve().parents[1]

def test_current_source_inventory_preserves_native_grids_and_explicit_gaps():
    bound=reference.references();assert set(bound)=={'ra.brain-anatomy'}
    manifest=json.loads(reference.validate_file('manifest.json').read_bytes())
    assert len(manifest['labels'])==217 and manifest['additionalSourceClassCount']==205
    assert len(manifest['labelMeshes'])==217 and sum(bool(m.get('sharedSource')) for m in manifest['labelMeshes'])==10
    assert manifest['newFittedTransforms'] is False and manifest['clinicalApproval'] is False
    for group in manifest['groups']:
        assert group['completeReportingRequirementApproved'] is False
        if group['id'] in {'sulcal-landmarks','cisterns-and-extra-axial','vascular-localisation'}:assert group['codes']==[] and group['missing_or_unresolved_structures']
    commissure=next(row for row in manifest['labels'] if row['code']==142)
    assert commissure['componentSizes26']==[724,2] and commissure['components26'][1]['focusRAS'] in [[9.,15.,28.],[9.,15.,29.]]
    for file in ['../manifest.json','missing.gz','%69ndex.html']:
        with pytest.raises(ValueError):reference.validate_file(file)

@pytest.mark.parametrize('path',sorted(bridge.PATHS))
def test_exact_shared_inverse_retains_unrelated_bytes(path):
    row=bridge.reviewed()['files'][path];raw=(ROOT/path).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==row['after_sha256']
    previous=bridge.before_reporting_bytes(path,raw);assert hashlib.sha256(previous).hexdigest()==row['before_sha256']
    assert bridge.before_reporting_bytes(path,previous)==previous
    with pytest.raises(ValueError,match='Unreviewed'):bridge.before_reporting_bytes(path,raw+b'\n# unrelated drift\n')

def test_reference_inverse_accepts_only_exact_single_added_inspector():
    item=reference.registry()['inspectors'][reference.IDENTIFIER];current={'source_native_inspectors':[item]}
    assert bridge.before_reporting_reference_fields('ra.brain-anatomy',current)=={'source_native_inspectors':[]}
    assert current['source_native_inspectors']==[item]
    for mutation in ['duplicate','approval','description']:
        bad=copy.deepcopy(current)
        if mutation=='duplicate':bad['source_native_inspectors'].append(item)
        elif mutation=='approval':bad['source_native_inspectors'][0]['clinical_approval']=True
        else:bad['source_native_inspectors'][0]['caption']+=' Unreviewed.'
        with pytest.raises(ValueError,match='Unreviewed'):bridge.before_reporting_reference_fields('ra.brain-anatomy',bad)

def test_reader_delivery_and_API_keep_access_and_approval_boundaries(tmp_path):
    env={k:v for k,v in os.environ.items() if not k.startswith(('TURSO','PRIMER_ACCESS_','VERCEL','BLOB_'))}
    env.update(PRIMER_DB=str(tmp_path/'record.db'),PRIMER_CONTENT_DIR=str(tmp_path/'content'),PRIMER_BACKUP_DIR=str(tmp_path/'backups'),PRIMER_ACCESS_USERNAME='synthetic-test-reader',PRIMER_ACCESS_PASSWORD='synthetic-test-password',TURSO_DATABASE_URL='',TURSO_AUTH_TOKEN='')
    script='''
from fastapi.testclient import TestClient
import primer.server as server
from primer import spl_reporting_reference as source
with TestClient(server.app) as client:
 for name in ['index.html','viewer.js','manifest.json','label-11.mesh.gz']:
  url=source.PREFIX+name
  assert client.get(url).status_code==401
  r=client.get(url,auth=('synthetic-test-reader','synthetic-test-password'));assert r.status_code==200
  assert r.headers['cache-control']=='private, no-store'
  if name=='index.html':assert "frame-ancestors 'self'" in r.headers['content-security-policy']
 for name in ['missing.gz','%69ndex.html']:
  assert client.get(source.PREFIX+name,auth=('synthetic-test-reader','synthetic-test-password')).status_code==404
 r=client.get('/api/radiology/modules/ra.brain-anatomy',auth=('synthetic-test-reader','synthetic-test-password'));assert r.status_code==200
 ref=r.json()['radiology_reference'];item=next(v for v in ref['source_native_inspectors'] if v['id']==source.IDENTIFIER)
 assert item==source.registry()['inspectors'][source.IDENTIFIER]
 assert item['clinical_approval'] is False and item['complete_reporting_anatomy_approved'] is False
 assert any(v['id']=='spl-nac-limbic-native-reference' for v in ref['source_native_inspectors'])
print('reader delivery, original context and explicit source limits verified')
'''
    result=subprocess.run([sys.executable,'-B','-c',script],cwd=ROOT,env=env,capture_output=True,text=True,timeout=90)
    assert result.returncode==0,result.stdout+result.stderr


def test_lossless_runtime_manifest_matches_canonical_response_bytes():
    raw=reference.manifest_bytes();assert raw==(ROOT/'web/anatomy/spl-nac-reporting/manifest.json').read_bytes()
    row=reference.registry()['runtime_manifest'];assert row['decoded_sha256']==hashlib.sha256(raw).hexdigest()
    assert row['bytes']<len(raw)//5


def test_production_metadata_works_without_plain_manifest_or_static_payloads(tmp_path,monkeypatch):
    import shutil
    assets=tmp_path/'web/anatomy/spl-nac-reporting';assets.mkdir(parents=True)
    for name in ['index.html','viewer.js','viewer.css']:shutil.copyfile(ROOT/'web/anatomy/spl-nac-reporting'/name,assets/name)
    runtime=tmp_path/'data/radiology';runtime.mkdir(parents=True)
    for name in ['spl-reporting-reference.json','spl-reporting-runtime-manifest.json.gz']:shutil.copyfile(ROOT/'data/radiology'/name,runtime/name)
    reference.references.cache_clear();reference.registry.cache_clear();reference.manifest_bytes.cache_clear()
    monkeypatch.setattr(reference,'ROOT',tmp_path);monkeypatch.setattr(reference,'REGISTRY',runtime/'spl-reporting-reference.json');monkeypatch.setenv('VERCEL','1')
    try:
        assert not (assets/'manifest.json').exists()
        assert reference.references()['ra.brain-anatomy'][0]['id']==reference.IDENTIFIER
        assert hashlib.sha256(reference.manifest_bytes()).hexdigest()==reference.registry()['files']['manifest.json']['sha256']
    finally:
        reference.references.cache_clear();reference.registry.cache_clear();reference.manifest_bytes.cache_clear()
