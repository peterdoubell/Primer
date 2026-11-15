"""Original renal pieces, duplicates, tissue contacts and fine-label gaps are retained."""
import gzip
import hashlib
import json
from pathlib import Path
import pytest
from tools.anatomy_sources.audit_bodyparts_renal_interfaces import source_category, classify_source_pair

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/bodyparts-renal-source-review'


def read(name):
    return json.loads((REVIEW / name).read_text())


def test_versioned_original_ids_and_actual_partof_returns_are_preserved():
    acquisition = read('acquisition.json')
    assert len(acquisition['source_groups']) == 14 and len(acquisition['objects']) == 31
    assert sum(r['faces'] for r in acquisition['objects']) == 46322
    assert acquisition['archive_crc_verified'] and acquisition['upstream_default_license'] == 'CC BY-SA 2.1 Japan'
    assert not acquisition['archive_40_cc_by_40_grant_reused_for_upstream_meshes']
    alternatives = [r for r in acquisition['objects'] if not r['returned_representation_matches_is_a']]
    assert len(alternatives) == 18 and all(r['returned_representation_matches_partof'] for r in alternatives)
    for r in alternatives:
        assert r['original_obj_header']['Representation ID'] == r['representation_id']
        assert r['original_obj_header']['Concept ID'] == r['source_fma']
    assert not acquisition['runtime_promoted'] and not acquisition['clinical_approval']


def test_closed_source_topology_does_not_hide_coincident_components_or_disconnected_pieces():
    geometry = read('original-obj-geometry-review.json')
    assert geometry['all_expected_original_objects_inspected'] and geometry['expected_original_object_count'] == 31
    assert geometry['original_acquisition_sha256'] == hashlib.sha256((REVIEW / 'acquisition.json').read_bytes()).hexdigest()
    assert sum(len(r['exact_position_analysis_topology']['components']) for r in geometry['records']) == 53
    assert all(r['exact_position_analysis_topology']['boundary_edges'] == 0 and not r['source_positions_faces_or_normals_changed'] for r in geometry['records'])
    findings = read('coincident-source-face-review.json')['findings']
    assert len(findings) == 3 and all(r['element_id'] == 'FJ3473' for r in findings)
    assert [r['face_indices'] for r in findings] == [[20, 26], [23, 29], [32, 33]]
    assert all(r['coincident_component_is_only_the_two_original_faces'] for r in findings)
    assert all(not r['anatomical_tissue_or_native_defect_classified'] and not r['source_geometry_changed'] for r in findings)
    assert len(read('complete-source-boundary-review.json')['records']) == 31


def test_every_original_piece_has_complete_lossless_self_contact_accounting():
    summary = read('complete-self-contact-summary.json')
    assert summary['all_expected_original_objects_complete'] and summary['expected_original_object_count'] == 31
    assert sum(r['candidate_pairs'] for r in summary['records']) == 390183
    assert sum(r['contact_count'] for r in summary['records']) == 3
    for row in summary['records']:
        packed = (REVIEW / row['file']).read_bytes(); raw = gzip.decompress(packed)
        assert hashlib.sha256(packed).hexdigest() == row['compressed_sha256']
        assert hashlib.sha256(raw).hexdigest() == row['uncompressed_sha256']
        assert row['invalid_source_faces'] == 0 and row['source_triangles'] == row['testable_triangles']
        assert row['candidate_pairs'] == row['explicitly_tested_pairs'] + row['resolved_noncoplanar_shared_edge_pairs']


def test_all_pairs_and_tissue_categories_retain_contacts_without_approved_junctions():
    summary = read('complete-source-pair-summary.json')
    assert summary['all_thirty_one_original_objects_inspected']
    assert summary['contact_count'] == 9358 and summary['within_object_contact_count'] == 3
    assert summary['same_source_group_between_object_contact_count'] == 2488
    assert summary['different_source_group_contact_count'] == 6867
    assert summary['different_tissue_category_contact_count'] == 5794
    packed = (REVIEW / summary['file']).read_bytes(); raw = gzip.decompress(packed)
    assert hashlib.sha256(packed).hexdigest() == summary['compressed_sha256']
    assert hashlib.sha256(raw).hexdigest() == summary['uncompressed_sha256']
    categories = json.loads(raw)['source_tissue_category_by_part']
    assert set(categories.values()) == {'kidney', 'ureter', 'arterial', 'venous'}
    review = read('complete-pair-proximity-contact-review.json')
    assert len(review['pairs']) == 465
    assert sum(r['continuous_triangle_contact_count'] for r in review['pairs']) + review['within_source_contact_count'] == 9358
    assert sum(r['minimum_vertex_pair_distance_mm'] > 0 and r['continuous_triangle_contact_count'] > 0 for r in review['pairs']) == 95
    assert all(not r['biological_junction_or_gap_verified'] for r in review['pairs'])
    comparisons = read('source-geometry-correspondence.json')['comparisons']
    assert len(comparisons) == 39 and all(not r['face_indices_exactly_equal'] for r in comparisons)
    assert all(r['same_index_continuous_triangle_displacement_upper_bound_mm'] is None for r in comparisons)


def test_rendered_source_views_and_holds_cannot_supply_missing_renal_layers_or_trauma():
    figures = read('source-figure-review.json')
    assert len(figures['figures']) == 28
    for angle in [35, 215]:
        panels = [p for r in figures['figures'] if r['azimuth_degrees'] == angle for p in r['panels']]
        assert len(panels) == 31 and sum(p['original_triangle_count'] for p in panels) == 46322
    for row in figures['figures']:
        assert hashlib.sha256((REVIEW / row['file']).read_bytes()).hexdigest() == row['sha256']
    contacts = read('source-pair-location-review.json')
    assert hashlib.sha256((REVIEW / contacts['file']).read_bytes()).hexdigest() == contacts['sha256']
    assert contacts['panels'][0]['contact_pairs'] == 9358
    closeup = read('coincident-source-face-figure-review.json')
    assert hashlib.sha256((REVIEW / closeup['file']).read_bytes()).hexdigest() == closeup['sha256']
    assert hashlib.sha256((REVIEW / 'coincident-source-face-review.json').read_bytes()).hexdigest() == closeup['source_review_sha256']
    assert not closeup['source_positions_or_faces_changed'] and not closeup['clinical_approval']
    holds = read('source-selection-holds.json')
    assert len(holds['separately_named_target_queries']) == 8 and all(not v for v in holds['separately_named_target_queries'].values())
    assert not holds['missing_fine_regions_supplied_by_parent_labels'] and not holds['tumour_case_supplies_normal_or_trauma_anatomy']
    assert not figures['runtime_promoted'] and not figures['clinical_approval']


def test_tissue_classification_does_not_default_kidneys_or_ureters_to_vessels():
    assert source_category('Left kidney') == 'kidney'
    assert source_category('Right ureter') == 'ureter'
    assert source_category('Ureteric segment of left renal artery') == 'arterial'
    assert source_category('Left renal vein') == 'venous'
    with pytest.raises(ValueError, match='Unreviewed'):
        source_category('Unknown renal structure')
    result = classify_source_pair({'a', 'b'}, {'a': 'kidney', 'b': 'vein'}, {'a': ['shared'], 'b': ['shared']}, {'a': 'kidney', 'b': 'venous'})
    assert result['different_source_tissue_categories'] and result['shares_requested_source_group'] and not result['same_source_fma_group']
