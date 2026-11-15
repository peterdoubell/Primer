"""Regional piece contacts do not approve biological continuity or a patent bowel lumen."""
from collections import Counter
import gzip
import hashlib
import itertools
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/bodyparts-bowel-source-review'


def evidence():
    summary=json.loads((REVIEW/'complete-source-pair-summary.json').read_text());packed=(REVIEW/summary['file']).read_bytes();payload=gzip.decompress(packed)
    assert hashlib.sha256(packed).hexdigest()==summary['compressed_sha256']
    assert hashlib.sha256(payload).hexdigest()==summary['uncompressed_sha256']
    return summary,json.loads(payload)


def test_complete_all_piece_contact_accounting_preserves_regional_categories():
    summary,proof=evidence();audit=proof['triangle_contact_audit']
    assert summary['source_triangles']==summary['testable_triangles']==30546
    assert summary['candidate_pairs']==258590
    assert audit['pairs_explicitly_intersection_tested']+audit['noncoplanar_shared_edge_pairs_resolved_geometrically']==258590
    assert summary['contact_count']==len(audit['unexpected_contacts'])==7865
    assert summary['within_object_contact_count']==0
    assert summary['same_source_group_between_object_contact_count']==5726
    assert summary['different_source_group_contact_count']==2139
    groups=proof['source_fma_groups']
    for c in audit['unexpected_contacts']:
        ids={f['source_part'] for f in c['original_source_faces']}
        assert c['same_source_fma_group']==(len({groups[i] for i in ids})==1)
    assert proof['biological_tree_assembled_or_approved'] is False and proof['runtime_promoted'] is False


def test_all_1770_source_pairs_retained_without_vertex_gap_inference():
    _,proof=evidence();p=json.loads((REVIEW/'all-source-pair-proximity-review.json').read_text())
    pairs={tuple(r['source_ids']):r for r in p['pairs']}
    assert len(pairs)==1770 and set(pairs)==set(itertools.combinations(sorted(proof['source_part_ids']),2))
    contacts=Counter(tuple(sorted(f['source_part'] for f in c['original_source_faces'])) for c in proof['triangle_contact_audit']['unexpected_contacts'])
    assert any(pairs[k]['minimum_vertex_pair_distance_mm']>0 for k in contacts)
    assert all(r['vertex_distance_is_continuous_surface_distance'] is False and r['gap_or_biological_junction_verified'] is False for r in pairs.values())
    assert p['source_objects_fused_or_fitted'] is False


def test_all_contact_points_and_faces_remain_in_original_context_views():
    summary,proof=evidence();location=json.loads((REVIEW/'source-pair-location-review.json').read_text())
    assert hashlib.sha256((REVIEW/location['file']).read_bytes()).hexdigest()==location['sha256']
    assert location['complete_contact_evidence_uncompressed_sha256']==summary['uncompressed_sha256']
    contacts=proof['triangle_contact_audit']['unexpected_contacts']
    for panel in location['panels']:
        subset=[c for c in contacts if panel['category']=='all_source_contacts' or (panel['category']=='same_source_label_contacts')==c['same_source_fma_group']]
        expected={(f['source_part'],f['source_face_index']) for c in subset for f in c['original_source_faces']}
        observed={(r['element_id'],i) for r in panel['original_affected_faces'] for i in r['face_indices']}
        assert expected==observed
        assert panel['contact_pairs']==len(subset) and panel['contact_points_displayed']==sum(len(c['contact_points_mm']) for c in subset)
        assert panel['all_original_context_triangles']==30546
    assert location['clinical_approval'] is False and location['biological_tree_assembled_or_approved'] is False
