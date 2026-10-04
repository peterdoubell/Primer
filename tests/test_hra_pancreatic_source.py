"""Original gross pancreatic regions do not imply a repaired or clinically approved model."""
import copy
import hashlib
import json
from pathlib import Path
import pytest
from tools.anatomy_sources.acquire_hra_pancreatic_reference import distributions
from tools.anatomy_sources.inspect_hra_renal_glb import ontology_uri

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/hra-pancreatic-source-review'


def test_fma_neck_uri_is_not_falsely_rewritten_as_uberon():
    assert ontology_uri('FMA:14517')=='http://purl.org/sig/ont/fma/fma14517'
    assert ontology_uri('UBERON:0010373')=='http://purl.obolibrary.org/obo/UBERON_0010373'
    with pytest.raises(ValueError,match='namespace'):ontology_uri('FMA:14517/other')
    with pytest.raises(ValueError,match='namespace'):ontology_uri('OTHER:14517')


@pytest.mark.parametrize('sex',['female','male'])
def test_raw_model_license_cannot_be_inferred_from_graph_license(sex):
    metadata=json.loads((REVIEW/('pancreas-'+sex+'-v1.3-metadata.jsonld')).read_text())
    raw,files=distributions(metadata,sex)
    assert len(files)==2 and raw['ccf:doi']['@id'].startswith('https://doi.org/10.48539/')
    wrong=copy.deepcopy(metadata)
    next(r for r in wrong['@graph'] if r['@id'].endswith('#raw-data'))['dct:license']='CC BY-NC 4.0'
    with pytest.raises(ValueError,match='Raw model grant'):distributions(wrong,sex)
    wrong=copy.deepcopy(metadata)
    dist=next(r for r in wrong['@graph'] if r['@id'].endswith('#crosswalk.csv'))
    dist['dcat:downloadURL']['@value']=dist['dcat:downloadURL']['@value'].replace('/v1.3/','/v1.2/')
    with pytest.raises(ValueError,match='Unrelated'):distributions(wrong,sex)


def test_source_region_and_boundary_evidence_retains_actual_defects():
    for sex,total,boundary,pairs,unmatched in [('female',12894,576,288,0),('male',38930,662,250,162)]:
        path=REVIEW/('pancreas-'+sex+'-v1.3-original-primitives.json');p=json.loads(path.read_text())
        assert p['all_scene_nodes_inspected'] and p['all_source_meshes_inspected']
        assert len(p['records'])==5 and sum(r['triangles'] for r in p['records'])==total
        assert {r['source_ontology_id'] for r in p['records']}=={'UBERON:0001151','UBERON:0001150','UBERON:0010373','UBERON:0001069','FMA:14517'}
        assert all(r['semantic_metadata_exact_match'] for r in p['records'])
        assert all(r['source_geometry_modified'] is False for r in p['records'])
        b=json.loads((REVIEW/('pancreas-'+sex+'-v1.3-boundary-review.json')).read_text())
        assert b['source_inventory_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
        assert b['source_boundary_edge_occurrences']==boundary
        assert b['exact_boundary_pair_edges']==pairs and b['unmatched_boundary_edges']==unmatched
        assert 2*pairs+unmatched==boundary and b['multiple_owner_boundary_edges']==0
        assert all(r['same_direction_edges']==0 for r in b['pairs'])
        assert b['source_meshes_modified_or_fused'] is False and b['clinical_approval'] is False
        if sex=='female':
            assert sum(r['zero_area_triangles'] for r in p['records'])==8
            assert sum(r['exact_position_nonmanifold_edges'] for r in p['records'])==8
        else:
            assert sum(r['exact_position_nonmanifold_edges'] for r in p['records'])==12
            assert sorted(c['edges'] for c in b['unmatched_boundary_components'])==[56,106]


def test_rendered_figures_preserve_all_source_triangles_without_registration():
    p=json.loads((REVIEW/'source-figure-review.json').read_text())
    assert p['source_geometry_repaired'] is False and p['runtime_promoted'] is False and p['clinical_approval'] is False
    assert len(p['figures'])==4
    for f in p['figures']:
        assert hashlib.sha256((REVIEW/f['file']).read_bytes()).hexdigest()==f['sha256']
        assert len(f['panels'])==6
        assert f['panels'][0]['source_triangle_count']==sum(r['source_triangle_count'] for r in f['panels'][1:])
        assert all(r['source_vertex_or_face_values_changed'] is False for r in f['panels'])
