"""Reporting references are complete, direct, and separate from learner records."""
import copy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from primer import radiology


@pytest.fixture(scope='module')
def curriculum():
    from primer.curriculum import Curriculum
    return Curriculum()


def test_all_modules_have_reviewed_reporting_content_and_a_3d_companion(curriculum):
    nodes = [node for node in curriculum.nodes.values()
             if node['domain'] == 'radiology' and node['id'].startswith('rad.')]
    assert len(nodes) == 96
    model_ids = set()
    for node in nodes:
        ref = node['radiology_reference']
        guide = ref['reporting']
        radiology.validate_reporting_guide(guide)
        assert len(guide['checklist']) >= 4, node['id']
        assert len(guide['template_sections']) >= 5, node['id']
        assert len(guide['pitfalls']) >= 2, node['id']
        assert len(guide['impression_prompts']) >= 3, node['id']
        assert any(item['kind'] == 'illustration' for item in node['lesson_media'])
        assert ref['key_images'] and all(image['src'] for image in ref['key_images'])
        model = ref['spatial_model']
        assert model['scenario'] == 'radiology-reference:' + node['id']
        assert model['id'] not in model_ids
        model_ids.add(model['id'])
        for template in ref['report_templates']:
            assert not any(section['body'] == '[Observations / measurements with units / not assessed and reason].'
                           for section in template['sections']), node['id']
        if node['id'] not in ('rad.5.coronary-ct', 'rad.5.prostate-mri'):
            template = ref['report_templates'][0]
            assert template['sections'][4:-2] == guide['template_sections']
    assert len({node['radiology_reference']['spatial_model']['family'] for node in nodes}) >= 16


def test_reference_merge_preserves_flagship_reports_and_blank_patient_fields(curriculum):
    originals = json.loads((ROOT / 'data/radiology/flagship-templates.json').read_text())
    for identifier, original in originals.items():
        report = curriculum.node(identifier)['radiology_reference']['report_templates'][0]
        assert report['sections'] == original['report_templates'][0]['sections']
        assert '[ ]' in next(s['body'] for s in report['sections'] if s['heading'] == 'IMPRESSION')


def test_invalid_reference_content_is_rejected(curriculum):
    guide = curriculum.node('rad.5.coronary-ct')['radiology_reference']['reporting']
    invalid = copy.deepcopy(guide)
    invalid['sources'] = []
    with pytest.raises(ValueError, match='sources'):
        radiology.validate_reporting_guide(invalid)
    invalid = copy.deepcopy(guide)
    invalid['template_sections'].append(copy.deepcopy(invalid['template_sections'][0]))
    with pytest.raises(ValueError, match='unique'):
        radiology.validate_reporting_guide(invalid)
    invalid = copy.deepcopy(guide)
    invalid['classification'] = {'name': 'Unversioned'}
    with pytest.raises(ValueError, match='version and scope'):
        radiology.validate_reporting_guide(invalid)


def test_reporting_endpoints_are_direct_and_do_not_fetch_wiki_or_change_progress(curriculum, tmp_path, monkeypatch):
    monkeypatch.setenv('PRIMER_DB', str(tmp_path / 'reporting.db'))
    from fastapi.testclient import TestClient
    from primer.learner import LearnerStore
    import primer.server as server
    monkeypatch.setattr(server, 'curr', curriculum)
    store = LearnerStore(str(tmp_path / 'reader.db'))
    monkeypatch.setattr(server, 'learner', store)
    def unexpected(*args, **kwargs):
        raise AssertionError('Reporting reference must not invoke learning or external Wikipedia services')
    monkeypatch.setattr(server.wiki, 'get_summary', unexpected)
    monkeypatch.setattr(store, 'mastery_map', unexpected)
    monkeypatch.setattr(store, 'gate_map', unexpected)
    client = TestClient(server.app)
    try:
        index = client.get('/api/radiology/modules')
        detail = client.get('/api/radiology/modules/rad.5.prostate-mri')
        assert index.status_code == detail.status_code == 200
        assert index.json()['count'] == 136
        assert len(index.json()['modules']) == 136
        assert 'report_templates' not in index.text
        assert 'key_images' not in index.text
        body = detail.json()
        assert set(body) == {'id', 'module_id', 'title', 'section', 'topic', 'modality', 'source_titles', 'goal', 'radiology_reference', 'lesson_media'}
        assert body['radiology_reference']['spatial_model']['scenario'] == 'radiology-reference:rad.5.prostate-mri'
        assert 'quiz' not in body and 'mastery' not in body and 'unlocked' not in body
        assert client.get('/api/radiology/modules/math.0.counting').status_code == 404
        assert client.get('/api/radiology/modules/rad.missing').status_code == 404
    finally:
        client.close()


def test_reporting_endpoints_keep_the_existing_hosted_access_gate(curriculum, tmp_path, monkeypatch):
    monkeypatch.setenv('PRIMER_DB', str(tmp_path / 'hosted.db'))
    from fastapi.testclient import TestClient
    import primer.server as server
    monkeypatch.setattr(server, 'curr', curriculum)
    monkeypatch.setenv('VERCEL', '1')
    monkeypatch.setenv(server.ACCESS_USERNAME_ENV, 'reader')
    monkeypatch.setenv(server.ACCESS_PASSWORD_ENV, 'secret')
    client = TestClient(server.app)
    try:
        for path in ('/api/radiology/modules', '/api/radiology/modules/rad.5.coronary-ct'):
            assert client.get(path).status_code == 401
            assert client.get(path, auth=('reader', 'secret')).status_code == 200
    finally:
        client.close()
