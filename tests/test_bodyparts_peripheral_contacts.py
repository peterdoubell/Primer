"""Source aliases, exact contacts and paired zero-volume faces do not certify vascular anatomy."""
import gzip,hashlib,json,re
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/bodyparts-peripheral-native-source-review'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_complete_contact_evidence_preserves_all_original_triangles_and_face_owners():
    summary=json.loads((OUT/'source-contact-summary.json').read_text());encoded=(OUT/summary['file']).read_bytes();payload=gzip.decompress(encoded);assert sha(encoded)==summary['compressed_sha256'] and sha(payload)==summary['uncompressed_sha256'];proof=json.loads(payload)
    assert summary['source_objects']==70 and summary['source_triangles']==summary['testable_triangles']==278094
    assert summary['contact_count']==19755 and summary['within_object_contact_count']==10 and summary['between_object_contact_count']==19745
    assert len(proof['triangle_contact_audit']['unexpected_contacts'])==19755 and proof['triangle_contact_audit']['conservative_aabb_candidate_pairs']==2947017
    source=json.loads((OUT/'source-identity-review.json').read_text());by_id={r['id']:r for r in source['objects']};geometry=json.loads((OUT/'original-geometry-review.json').read_text());face_counts={r['id']:r['original_triangles'] for r in geometry['objects']}
    assert proof['source_identity_review_sha256']==sha((OUT/'source-identity-review.json').read_bytes())
    for contact in proof['triangle_contact_audit']['unexpected_contacts']:
        assert len(contact['original_source_faces'])==2
        for face in contact['original_source_faces']:assert face['source_part'] in by_id and 0<=face['source_face_index']<face_counts[face['source_part']]
    assert not proof['original_geometry_changed_or_repaired'] and not proof['continuous_vessel_lumens_or_wall_layers_verified'] and not proof['clinical_approval']
def test_direct_requested_representation_resolves_header_without_editing_source_geometry():
    p=json.loads((OUT/'FJ2127-requested-representation-review.json').read_text());assert p['direct_request_matches_requested_representation'] and all(p['exact_geometry_array_equal'].values())
    a=gzip.decompress((OUT/p['original_batch_object_file']).read_bytes());b=gzip.decompress((OUT/p['direct_requested_object_file']).read_bytes());assert sha(a)==p['original_batch_object_sha256'] and sha(b)==p['direct_requested_object_sha256'] and sha((OUT/p['direct_requested_object_file']).read_bytes())==p['direct_compressed_sha256']
    assert re.search(rb'Concept ID\s*:\s*FMA20731\b',a) and re.search(rb'Concept ID\s*:\s*FMA20796\b',b)
    assert re.search(rb'Representation ID\s*:\s*BP23446\b',a) and re.search(rb'Representation ID\s*:\s*BP29028\b',b)
    assert not p['metadata_header_rewritten_by_us'] and p['old_batch_identity_conflict_retained'] and not p['source_geometry_is_independent_patient_side_or_clinically_validated']
    # Replay every source geometry line, not just the self-reported numeric equality.
    geometry=lambda raw:[line for line in raw.splitlines() if line.startswith((b'v ',b'vn ',b'f '))]
    assert geometry(a)==geometry(b)
def test_closed_component_counts_do_not_approve_isolated_double_faces_or_connections():
    p=json.loads((OUT/'source-contact-findings-review.json').read_text());assert len(p['within_object_findings'])==10
    assert {r['source_id'] for r in p['within_object_findings']}=={'FJ2095','FJ2204'}
    for row in p['within_object_findings']:
        assert row['exactly_same_triangle_position_set'] and row['opposite_face_winding'] and row['isolated_two_face_component_by_original_indices']
        assert not row['two_faces_are_resolved_vessel_wall_or_lumen'] and not row['source_faces_removed_or_repaired']
    assert not p['zero_volume_components_deleted_as_noise'] and not p['clinical_approval']
    junction=json.loads((OUT/'source-junction-proximity-review.json').read_text());assert len(junction['pairs'])==20
    for row in junction['pairs']:
        assert row['bounding_box_surface_distance_lower_bound_declared_mm']==0 and row['nearest_referenced_vertex_pair_distance_upper_bound_declared_mm']>0
        assert not row['vertex_distance_is_exact_continuous_surface_distance'] and not row['direct_biological_junction_or_missing_artery_diagnosed'] and not row['source_objects_merged_fitted_or_connected']
    assert not junction['tibioperoneal_trunk_independently_resolved_in_selected_source_objects']
def test_actual_duplicate_face_positions_and_winding_replay_when_scientific_runtime_available():
    np=pytest.importorskip('numpy')
    from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj
    source=json.loads((OUT/'source-identity-review.json').read_text());by={r['id']:r for r in source['objects']};p=json.loads((OUT/'source-contact-findings-review.json').read_text());cache={}
    for row in p['within_object_findings']:
        identifier=row['source_id']
        if identifier not in cache:cache[identifier]=read_obj(gzip.decompress((OUT/by[identifier]['file']).read_bytes()).decode())
        v,n,f,nf=cache[identifier];tri=v[f[row['source_face_indices']]];assert tri.tolist()==row['original_triangle_positions'] and set(map(tuple,tri[0]))==set(map(tuple,tri[1]))
        normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normals/=np.linalg.norm(normals,axis=1)[:,None];assert float(normals[0]@normals[1])<-.9999999999

def test_contact_visual_preserves_original_faces_and_sharealike():
    p=json.loads((OUT/'digital-contact-display-review.json').read_text());assert sha((OUT/p['file']).read_bytes())==p['sha256'] and p['license']=='CC BY-SA 2.1 Japan'
    assert {r['source_id'] for r in p['sources']}=={'FJ2095','FJ2204'} and all(not r['original_coordinates_changed'] for r in p['sources'])
    assert not p['source_geometry_changed_or_defects_removed'] and not p['runtime_promoted']
