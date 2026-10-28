"""Source scope, lossless-channel evidence and exact reader identities for OpenEar."""
from pathlib import Path
import copy
import hashlib
import json
import shutil
import subprocess
import pytest
from primer import openear_native_reference as source

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'docs/openear-native-review-20261027'


def clear():
    source.registry.cache_clear()
    source.references.cache_clear()
    source._check.cache_clear()


@pytest.fixture
def isolated(tmp_path,monkeypatch):
    target=tmp_path/'web/anatomy/openear-zeta-native';target.mkdir(parents=True)
    for name in [*source.AUTHORED,'registry.json']:
        shutil.copy2(ROOT/'web/anatomy/openear-zeta-native'/name,target/name)
    monkeypatch.setattr(source,'ROOT',tmp_path)
    monkeypatch.setattr(source,'REGISTRY',target/'registry.json')
    clear()
    yield target
    clear()


def test_source_scope_and_original_independent_channels():
    refs=source.references()
    assert set(refs)=={'ra.ct-temporal-bone','ra.tinnitus'}
    assert all(all(row[k] is False for k in source.FLAGS)for items in refs.values()for row in items)
    m=json.loads(source.validate_file('manifest.json').read_bytes())
    assert m['overlap']['originalIndependentBinaryChannels']==13
    assert m['overlap']['additionalSeparateFullBoneChannel']==13
    assert m['overlap']['overlappingOriginalChannelPositions']==773
    assert m['effectiveSpatialResolutionEstablished'] is False
    assert m['registeredSpacingEqualsReportedAcquisitionVoxelSize']=={'embedded':True,'unembedded':False}
    assert m['originalAcquisitionVoxelMm']=={'embedded':.125,'unembedded':.25}
    assert sum(len(s['components26'])for s in m['selections'])==57
    assert m['selections'][10]['meshId']=='openear-zeta-part9'
    assert m['selections'][11]['meshId']=='openear-zeta-part10'
    assert m['selections'][12]['meshId']=='openear-zeta-part11'
    assert m['selections'][8]['meshId']==m['selections'][13]['meshId']=='openear-zeta-part12'


@pytest.mark.parametrize('name',['../index.html','%69ndex.html','registry.json','source-mesh-0.ply','missing.pack'])
def test_only_registered_authored_files_are_exposed(name):
    with pytest.raises(ValueError):source.validate_file(name)


@pytest.mark.parametrize('mutation',['approval','binding','source_hash','incomplete_delivery','licence','source_link'])
def test_changed_registry_scope_fails_even_if_transport_pin_is_refreshed(isolated,monkeypatch,mutation):
    data=copy.deepcopy(source.registry())
    if mutation=='approval':data['clinical_approval']=True
    elif mutation=='binding':data['bindings'].append('ra.mri-trigeminal')
    elif mutation=='source_hash':data['source_original_hashes']['CBCT_Unembedded.nrrd']='0'*64
    elif mutation=='incomplete_delivery':data['delivery']['allRemoteHashesMatch']=False
    elif mutation=='licence':data['inspector']['license']='CC0'
    else:data['inspector']['source_url']='https://example.invalid/unreviewed'
    raw=(json.dumps(data)+'\n').encode();source.REGISTRY.write_bytes(raw);monkeypatch.setattr(source,'REGISTRY_SHA256',hashlib.sha256(raw).hexdigest());clear()
    with pytest.raises(ValueError):source.references()


def test_changed_and_symlinked_reader_files_fail(isolated):
    path=isolated/'viewer.js';path.write_bytes(path.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='length'):source.validate_file('viewer.js')
    path.unlink();path.symlink_to(ROOT/'web/anatomy/openear-zeta-native/viewer.js')
    with pytest.raises(ValueError,match='symlink'):source.validate_file('viewer.js')


def test_complete_native_package_and_original_source_evidence():
    p=json.loads((EVIDENCE/'package-independent-proof.json').read_bytes())
    assert p['allPassed'] and p['manifestSHA256']==source.MANIFEST_SHA256
    assert p['originalChannelValuesCompared']==2536855825
    assert p['planeValuesCompared']==2205652500 and p['planes']==5640
    assert p['meshClasses']==13 and p['sourceTriangles']==7349910
    assert p['meshBytesCompared']==132282312 and p['overlappingOriginalPositionsPreserved']==773
    c=json.loads((EVIDENCE/'mesh-coordinate-proof.json').read_bytes())
    assert c['allPassed'] and c['allSourceCoordinateChecksPassed'] and not c['clinicalApproval']
    assert len(c['meshes'])==13
    for row in c['meshes']:
        correct=row['checks']['source_identity']
        assert correct['verticesWithinOriginalDeclaredGrid']==row['vertices']
        assert correct['verticesWithin0_25mmOfPositiveSourceCells']==row['vertices']
        assert all(v['verticesWithin0_25mmOfPositiveSourceCells']<row['vertices']*.8 for name,v in row['checks'].items()if name!='source_identity')
    delivery=source.registry()['delivery'];assert len(delivery['files'])==135 and len(delivery['originals'])==17
    assert delivery['allRemoteHashesMatch']


@pytest.mark.parametrize('prefix,states,pixels',[('',84,98825244),('variant-',24,28235784)])
def test_actual_gpu_and_independent_rendered_pixels_match_current_reader(prefix,states,pixels):
    folder=EVIDENCE/'reader';browser=json.loads((folder/(prefix+'browser-proof.json')).read_bytes())
    assert browser['allPassed'] and browser['errors']==[] and len(browser['cases'])==states
    for name,digest in browser['files'].items():
        assert hashlib.sha256(source.validate_file(name).read_bytes()).hexdigest()==digest,name
    proof=json.loads((folder/(prefix+'pixel-proof.json')).read_bytes())
    assert proof['allPassed'] and proof['pixelsCompared']==pixels
    assert proof['browserProofSHA256']==hashlib.sha256((folder/(prefix+'browser-proof.json')).read_bytes()).hexdigest()
    if not prefix:
        assert len(browser['gpu'])==28 and len(browser['components'])==114
        assert all(r['error']==0 and r['visible']>10 for r in browser['gpu'])
        assert all(c['nativePixelsUnchanged'] and c['scaleRemainsPhysical']for c in browser['controls'])
    else:assert browser['overlapCells']==1546


def test_failure_recovery_and_adverse_context_ownership():
    r=json.loads((EVIDENCE/'reader/recovery-proof.json').read_bytes());assert r['allPassed'] and r['errors']==[]
    assert {x['failure']for x in r['cases']}=={'ignored-range','corrupt','mesh503','stale selection','invalid CBCT window','empty CBCT window','WebGL loss during mesh transfer','WebGL unavailable'}
    for name,digest in r['files'].items():assert hashlib.sha256(source.validate_file(name).read_bytes()).hexdigest()==digest
    adverse=json.loads((EVIDENCE/'independent-review/context-epoch-after.json').read_bytes())
    assert adverse['allPassed'] and adverse['pageErrors']==[]
    current=json.loads((EVIDENCE/'independent-review/adverse-reader.json').read_bytes())
    assert current['allPassed'] and current['pageErrors']==[]
    for name,digest in current['sourceSHA256'].items():assert hashlib.sha256(source.validate_file(name).read_bytes()).hexdigest()==digest


def test_bounded_payload_deadlines_and_cancellation_behavior():
    result=subprocess.run(['node',str(ROOT/'tools/check_openear_native_transport.cjs')],cwd=ROOT,text=True,capture_output=True,timeout=30)
    assert result.returncode==0,result.stdout+result.stderr
    proof=json.loads(result.stdout)
    assert proof['allPassed'] and proof['configuredTimeoutMs']==45000 and len(proof['cases'])==8
    assert proof['transportSHA256']==hashlib.sha256(source.validate_file('transport.js').read_bytes()).hexdigest()
