"""Original adrenal candidates retain source identity, every face and unresolved fidelity."""
import gzip
import hashlib
import json
from pathlib import Path

from tools.anatomy_sources.acquire_bodyparts_adrenal_upstream import TARGETS
from tools.anatomy_sources.acquire_bodyparts_pancreatic_upstream import select

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/bodyparts-adrenal-source-review'


def test_eight_original_adrenal_elements_match_version_and_mapping_excerpts():
    acquisition = json.loads((REVIEW / 'acquisition.json').read_text())
    mapping = json.loads((REVIEW / 'selected-original-mapping-rows.json').read_text())
    rows = mapping['obj2FMA-4.3.html']
    html = '<table>' + ''.join('<tr>' + ''.join('<td>' + v + '</td>' for v in r) + '</tr>'
                             for r in [rows['header'], *rows['rows']]) + '</table>'
    groups, selected = select((REVIEW / 'selected-version-manifest.txt').read_text(), html, TARGETS)
    assert groups == acquisition['source_groups']
    assert set(selected) == {'FJ3129', 'FJ3130', 'FJ3467', 'FJ3472', 'FJ3480', 'FJ3580', 'FJ3584', 'FJ3586'}
    assert sum(r['faces'] for r in acquisition['objects']) == 10486
    assert acquisition['archive_crc_verified'] is True
    assert acquisition['upstream_default_license'] == 'CC BY-SA 2.1 Japan'
    assert acquisition['archive_40_cc_by_40_grant_reused_for_upstream_meshes'] is False
    assert acquisition['source_geometry_altered'] is False and acquisition['runtime_promoted'] is False
    assert all(r['original_obj_header']['File ID'] == r['id'] for r in acquisition['objects'])


def test_all_original_faces_and_unrepaired_components_are_preserved():
    geometry = json.loads((REVIEW / 'original-obj-geometry-review.json').read_text())
    assert geometry['all_expected_original_objects_inspected'] is True
    assert geometry['expected_original_object_count'] == 8
    assert sum(r['triangles'] for r in geometry['records']) == 10486
    for r in geometry['records']:
        assert r['zero_area_triangles'] == 0
        assert r['exact_position_analysis_topology']['boundary_edges'] == 0
        assert r['exact_position_analysis_topology']['nonmanifold_edges'] == 0
        assert r['source_positions_faces_or_normals_changed'] is False
    artery = next(r for r in geometry['records'] if r['id'] == 'FJ3467')
    assert [c['faces'] for c in artery['exact_position_analysis_topology']['components']] == [952, 2]
    sheet = json.loads((REVIEW / 'coincident-source-component.json').read_text())
    assert sheet['source_sha256'] == artery['source_sha256']
    assert sheet['source_face_indices'] == [462, 463]
    a, b = sheet['original_vertex_positions_mm']
    assert b == [a[1], a[0], a[2]]
    assert sheet['no_shared_exact_positions_with_other_source_faces'] is True
    assert sheet['component_pruned_or_repaired'] is False
    assert geometry['clinical_approval'] is False and geometry['runtime_promoted'] is False
    figures = json.loads((REVIEW / 'source-figure-review.json').read_text())
    assert len(figures['figures']) == 2
    for figure in figures['figures']:
        assert sum(p['original_triangle_count'] for p in figure['panels']) == 10486
        assert hashlib.sha256((REVIEW / figure['file']).read_bytes()).hexdigest() == figure['sha256']


def test_complete_contacts_and_every_location_retain_original_face_identity():
    summary = json.loads((REVIEW / 'complete-contact-summary.json').read_text())
    packed = (REVIEW / summary['file']).read_bytes(); payload = gzip.decompress(packed)
    assert hashlib.sha256(packed).hexdigest() == summary['compressed_sha256']
    assert hashlib.sha256(payload).hexdigest() == summary['uncompressed_sha256']
    evidence = json.loads(payload); contacts = evidence['triangle_contact_audit']
    assert summary['source_triangles'] == summary['testable_triangles'] == 10486
    assert summary['contact_count'] == len(contacts['unexpected_contacts']) == 724
    assert summary['within_object_contact_count'] == 1 and summary['between_object_contact_count'] == 723
    assert contacts['conservative_aabb_candidate_pairs'] == 96505
    assert contacts['pairs_explicitly_intersection_tested'] + contacts['noncoplanar_shared_edge_pairs_resolved_geometrically'] == 96505
    within = next(r for r in contacts['unexpected_contacts'] if r['same_source_part'])
    assert within['shared_vertex_count'] == 3
    assert within['original_source_faces'] == [{'source_part': 'FJ3467', 'source_face_index': 462},
                                              {'source_part': 'FJ3467', 'source_face_index': 463}]
    locations = json.loads((REVIEW / 'contact-location-review.json').read_text())
    figure = locations['figures'][0]
    assert figure['panels'][0]['contact_pairs'] == 724
    expected = {(f['source_part'], f['source_face_index']) for c in contacts['unexpected_contacts'] for f in c['original_source_faces']}
    observed = {(r['element_id'], i) for r in figure['panels'][0]['original_affected_faces'] for i in r['face_indices']}
    assert observed == expected
    assert figure['contact_evidence_sha256'] == summary['uncompressed_sha256']
    assert hashlib.sha256((REVIEW / figure['file']).read_bytes()).hexdigest() == figure['sha256']
    assert evidence['clinical_approval'] is False and locations['runtime_promoted'] is False
