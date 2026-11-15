"""Arithmetic agreement and plausible geometry cannot clear unverified codec/anatomy assumptions."""
import gzip
import hashlib
import json
from pathlib import Path
import pytest
from tools.anatomy_sources.decode_rh_candidate import R,uic
from tools.anatomy_sources.rh_arithmetic import BitStream

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/cvh5-candidate-geometry-review'


def test_published_integer_and_cube_examples_and_raw_span_accounting():
    assert uic(bytes.fromhex('004cb8fe5d5d5d'),8,True)==[0,1043332]*4
    raw=bytes.fromhex('02 000000bf 0000003f 84eb0f00 0a07 004cb8fe5d5d5d 000000bf 0000003f 84eb0f00 0a07 0d4cb8fe0e4000 000000bf 0000003f 84eb0f00 0a06 4cb8fe0e400e')
    r=R(raw);v=r.floats(8,3)
    assert v==[(-.5,-.5,.5),(.5,-.5,.5),(-.5,.5,.5),(.5,.5,.5),(-.5,.5,-.5),(.5,.5,-.5),(-.5,-.5,-.5),(.5,-.5,-.5)]
    assert r.p==len(raw)
    literal=R(bytes.fromhex('44 0600 0000 1000 ffff'))
    assert literal.ints(3,65535)==[0,16,65535] and literal.p==len(literal.b)
    with pytest.raises(ValueError):R(bytes.fromhex('44 0600 0000')).ints(3,65535)
    with pytest.raises(ValueError):R(b'\x03').floats(1,3)


def test_independent_interval_reader_uniform_symbols_and_literal_values():
    r=BitStream(bytes.fromhex('d80000'))
    assert [r.read_symbol(1028) for _ in range(4)]==[1,2,3,4]
    assert BitStream(bytes.fromhex('e1550000')).read_u16()==0x55e1


def test_all_resources_and_model_names_remain_bound_to_unchanged_source():
    r=json.loads((REVIEW/'candidate-geometry-review.json').read_text())
    source=ROOT/'docs/cvh5-pelvic-source-review';inv=json.loads((source/'original-model-inventory.json').read_text())
    assert r['source_model_inventory_sha256']==hashlib.sha256((source/'original-model-inventory.json').read_bytes()).hexdigest()
    original=gzip.decompress((source/'original-model.u3d.gz').read_bytes())
    assert r['original_u3d_sha256']==hashlib.sha256(original).hexdigest()
    assert r['resource_count']==47 and r['positions']==341454 and r['triangles']==688510
    assert r['declared_unit_scale_to_metres']==.001
    assert {n['name'] for row in r['resources'] for n in row['source_model_nodes']}=={n['name'] for n in inv['model_nodes']}
    for row in r['resources']:
        packed=(REVIEW/row['file']).read_bytes();raw=gzip.decompress(packed)
        assert hashlib.sha256(packed).hexdigest()==row['sha256'] and hashlib.sha256(raw).hexdigest()==row['uncompressed_sha256']
        m=json.loads(raw);assert len(m['positions'])==row['positions'] and len(m['faces'])==row['triangles']
        assert m['counts'][:2]==[row['triangles'],row['positions']]
        block=next(c for c in inv['modifier_chains'] if c['name']==row['resource_name'] and c['chain_type']==1)['modifiers'][-1]
        payload=original[block['data_start']:block['data_end']]
        assert len(payload)==m['source_payload_bytes_accounted'] and hashlib.sha256(payload).hexdigest()==m['source_payload_sha256']
        assert not m['uic1_bootstrap_independently_verified'] and not m['decoder_interpretation_verified']
        assert not row['source_geometry_defect_diagnosis_granted']
    assert not r['normal_attribute_decoding_complete'] and not r['structure_coverage_granted'] and not r['runtime_promoted']


def test_arithmetic_cross_check_is_explicitly_narrow_and_all_views_are_accounted():
    r=json.loads((REVIEW/'arithmetic-cross-check.json').read_text())
    assert r['independent_arithmetic_reader_matches'] and len(r['resources'])==47
    assert all(i['arrays_equal'] for i in r['resources']) and not r['whole_RH_interpretation_independently_verified']
    assert not r['reference_code_distributed'] and not r['clinical_approval']
    assert r['own_arithmetic_sha256']==hashlib.sha256((ROOT/'tools/anatomy_sources/rh_arithmetic.py').read_bytes()).hexdigest()
    assert r['candidate_review_sha256']==hashlib.sha256((REVIEW/'candidate-geometry-review.json').read_bytes()).hexdigest()
    view=json.loads((REVIEW/'candidate-view-review.json').read_text())
    assert view['candidate_review_sha256']==r['candidate_review_sha256']
    assert len(view['figures'])==6 and sum(i['all_candidate_triangles_displayed'] for i in view['figures'])==688510
    assert len({n for i in view['figures'] for n in i['resource_names']})==47
    for i in view['figures']:assert hashlib.sha256((REVIEW/i['file']).read_bytes()).hexdigest()==i['sha256']
    assert not view['decoder_interpretation_verified'] and not view['clinical_approval']
