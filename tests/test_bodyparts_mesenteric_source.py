"""Source vessel groups preserve open/disconnected geometry and never approve full perfusion anatomy."""
import gzip
import hashlib
import json
from pathlib import Path
import pytest
from tools.anatomy_sources.acquire_bodyparts_mesenteric_upstream import TARGETS, REQUESTED_TARGETS, SOURCE_HOLDS
from tools.anatomy_sources.acquire_bodyparts_pancreatic_upstream import select

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/bodyparts-mesenteric-source-review'


def read(name):
    return json.loads((REVIEW / name).read_text())


def test_complete_version_manifest_and_all_original_groups_preserve_missing_branch():
    acquisition = read('acquisition.json')
    rows = read('selected-original-mapping-rows.json')['obj2FMA-4.3.html']
    html = '<table>' + ''.join('<tr>' + ''.join('<td>' + v + '</td>' for v in row) + '</tr>' for row in [rows['header'], *rows['rows']]) + '</table>'
    manifest = (REVIEW / 'complete-version-manifest.txt').read_bytes()
    assert hashlib.sha256(manifest).hexdigest() == acquisition['source_metadata_sha256']['FMA2Obj-4.3.txt']
    groups, objects = select(manifest.decode(), html, TARGETS)
    assert len(TARGETS) == 33 and len(REQUESTED_TARGETS) == 34 and len(objects) == 38
    assert groups == acquisition['source_groups']
    assert SOURCE_HOLDS == read('source-selection-holds.json')['source_holds']
    with pytest.raises(ValueError, match='absent from version manifest'):
        select(manifest.decode(), html, REQUESTED_TARGETS)
    assert groups['FMA66358'] == ['FJ3644'] and 'FJ3644' in groups['FMA14749']
    assert acquisition['archive_crc_verified'] and sum(r['faces'] for r in acquisition['objects']) == 26700
    assert acquisition['upstream_default_license'] == 'CC BY-SA 2.1 Japan'
    assert not acquisition['archive_40_cc_by_40_grant_reused_for_upstream_meshes']
    returned = [r for r in acquisition['objects'] if not r['returned_representation_matches_is_a']]
    assert len(returned) == 7 and all(r['returned_representation_matches_partof'] for r in returned)


def test_open_and_disconnected_source_geometry_is_retained_without_invented_lumina():
    geometry = read('original-obj-geometry-review.json')
    rows = {r['id']: r for r in geometry['records']}
    assert geometry['all_expected_original_objects_inspected'] and geometry['expected_original_object_count'] == 38
    assert sum(len(r['exact_position_analysis_topology']['components']) for r in rows.values()) == 43
    assert rows['FJ3553']['exact_position_analysis_topology']['boundary_edges'] == 12
    assert len(rows['FJ2025']['exact_position_analysis_topology']['components']) == 5
    assert len(rows['FJ3588']['exact_position_analysis_topology']['components']) == 2
    assert .1101 < rows['FJ2034']['maximum_source_declared_vs_actual_bounds_difference_mm'] < .1103
    assert all(r['zero_area_triangles'] == 0 and not r['source_positions_faces_or_normals_changed'] for r in rows.values())
    boundary = read('complete-source-boundary-review.json')
    assert boundary['source_geometry_review_sha256'] == hashlib.sha256((REVIEW / 'original-obj-geometry-review.json').read_bytes()).hexdigest()
    open_rows = [r for r in boundary['records'] if r['boundary_edges']]
    assert len(boundary['records']) == 38 and len(open_rows) == 1
    edges = open_rows[0]['boundary_edges']; component = open_rows[0]['boundary_graph_components'][0]
    assert len(edges) == component['edge_count'] == 12 and component['all_vertices_degree_two']
    assert len({r['original_face_index'] for r in edges}) == 12
    assert not open_rows[0]['caps_added'] and not open_rows[0]['anatomical_open_ends_or_defects_classified']


def test_every_original_object_has_complete_separate_contact_evidence():
    summary = read('complete-self-contact-summary.json')
    assert summary['all_thirty_eight_original_objects_complete'] and len(summary['records']) == 38
    assert sum(r['source_triangles'] for r in summary['records']) == 26700
    assert sum(r['candidate_pairs'] for r in summary['records']) == 231629
    for row in summary['records']:
        packed = (REVIEW / row['file']).read_bytes(); raw = gzip.decompress(packed); result = json.loads(raw)
        assert hashlib.sha256(packed).hexdigest() == row['compressed_sha256']
        assert hashlib.sha256(raw).hexdigest() == row['uncompressed_sha256']
        assert row['source_triangles'] == row['testable_triangles'] and row['invalid_source_faces'] == 0
        assert row['candidate_pairs'] == row['explicitly_tested_pairs'] + row['resolved_noncoplanar_shared_edge_pairs']
        assert row['contact_count'] == 0 and not result['other_source_objects_compared_or_fused']
        assert not result['clinical_approval'] and not result['runtime_promoted']


def test_source_views_show_every_triangle_twice_without_coverage_or_patency_credit():
    figures = read('source-figure-review.json')
    assert len(figures['figures']) == 14 and figures['display_colours_are_arterial_venous_review_categories_only']
    for angle in [35, 215]:
        panels = [p for r in figures['figures'] if r['azimuth_degrees'] == angle for p in r['panels']]
        assert len(panels) == len({p['element_id'] for p in panels}) == 38
        assert sum(p['original_triangle_count'] for p in panels) == 26700
    for row in figures['figures']:
        assert hashlib.sha256((REVIEW / row['file']).read_bytes()).hexdigest() == row['sha256']
    assert not figures['perfusion_or_vessel_patency_verified'] and not figures['clinical_approval'] and not figures['runtime_promoted']


def test_exact_position_boundary_analysis_preserves_open_sheet_and_closed_solid():
    np = pytest.importorskip('numpy')
    from tools.anatomy_sources.review_bodyparts_source_boundaries import boundaries
    vertices = np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,0]], dtype=float)
    faces = np.array([[0,1,2],[4,2,3]])
    original_v = vertices.copy(); original_f = faces.copy(); result = boundaries(vertices, faces)
    assert len(result['boundary_edges']) == 4 and result['boundary_graph_components'][0]['all_vertices_degree_two']
    assert result['boundary_graph_components'][0]['original_vertex_record_groups'][0] == [0,4]
    assert np.array_equal(vertices, original_v) and np.array_equal(faces, original_f)
    tetra = boundaries(np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1]], dtype=float), np.array([[0,2,1],[0,1,3],[0,3,2],[1,2,3]]))
    assert tetra['boundary_edges'] == [] and not tetra['caps_added']
