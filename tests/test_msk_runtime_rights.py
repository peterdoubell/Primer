"""Displayed reference figures cannot disappear from commercial-readiness review."""
import copy
import hashlib
from pathlib import Path

import pytest

from tools.msk_runtime_rights import reference_images, audit_reference_image_rights


@pytest.fixture
def local_case(tmp_path):
    path = tmp_path / 'web/reference-media/example.jpg'
    path.parent.mkdir(parents=True)
    path.write_bytes(b'synthetic image fixture; no real clinical claim')
    (tmp_path / 'rights.md').write_text('Synthetic permission evidence fixture')
    inventory = {'surfaces': ['reporting:ra.example'], 'images': [{
        'src': '/app/reference-media/example.jpg', 'uses': [{'surface': 'reporting:ra.example'}]}]}
    asset = {'id': 'fixture', 'local_path': 'web/reference-media/example.jpg',
             'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
             'source': {'url': 'https://example.test/source', 'license': {
                 'url': 'https://example.test/license', 'commercial_use': True,
                 'redistribution': True, 'review_status': 'verified', 'attribution': 'Synthetic author',
                 'evidence_path': 'rights.md'}},
             'anatomical_review': {'status': 'pending'}, 'visual_review': {'status': 'pending'}}
    return inventory, {'assets': [asset]}, tmp_path


def test_rights_can_be_cleared_without_claiming_anatomical_approval(local_case):
    inventory, evidence, root = local_case
    result = audit_reference_image_rights(inventory, evidence, root)
    assert result['rights_ready']
    assert result['counts'] == {'images': 1, 'cleared': 1, 'unverified': 0}
    assert evidence['assets'][0]['anatomical_review']['status'] == 'pending'


@pytest.mark.parametrize('change', ['unregistered', 'different_bytes', 'no_commercial',
                                    'no_redistribution', 'no_review', 'missing_proof', 'stale_proof'])
def test_runtime_rights_require_current_byte_bound_evidence(local_case, change):
    inventory, evidence, root = local_case
    asset = evidence['assets'][0]
    license_info = asset['source']['license']
    if change == 'unregistered': evidence['assets'] = []
    if change == 'different_bytes': (root / asset['local_path']).write_bytes(b'changed')
    if change == 'no_commercial': license_info['commercial_use'] = False
    if change == 'no_redistribution': license_info['redistribution'] = False
    if change == 'no_review': license_info['review_status'] = 'unverified'
    if change == 'missing_proof': (root / 'rights.md').unlink()
    if change == 'stale_proof': license_info['evidence_sha256'] = '0' * 64
    result = audit_reference_image_rights(inventory, evidence, root)
    assert not result['rights_ready']
    assert result['counts']['unverified'] == 1


def test_uncounted_and_unpinned_remote_images_block_readiness(local_case):
    inventory, evidence, root = local_case
    assert not audit_reference_image_rights(None, evidence, root)['rights_ready']
    inventory['images'].append({'src': 'https://publisher.test/another.jpg', 'uses': []})
    result = audit_reference_image_rights(inventory, evidence, root)
    assert not result['rights_ready']
    assert result['counts'] == {'images': 2, 'cleared': 1, 'unverified': 1}
    assert 'no_byte_bound_runtime_rights_record' in result['images'][1]['issues']


def test_local_runtime_path_cannot_leave_the_web_directory(local_case):
    inventory, evidence, root = local_case
    inventory['images'][0]['src'] = '/app/../../private.jpg'
    with pytest.raises(ValueError, match='leaves web'):
        audit_reference_image_rights(inventory, evidence, root)


def test_inventory_comes_from_rendered_references_and_includes_declared_extra_scope():
    shared = {'id': 'shared', 'src': 'https://publisher.test/shared.jpg',
              'source_url': 'https://publisher.test/article'}
    catalog = {'investigations': [
        {'id': 'ra.msk', 'section': 'Musculoskeletal', 'module_id': 'msk'},
        {'id': 'ra.extra', 'section': 'Pediatrics', 'module_id': 'extra'},
        {'id': 'ra.outside', 'section': 'Chest', 'module_id': 'outside'}]}
    requirements = {'additional_scope': [{'investigation_id': 'ra.extra', 'module_id': 'extra'}]}
    class Curriculum:
        def node(self, identifier):
            return {'radiology_reference': {'key_images': [shared]}}
    def detail(curriculum, item):
        return {'radiology_reference': {'key_images': [shared], 'structure_atlas': [{
            'id': item['id'], 'src': '/app/reference-media/' + item['id'] + '.jpg'}]}}
    result = reference_images(Curriculum(), catalog, requirements, detail)
    assert result['surfaces'] == ['reporting:ra.extra', 'reporting:ra.msk', 'lesson:extra', 'lesson:msk']
    assert len(result['images']) == 3
    source = next(item for item in result['images'] if item['src'] == shared['src'])
    assert len(source['uses']) == 4
    assert not any('outside' in str(item) for item in result['images'])
    requirements['additional_scope'][0]['investigation_id'] = 'ra.missing'
    with pytest.raises(ValueError, match='missing from catalogue'):
        reference_images(Curriculum(), catalog, requirements, detail)
