"""Original wall self-crossings retain geometry, material identity and reflected lineage."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/zanatomy-wall-source-review'


def read(name):return json.loads((REVIEW/name).read_text())


def test_all_24_findings_are_native_triangle_interior_crossings_not_duplicate_faces():
    r=read('native-self-crossing-review.json');summary=read('wall-interface-summary.json')
    assert r['complete_contact_evidence_sha256']==summary['uncompressed_sha256']
    assert r['native_review_sha256']==hashlib.sha256((REVIEW/'native-wall-review.json').read_bytes()).hexdigest()
    assert r['record_count']==24 and r['unique_native_geometry_face_pairs']==12
    assert r['classifications']=={'nonparallel_native_triangle_interior_crossing':24}
    assert len(r['regions'])==8
    assert len(r['model_quality_holds'])==4 and sum(h['original_crossing_count'] for h in r['model_quality_holds'])==24
    assert all(h['status']=='source_surface_resolution_and_anatomical_review_required_before_clinical_promotion' for h in r['model_quality_holds'])
    assert all(len(c['native_shared_vertex_ids'])<=1 for c in r['records'])
    assert all(c['unit_normal_cross_norm']>.17 for c in r['records'])
    assert min(c['contact_segment_length_mm'] for c in r['records'])==pytest.approx(.015169068192743818)
    assert max(c['contact_segment_length_mm'] for c in r['records'])==pytest.approx(2.6734901653293237)
    assert all(min(w)>.001 for c in r['records'] for w in c['midpoint_barycentric_weights'])
    assert max(max(c['midpoint_reconstruction_errors_mm']) for c in r['records'])<3e-13
    assert all(min(e['weights'])>=-1e-9 and e['plane_reconstruction_error_mm']<1e-9
               for c in r['records'] for endpoints in c['endpoint_barycentric_coordinates'] for e in endpoints)
    counts=Counter(c['source_model_name'] for c in r['records'])
    assert counts=={'Internal abdominal oblique muscle.r':6,'Internal abdominal oblique muscle.l':6,
                    'External abdominal oblique muscle.r':6,'External abdominal oblique muscle.l':6}
    assert sum(c['source_instance_is_reflected'] for c in r['records'])==12
    assert all(c['source_material_slots'][0]==c['source_material_slots'][1] for c in r['records'])
    assert all(not c['anatomical_tissue_or_pathology_classified'] and not c['source_geometry_changed'] for c in r['records'])


def test_geometry_reconstruction_matches_original_model_faces_and_supplied_points():
    np=pytest.importorskip('numpy')
    from tools.anatomy_sources.render_zanatomy_wall_source import decode
    from tools.anatomy_sources.review_zanatomy_wall_source import native_polygons
    from tools.anatomy_sources.review_zanatomy_wall_self_crossings import barycentric
    native=read('native-wall-review.json');models={str(i['source_model_id']):i for i in native['instances']};geos={g['geometry_id']:g for g in native['geometries']};cache={}
    for c in read('native-self-crossing-review.json')['records']:
        gid=c['source_geometry_id'];model=models[c['source_model_id']]
        if gid not in cache:
            e=json.loads(gzip.decompress((REVIEW/geos[gid]['file']).read_bytes()))
            local=np.asarray(decode(e['positions'])).reshape(-1,3)
            cache[gid]=(local,native_polygons(decode(e['polygon_vertex_index']),len(local)))
        local,polygons=cache[gid];matrix=np.asarray(model['world_transform_columns']).T
        world=(np.column_stack([local,np.ones(len(local))])@matrix.T)*10
        triangles=world[np.asarray([polygons[f] for f in c['native_source_face_ids']])]
        assert np.array_equal(triangles,np.asarray(c['native_source_triangles_world_mm']))
        for t in triangles:
            for point in c['source_contact_points_mm']:
                w,error=barycentric(t,np.asarray(point));assert min(w)>=-1e-9 and error<1e-9
    t=np.array([[-1,-1,0],[1,-1,0],[0,1,0]],float)
    w,error=barycentric(t,np.array([0,0,0],float))
    assert np.allclose(w,[.25,.25,.5]) and error<1e-12
    _,error=barycentric(t,np.array([0,0,2],float));assert error==pytest.approx(2)


def test_every_region_and_contact_is_shown_without_loss_or_source_editing():
    r=read('native-self-crossing-review.json');locations=read('native-self-crossing-location-review.json')
    assert locations['source_crossing_review_sha256']==hashlib.sha256((REVIEW/'native-self-crossing-review.json').read_bytes()).hexdigest()
    assert len(locations['figures'])==len(r['regions'])==8
    assert sorted(i for f in locations['figures'] for i in f['contact_record_indices'])==list(range(24))
    assert sum(f['contact_segments_displayed'] for f in locations['figures'])==24
    for f in locations['figures']:
        assert hashlib.sha256((REVIEW/f['file']).read_bytes()).hexdigest()==f['sha256']
        assert f['all_original_context_triangles'] in [28869,29622]
        assert not f['source_geometry_changed']
    assert not r['clinical_approval'] and not r['runtime_promoted']
