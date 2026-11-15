"""Wall contacts retain every source instance and explicit analysis tessellation."""
from collections import Counter
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/zanatomy-wall-source-review'


def test_sweep_matches_independent_brute_force_closed_aabb_overlap():
    np=pytest.importorskip('numpy')
    from tools.anatomy_sources.audit_zanatomy_wall_interfaces import candidates
    from tools.anatomy_sources.audit_massp_surface_intersections import TOLERANCE_MM
    rng=np.random.default_rng(8761);triangles=rng.normal(size=(120,3,3))
    # Exact boundary touching and a long, thin fascia-like box must be retained.
    triangles[0]=[[0,0,0],[1,0,0],[0,1,0]]
    triangles[1]=[[1,0,0],[2,0,0],[1,1,0]]
    triangles[2]=[[-100,0,0],[100,0,0],[0,.01,.01]]
    lo=triangles.min(1);hi=triangles.max(1)
    expected={p for p in itertools.combinations(range(len(triangles)),2)
              if all(max(lo[p[0],a],lo[p[1],a])<=min(hi[p[0],a],hi[p[1],a])+TOLERANCE_MM for a in range(3))}
    actual=candidates(triangles)
    assert {tuple(p) for p in actual}==expected and len(actual)==len(expected)
    assert (0,1) in expected


def test_all_native_polygons_have_original_corner_vertex_and_boundary_conservation():
    from tools.anatomy_sources.render_zanatomy_wall_source import decode
    from tools.anatomy_sources.review_zanatomy_wall_source import native_polygons
    proof=json.loads(gzip.decompress((REVIEW/'analysis-tessellation.json.gz').read_bytes()))
    native=json.loads((REVIEW/'native-wall-review.json').read_text())
    assert proof['native_review_sha256']==hashlib.sha256((REVIEW/'native-wall-review.json').read_bytes()).hexdigest()
    assert proof['source_fbx_sha256']==native['source_fbx_sha256']
    assert proof['all_native_oriented_boundaries_preserved'] and not proof['source_arrays_changed']
    assert not proof['tessellation_is_anatomically_approved']
    assert proof['exporter_sha256']==hashlib.sha256((ROOT/'tools/anatomy_sources/export_zanatomy_wall_triangles.c').read_bytes()).hexdigest()
    assert {g['geometry_id'] for g in proof['geometries']}=={g['geometry_id'] for g in native['geometries']}
    for g in native['geometries']:
        e=json.loads(gzip.decompress((REVIEW/g['file']).read_bytes()))
        encoded=decode(e['polygon_vertex_index']);corner_vertices=[i if i>=0 else -i-1 for i in encoded]
        polygons=native_polygons(encoded,g['positions'])
        row=next(r for r in proof['geometries'] if r['geometry_id']==g['geometry_id'])
        assert row['native_faces']==len(polygons)
        counts=Counter(t[0] for t in row['triangles'])
        assert all(counts[fid]==len(p)-2 for fid,p in enumerate(polygons))
        offsets=[0]
        for p in polygons:offsets.append(offsets[-1]+len(p))
        edges={i:Counter() for i in range(len(polygons))}
        for fid,a,b,c,x,y,z in row['triangles']:
            assert all(offsets[fid]<=i<offsets[fid+1] for i in [a,b,c])
            assert [corner_vertices[i] for i in [a,b,c]]==[x,y,z]
            for edge in [(x,y),(y,z),(z,x)]:edges[fid][edge]+=1
        for fid,p in enumerate(polygons):
            for a,b in zip(p,p[1:]+p[:1]):
                assert edges[fid][(a,b)]==1;edges[fid][(a,b)]-=1
            assert all(n==edges[fid][(b,a)] for (a,b),n in edges[fid].items())


def test_complete_interface_accounting_retains_native_ids_and_all_120_pairs():
    summary=json.loads((REVIEW/'wall-interface-summary.json').read_text())
    packed=(REVIEW/summary['file']).read_bytes();raw=gzip.decompress(packed);e=json.loads(raw)
    assert hashlib.sha256(packed).hexdigest()==summary['compressed_sha256']
    assert hashlib.sha256(raw).hexdigest()==summary['uncompressed_sha256']
    assert summary['source_instances']==16 and summary['native_faces_across_instances']==244931
    assert summary['analysis_triangles']==257939
    assert summary['contact_count']==52517 and summary['within_instance_contacts']==24
    assert summary['between_instance_contacts']==52493
    assert summary['contacts_including_nontriangle_native_polygon']==1383
    assert summary['candidate_pairs']==3566005
    assert summary['testable_triangles']+summary['invalid_triangles']==257939
    assert summary['candidate_pairs']==summary['explicitly_tested_pairs']+summary['analytically_resolved_shared_edge_pairs']
    assert summary['contact_count']==len(e['contacts'])==summary['within_instance_contacts']+summary['between_instance_contacts']
    assert len(summary['pairs'])==120
    assert sum(p['contact_count'] for p in summary['pairs'])==summary['between_instance_contacts']
    models={i['model_id'] for i in e['source_instances']}
    assert {tuple(p['source_model_ids']) for p in summary['pairs']}==set(itertools.combinations(sorted(models),2))
    native=json.loads((REVIEW/'native-wall-review.json').read_text())
    source={str(i['source_model_id']):i for i in native['instances']}
    proof=json.loads(gzip.decompress((REVIEW/'analysis-tessellation.json.gz').read_bytes()))
    triangles={g['geometry_id']:g['triangles'] for g in proof['geometries']}
    for c in e['contacts']:
        assert c['contact_points_mm']
        for f in c['original_source_faces']:
            assert triangles[source[f['source_part']]['source_geometry_id']][f['source_face_index']][0]==f['native_face_index']
    assert not e['clinical_approval'] and not e['source_geometry_changed'] and not e['runtime_promoted']


def test_shared_edge_is_retained_between_instances_but_allowed_within_one():
    np=pytest.importorskip('numpy')
    from tools.anatomy_sources.audit_zanatomy_wall_interfaces import compare_pair
    vertices=np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1]],float)
    faces=np.array([[0,1,2],[1,0,3]])
    normals=np.cross(vertices[faces[:,1]]-vertices[faces[:,0]],vertices[faces[:,2]]-vertices[faces[:,0]])
    normals/=np.linalg.norm(normals,axis=1)[:,None]
    points,same,analytic,allowed=compare_pair(vertices,faces,normals,[{'source_part':'rectus'},{'source_part':'fascia'}],0,1)
    assert not same and analytic and not allowed
    assert {tuple(p) for p in points}=={(0.,0.,0.),(1.,0.,0.)}
    points,same,analytic,allowed=compare_pair(vertices,faces,normals,[{'source_part':'rectus'},{'source_part':'rectus'}],0,1)
    assert same and analytic and allowed and not points


def test_contact_location_sheet_retains_all_points_and_original_context():
    summary=json.loads((REVIEW/'wall-interface-summary.json').read_text())
    e=json.loads(gzip.decompress((REVIEW/summary['file']).read_bytes()))
    locations=json.loads((REVIEW/'wall-interface-location-review.json').read_text())
    assert hashlib.sha256((REVIEW/locations['file']).read_bytes()).hexdigest()==locations['sha256']
    assert locations['complete_contact_evidence_sha256']==summary['uncompressed_sha256']
    all_panel=locations['panels'][0]
    assert all_panel['contact_pairs']==len(e['contacts'])
    assert all_panel['contact_points_displayed']==sum(len(c['contact_points_mm']) for c in e['contacts'])
    assert all(p['all_original_context_faces']==244931 for p in locations['panels'])
    assert locations['panels'][1]['contact_pairs']==24 and locations['panels'][2]['contact_pairs']==52493
    assert not locations['clinical_approval'] and not locations['source_geometry_changed']
