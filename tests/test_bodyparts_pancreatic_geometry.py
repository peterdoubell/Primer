"""Original OBJ indices and seams must survive inspection without source repairs."""
import hashlib
import json
from pathlib import Path
import pytest
from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/bodyparts-pancreatic-upstream-review'


def test_relative_obj_indices_and_source_normals_are_preserved():
    np=pytest.importorskip('numpy')
    text='v 0 0 0\nv 1 0 0\nv 0 1 0\nvn 0 0 2\nvn 0 0 2\nvn 0 0 2\nf -3//-3 -2//-2 -1//-1\n'
    v,n,f,nf=read_obj(text)
    assert np.array_equal(v,[[0,0,0],[1,0,0],[0,1,0]])
    assert np.array_equal(f,[[0,1,2]]) and np.array_equal(nf,f)
    assert np.array_equal(n,[[0,0,2]]*3)  # no normal replacement/renormalization


def test_unreviewed_face_triangulation_and_outside_indices_are_rejected():
    pytest.importorskip('numpy')
    prefix='v 0 0 0\nv 1 0 0\nv 0 1 0\nvn 0 0 1\nvn 0 0 1\nvn 0 0 1\n'
    with pytest.raises(ValueError,match='non-triangle'):read_obj(prefix+'f 1//1 2//2 3//3 1//1\n')
    with pytest.raises(ValueError,match='invalid'):read_obj(prefix+'f 1//1 2//2 4//3\n')
    with pytest.raises(ValueError,match='attributes'):read_obj(prefix+'f 1/1/1 2/2/2 3/3/3\n')


def test_actual_25_source_elements_keep_seams_components_and_bounds_discrepancies():
    p=json.loads((REVIEW/'original-obj-geometry-review.json').read_text())
    source=REVIEW/'acquisition.json';receipt=json.loads(source.read_text())
    assert p['original_acquisition_sha256']==hashlib.sha256(source.read_bytes()).hexdigest()
    assert p['all_25_original_objects_inspected'] and len(p['records'])==25
    assert sum(r['triangles'] for r in p['records'])==26488
    assert sum(r['zero_area_triangles'] for r in p['records'])==0
    expected={r['id']:r for r in receipt['objects']}
    for r in p['records']:
        assert r['source_sha256']==expected[r['id']]['sha256']
        assert r['vertices']==expected[r['id']]['vertices'] and r['triangles']==expected[r['id']]['faces']
        assert r['source_positions_faces_or_normals_changed'] is False and r['analysis_welding_changes_source'] is False
        assert r['declared_bounds_corrected_or_used_to_fit_mesh'] is False
        assert sum(c['faces'] for c in r['indexed_topology']['components'])==r['triangles']
        assert sum(c['faces'] for c in r['exact_position_analysis_topology']['components'])==r['triangles']
    duct=next(r for r in p['records'] if r['id']=='FJ1896')
    assert len(duct['indexed_topology']['components'])==484
    assert duct['indexed_topology']['boundary_edges']==3594
    assert len(duct['exact_position_analysis_topology']['components'])==1
    assert duct['exact_position_analysis_topology']['boundary_edges']==0
    assert duct['maximum_source_declared_vs_actual_bounds_difference_mm']==pytest.approx(.0314)
    assert [(r['id'],r['exact_position_analysis_topology']['boundary_edges']) for r in p['records'] if r['exact_position_analysis_topology']['boundary_edges']]==[('FJ3553',12)]
    assert len(next(r for r in p['records'] if r['id']=='FJ2025')['exact_position_analysis_topology']['components'])==5
    assert sum(r['maximum_source_declared_vs_actual_bounds_difference_mm']>0 for r in p['records'])==13
    assert p['clinical_approval'] is False and p['runtime_promoted'] is False


def test_source_figures_show_every_original_element_and_separate_parenchyma():
    path=REVIEW/'original-obj-geometry-review.json';p=json.loads((REVIEW/'source-figure-review.json').read_text())
    assert p['source_geometry_review_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    assert p['derived_figure_license']=='CC BY-SA 2.1 Japan'
    assert p['source_coordinate_transforms_performed'] is False and p['source_elements_repaired_or_fused'] is False
    assert p['clinical_approval'] is False and p['runtime_promoted'] is False
    for f in p['figures']:
        assert hashlib.sha256((REVIEW/f['file']).read_bytes()).hexdigest()==f['sha256']
        assert all(r['source_vertices_or_faces_changed'] is False for r in f['panels'])
    for f in p['figures'][:2]:
        assert len(f['panels'])==12
        ids=[fid for panel in f['panels'] for fid in panel['element_ids']]
        assert len(ids)==len(set(ids))==25
        assert sum(r['all_original_triangles'] for r in f['panels'])==26488
    contexts=p['figures'][2]
    assert contexts['alternative_source_parenchyma_fused'] is False
    assert all(not {'FJ1895','FJ2629'}.issubset(panel['element_ids']) for panel in contexts['panels'])
