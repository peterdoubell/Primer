"""Source-pair contact and vertex proximity cannot establish approved duct connectivity."""
from collections import Counter
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/bodyparts-biliary-source-review'


def evidence():
    summary = json.loads((REVIEW / 'complete-source-pair-summary.json').read_text())
    packed = (REVIEW / summary['file']).read_bytes(); payload = gzip.decompress(packed)
    assert hashlib.sha256(packed).hexdigest() == summary['compressed_sha256']
    assert hashlib.sha256(payload).hexdigest() == summary['uncompressed_sha256']
    return summary, json.loads(payload)


def test_complete_source_pair_audit_preserves_same_label_overlap_separately():
    summary, proof = evidence(); contacts = proof['triangle_contact_audit']
    assert summary['source_triangles'] == summary['testable_triangles'] == 16114
    assert summary['candidate_pairs'] == 186182
    assert contacts['pairs_explicitly_intersection_tested'] + contacts['noncoplanar_shared_edge_pairs_resolved_geometrically'] == 186182
    assert summary['contact_count'] == len(contacts['unexpected_contacts']) == 3914
    assert summary['within_object_contact_count'] == 0
    assert summary['same_source_group_between_object_contact_count'] == 2276
    assert summary['different_source_group_contact_count'] == 1638
    groups = proof['source_fma_groups']
    for c in contacts['unexpected_contacts']:
        ids = {f['source_part'] for f in c['original_source_faces']}
        assert c['same_source_fma_group'] == (len({groups[i] for i in ids}) == 1)
    assert proof['biological_tree_assembled_or_approved'] is False
    assert proof['clinical_approval'] is False and proof['runtime_promoted'] is False


def test_all_190_source_pairs_keep_proximity_as_an_upper_bound_not_a_gap():
    _, proof = evidence()
    proximity = json.loads((REVIEW / 'all-source-pair-proximity-review.json').read_text())
    pairs = {tuple(r['source_ids']): r for r in proximity['pairs']}
    assert set(pairs) == set(itertools.combinations(sorted(proof['source_part_ids']), 2))
    assert len(pairs) == 190
    counts = Counter(tuple(sorted(f['source_part'] for f in c['original_source_faces']))
                     for c in proof['triangle_contact_audit']['unexpected_contacts'])
    for pair in [('FJ3079', 'FJ3080'), ('FJ3079', 'FJ4526'), ('FJ3079', 'FJ3123'), ('FJ3079', 'FJ3096'), ('FJ3096', 'FJ3123')]:
        r = pairs[pair]
        assert r['minimum_vertex_pair_distance_mm'] > 0 and counts[pair] > 0
        a, b = r['closest_source_positions_mm']
        assert math.isclose(math.sqrt(sum((x-y)**2 for x, y in zip(a, b))), r['minimum_vertex_pair_distance_mm'], rel_tol=1e-12)
        assert r['vertex_distance_is_continuous_surface_distance'] is False
        assert r['gap_or_biological_junction_verified'] is False
    assert proximity['source_objects_fused_or_fitted'] is False


def test_every_contact_face_and_point_is_retained_in_the_location_views():
    summary, proof = evidence(); location = json.loads((REVIEW / 'source-pair-location-review.json').read_text())
    assert hashlib.sha256((REVIEW / location['file']).read_bytes()).hexdigest() == location['sha256']
    assert location['complete_contact_evidence_uncompressed_sha256'] == summary['uncompressed_sha256']
    contacts = proof['triangle_contact_audit']['unexpected_contacts']
    for panel in location['panels']:
        subset = [c for c in contacts if panel['category'] == 'all_source_contacts'
                  or (panel['category'] == 'same_source_label_contacts') == c['same_source_fma_group']]
        expected = {(f['source_part'], f['source_face_index']) for c in subset for f in c['original_source_faces']}
        observed = {(r['element_id'], i) for r in panel['original_affected_faces'] for i in r['face_indices']}
        assert expected == observed
        assert panel['contact_pairs'] == len(subset)
        assert panel['contact_points_displayed'] == sum(len(c['contact_points_mm']) for c in subset)
        assert panel['all_original_context_triangles'] == 16114
    assert location['biological_tree_assembled_or_approved'] is False and location['runtime_promoted'] is False
