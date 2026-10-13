"""Actual whole-module questions, report scope and exclusive source bindings."""
import copy
import json
from pathlib import Path
import pytest
from primer.curriculum import Curriculum,_validate_lesson_media
from primer import radiology_catalog
from primer.module_media import radiology_model_props
from primer.quiz import score_quiz
from tools.check_radiology_fidelity import build_scope,digest
from tools.anatomy_sources.pulmonary_ui_compatibility import restore_previous_app
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/pulmonary-nodule-integration-review-20261011'


def test_complete_amended_questions_and_unfilled_reporting_scope():
    c=Curriculum();node=c.nodes['rad.4.pulmonary-nodule']
    amended=json.loads((ROOT/'docs/pulmonary-nodule-independent-review-20261011/clinical-amendment-proposal.json').read_text())
    assert node['quiz']==amended['independent_amended_questions'] and len(node['quiz'])==13
    assert all(score_quiz([q],[q['answer']])['score']==1 for q in node['quiz'])
    ref=radiology_catalog.detail(c,radiology_catalog.resolve('ra.ct-pulmonary-nodules'))['radiology_reference']
    assert ref['source_native_only'] is True and ref['key_images']==[]
    assert node['radiology_reference']['key_images']==[]
    assert ref['walkthrough']['preset_mode']=='assessment-prompts'
    assert len(ref['walkthrough']['steps'])==5
    assert all(s['parts']==s['images']==[] and s['landmark']=='native-source' for s in ref['walkthrough']['steps'])
    assert all('[ ]' in text for s in ref['walkthrough']['steps'] for text in s['normal'].values())
    inventory=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())
    case=next(r for r in inventory['investigations'] if r['investigation_id']=='ra.ct-pulmonary-nodules')
    assert len(case['structures'])==79 and sum(len(s['required_parts']) for s in case['structures'])==625
    assert case['representation_obligations_floor']==1875 and case['verified_representation_obligations']==0
    assert not case['clinical_approval'] and not case['fine_anatomical_approval'] and not case['structure_coverage_granted']
    assert case['source_contract_sha256']==digest({k:ref[k] for k in ['reporting','report_templates','walkthrough','reading']})


def test_all_other_effective_contracts_and_original_inventory_entries_preserved():
    current=build_scope();lookup={r['id']:r['reporting_contract_sha256'] for r in current['investigations']}
    base=json.loads((REVIEW/'baseline-effective-contracts.json').read_text())
    assert len(base['investigations'])==len(lookup)==136
    assert [r['id'] for r in base['investigations'] if r['sha256']!=lookup[r['id']]]==['ra.thoracic-ultrasound','ra.ct-pulmonary-nodules']
    original=json.loads((REVIEW/'baseline/data/radiology/non-msk-structure-requirements.json').read_text())
    actual=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())
    actual['investigations']=[r for r in actual['investigations'] if r['investigation_id']!='ra.ct-pulmonary-nodules']
    assert actual['scope']['catalog_investigation_ids'].pop()=='ra.ct-pulmonary-nodules'
    assert actual==original


@pytest.mark.parametrize('field,value',[('node_id','rad.5.brain-anatomy'),('source_native_only',False),('native_inspectors',[])])
def test_shared_source_model_rejects_cross_lesson_or_missing_native_binding(field,value):
    node=copy.deepcopy(Curriculum().nodes['rad.4.pulmonary-nodule'])
    model=next(m for m in node['lesson_media'] if m.get('renderer')=='radiology-anatomy')
    assert model['props']['source_native_only'] is True
    model['props'][field]=value
    with pytest.raises(ValueError,match='cross-lesson'):_validate_lesson_media(node)


def test_native_only_flag_cannot_promote_another_lesson():
    node=copy.deepcopy(Curriculum().nodes['rad.5.brain-anatomy'])
    node['radiology_reference']['spatial_model']['source_native_only']=True
    with pytest.raises(ValueError,match='exact pulmonary source'):radiology_model_props(node)


def test_ui_bridge_rejects_any_unscoped_app_change():
    body=(ROOT/'web/app.js').read_text()
    from tools.pulmonary_evidence_storage import historical_evidence_bytes
    baseline=historical_evidence_bytes('docs/pulmonary-nodule-integration-review-20261011/baseline/web/app.js','d77de3b299fc8af358e6c5fd2c785b22f3a8f19aa89f27a713d40be7c22b11a0').decode()
    assert restore_previous_app(body)==baseline
    with pytest.raises(ValueError,match='Unreviewed'):restore_previous_app(body+'\n// Unreviewed change\n')
