"""Native studies reach the reader/lesson without fabricated meshes or diagnoses."""
import copy
import json
from pathlib import Path
import subprocess
from unittest.mock import patch

import pytest

from primer.curriculum import Curriculum, _validate_lesson_media
from primer import radiology_catalog as catalog
from primer.source_study import validate_study_references
from tools.check_static_source_study_inventory import inventory

ROOT = Path(__file__).resolve().parents[1]


def registry():
    return json.loads((ROOT / 'data/radiology/source-study-references.json').read_text())


def test_complete_native_study_reaches_both_surfaces_without_mesh_registration():
    curr = Curriculum()
    node = curr.node('rad.5.bladder-virads')
    ref = catalog.detail(curr, catalog.resolve('ra.mri-bladder'))['radiology_reference']
    row = ref['source_study_references'][0]
    media = next(m for m in node['lesson_media'] if m['kind'] == 'source-studies')
    assert media['investigation_ids'] == ['ra.mri-bladder']
    _validate_lesson_media(node)
    assert row == registry()['ra.mri-bladder'][0]
    assert (row['source_series'], row['source_frames'], row['source_pixel_samples']) == (22, 1359, 107937792)
    assert all((s['atlas'].startswith('hra-bladder-') and not s.get('source_volume'))
               or (s['atlas'].startswith('fedbca-') and s['source_volume']['src'].startswith('/app/anatomy/'+s['atlas']+'/'))
               for s in ref['source_anatomy_references'])  # No registration to this TCIA study is invented.
    assert row['reference_only'] and not row['clinical_approval'] and not row['anatomical_approval']
    assert row['structure_ids'] == row['requirement_coverage'] == []
    assert inventory() == json.loads((ROOT / 'data/radiology/radiology-static-source-studies.json').read_text())


@pytest.mark.parametrize('change', ['path', 'identity', 'hash', 'count', 'series', 'frames', 'samples',
                                    'licence', 'approval', 'coverage', 'registration', 'patient', 'study', 'modality', 'unknown', 'duplicate'])
def test_invalid_or_incomplete_study_is_rejected(change):
    data = registry(); row = data['ra.mri-bladder'][0]
    if change == 'path': row['src'] = '/app/studies/tcga-dk-aa6p/../../app.js'
    elif change == 'identity': row['id'] = '../other'
    elif change == 'hash': row['files']['mri-reference.html']['sha256'] = '0' * 64
    elif change == 'count': row['files']['mri-reference.html']['bytes'] += 1
    elif change == 'series': row['series_transport'].pop()
    elif change == 'frames': row['source_frames'] -= 1
    elif change == 'samples': row['source_pixel_samples'] -= 1
    elif change == 'licence': row['license'] = 'CC BY-NC 3.0'
    elif change == 'approval': row['anatomical_approval'] = True
    elif change == 'coverage': row['structure_ids'] = ['bladder-wall']
    elif change == 'registration': row['source_context']['current_patient_registered'] = True
    elif change == 'patient': row['source_context']['patient_id'] = 'Another-case'
    elif change == 'study': row['source_context']['study_instance_uid'] = '1.2.3'
    elif change == 'modality': row['modality'] = 'CT'
    elif change == 'unknown': data['ra.mri-prostate'] = data.pop('ra.mri-bladder')
    else: data['ra.mri-bladder'].append(copy.deepcopy(row))
    with pytest.raises(ValueError): validate_study_references(data, {'ra.mri-bladder'}, ROOT / 'web')


def test_study_media_cannot_be_attached_to_another_lesson():
    node = copy.deepcopy(Curriculum().node('rad.5.bladder-virads'))
    node['id'] = 'rad.5.prostate-mri'
    with pytest.raises(ValueError, match='cross-lesson'): _validate_lesson_media(node)


def test_hosted_metadata_is_bound_to_all_excluded_files(monkeypatch):
    original = Path.is_file
    with patch.object(Path, 'is_file', lambda p: False if 'studies' in p.parts else original(p)):
        monkeypatch.delenv('VERCEL', raising=False)
        with pytest.raises(ValueError, match='missing'):
            validate_study_references(registry(), {'ra.mri-bladder'}, ROOT / 'web')
        monkeypatch.setenv('VERCEL', '1')
        validate_study_references(registry(), {'ra.mri-bladder'}, ROOT / 'web')
        data = registry(); data['ra.mri-bladder'][0]['files']['mri-reference.js']['sha256'] = '0' * 64
        with pytest.raises(ValueError, match='inventory'):
            validate_study_references(data, {'ra.mri-bladder'}, ROOT / 'web')


def test_guarded_study_route_delivers_only_registered_files(monkeypatch, tmp_path):
    monkeypatch.setenv('PRIMER_DB', str(tmp_path / 'reader.db'))
    from fastapi.testclient import TestClient
    import primer.server as server
    monkeypatch.setenv(server.ACCESS_USERNAME_ENV, 'reader')
    monkeypatch.setenv(server.ACCESS_PASSWORD_ENV, 'test-password')
    with TestClient(server.app) as client:
        path = '/app/studies/tcga-dk-aa6p/mri-reference.html'
        assert client.get(path).status_code == 401
        assert client.get(path, auth=('reader', 'test-password')).status_code == 200
        response = client.get('/app/studies/tcga-dk-aa6p/series-0013.bin.gz', auth=('reader', 'test-password'))
        assert response.status_code == 200 and 'content-encoding' not in response.headers
        assert response.headers['content-type'] == 'application/octet-stream'
        assert response.content == (ROOT / 'web/studies/tcga-dk-aa6p/series-0013.bin.gz').read_bytes()
        revalidated = client.get('/app/studies/tcga-dk-aa6p/series-0013.bin.gz', auth=('reader', 'test-password'),
                                 headers={'If-None-Match': response.headers['etag']})
        assert revalidated.status_code == 200 and revalidated.content == response.content
        assert 'content-encoding' not in revalidated.headers
        monkeypatch.setenv('VERCEL', '1')
        response = client.get(path, auth=('reader', 'test-password'), follow_redirects=False)
        assert response.status_code == 307 and response.headers['location'] == '/source-media/studies/tcga-dk-aa6p/mri-reference.html'
        assert client.get('/app/studies/tcga-dk-aa6p/unregistered.bin.gz', auth=('reader', 'test-password')).status_code == 404
        assert client.get('/healthz').json()['source_study_metadata_validated']


def test_study_gallery_loads_its_native_case_and_never_requests_a_mesh():
    script = r'''
const assert=require('node:assert/strict');
global.window={addEventListener(){}};global.document={addEventListener(){}};
const {lessonSourceGallery,sourceStudyReference}=require('./web/app.js');
class E {constructor(tag,p={},...c){this.tag=tag;Object.assign(this,p);this.children=c;}append(...c){this.children.push(...c);}}
const el=(t,p,...c)=>new E(t,p,...c); let calls=0;
const asset={title:'Original study',caption:'Separate case',src:'/app/studies/tcga-dk-aa6p/mri-reference.html',limits:'No assigned score',attribution:'TCIA',source_url:'https://doi.org/example',license:'CC BY 3.0',license_url:'https://creativecommons.org/licenses/by/3.0/'};
const card=sourceStudyReference(asset,{createElement:el,sourceLink:(title,url)=>el('a',{href:url},title)});
const link=card.children.find(x=>x.tag==='a');assert.equal(link.href,asset.src);assert.equal(link.rel,'noopener noreferrer');
const gallery=lessonSourceGallery({kind:'source-studies',title:'Study',instructions:'Native planes',investigation_ids:['ra.mri-bladder']},
 {createElement:el,createButton:(p,t)=>el('button',p,t),loadReference:async id=>{calls++;return {id,title:'Bladder MRI',radiology_reference:{source_study_references:[asset]}};},
  renderStudy:a=>{assert.equal(a,asset);return card;},renderFigure:()=>{throw Error('Study must not become a figure or mesh');},wirePictures:()=>{}});
assert.equal(calls,0);(async()=>{const b=gallery.children.find(c=>c.tag==='button');await b.onclick();assert.equal(calls,1);assert.equal(b.disabled,true);assert.equal(gallery.children.filter(c=>c.tag==='details').length,1);})().catch(e=>{console.error(e);process.exitCode=1;});
'''
    result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_vi_rads_quality_and_assessment_premises_do_not_infer_pathology():
    node = Curriculum().node('rad.5.bladder-virads')
    assert node['quiz'][2]['answer'] == '4' and node['quiz'][8]['answer'] == '3'
    assert 'independently confirmed' in node['quiz'][8]['prompt']
    assert 'pathological' in node['quiz'][2]['explain']
    assert 'histological stage' in node['quiz'][3]['answer']
    assert 'does not guarantee' in node['quiz'][6]['explain']
    assert 'without claiming inflammation' in node['quiz'][7]['answer']
    assert 'without declaring resectability' in node['quiz'][9]['answer']
    assert 'does not prove' in node['quiz'][11]['answer']
    ref = catalog.detail(Curriculum(), catalog.resolve('ra.mri-bladder'))['radiology_reference']
    assert any('optimal-quality DWI' in x['detail'] for x in ref['reporting']['checklist'])
    assert any('diverticulum' in x for x in ref['reporting']['pitfalls'])


def test_every_delivered_frame_retains_original_source_geometry_and_acquisition():
    import gzip
    import re
    folder = ROOT / 'web/studies/tcga-dk-aa6p'
    data = json.loads(re.search(r'<script id="dataset" type="application/json">(.*?)</script>', (folder / 'mri-reference.html').read_text(), re.S).group(1))
    proof = ROOT / 'docs/bladder-native-study-review/TCGA-DK-AA6P'
    count = 0
    for series in data['series']:
        native = json.loads(gzip.decompress((proof / f"series-{series['number']:04d}-review.json.gz").read_bytes()))
        originals = {f['sop_instance_uid']: f for f in native['frames']}
        assert len(originals) == len(series['frames'])
        for frame in series['frames']:
            original = originals[frame['sop']]; tags = original['source_tags']
            for new, old in [('orientation', 'image_orientation_patient'), ('position', 'image_position_patient'), ('spacing', 'pixel_spacing'), ('rows', 'rows'), ('columns', 'columns')]:
                assert frame[new] == original[old]
            for new, old in [('acquisition_matrix', 'AcquisitionMatrix'), ('acquisition_type', 'MRAcquisitionType'), ('slice_thickness', 'SliceThickness'), ('spacing_between_slices', 'SpacingBetweenSlices'), ('image_type', 'ImageType')]:
                assert frame[new] == tags[old]
            assert frame['source_pixel_int16_le_sha256'] == original['pixel_int16_le_sha256']
            count += 1
    assert count == 1359


def test_complete_study_rights_are_audited_on_both_surfaces_without_anatomy_credit():
    from tools.msk_runtime_rights import reference_images, audit_reference_image_rights
    curr = Curriculum()
    actual = reference_images(curr, catalog.catalogue(), {}, catalog.detail, catalog_section=None)
    resources = [r for r in actual['images'] if r['src'].startswith('/app/studies/tcga-dk-aa6p/')]
    assert len(resources) == 24
    for r in resources:
        assert {u['surface'] for u in r['uses']} == {'lesson:rad.5.bladder-virads', 'reporting:ra.mri-bladder'}
    evidence = json.loads((ROOT / 'data/radiology/radiology-asset-evidence.json').read_text())
    report = audit_reference_image_rights({'images': resources, 'surfaces': actual['surfaces']}, evidence, ROOT)
    assert report['rights_ready'] and report['counts']['cleared'] == 24
    for a in evidence['reference_rights_assets']:
        if a['kind'] == 'source_study_reference':
            assert a['structure_ids'] == [] and a['requirement_coverage'] == {} and a['reference_only']
