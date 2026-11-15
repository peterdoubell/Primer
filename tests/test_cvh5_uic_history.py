"""A passing toy stream or individual range check cannot certify history initialization."""
import hashlib
import json
from pathlib import Path
import pytest
from tools.anatomy_sources.decode_rh_candidate import uic

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/cvh5-uic-history-review'


def test_toy_example_does_not_distinguish_history_and_invalid_inputs_reject():
    data=bytes.fromhex('004cb8fe5d5d5d');expected=[0,1043332]*4
    assert uic(data,8,True)==expected
    assert uic(data,8,True,initial_values=[0]*32)==expected
    with pytest.raises(ValueError):uic(data,8,True,initial_values=[0]*31)
    with pytest.raises(ValueError):uic(data,8,True,initial_values=[-1]*32)


def test_all_resources_and_original_artifacts_remain_bound_and_unchanged():
    r=json.loads((REVIEW/'uic-history-review.json').read_text())
    links=[('source_inventory_sha256','docs/cvh5-pelvic-source-review/original-model-inventory.json'),
           ('candidate_review_sha256','docs/cvh5-candidate-geometry-review/candidate-geometry-review.json'),
           ('normal_review_sha256','docs/cvh5-normal-interpretation-review/normal-interpretation-review.json')]
    for key,path in links:assert r[key]==hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
    assert len(r['resources'])==47 and sum(i['uic1_block_count']>0 for i in r['resources'])==40
    assert r['prefix_face_count']==128 and set(r['histories'])=={'reverse_rank','all_zero','forward_rank','reverse_rank_plus_one'}
    for row in r['resources']:
        assert {x['history'] for x in row['comparisons']}==set(r['histories'])
        baseline=next(x for x in row['comparisons'] if x['history']=='reverse_rank')
        if row['uic1_block_count']:
            assert baseline['status']=='source_ranges_and_spans_accounted' and baseline['affected_faces']==0
        else:assert baseline['status']=='not_applicable_no_uic1_blocks'
    assert not r['source_arrays_changed'] and not r['bootstrap_independently_verified']
    assert not r['finite_hypotheses_are_exhaustive'] and not r['normal_direction_channel_is_independent_original_decoder']
    assert not r['clinical_approval'] and not r['runtime_promoted'] and not r['structure_coverage_granted']


def test_range_passing_alternatives_can_change_geometry_without_approval():
    r=json.loads((REVIEW/'uic-history-review.json').read_text())
    for name,accepted,rejected,changed in [('all_zero',29,11,38139),('forward_rank',34,6,58964),('reverse_rank_plus_one',36,4,62164)]:
        rows=[next(x for x in row['comparisons'] if x['history']==name) for row in r['resources']]
        valid=[x for x in rows if x['status']=='source_ranges_and_spans_accounted']
        assert len(valid)==accepted and sum(x['status']=='rejected_by_numeric_decode_constraints' for x in rows)==rejected
        assert sum(x['affected_faces'] for x in valid)==changed
        assert any(x['first_128_faces']['median_corner_face_dot']<0 for x in valid if x['first_128_faces']['median_corner_face_dot'] is not None)
        assert all(not x['is_clinical_acceptance_threshold'] for x in valid)
        assert all(not x['rejection_is_original_source_defect'] for x in rows if x['status']=='rejected_by_numeric_decode_constraints')
