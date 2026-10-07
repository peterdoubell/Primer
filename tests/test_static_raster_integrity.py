"""Simulate a hosted build that keeps provenance JSON but serves source rasters from the CDN."""
import copy,json
from pathlib import Path
from unittest.mock import patch
import pytest
from primer import radiology_catalog as catalog
from primer import source_raster_integrity as integrity
from tools.check_static_raster_inventory import inventory
ROOT=Path(__file__).resolve().parents[1];RAD=(ROOT/'web/reference-media/radiology-open').resolve()
def test_committed_inventory_matches_every_actual_source_file():
    assert json.loads((ROOT/'data/radiology/radiology-static-rasters.json').read_text())==inventory()
def row():
    return next(r for r in catalog._read('radiology-open-images.json')['ra.hrct-lung'] if r['id']=='open-hipct-lung-pmc9163096-fig1')
def missing_raster(path):return path.is_relative_to(RAD) and path.suffix.lower() in {'.png','.jpg','.jpeg','.webp','.gif'}
def test_every_gallery_loads_with_hosted_rasters_absent_and_local_provenance_kept(monkeypatch):
    monkeypatch.setenv('VERCEL','1');original=Path.is_file;catalog._structure_atlases.cache_clear();integrity._inventory.cache_clear()
    try:
        with patch.object(Path,'is_file',lambda p:False if missing_raster(p) else original(p)):
            atlas=catalog._structure_atlases()
            assert len(atlas['ra.hrct-lung'])==8 and len(atlas['ra.chest-radiography'])==11
            assert any(r.get('origin')=='native-volume-sections' for rows in atlas.values() for r in rows)
    finally:catalog._structure_atlases.cache_clear();integrity._inventory.cache_clear()
def test_local_missing_file_still_rejected(monkeypatch):
    monkeypatch.delenv('VERCEL',raising=False);original=Path.is_file
    with patch.object(Path,'is_file',lambda p:False if missing_raster(p) else original(p)):
        with pytest.raises(ValueError,match='missing'):integrity.verified_raster_header(row(),RAD,ROOT/'data/radiology')
@pytest.mark.parametrize('change',['sha','dimensions','unknown','escape','null_header'])
def test_hosted_inventory_does_not_accept_forged_source_metadata(monkeypatch,change):
    monkeypatch.setenv('VERCEL','1');image=copy.deepcopy(row());original=Path.is_file
    if change=='sha':image['sha256']='0'*64
    if change=='dimensions':image['width']+=1
    if change=='unknown':image['src']='/app/reference-media/radiology-open/unknown.jpg'
    if change=='escape':image['src']='/app/reference-media/radiology-open/../../index.html'
    if change=='null_header':
        data=copy.deepcopy(integrity._inventory(str(ROOT/'data/radiology/radiology-static-rasters.json')));data[image['src']]['header_hex']=None;monkeypatch.setattr(integrity,'_inventory',lambda p:data)
    with patch.object(Path,'is_file',lambda p:False if missing_raster(p) else original(p)):
        with pytest.raises(ValueError):integrity.verified_raster_header(image,RAD,ROOT/'data/radiology')


def test_authenticated_reference_api_works_with_hosted_source_file_layout(monkeypatch):
    from fastapi.testclient import TestClient
    import primer.server as server
    monkeypatch.setenv('VERCEL','1')
    monkeypatch.setenv(server.ACCESS_USERNAME_ENV,'reader')
    monkeypatch.setenv(server.ACCESS_PASSWORD_ENV,'secret')
    original_file,original_read=Path.is_file,Path.read_bytes
    catalog._structure_atlases.cache_clear();integrity._inventory.cache_clear()
    def read(path):
        if missing_raster(path):raise FileNotFoundError('Raster is hosted statically')
        return original_read(path)
    try:
        with patch.object(Path,'is_file',lambda p:False if missing_raster(p) else original_file(p)), patch.object(Path,'read_bytes',read):
            with TestClient(server.app) as client:
                response=client.get('/api/radiology/modules/ra.hrct-lung',auth=('reader','secret'))
                assert response.status_code==200
                assert len(response.json()['radiology_reference']['structure_atlas'])==8
                health=client.get('/healthz')
                assert health.status_code==200 and health.json()['source_gallery_metadata_validated'] is True
    finally:catalog._structure_atlases.cache_clear();integrity._inventory.cache_clear()


def test_health_does_not_claim_success_when_reference_gallery_validation_fails(monkeypatch):
    from fastapi.testclient import TestClient
    import primer.server as server
    def invalid():raise ValueError('Source integrity failure')
    monkeypatch.setattr(catalog,'_structure_atlases',invalid)
    with TestClient(server.app,raise_server_exceptions=False) as client:
        assert client.get('/healthz').status_code==500
