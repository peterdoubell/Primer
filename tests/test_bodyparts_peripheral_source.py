"""Exact original vessel objects do not establish MRI registration or repair an ontology conflict."""
import gzip,hashlib,json
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/bodyparts-peripheral-native-source-review'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_all_original_objects_are_preserved_and_conflicted_identity_is_held():
    p=json.loads((OUT/'source-identity-review.json').read_text());assert p['source_version']=='4.3' and p['license']=='CC BY-SA 2.1 Japan' and len(p['objects'])==70 and p['archive_crc_verified']
    assert {r['id'] for r in p['identity_holds']}=={'FJ2127'};conflict=next(r for r in p['objects'] if r['id']=='FJ2127');assert conflict['requested_is_a_mapping']['source_fma']=='FMA20796' and conflict['original_obj_header']['Concept ID']=='FMA20731' and not conflict['matches_requested_mapping']
    assert 'left thigh' in conflict['requested_is_a_mapping']['source_obj_name']
    for row in p['objects']:
        encoded=(OUT/row['file']).read_bytes();assert sha(encoded)==row['compressed_file_sha256'];raw=gzip.decompress(encoded);assert len(raw)==row['bytes'] and sha(raw)==row['sha256'] and row['zip_crc_verified']
        assert not row['source_positions_faces_or_normals_changed'] and not row['independent_patient_laterality_or_anatomical_validation'] and not row['runtime_promoted']
    assert not p['native_MRI_or_patient_registration_verified'] and not p['full_reportable_tree_wall_or_disease_coverage_verified'] and not p['clinical_approval']
def test_actual_source_geometry_replays_without_repair_when_scientific_runtime_available():
    pytest.importorskip('numpy')
    from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj
    p=json.loads((OUT/'original-geometry-review.json').read_text());assert p['original_object_count']==70 and p['original_triangles']==278094 and p['held_identity_ids']==['FJ2127']
    for row in p['objects']:
        v,n,f,nf=read_obj(gzip.decompress((OUT/row['source_file']).read_bytes()).decode());assert len(v)==row['original_vertices'] and len(f)==row['original_triangles']
        assert sha(v.astype('<f8').tobytes())==row['source_positions_f64_sha256'] and sha(f.astype('<i8').tobytes())==row['source_face_indices_i64_sha256'] and sha(n.astype('<f8').tobytes())==row['source_normals_f64_sha256'] and sha(nf.astype('<i8').tobytes())==row['source_normal_indices_i64_sha256']
        assert not row['source_geometry_or_topology_repaired'] and not row['anatomical_vessel_connections_or_wall_volume_verified'] and not row['self_intersections_independently_audited']
def test_source_render_excludes_conflict_and_does_not_fuse_patient_MRI():
    p=json.loads((OUT/'source-display-review.json').read_text());assert sha((OUT/p['file']).read_bytes())==p['sha256'];assert len(p['panels'][0]['source_ids'])==69 and len(p['panels'][1]['source_ids'])==25
    assert all('FJ2127' not in panel['source_ids'] and panel['entire_selected_object_triangles_displayed'] for panel in p['panels'])
    assert not p['source_geometry_changed_or_refitted'] and not p['MRI_registration_or_fusion_performed'] and not p['closed_objects_prove_wall_volume_or_lumen_connections'] and not p['runtime_promoted']
