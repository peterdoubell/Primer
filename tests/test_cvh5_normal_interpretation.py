"""Encoded-direction consistency cannot silently approve a full decoder or clinical anatomy."""
import gzip
import hashlib
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/cvh5-normal-interpretation-review'


def test_all_original_normal_spans_and_candidate_links_are_retained():
    r=json.loads((REVIEW/'normal-interpretation-review.json').read_text())
    candidate=ROOT/'docs/cvh5-candidate-geometry-review';source=ROOT/'docs/cvh5-pelvic-source-review'
    assert r['candidate_geometry_review_sha256']==hashlib.sha256((candidate/'candidate-geometry-review.json').read_bytes()).hexdigest()
    assert r['source_inventory_sha256']==hashlib.sha256((source/'original-model-inventory.json').read_bytes()).hexdigest()
    original=gzip.decompress((source/'original-model.u3d.gz').read_bytes())
    assert r['original_u3d_sha256']==hashlib.sha256(original).hexdigest()
    inv=json.loads((source/'original-model-inventory.json').read_text())
    assert len(r['resources'])==47 and r['normal_count']==642362 and r['held_out_resource_count']==46
    for row in r['resources']:
        packed=(REVIEW/row['file']).read_bytes();raw=gzip.decompress(packed);m=json.loads(raw)
        assert hashlib.sha256(packed).hexdigest()==row['sha256'] and hashlib.sha256(raw).hexdigest()==row['uncompressed_sha256']
        block=next(c for c in inv['modifier_chains'] if c['chain_type']==1 and c['name']==row['resource_name'])['modifiers'][-1]
        payload=original[block['data_start']:block['data_end']]
        assert hashlib.sha256(payload[m['normal_span_start']:m['normal_span_end']]).hexdigest()==row['normal_span_sha256']
        assert len(m['quantized_alpha'])==len(m['quantized_theta'])==len(m['interpreted_normal_vectors'])==row['normal_count']
        assert m['stored_quants_value']==5759 and m['integer_alphabet_size']==5760
        assert m['normal_integer_block']['count']==2*row['normal_count']
        assert not m['normal_attribute_interpretation_verified'] and not m['original_authoring_normals_restored']
    assert not r['whole_decoder_independently_verified'] and not r['uic1_bootstrap_independently_verified']
    assert not r['clinical_approval'] and not r['runtime_promoted'] and not r['structure_coverage_granted']


def test_spherical_formula_has_independent_axis_cases_and_all_vectors_are_unit_length():
    np=pytest.importorskip('numpy')
    from tools.anatomy_sources.review_cvh5_normal_interpretation import angle_vectors
    expected=[[0,0,1],[1,0,0],[0,1,0],[0,0,-1]]
    assert np.allclose(angle_vectors([0,0,1,0],[0,1,1,2],4),expected,atol=1e-15)
    r=json.loads((REVIEW/'normal-interpretation-review.json').read_text())
    for row in r['resources']:
        m=json.loads(gzip.decompress((REVIEW/row['file']).read_bytes()));vectors=np.asarray(m['interpreted_normal_vectors'])
        assert np.isfinite(vectors).all() and np.allclose(np.linalg.norm(vectors,axis=1),1,rtol=0,atol=1e-14)
        assert hashlib.sha256(vectors.astype('<f8').tobytes()).hexdigest()==m['interpreted_vectors_float64_sha256']


def test_held_out_consistency_does_not_become_a_clinical_acceptance_threshold():
    r=json.loads((REVIEW/'normal-interpretation-review.json').read_text())
    assert min(i['median_corner_face_dot'] for i in r['resources'])==pytest.approx(.9556059487551222)
    assert max(i['median_corner_face_dot'] for i in r['resources'])==pytest.approx(.9968866909697226)
    assert all(not i['is_clinical_acceptance_threshold'] for i in r['resources'])
    hypotheses=json.loads((REVIEW/'development-hypotheses.json').read_text())
    assert len(hypotheses)==16
    best=max(hypotheses,key=lambda h:h['median_dot'])
    assert best['alphabet']==5760 and best['layout']=='planar' and best['swap'] is False
    assert best['denominator']==5759
    assert max(h['median_dot'] for h in hypotheses if h['alphabet']==5759)<.01
