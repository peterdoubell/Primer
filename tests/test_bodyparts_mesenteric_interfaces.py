"""Source contacts and shared requested compounds cannot approve anatomical vessel junctions."""
from collections import Counter, defaultdict
import gzip
import hashlib
import itertools
import json
from pathlib import Path
from tools.anatomy_sources.audit_bodyparts_mesenteric_interfaces import classify_source_pair

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/bodyparts-mesenteric-source-review'


def read(name):
    return json.loads((REVIEW / name).read_text())


def evidence():
    summary = read('complete-source-pair-summary.json'); packed = (REVIEW / summary['file']).read_bytes(); raw = gzip.decompress(packed)
    assert hashlib.sha256(packed).hexdigest() == summary['compressed_sha256']
    assert hashlib.sha256(raw).hexdigest() == summary['uncompressed_sha256']
    return summary, json.loads(raw)


def test_shared_requested_parent_does_not_turn_distinct_source_labels_into_same_vessel():
    result = classify_source_pair({'a', 'b'}, {'a': 'trunk', 'b': 'branch'},
                                  {'a': ['compound', 'trunk'], 'b': ['branch', 'compound']},
                                  {'a': 'arterial', 'b': 'arterial'})
    assert result['shares_requested_source_group'] and not result['same_source_fma_group']
    assert not result['different_source_vessel_categories']
    result = classify_source_pair({'a', 'b'}, {'a': 'artery', 'b': 'vein'},
                                  {'a': ['shared-request'], 'b': ['shared-request']},
                                  {'a': 'arterial', 'b': 'venous'})
    assert result['different_source_vessel_categories'] and not result['same_source_fma_group']


def test_all_original_triangle_contacts_preserve_actual_labels_and_overlapping_requests():
    summary, proof = evidence(); audit = proof['triangle_contact_audit']; contacts = audit['unexpected_contacts']
    geometry = read('original-obj-geometry-review.json'); rows = {r['id']: r for r in geometry['records']}
    assert summary['all_thirty_eight_original_objects_inspected']
    assert summary['source_triangles'] == summary['testable_triangles'] == 26700
    assert summary['candidate_pairs'] == 307880
    assert audit['pairs_explicitly_intersection_tested'] + audit['noncoplanar_shared_edge_pairs_resolved_geometrically'] == 307880
    assert summary['contact_count'] == len(contacts) == 3823 and summary['within_object_contact_count'] == 0
    assert summary['same_source_group_between_object_contact_count'] == 177
    assert summary['different_source_group_contact_count'] == 3646
    assert summary['different_vessel_category_contact_count'] == 713
    assert summary['shared_requested_group_between_object_contact_count'] == 1606
    assert proof['source_geometry_review_sha256'] == hashlib.sha256((REVIEW / 'original-obj-geometry-review.json').read_bytes()).hexdigest()
    assert proof['source_fma_groups'] == {key: r['source_fma'] for key, r in rows.items()}
    for contact in contacts:
        ids = {r['source_part'] for r in contact['original_source_faces']}
        expected = classify_source_pair(ids, proof['source_fma_groups'], proof['requested_source_groups_by_part'], proof['source_vessel_category_by_part'])
        assert all(contact[k] == v for k, v in expected.items())
        for face in contact['original_source_faces']:
            assert 0 <= face['source_face_index'] < rows[face['source_part']]['triangles']
    assert not proof['source_positions_faces_or_normals_changed'] and not proof['biological_tree_assembled_or_approved']


def test_all_703_pairs_join_vertex_bounds_to_full_contacts_without_gap_or_patency_inference():
    summary, proof = evidence(); aggregate = read('complete-pair-proximity-contact-review.json')
    pairs = {tuple(r['source_ids']): r for r in aggregate['pairs']}
    assert len(pairs) == 703 and set(pairs) == set(itertools.combinations(sorted(proof['source_part_ids']), 2))
    counts = Counter(tuple(sorted(f['source_part'] for f in c['original_source_faces'])) for c in proof['triangle_contact_audit']['unexpected_contacts'])
    assert len(counts) == 78 and sum(counts.values()) == 3823
    assert sum(pairs[k]['minimum_vertex_pair_distance_mm'] > 0 for k in counts) == 77
    for key, row in pairs.items():
        assert row['continuous_triangle_contact_count'] == counts[key]
        assert not row['biological_junction_or_gap_verified'] and not row['vertex_distance_is_continuous_surface_distance']
    assert pairs[('FJ3082', 'FJ3647')]['continuous_triangle_contact_count'] == 96
    assert pairs[('FJ3542', 'FJ3543')]['continuous_triangle_contact_count'] == 107
    assert pairs[('FJ3542', 'FJ3543')]['different_source_vessel_categories']
    assert aggregate['complete_contact_evidence_uncompressed_sha256'] == summary['uncompressed_sha256']
    assert not aggregate['clinical_approval'] and not aggregate['runtime_promoted']


def test_seven_same_label_comparisons_retain_all_distinct_original_representations():
    groups = defaultdict(list)
    for row in read('original-obj-geometry-review.json')['records']:
        groups[row['source_fma']].append(row['id'])
    expected = {tuple(sorted(pair)) for ids in groups.values() for pair in itertools.combinations(ids, 2)}
    proof = read('source-geometry-correspondence.json'); rows = proof['comparisons']
    assert len(rows) == len(expected) == 7 and {tuple(r['source_ids']) for r in rows} == expected
    assert all(not r['face_indices_exactly_equal'] and not r['position_records_exactly_equal'] for r in rows)
    assert all(r['same_index_continuous_triangle_displacement_upper_bound_mm'] is None for r in rows)
    assert all(not r['biological_identity_or_independent_branch_verified'] for r in rows)
    assert not proof['repeated_objects_deduplicated_fitted_or_fused']


def test_complete_contact_views_retain_every_original_affected_face_and_point():
    summary, proof = evidence(); location = read('source-pair-location-review.json'); contacts = proof['triangle_contact_audit']['unexpected_contacts']
    assert hashlib.sha256((REVIEW / location['file']).read_bytes()).hexdigest() == location['sha256']
    assert location['complete_contact_evidence_uncompressed_sha256'] == summary['uncompressed_sha256']
    selectors = {
        'all_source_contacts': lambda c: True,
        'same_source_label_contacts': lambda c: c['same_source_fma_group'],
        'different_source_label_contacts': lambda c: not c['same_source_fma_group'],
        'arterial_venous_contacts': lambda c: c['different_source_vessel_categories'],
    }
    assert {p['category'] for p in location['panels']} == set(selectors)
    for panel in location['panels']:
        selected = [c for c in contacts if selectors[panel['category']](c)]
        expected = {(r['source_part'], r['source_face_index']) for c in selected for r in c['original_source_faces']}
        observed = {(r['element_id'], i) for r in panel['original_affected_faces'] for i in r['face_indices']}
        assert expected == observed
        assert panel['contact_pairs'] == len(selected)
        assert panel['contact_points_displayed'] == sum(len(c['contact_points_mm']) for c in selected)
        assert panel['all_original_context_triangles'] == 26700
    assert not location['biological_tree_assembled_or_approved'] and not location['clinical_approval']
