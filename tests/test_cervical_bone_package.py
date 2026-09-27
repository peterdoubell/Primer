import hashlib,json,struct
from pathlib import Path
from tools.anatomy_sources.package_cervical_bones import build
ROOT=Path(__file__).resolve().parents[1]


def test_offline_package_contains_only_checked_native_bones():
    folder=ROOT/'output/msk-cervical-bones'
    manifest=json.loads((folder/'manifest.json').read_text())
    audit=json.loads((ROOT/'docs/msk-atlantoaxial-source-review/export-audit.json').read_text())
    expected={x['source_model_id']:x for x in audit['parts'] if x['name'] in ['Atlas (C1)','Axis (C2)']}
    assert len(manifest['parts'])==2
    assert sum(x['triangles'] for x in manifest['parts'].values())==4528
    assert not manifest['clinical_approval']
    assert manifest['license']=='CC BY-SA 4.0'
    for p in manifest['parts'].values():
        data=(folder/p['file']).read_bytes()
        assert hashlib.sha256(data).hexdigest()==p['sha256']==expected[p['source_model_id']]['sha256']
        magic,n,k=struct.unpack('<4sII',data[:12])
        assert magic==b'BP3D' and len(data)==12+24*n+4*k
        assert k//3==p['triangles']
        assert p['fidelity_review']=='pending'
    assert any('Occipital' in x for x in manifest['excluded'])


def test_repackaging_preserves_bytes_and_metadata(tmp_path):
    import pytest
    if not Path('/tmp/primer-msk-sources/atlantoaxial-staged/world-inventory.json').exists():
        pytest.skip('Original acquisition staging unavailable')
    result=build(tmp_path)
    current=json.loads((ROOT/'output/msk-cervical-bones/manifest.json').read_text())
    assert result==current
    for p in result['parts'].values():
        assert (tmp_path/p['file']).read_bytes()==(ROOT/'output/msk-cervical-bones'/p['file']).read_bytes()


def test_runtime_cervical_manifest_retains_only_packaged_bone_bytes():
    runtime=ROOT/'web/anatomy/msk-cervical'
    manifest=json.loads((runtime/'manifest.json').read_text())
    package=json.loads((ROOT/'output/msk-cervical-bones/manifest.json').read_text())
    assert set(manifest['parts'])==set(package['parts'])
    assert set(manifest['regions'])=={'cervical'}
    for identifier,p in manifest['parts'].items():
        path=ROOT/'web'/p['file'].removeprefix('/app/')
        assert path.read_bytes()==(ROOT/'output/msk-cervical-bones'/package['parts'][identifier]['file']).read_bytes()
    assert not manifest['clinical_approval']
    assert any('occipital' in n.lower() for n in manifest['viewer_notes'])
    assert 'ligament' in manifest['limitations']
