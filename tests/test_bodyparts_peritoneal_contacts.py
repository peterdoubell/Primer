"""Peritoneal object contacts preserve every original face and cannot approve complete anatomy."""
import gzip,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];REVIEW=ROOT/'docs/bodyparts-peritoneal-source-review'


def test_all_four_original_objects_have_complete_separate_contact_evidence():
    p=json.loads((REVIEW/'complete-self-contact-summary.json').read_text())
    inventory=json.loads(gzip.decompress((REVIEW/'original-obj-geometry-review.json.gz').read_bytes()))
    source={r['id']:r for r in inventory['records']}
    assert p['all_four_original_objects_complete'] is True
    assert {r['element_id'] for r in p['records']}==set(source)
    assert sum(r['source_triangles'] for r in p['records'])==79516
    assert p['clinical_approval'] is False and p['source_geometry_changed'] is False and p['runtime_promoted'] is False
    for r in p['records']:
        packed=(REVIEW/r['file']).read_bytes();payload=gzip.decompress(packed);e=json.loads(payload)
        assert hashlib.sha256(packed).hexdigest()==r['compressed_sha256'] and hashlib.sha256(payload).hexdigest()==r['uncompressed_sha256']
        assert len(payload)==r['uncompressed_bytes'] and len(packed)==r['compressed_bytes']
        assert e['element_id']==r['element_id'] and e['source_obj_sha256']==source[r['element_id']]['source_sha256']
        assert e['other_source_objects_compared_or_fused'] is False
        assert e['source_coordinate_units']=='millimetres' and e['source_positions_faces_normals_changed'] is False
        prep=e['preparation'];contacts=e['triangle_contact_audit']
        assert prep['original_source_triangles']==source[r['element_id']]['triangles']
        assert prep['numerically_testable_triangles']+len(prep['invalid_source_triangles'])==prep['original_source_triangles']
        assert prep['invalid_source_triangles_removed_from_model'] is False
        assert contacts['conservative_aabb_candidate_pairs']==contacts['pairs_explicitly_intersection_tested']+contacts['noncoplanar_shared_edge_pairs_resolved_geometrically']
        assert contacts['unexpected_contact_count']==len(contacts['unexpected_contacts'])==r['contact_count']
        for c in contacts['unexpected_contacts']:
            assert len(c['original_source_faces'])==2
            assert all(f['source_part']==r['element_id'] and 0<=f['source_face_index']<r['source_triangles'] for f in c['original_source_faces'])
        assert e['clinical_approval'] is False and e['runtime_promoted'] is False


def test_all_contact_location_views_cover_every_affected_original_face():
    p=json.loads((REVIEW/'complete-self-contact-summary.json').read_text());figures=json.loads((REVIEW/'self-contact-location-review.json').read_text())
    assert len(figures['figures'])==4 and figures['derived_figure_license']=='CC BY-SA 2.1 Japan'
    expected={'FJ4650':2205,'FJ3396':2204,'FJ3398':216,'FJ4651':216}
    for r in p['records']:
        e=json.loads(gzip.decompress((REVIEW/r['file']).read_bytes()))
        f=next(f for f in figures['figures'] if f['element_id']==r['element_id'])
        indices=sorted({face['source_face_index'] for c in e['triangle_contact_audit']['unexpected_contacts'] for face in c['original_source_faces']})
        assert f['affected_original_face_indices']==indices
        assert f['contact_pairs_displayed']==r['contact_count']==expected[r['element_id']]
        assert f['all_original_context_triangles']==r['source_triangles']
        assert hashlib.sha256((REVIEW/f['file']).read_bytes()).hexdigest()==f['sha256']
        assert f['complete_contact_evidence_uncompressed_sha256']==r['uncompressed_sha256']
        assert f['source_positions_faces_or_normals_changed'] is False
    assert figures['clinical_approval'] is False and figures['runtime_promoted'] is False
