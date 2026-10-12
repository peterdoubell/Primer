"""Frozen source/evidence guards; no clinical completion from technical parity."""
from pathlib import Path
import hashlib,json
from primer.quiz import score_quiz
from tools.pulmonary_readout_review_guard import reconstruct_original_readout
ROOT=Path(__file__).resolve().parents[1]
OWNER=ROOT/'docs/pulmonary-nodule-source-review-20261011'
REVIEW=ROOT/'docs/pulmonary-nodule-independent-review-20261011'

def test_every_frozen_source_unit_matches_proposal_and_whole_study_oracle():
    p=json.loads((OWNER/'integration-proposal.json').read_text());o=json.loads((REVIEW/'source-oracle.json').read_text())
    assert o['integration_proposal_sha256']==hashlib.sha256((OWNER/'integration-proposal.json').read_bytes()).hexdigest()
    assert len(p['runtime_files'])==483 and p['runtime_source_payload_files']==480
    for r in p['runtime_files']:
        body=(ROOT/r['path']).read_bytes()
        if r['path']=='web/anatomy/lidc-idri-0525/reference.js':body=reconstruct_original_readout(body)
        assert len(body)==r['bytes'] and hashlib.sha256(body).hexdigest()==r['sha256']
    assert o['full_original_CT_instances']==429 and o['full_original_CT_samples']==112459776
    assert o['complete_original_SEG_samples']==19136512 and o['complete_original_SEG_objects']==o['complete_original_SR_objects']==8
    assert o['XML_sessions']==4 and o['XML_marks']==33 and o['XML_exclusion_contours']==1
    assert sum(r['triangles'] for r in o['annotations'])==12568
    assert all(r['balanced_oriented_cell_boundary'] for r in o['annotations'])
    assert not o['acquired_collimation_verified']


def test_both_real_reader_proofs_pin_actual_source_pixels_and_complete_GPU_buffers():
    m=ROOT/'web/anatomy/lidc-idri-0525/manifest.json';o=json.loads((REVIEW/'source-oracle.json').read_text());b=json.loads((REVIEW/'browser/proof.json').read_text())
    assert b['manifest_sha256']==o['manifest_sha256']==hashlib.sha256(m.read_bytes()).hexdigest()
    assert [r['width'] for r in b['rows']]==[1440,390]
    expected={r['id']:r for r in o['GPU_buffer_oracles']}
    for r in b['rows']:
        assert r['original_RGB_planes']==42 and len(r['original_XML_marks'])==33 and r['errors']==[] and not r['body_overflow']
        assert len(r['full_original_models_and_GPU_buffers'])==8
        for a in r['full_original_models_and_GPU_buffers']:
            assert a['GPU']['sha256']==expected[a['id']]['sha256'] and a['GPU']['bytes']==expected[a['id']]['bytes']
            assert a['GPU']['draw']['count']==expected[a['id']]['triangles']*3
    assert len(b['failure_recovery'])==4 and all(r['recovered'] for r in b['failure_recovery'])
    supplement=json.loads((REVIEW/'browser/overlay-cursor-supplement.json').read_text())
    assert supplement['manifest_sha256']==o['manifest_sha256']
    assert [r['width'] for r in supplement['rows']]==[1440,390]
    for r in supplement['rows']:
        assert len(r['overlays'])==8 and len(r['keyboard_directions'])==12
        assert r['previously_loaded_source_planes_physically_cleared']==[True,True,True]
        assert r['corrupt_reload_refused'] and r['exact_source_recovered'] and r['errors']==[]


def test_clinical_amendments_preserve_originals_answers_and_all_unverified_scope():
    c=json.loads((REVIEW/'clinical-amendment-proposal.json').read_text());owner=json.loads((OWNER/'complete-clinical-question-proposal.json').read_text());scope=json.loads((OWNER/'structure-requirements-proposal.json').read_text())
    assert c['original_questions']==[r['original'] for r in owner['questions']]
    assert c['owner_proposed_questions']==[r['proposed'] for r in owner['questions']]
    assert [r['index'] for r in c['bounded_explain_only_amendments']]==[8,12]
    for a,b in zip(c['owner_proposed_questions'],c['independent_amended_questions']):
        assert {k:v for k,v in a.items() if k!='explain'}=={k:v for k,v in b.items() if k!='explain'}
    for name in ['original_questions','owner_proposed_questions','independent_amended_questions']:
        for q in c[name]:assert score_quiz([q],[str(q['answer'])])['score']==1
    assert len(scope['structures'])==79 and sum(len(r['required_parts']) for r in scope['structures'])==625
    assert scope['representation_obligations_floor']==1875 and scope['verified_representation_obligations']==0
    for r in scope['structures']:
        assert r['image_bindings']==r['schematic_bindings']==r['model_bindings']==[]
        assert not r['clinical_approval'] and not r['fine_anatomical_approval']
    assert not c['clinical_approval'] and not c['fine_anatomical_approval'] and not c['structure_coverage_granted']


def test_readout_guard_rejects_unscoped_reader_and_receipt_changes():
    import pytest
    body=(ROOT/'web/anatomy/lidc-idri-0525/reference.js').read_bytes()
    assert reconstruct_original_readout(body)==(REVIEW/'frozen-reference.js').read_bytes()
    with pytest.raises(ValueError,match='Unreviewed pulmonary reader change'):
        reconstruct_original_readout(body.replace(b'clearMesh()',b'clearMesh(1)',1))
    receipt=(REVIEW/'root-readout-provenance-repair-candidate.json').read_bytes()
    with pytest.raises(ValueError,match='Unreviewed readout amendment record'):
        reconstruct_original_readout(body,receipt+b' ')


def test_current_reader_distinguishes_original_binary_cells_from_missing_frames():
    b=json.loads((REVIEW/'browser-readout-amended/proof.json').read_text())
    r=json.loads((REVIEW/'browser-readout-amended/readout-proof.json').read_text())
    current=(ROOT/'web/anatomy/lidc-idri-0525/reference.js').read_bytes()
    assert hashlib.sha256(current).hexdigest()==b['reference_js_sha256']==r['current_JS_sha256']
    assert r['pure_original_frame_vs_padding_cases']==3432
    assert [x['width'] for x in r['rows']]==[1440,390]
    for row in r['rows']:
        assert len(row['checks'])==32 and row['errors']==[] and not row['body_overflow']
        for case in row['checks']:
            assert case['actual_readout'].endswith(' · '+case['expected'])
            if case['kind']=='absent-source-frame':
                assert 'selected released SEG cell' not in case['actual_readout']
            else:
                assert 'original released frame index' in case['actual_readout']
    assert all(x['original_RGB_planes']==42 and len(x['full_original_models_and_GPU_buffers'])==8 and x['errors']==[] for x in b['rows'])
