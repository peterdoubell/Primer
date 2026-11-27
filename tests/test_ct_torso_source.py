"""Check emitted clinical source bytes, overlapping mask memberships and report/lesson scope."""
import gzip
import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient
import numpy as np
from primer.server import app
from primer.curriculum import Curriculum
from primer.reporting_bridge import descriptor_variant
from primer.ct_torso_reference import ATLAS, EXAMS, references
from tools.ct_torso_compatibility import before_torso_bytes

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT/'web/anatomy'/ATLAS


def sha(data):
    return hashlib.sha256(data).hexdigest()


def test_full_case_memberships_and_file_inventory():
    manifest=json.loads((DIR/'manifest.json').read_bytes())
    inputs=json.loads((ROOT/'docs/ct-torso-s0028/acquisition.json').read_bytes())
    checked=json.loads((ROOT/'docs/ct-torso-s0028/source-comparison.json').read_bytes())
    assert manifest['encoding']=='int16-le+two-labels'
    labels=manifest['labels']; assert len(labels)==len(inputs['labels'])==117
    assert sum(bool(r['voxelCount']) for r in labels)==checked['nonemptyMasks']==109
    assert sum(r.get('touchesGridEdge',False) for r in labels)==20
    assert sum(r['mesh']['triangles'] for r in labels if r.get('mesh'))==checked['verifiedTriangles']==2368866
    files=json.loads((DIR/'delivery.json').read_bytes())['files']
    assert set(files)=={p.name for p in DIR.iterdir() if p.is_file() and p.name!='delivery.json'}
    for name,record in files.items():
        raw=(DIR/name).read_bytes()
        assert (len(raw),sha(raw))==(record['bytes'],record['sha256'])
    counts=np.zeros(256,dtype=np.int64)
    shared=total=0
    for brick in manifest['bricks']:
        data=gzip.decompress((DIR/brick['file']).read_bytes());assert sha(data)==brick['decodedSHA256']
        cells=np.frombuffer(data,dtype='u1').reshape(-1,4)
        total+=len(cells); shared+=np.count_nonzero(cells[:,3])
        counts+=np.bincount(cells[:,2:].ravel(),minlength=256)
    assert total==checked['storedSamples']==35223994
    assert shared==manifest['overlapVoxels']==checked['sharedVoxels']==5676
    assert all(counts[l['code']]==l['voxelCount'] for l in labels)
    assert len(checked['probes'])==109 and checked['overlapProbe']['storedCT']==51


def test_both_descriptors_have_exact_report_areas_and_owned_lesson_entries():
    curriculum=Curriculum()
    with TestClient(app) as client:
        for lesson,exam in EXAMS.items():
            published=descriptor_variant(exam)
            assert published['guide_id']==lesson
            ref=client.get('/api/radiology/modules/'+exam).json()['radiology_reference']
            card,=[x for x in ref['source_native_inspectors'] if x['id']==ATLAS]
            assert card==references()[exam][0]
            assert [x['row'] for x in card['report_area_links']]==[x['anatomy_id'] for x in published['sections']]
            assert [x['name'] for x in card['report_area_links']]==[x['label'] for x in published['sections']]
            assert not card['clinical_approval'] and not card['current_patient_registration']
            assert not card['structure_ids'] and not card['requirement_coverage']
            assert any(exam in m.get('investigation_ids',[]) and m['kind']=='source-native-inspectors'
                       for m in curriculum.nodes[lesson]['lesson_media'])
            assert client.get(card['src']).status_code==200
            for link in card['report_area_links']:
                assert link['src']==card['src']+'&row='+link['row']
        areas={r['row']:r for r in references()['ct.chest-abdomen-pelvis'][0]['report_area_links']}
        assert areas['reproductive-organs']['present']==0 and areas['reproductive-organs']['empty']==1
        assert areas['target-lesions']['present']==areas['pleura-and-pericardium']['present']==0


def test_hosted_redirects_original_bricks_and_rejects_unknown_names(monkeypatch):
    auth=('torso-fixture','fixture-only')
    monkeypatch.setenv('PRIMER_ACCESS_USERNAME',auth[0]);monkeypatch.setenv('PRIMER_ACCESS_PASSWORD',auth[1])
    prefix='/app/anatomy/ct-torso-s0028/'
    with TestClient(app) as client:
        assert client.get(prefix+'index.html').status_code==401
        assert "frame-ancestors 'self';" in client.head(prefix+'index.html',auth=auth).headers['content-security-policy']
        monkeypatch.setenv('VERCEL','1')
        for file in ['liver.mesh.gz','brick-0-0-0.gz']:
            res=client.head(prefix+file,auth=auth,follow_redirects=False)
            assert res.status_code==307 and res.headers['location']=='/source-media/anatomy/ct-torso-s0028/'+file
        assert client.head(prefix+'unlisted.gz',auth=auth).status_code==404


def test_source_integration_has_an_exact_inverse_for_every_shared_file():
    from tools.report_working_draft_compatibility import before_working_draft_bytes
    proof=json.loads((ROOT/'docs/ct-torso-s0028/runtime-inverse.json').read_bytes())
    for name,row in proof.items():
        if name=='lessons': continue
        raw=before_working_draft_bytes(name,(ROOT/name).read_bytes())
        assert sha(raw)==row['after'] and sha(before_torso_bytes(name,raw))==row['before']
        assert before_torso_bytes(name,raw+b'\n')==raw+b'\n'
