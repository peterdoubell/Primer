"""Faithful source regions and tissue images cannot imply every bladder layer."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import struct

import pytest

from primer.curriculum import Curriculum, _validate_lesson_media
from primer.radiology_catalog import detail, resolve, _structure_atlases
from primer.module_media import source_model_bindings
from tools.check_msk_fidelity import audit, inspect_binding, requirements_for, validate_reporting_snapshots
from tools.check_radiology_fidelity import digest
from tools.anatomy_sources.package_hra_bladder import source

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / 'docs/bladder-anatomy-fidelity-review'


def inventory():
    data = json.loads((ROOT / 'data/radiology/non-msk-structure-requirements.json').read_text())
    row = next(i for i in data['investigations'] if i['investigation_id'] == 'ra.mri-bladder')
    return {**data, 'investigations': [row], 'scope': {'catalog_investigation_ids': ['ra.mri-bladder']}}, row


def test_report_bound_inventory_retains_all_unfulfilled_structure_requirements():
    data, row = inventory(); ref = detail(Curriculum(), resolve('ra.mri-bladder'))['radiology_reference']
    validate_reporting_snapshots(data, {'ra.mri-bladder': ref['reporting']})
    assert row['source_contract_sha256'] == digest({k: ref.get(k) for k in ['reporting', 'report_templates', 'walkthrough', 'reading']})
    leaves = {r['id']: r for r in requirements_for(row)}
    assert len(row['structures']) == 56 and len(leaves) == 323
    assert {r['checklist_index'] for s in row['structures'] for r in s['report_refs']} == set(range(5))
    for key in ['histology.muscularis_mucosae.tissue_interface', 'histology.serosa.actual_sample_extent',
                'uvj.left.intramural_ureter', 'nodes.right_common_iliac.whole_margin',
                'upper_tract.left.unopacified_or_unacquired_segments', 'lesion.muscle_invasion.deepest_interface']:
        assert 'bladder.' + key in leaves
    result = audit(data, {'assets': [{'id': 'whole-bladder', 'kind': 'model', 'investigation_ids': ['ra.mri-bladder'], 'structure_ids': ['bladder.detrusor']}]}, expected_catalog_ids={'ra.mri-bladder'})
    assert result['representation_requirements'] == 969 and result['counts']['missing'] == 969


def test_histology_is_distinct_from_mri_and_processed_masks():
    _, row = inventory(); leaves = {r['id']: r for r in requirements_for(row)}
    asset = {'kind': 'clinical_image', 'modality': 'Histology', 'source_context': {'setting': 'ex_vivo'}}
    assert inspect_binding(asset, leaves['bladder.histology.urothelium.actual_sample_extent']) == []
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(asset, leaves['bladder.detrusor.source_resolved_extent'])
    figure = _structure_atlases()['ra.mri-bladder'][0]
    assert figure['modality'] == 'Histology' and figure['clinical_panels'] == ['a']
    assert figure['source_context']['panel_types'] == {'a': 'Histology', 'b': 'Segmentation mask', 'c': 'Segmentation mask', 'd': 'Masked histology'}
    assert {p for a in figure['ancillary_panels'] for p in a['panels']} == {'b', 'c', 'd'}
    assert hashlib.sha256((ROOT / 'web' / figure['src'].removeprefix('/app/')).read_bytes()).hexdigest() == figure['sha256']
    assert not figure['source_context']['source_native_registration_verified']


@pytest.mark.parametrize('sex,total,contacts,unmatched', [('female', 41290, 82, 768), ('male', 10073, 0, 149)])
def test_all_original_meshes_normals_indices_and_source_defects_are_preserved(sex, total, contacts, unmatched, tmp_path):
    # The original complete GLB is retained as compressed immutable evidence.
    name = 'VH_' + sex[0].upper() + '_Urinary_Bladder.glb'
    raw = gzip.decompress((PROOF / (sex + '-original.glb.gz')).read_bytes())
    (tmp_path / name).write_bytes(raw)
    (tmp_path / 'crosswalk.csv').write_bytes((PROOF / (sex + '-crosswalk.csv')).read_bytes())
    review, originals = source(tmp_path, sex)
    manifest = json.loads((ROOT / 'web/anatomy' / ('hra-bladder-' + sex + '-v1.1') / 'manifest.json').read_text())
    assert len(manifest['parts']) == 6 and manifest['total_triangles'] == total
    assert manifest['coordinate_system']['display_basis'] == 'native-gltf-y-up'
    assert not manifest['clinical_approval'] and not manifest['complete_reporting_anatomy_approved']
    assert sum(not p['canonical_uri_metadata_match'] for p in manifest['parts'].values()) == 2
    import numpy as np
    for original in originals:
        part = next(p for p in manifest['parts'].values() if p['source_node_name'] == original['id'])
        payload = (ROOT / 'web' / part['file'].removeprefix('/app/')).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == part['sha256']
        decoded = gzip.decompress(payload)
        assert struct.unpack('<4sII', decoded[:12]) == (b'BP3D', part['vertices'], part['triangles'] * 3)
        n = part['vertices']; m = part['triangles'] * 3
        assert np.array_equal(np.frombuffer(decoded, '<f4', count=n*3, offset=12).reshape(-1, 3), original['vertices'])
        assert np.array_equal(np.frombuffer(decoded, '<f4', count=n*3, offset=12+n*12).reshape(-1, 3), original['normals'])
        assert np.array_equal(np.frombuffer(decoded, '<u4', count=m, offset=12+n*24), original['source_indices'])
    contact = json.loads(gzip.decompress((PROOF / (sex + '-complete-contact-review.json.gz')).read_bytes()))
    assert contact['triangle_contact_audit']['unexpected_contact_count'] == contacts
    assert contact['preparation']['original_source_triangles'] == total
    assert not contact['source_faces_and_coordinates_changed']
    boundary = json.loads((PROOF / (sex + '-boundary-review.json')).read_text())
    assert boundary['unmatched_boundary_edges'] == unmatched and not boundary['source_meshes_modified_or_fused']


def test_every_available_source_model_reaches_its_matching_lesson_with_exact_context():
    curr = Curriculum(); bindings = source_model_bindings()
    proof = json.loads((PROOF / 'source-model-lesson-delivery-review.json').read_text())
    assert len(bindings) == proof['matching_lessons'] == 11 and proof['source_references'] == 16
    fields = ['goal','learning_outcomes','lesson','reference','radiology_reference','visual_spec','lesson_media','model_family','model_context','practice','quiz','kid_text']
    for row in proof['modules']:
        node = curr.node(row['module_id']); _validate_lesson_media(node)
        model = next(m for m in node['lesson_media'] if m.get('renderer') == 'radiology-anatomy')
        assert model['props']['source_references'] == bindings[node['id']]
        historical_props = copy.deepcopy(model['props'])
        historical_props['source_references'] = [s for s in historical_props['source_references'] if not s['atlas'].startswith('fedbca-')]
        historical = copy.deepcopy({k: node.get(k) for k in fields})
        next(m for m in historical['lesson_media'] if m.get('renderer') == 'radiology-anatomy')['props'] = historical_props
        assert digest(historical_props) == row['model_props_sha256']
        assert digest(historical) == row['complete_current_module_contract_sha256']
        assert digest(historical_props['source_references']) == row['source_references_sha256']
        assert not row['clinical_or_complete_anatomical_approval']


def test_source_model_props_cannot_borrow_another_case_or_invent_registration():
    curr = Curriculum(); node = copy.deepcopy(curr.node('rad.5.bladder-virads'))
    model = next(m for m in node['lesson_media'] if m.get('renderer') == 'radiology-anatomy')
    model['props']['source_references'][0]['population_note'] = 'Registered to current MRI patient'
    with pytest.raises(ValueError, match='cross-lesson'): _validate_lesson_media(node)
    model['props']['source_references'] = source_model_bindings()['rad.5.prostate-mri']
    with pytest.raises(ValueError, match='cross-lesson'): _validate_lesson_media(node)
