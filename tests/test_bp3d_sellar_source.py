"""Source geometry alternatives, correct grant and a held ICA cannot become invented anatomy."""
import gzip
import hashlib
import json
from pathlib import Path
import struct

import numpy as np

from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj

ROOT=Path(__file__).resolve().parents[1]
ATLAS=ROOT/'web/anatomy/bp3d-sella-4.3'
EVIDENCE=ROOT/'docs/bp3d-sellar-native-source-review'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def test_all_original_source_headers_positions_normals_faces_and_hold_survive():
    manifest=json.loads((ATLAS/'manifest.json').read_text())
    receipt=json.loads((EVIDENCE/'upstream-acquisition.json').read_text())
    assert manifest['published_source_parts']==12 and len(manifest['parts'])==12
    assert manifest['total_triangles']==18942
    assert len(receipt['objects'])==manifest['original_objects_retained_in_evidence']==13
    assert manifest['held_source_element_ids']==['FJ3483']
    for record in receipt['objects']:
        raw=gzip.decompress((EVIDENCE/'original-objects'/(record['id']+'.obj.gz')).read_bytes())
        assert sha(raw)==record['sha256']
        v,n,f,nf=read_obj(raw.decode())
        if record['id']=='FJ3483':
            assert not any(p['source_element_id']=='FJ3483' for p in manifest['parts'].values())
            continue
        part=next(p for p in manifest['parts'].values() if p['source_element_id']==record['id'])
        assert part['original_source_header']==record['original_obj_header']
        assert part['source_fma']==record['source_fma'] and part['source_representation_id']==record['representation_id']
        encoded=(ROOT/'web'/part['file'].removeprefix('/app/')).read_bytes()
        assert sha(encoded)==part['sha256']
        decoded=gzip.decompress(encoded);assert sha(decoded)==part['decoded_sha256']
        assert struct.unpack('<4sII',decoded[:12])==(b'BP3D',len(v),f.size)
        positions=np.frombuffer(decoded,'<f4',count=v.size,offset=12).reshape(v.shape)
        normals=np.frombuffer(decoded,'<f4',count=n.size,offset=12+v.size*4).reshape(n.shape)
        faces=np.frombuffer(decoded,'<u4',count=f.size,offset=12+(v.size+n.size)*4).reshape(f.shape)
        assert np.array_equal(positions,v.astype('<f4')) and np.array_equal(normals,n.astype('<f4'))
        assert np.array_equal(faces,f) and np.array_equal(f,nf)
        assert sha(v.astype('<f8').tobytes())==part['source_positions_float64_sha256']
        assert sha(n.astype('<f8').tobytes())==part['source_normals_float64_sha256']
        assert sha(f.astype('<i8').tobytes())==part['source_faces_int64_sha256']
        assert np.abs(positions.astype(float)-v).max()==part['maximum_Float32_position_error_mm']
        assert part['maximum_Float32_position_error_mm']<.0001


def test_incompatible_source_forms_are_exclusive_in_every_display_group():
    manifest=json.loads((ATLAS/'manifest.json').read_text())
    for region in manifest['regions'].values():
        ids={manifest['parts'][p['id']]['source_element_id'] for p in region['parts']}
        assert not {'FJ1796','FJ3848'}.issubset(ids)
        assert not {'FJ1682','FJ4993'}.issubset(ids)
        assert not (ids.intersection({'FJ7503','FJ7503M'}) and ids.intersection({'FJ7505','FJ7505M'}))
        assert 'FJ3483' not in ids
        assert not region['source_assembly_anatomically_approved']
    default={manifest['parts'][p['id']]['source_element_id'] for p in manifest['regions'][manifest['default_region']]['parts']}
    assert default=={'FJ1796','FJ7501','FJ7501M','FJ7502','FJ7502M','FJ7503','FJ7503M'}
    assert not any('first cranial nerve' in p['name'].lower() for p in manifest['parts'].values())


def test_actual_upstream_sharealike_grant_and_anatomical_uncertainty_remain():
    manifest=json.loads((ATLAS/'manifest.json').read_text())
    assert manifest['license']=='CC BY-SA 2.1 Japan'
    assert manifest['license_url']=='https://creativecommons.org/licenses/by-sa/2.1/jp/'
    notice=(ATLAS/'ATTRIBUTION.md').read_text()
    assert 'Copyright 2008' in notice and 'CC BY-SA2.1 Japan' in notice
    assert 'CC BY4.0 grant is not applied to upstream4.3' in notice
    assert not manifest['clinical_approval'] and not manifest['complete_reporting_anatomy_approved']
    assert not manifest['source_geometry_smoothed_repaired_fitted_cropped_or_merged']
    hold=json.loads((EVIDENCE/'held-source-identities.json').read_text())[0]
    assert hold['id']=='FJ3483' and hold['source_original_retained']
    assert not hold['in_published_anatomical_part_list']
    assert hold['actual_bounds_mm'][1][2]<1374
    assert all(p['clinical_fidelity']=='unverified' for p in manifest['parts'].values())


def test_runtime_bindings_and_authenticated_delivery_keep_all_exclusive_original_source_families(tmp_path,monkeypatch):
    from fastapi.testclient import TestClient
    from primer.curriculum import Curriculum
    from primer import radiology_catalog as catalog
    from primer.module_media import source_model_bindings
    from primer.learner import LearnerStore
    from primer.wiki import WikiService
    import primer.server as server
    raw=(ATLAS/'manifest.json').read_bytes();manifest=json.loads(raw)
    bindings=source_model_bindings()
    assert len(bindings)==12 and sum(len(value) for value in bindings.values())==27
    references=catalog._source_anatomy_references()['ra.mri-sella']
    assert len(references)==7 and {r['family'] for r in references}==set(manifest['regions'])
    model=next(m for m in Curriculum().node('rad.5.sella')['lesson_media'] if m.get('renderer')=='radiology-anatomy')
    assert model['props']['source_references']==bindings['rad.5.sella']==references
    for reference in references:
        assert reference['atlas']=='bp3d-sella-4.3' and reference['manifest_sha256']==sha(raw)
        assert reference['initial_layer']=='source-surfaces' and reference['initial_cropped'] is False
        ids={manifest['parts'][p['id']]['source_element_id'] for p in manifest['regions'][reference['family']]['parts']}
        assert 'FJ3483' not in ids
        assert not {'FJ1796','FJ3848'}.issubset(ids) and not {'FJ1682','FJ4993'}.issubset(ids)
        assert not (ids.intersection({'FJ7503','FJ7503M'}) and ids.intersection({'FJ7505','FJ7505M'}))
    database=str(tmp_path/'reader.db')
    monkeypatch.setattr(server,'learner',LearnerStore(database))
    monkeypatch.setattr(server,'wiki',WikiService(database))
    monkeypatch.setattr(server,'BACKUP_DIR',str(tmp_path/'backups'))
    monkeypatch.setattr(server,'_maintenance_loop',lambda *_args:None)
    monkeypatch.setenv(server.ACCESS_USERNAME_ENV,'reader');monkeypatch.setenv(server.ACCESS_PASSWORD_ENV,'test-only-secret')
    monkeypatch.delenv('VERCEL',raising=False)
    with TestClient(server.app) as client:
        auth=('reader','test-only-secret')
        response=client.get('/api/radiology/modules/ra.mri-sella',auth=auth)
        assert response.status_code==200
        assert response.json()['radiology_reference']['source_anatomy_references']==references
        delivered=client.get('/app/anatomy/bp3d-sella-4.3/manifest.json',auth=auth)
        assert delivered.status_code==200 and delivered.content==raw
        notice=client.get('/app/anatomy/bp3d-sella-4.3/ATTRIBUTION.md',auth=auth)
        assert notice.status_code==200 and notice.content==(ATLAS/'ATTRIBUTION.md').read_bytes()
        assert 'CC BY-SA2.1 Japan' in notice.text and 'Copyright 2008' in notice.text
        for part in manifest['parts'].values():
            encoded=(ROOT/'web'/part['file'].removeprefix('/app/')).read_bytes()
            mesh=client.get(part['file'],auth=auth)
            assert mesh.status_code==200 and mesh.content==gzip.decompress(encoded)
            assert sha(mesh.content)==part['decoded_sha256']
        held='/app/anatomy/bp3d-sella-4.3/bp3d-sella-4.3-fj3483.bin.gz'
        assert client.get(held,auth=auth).status_code==404
        monkeypatch.setenv('VERCEL','1')
        for part in manifest['parts'].values():
            response=client.get(part['file'],auth=auth,follow_redirects=False)
            assert response.status_code==307
            assert response.headers['location']=='/source-media'+part['file'].removeprefix('/app')
        assert client.get('/app/anatomy/bp3d-sella-4.3/ATTRIBUTION.md',auth=auth).content==notice.content
