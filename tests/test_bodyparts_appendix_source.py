"""Original appendix/mesoappendix geometry remains separate from clinical coverage."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/bodyparts-appendix-source-review'


def read(name):
    return json.loads((REVIEW / name).read_text())


def test_all_original_ids_headers_and_partof_returns_are_retained():
    acquisition = read('acquisition.json')
    assert acquisition['source_groups'] == {'FMA14542': ['FJ2565'], 'FMA16549': ['FJ3397', 'FJ4649']}
    rows = {r['id']: r for r in acquisition['objects']}
    assert sum(r['faces'] for r in rows.values()) == 3218
    assert acquisition['archive_crc_verified'] and acquisition['upstream_default_license'] == 'CC BY-SA 2.1 Japan'
    assert not acquisition['archive_40_cc_by_40_grant_reused_for_upstream_meshes']
    for fid in ['FJ3397', 'FJ4649']:
        row = rows[fid]
        assert row['requested_is_a_representation_id'] == 'BP21447' and row['representation_id'] == 'BP22741'
        assert not row['returned_representation_matches_is_a'] and row['returned_representation_matches_partof']
        assert row['original_obj_header']['Build-up logic'] == 'FMA 3.0 part_of'
    assert rows['FJ2565']['returned_representation_matches_is_a']
    assert not acquisition['clinical_approval'] and not acquisition['runtime_promoted']


def test_original_components_and_declared_bounds_difference_are_preserved():
    geometry = read('original-obj-geometry-review.json')
    assert geometry['all_expected_original_objects_inspected'] and geometry['expected_original_object_count'] == 3
    assert geometry['original_acquisition_sha256'] == hashlib.sha256((REVIEW / 'acquisition.json').read_bytes()).hexdigest()
    for row in geometry['records']:
        assert len(row['exact_position_analysis_topology']['components']) == 1
        assert row['exact_position_analysis_topology']['boundary_edges'] == 0
        assert row['zero_area_triangles'] == 0 and not row['source_positions_faces_or_normals_changed']
    row = next(r for r in geometry['records'] if r['id'] == 'FJ4649')
    assert .0307 < row['maximum_source_declared_vs_actual_bounds_difference_mm'] < .0309
    boundary = read('complete-source-boundary-review.json')
    assert len(boundary['records']) == 3 and all(not r['boundary_edges'] and not r['caps_added'] for r in boundary['records'])
    correspondence = read('source-geometry-correspondence.json')['comparisons']
    assert len(correspondence) == 1
    assert not correspondence[0]['face_indices_exactly_equal']
    assert correspondence[0]['same_index_continuous_triangle_displacement_upper_bound_mm'] is None
    assert not correspondence[0]['biological_identity_or_independent_branch_verified']


def test_complete_contacts_retain_self_and_all_three_pair_accounting():
    self_summary = read('complete-self-contact-summary.json')
    assert self_summary['all_expected_original_objects_complete'] and self_summary['expected_original_object_count'] == 3
    assert sum(r['candidate_pairs'] for r in self_summary['records']) == 26865
    for row in self_summary['records']:
        packed = (REVIEW / row['file']).read_bytes()
        raw = gzip.decompress(packed)
        assert hashlib.sha256(packed).hexdigest() == row['compressed_sha256']
        assert hashlib.sha256(raw).hexdigest() == row['uncompressed_sha256']
        assert row['contact_count'] == row['invalid_source_faces'] == 0
        assert row['candidate_pairs'] == row['explicitly_tested_pairs'] + row['resolved_noncoplanar_shared_edge_pairs']
    summary = read('complete-source-pair-summary.json')
    assert summary['all_three_original_objects_inspected']
    assert summary['contact_count'] == 1419 and summary['within_object_contact_count'] == 0
    assert summary['same_source_group_between_object_contact_count'] == 1067
    assert summary['different_source_group_contact_count'] == 352
    packed = (REVIEW / summary['file']).read_bytes()
    assert hashlib.sha256(packed).hexdigest() == summary['compressed_sha256']
    assert hashlib.sha256(gzip.decompress(packed)).hexdigest() == summary['uncompressed_sha256']
    pairs = read('complete-pair-proximity-contact-review.json')['pairs']
    assert len(pairs) == 3 and sum(p['continuous_triangle_contact_count'] for p in pairs) == 1419
    different = [p for p in pairs if not p['same_source_fma_group']]
    assert len(different) == 2 and all(p['minimum_vertex_pair_distance_mm'] > .58 and p['continuous_triangle_contact_count'] == 176 for p in different)
    assert all(not p['biological_junction_or_gap_verified'] for p in pairs)


def test_source_views_and_holds_do_not_supply_missing_wall_lumen_or_fine_regions():
    figures = read('source-figure-review.json')
    assert len(figures['figures']) == 4
    for angle in [35, 215]:
        panels = [p for r in figures['figures'] if r['azimuth_degrees'] == angle for p in r['panels']]
        assert len(panels) == 3 and sum(p['original_triangle_count'] for p in panels) == 3218
    for row in figures['figures']:
        assert hashlib.sha256((REVIEW / row['file']).read_bytes()).hexdigest() == row['sha256']
    locations = read('source-pair-location-review.json')
    assert hashlib.sha256((REVIEW / locations['file']).read_bytes()).hexdigest() == locations['sha256']
    assert locations['panels'][0]['contact_pairs'] == 1419
    assert all(p['all_original_context_triangles'] == 3218 for p in locations['panels'])
    holds = read('source-selection-holds.json')
    assert len(holds['separately_named_target_queries']) == 10
    assert all(not matches for matches in holds['separately_named_target_queries'].values())
    assert len(holds['terminal_ileum_synonym_matches']) == 24
    assert not holds['missing_fine_regions_supplied_by_parent_labels']
    assert not figures['clinical_approval'] and not figures['runtime_promoted']
