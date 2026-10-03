import json,struct
import pytest
np=pytest.importorskip('numpy')
from tools.anatomy_sources.inspect_hra_renal_glb import read_glb,accessor


def glb(document,binary):
    text=json.dumps(document).encode();text+=b' '*((-len(text))%4);binary+=b'\0'*((-len(binary))%4)
    payload=struct.pack('<II',len(text),0x4e4f534a)+text+struct.pack('<II',len(binary),0x004e4942)+binary
    return struct.pack('<4sII',b'glTF',2,12+len(payload))+payload


def fixture():
    data=np.array([[1,2,3,99],[4,5,6,98]],dtype='<f4').tobytes()
    d={'asset':{'version':'2.0'},'buffers':[{'byteLength':len(data)}],
       'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':len(data),'byteStride':16}],
       'accessors':[{'bufferView':0,'componentType':5126,'count':2,'type':'VEC3'}]}
    return d,data


def test_interleaved_source_positions_exclude_other_attributes():
    d,b=fixture();doc,binary=read_glb(glb(d,b));points=accessor(doc,binary,0)
    assert np.array_equal(points,[[1,2,3],[4,5,6]])


def test_wrong_header_extent_is_rejected():
    d,b=fixture();raw=glb(d,b)
    with pytest.raises(ValueError,match='header'):read_glb(raw[:-1])


def test_accessor_cannot_read_an_adjacent_buffer_view_as_its_geometry():
    d,b=fixture();d['bufferViews'][0]['byteLength']=16
    with pytest.raises(ValueError,match='leaves buffer view'):accessor(d,b,0)


def test_external_geometry_cannot_be_silently_replaced():
    d,b=fixture();d['buffers'][0]['uri']='unrelated.bin'
    with pytest.raises(ValueError,match='External'):read_glb(glb(d,b))


def test_sparse_shape_changes_require_explicit_review():
    d,b=fixture();d['accessors'][0]['sparse']={'count':1}
    with pytest.raises(ValueError,match='sparse'):accessor(d,b,0)


def scene_fixture(tmp_path,transform=False):
    from tools.anatomy_sources.inspect_hra_renal_glb import inspect
    positions=np.array([[0,0,0],[1,0,0],[0,1,0]],dtype='<f4').tobytes();indices=np.array([0,1,2],dtype='<u2').tobytes();binary=positions+indices
    node={'name':'pelvis','mesh':0,'extras':{'label':'renal pelvis','representation_of':'http://purl.obolibrary.org/obo/UBERON_0001224'}}
    if transform:node['translation']=[1,0,0]
    d={'asset':{'version':'2.0'},'buffers':[{'byteLength':len(binary)}],
       'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':36},{'buffer':0,'byteOffset':36,'byteLength':6}],
       'accessors':[{'bufferView':0,'componentType':5126,'count':3,'type':'VEC3'},{'bufferView':1,'componentType':5123,'count':3,'type':'SCALAR'}],
       'meshes':[{'primitives':[{'attributes':{'POSITION':0},'indices':1}]}],
       'nodes':[{'name':'unmapped-container','children':[1]},node],'scenes':[{'nodes':[0]}]}
    path=tmp_path/'source.glb';path.write_bytes(glb(d,binary));crosswalk=tmp_path/'crosswalk.csv';crosswalk.write_text('node_name,OntologyID,label\npelvis,UBERON:0018116,Right renal pelvis\n')
    return inspect,path,crosswalk


def test_structural_group_is_retained_without_inventing_anatomical_identity(tmp_path):
    inspect,path,crosswalk=scene_fixture(tmp_path);r=inspect(path,crosswalk)
    assert r['all_scene_nodes_inspected']
    assert r['unmapped_nonmesh_groups'][0]['anatomical_identity_assigned'] is False
    part=r['records'][0]
    assert part['source_label']=='Right renal pelvis' and part['glb_source_label']=='renal pelvis'
    assert not part['semantic_metadata_exact_match']
    assert not part['semantic_specialization_or_conflict_reviewed']
    assert part['triangles']==1


def test_declared_transform_cannot_be_ignored_to_make_source_coordinates_match(tmp_path):
    inspect,path,crosswalk=scene_fixture(tmp_path,transform=True)
    with pytest.raises(ValueError,match='transforms need explicit'):
        inspect(path,crosswalk)
