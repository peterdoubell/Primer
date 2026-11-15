"""Source placement and authored colour are distinct from anatomical/renderer approval."""
import hashlib
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/cvh5-scene-review'


def test_complete_named_scene_bindings_keep_raw_material_and_matrix_identities():
    r=json.loads((REVIEW/'source-scene-review.json').read_text())
    source=json.loads((ROOT/'docs/cvh5-pelvic-source-review/original-model-inventory.json').read_text())
    assert len(r['group_nodes'])==1 and r['occurrence_count']==r['model_node_count']==47
    assert r['source_shader_count']==r['source_material_count']==41
    assert {o['node_name'] for o in r['occurrences']}=={o['name'] for o in source['model_nodes']}
    assert r['source_unit_scale_to_metres']==.001 and r['extra_scale_factor_applied']==1
    for o in r['occurrences']:
        assert o['source_linear_determinant']==1
        assert o['source_world_matrix_rows']==[[1,0,0,-186.51670837402344],[0,1,0,-112.73664855957031],[0,0,1,-93.01242065429688],[0,0,0,1]]
        assert o['source_material']==r['source_materials'][o['source_material_name']]
        assert o['source_shader']==r['source_shaders'][o['source_shader_name']]
        assert len(o['source_shading']['shader_lists'])==1 and not o['authored_colour_is_biological_signal']
    assert {m['opacity'] for m in r['source_materials'].values()}=={1.0}
    assert not r['geometry_fitted_or_repaired'] and not r['source_bytes_changed']
    assert not r['whole_decoder_independently_verified'] and not r['clinical_approval'] and not r['runtime_promoted']


def test_column_major_composition_normal_transform_and_invalid_hierarchy():
    np=pytest.importorskip('numpy')
    from tools.anatomy_sources.review_cvh5_scene import world_matrices,transform_points,transform_normals
    root=np.eye(4);root[:3,3]=[10,20,30]
    local=np.array([[0,-1,0,0],[1,0,0,0],[0,0,1,0],[0,0,0,1]],float)
    nodes={'root':{'parents':[{'name':'','matrix_values_in_source_order':root.flatten(order='F').tolist()}]},
           'part':{'parents':[{'name':'root','matrix_values_in_source_order':local.flatten(order='F').tolist()}]}}
    matrix=world_matrices(nodes,'part')[0]
    assert np.allclose(transform_points([[1,0,0]],matrix),[[10,21,30]])
    scale=np.diag([2,1,.5,1]);normal=transform_normals([[1,1,1]],scale)[0]
    assert np.allclose(normal,np.asarray([.5,1,2])/np.linalg.norm([.5,1,2]))
    nodes['root']['parents'][0]['name']='part'
    with pytest.raises(ValueError,match='Cyclic'):world_matrices(nodes,'part')
    with pytest.raises(ValueError,match='Unresolved'):world_matrices({},'missing')


def test_pdf_skin_view_controls_are_not_material_opacity_or_biological_colour():
    r=json.loads((REVIEW/'source-pdf-view-review.json').read_text())
    assert len(r['views'])==2 and r['default_view']['lighting_scheme']=='/CAD'
    skin=[next(o for o in v['node_overrides'] if o['node_name']=='Skin') for v in r['views']]
    assert skin[0]['visible'] is True and skin[0]['opacity']==.5
    assert skin[1]['visible'] is False and skin[1]['opacity']==.5
    assert all(v['reset_nodes_before_overrides'] for v in r['views'])
    assert all(any(o['node_name'] is None for o in v['node_overrides']) for v in r['views'])
    assert not r['pdf_or_3d_scripts_executed'] and not r['unnamed_override_scope_independently_verified']
    assert not r['view_transform_application_independently_verified'] and not r['clinical_approval']


def test_false_pdf_boolean_is_not_converted_using_object_truthiness():
    generic=pytest.importorskip('pypdf.generic')
    from tools.anatomy_sources.review_cvh5_pdf_views import pdf_bool
    assert pdf_bool(generic.BooleanObject(False)) is False
    assert pdf_bool(generic.BooleanObject(True)) is True
    assert pdf_bool(False) is False
    with pytest.raises(ValueError):pdf_bool('false')


def test_assembly_views_preserve_source_links_and_their_display_limits():
    r=json.loads((REVIEW/'assembly-view-review.json').read_text())
    assert r['scene_review_sha256']==hashlib.sha256((REVIEW/'source-scene-review.json').read_bytes()).hexdigest()
    assert r['pdf_view_review_sha256']==hashlib.sha256((REVIEW/'source-pdf-view-review.json').read_bytes()).hexdigest()
    assert hashlib.sha256((REVIEW/r['file']).read_bytes()).hexdigest()==r['sha256']
    assert [len(p['displayed_nodes']) for p in r['panels']]==[47,47,46,46]
    assert [p['displayed_triangles'] for p in r['panels']]==[688510,688510,670534,670534]
    assert all('Skin' not in p['displayed_nodes'] for p in r['panels'][2:])
    assert r['candidate_encoded_normals_used'] and not r['review_lighting_is_original_pdf_lighting']
    assert not r['pdf_view_matrices_applied'] and not r['original_renderer_pixel_equivalence_verified']
    assert not r['clinical_approval'] and not r['runtime_promoted']
