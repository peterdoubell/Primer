"""Hosted native references must survive CDN exclusion without accepting unreviewed geometry."""
import copy
import json
from pathlib import Path
from unittest.mock import patch
import pytest
from primer import radiology_catalog as catalog
from primer import source_mesh_integrity as integrity
from tools.check_static_source_mesh_inventory import inventory
ROOT = Path(__file__).resolve().parents[1]


def missing_mesh(path):
    return any(atlas in path.parts for atlas in integrity.CDN_ATLASES) and path.name.endswith(('.bin','.bin.gz'))


def source_part():
    root = ROOT/'web/anatomy/hvsmr2-pat7'
    return next(iter(json.loads((root/'manifest.json').read_text())['parts'].values())), root


def test_inventory_matches_every_actual_configured_CDN_source_reference():
    assert json.loads((ROOT/'data/radiology/radiology-static-source-meshes.json').read_text()) == inventory()


def test_all_source_references_load_when_hosted_mesh_bytes_are_excluded(monkeypatch):
    monkeypatch.setenv('VERCEL','1'); original_file, original_read = Path.is_file, Path.read_bytes
    catalog._source_anatomy_references.cache_clear(); integrity._inventory.cache_clear()
    def read(path):
        if missing_mesh(path): raise FileNotFoundError('Source is hosted statically')
        return original_read(path)
    try:
        with patch.object(Path,'is_file',lambda p:False if missing_mesh(p) else original_file(p)), patch.object(Path,'read_bytes',read):
            refs = catalog._source_anatomy_references()
            assert any(e['atlas']=='hvsmr2-pat7' for e in refs['ra.vascular-anomalies'])
            assert any(e['atlas']=='nasalseg-p001' for e in refs['ra.mri-sinuses'])
    finally: catalog._source_anatomy_references.cache_clear(); integrity._inventory.cache_clear()


def test_missing_local_source_is_rejected_even_with_inventory(monkeypatch):
    monkeypatch.delenv('VERCEL',raising=False); part, root = source_part(); original = Path.is_file
    with patch.object(Path,'is_file',lambda p:False if missing_mesh(p) else original(p)):
        with pytest.raises(ValueError,match='missing'): integrity.verified_mesh_contract(part,root,ROOT/'data/radiology')


@pytest.mark.parametrize('change',['hash','counts','unknown','escape','header','decoded_size'])
def test_hosted_forged_contracts_are_rejected(monkeypatch,change):
    monkeypatch.setenv('VERCEL','1'); part,root = source_part(); part = copy.deepcopy(part); original = Path.is_file
    data = copy.deepcopy(integrity._inventory(str(ROOT/'data/radiology/radiology-static-source-meshes.json')))
    if change=='hash': part['sha256']='0'*64
    elif change=='counts': part['triangles'] += 1
    elif change=='unknown': part['file']='/app/anatomy/hvsmr2-pat7/missing.bin.gz'
    elif change=='escape': part['file']='/app/anatomy/hvsmr2-pat7/../../other.bin.gz'
    elif change=='header': data[part['file']]['header_hex']='00'*12
    else: data[part['file']]['decoded_bytes']+=1
    monkeypatch.setattr(integrity,'_inventory',lambda p:data)
    with patch.object(Path,'is_file',lambda p:False if missing_mesh(p) else original(p)):
        with pytest.raises(ValueError): integrity.verified_mesh_contract(part,root,ROOT/'data/radiology')


def test_authenticated_API_survives_all_configured_hosted_mesh_exclusions(monkeypatch):
    from fastapi.testclient import TestClient
    import primer.server as server
    monkeypatch.setenv('VERCEL','1'); monkeypatch.setenv(server.ACCESS_USERNAME_ENV,'reader'); monkeypatch.setenv(server.ACCESS_PASSWORD_ENV,'secret')
    original_file,original_read = Path.is_file,Path.read_bytes
    catalog._source_anatomy_references.cache_clear(); integrity._inventory.cache_clear()
    def read(path):
        if missing_mesh(path): raise FileNotFoundError('CDN mesh excluded from function bundle')
        return original_read(path)
    try:
        with patch.object(Path,'is_file',lambda p:False if missing_mesh(p) else original_file(p)), patch.object(Path,'read_bytes',read):
            with TestClient(server.app) as client:
                for identifier in ['ra.vascular-anomalies','ra.mri-sinuses','ra.thoracolumbar-fractures']:
                    response = client.get('/api/radiology/modules/'+identifier,auth=('reader','secret'))
                    assert response.status_code == 200
                    assert response.json()['radiology_reference']['source_anatomy_references']
                health = client.get('/healthz')
                assert health.status_code == 200 and health.json()['source_model_metadata_validated'] is True
    finally: catalog._source_anatomy_references.cache_clear(); integrity._inventory.cache_clear()


def test_health_rejects_invalid_source_model_integrity(monkeypatch):
    from fastapi.testclient import TestClient
    import primer.server as server
    def invalid(): raise ValueError('Source model integrity failure')
    monkeypatch.setattr(catalog,'_source_anatomy_references',invalid)
    with TestClient(server.app,raise_server_exceptions=False) as client:
        assert client.get('/healthz').status_code == 500


def test_local_changed_mesh_cannot_fall_back_to_the_inventory(monkeypatch):
    monkeypatch.setenv('VERCEL','1'); part,root = source_part(); original = Path.read_bytes
    target = root/part['file'].split('/')[-1]
    with patch.object(Path,'read_bytes',lambda p:b'changed source bytes' if p==target else original(p)):
        with pytest.raises(ValueError,match='changed'):
            integrity.verified_mesh_contract(part,root,ROOT/'data/radiology')


def test_hosted_sources_without_CDN_configuration_still_need_local_mesh_bytes(monkeypatch):
    monkeypatch.setenv('VERCEL','1')
    root = ROOT/'web/anatomy/nasalseg-p001'
    part = next(iter(json.loads((root/'manifest.json').read_text())['parts'].values()))
    original = Path.is_file
    target = root/part['file'].split('/')[-1]
    with patch.object(Path,'is_file',lambda p:False if p==target else original(p)):
        with pytest.raises(ValueError,match='missing'):
            integrity.verified_mesh_contract(part,root,ROOT/'data/radiology')
