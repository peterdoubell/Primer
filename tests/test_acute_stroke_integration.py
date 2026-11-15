from tools.current_labs_runtime_compatibility import before_current_labs_bytes
"""Current stroke source/report requirements, zero anatomy credit and scope invariants."""
import copy
import hashlib
import json
from pathlib import Path
import re
import pytest
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
from tools.anatomy_sources import integrate_acute_stroke_sources as integration
from tools.check_msk_fidelity import audit,requirements_for,validate_reporting_snapshots,inspect_binding
from tools.check_radiology_fidelity import digest
from tools.msk_runtime_rights import license_issues
from tools.pulmonary_data_compatibility import restore_prior_view, restore_prior_contracts
ROOT=Path(__file__).resolve().parents[1];INV=integration.INV

@pytest.fixture(scope='module')
def state():
    integration.clear_catalog_caches();c=Curriculum();ref=catalog.detail(c,catalog.resolve(INV))['radiology_reference']
    inventory=json.loads((ROOT/integration.DATA_PATHS[2]).read_text());scope=next(i for i in inventory['investigations'] if i['investigation_id']==INV)
    rows=json.loads((ROOT/integration.DATA_PATHS[0]).read_text())[INV]
    assets=[a for a in json.loads((ROOT/integration.DATA_PATHS[1]).read_text())['assets'] if a['id'].startswith(integration.PREFIX)]
    receipt=json.loads((ROOT/integration.RECEIPT).read_text());return c,ref,inventory,scope,rows,assets,receipt


def test_independently_cleared_complete_CTP_packet_is_registered_without_native_no_go(state):
    c,ref,inventory,scope,rows,assets,receipt=state
    proposal,original,review=integration.source_inputs();assert len(rows)==len(assets)==13
    assert {r['id'] for r in rows}=={integration.FIG(i) for i in range(1,14)}
    for row,asset in zip(rows,assets):
        raw=(ROOT/'web'/row['src'].removeprefix('/app/')).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256']
        assert license_issues(asset,ROOT)==[] and row['original_publication_pdf']['unchanged_original'] is True
        assert asset['structure_ids']==[] and asset['requirement_coverage']=={}
        assert asset['anatomical_review']['status']=='pending'
        assert all(row[k] is False and asset[k] is False for k in ('clinical_approval','fine_anatomical_approval','patient_specific_3D_approved'))
    assert receipt['native_source_bound'] is False and receipt['native_rights_conflict_NO_GO_retained'] is True
    assert not any('isles22' in str(r) for r in ref['structure_atlas'])


def test_real_CT_MRI_tracing_and_processing_roles_are_partitioned(state):
    *_,rows,assets,receipt=state;by={r['figure_number']:r for r in rows}
    assert sum(len(r['source_context']['panel_types']) for r in rows)==85
    assert sum(t=='MRI' for r in rows for t in r['source_context']['panel_types'].values())==1
    assert sum(t=='CT' for r in rows for t in r['source_context']['panel_types'].values())==83
    assert sum(t=='Haemodynamic tracing' for r in rows for t in r['source_context']['panel_types'].values())==1
    assert 'F' not in by[6]['clinical_panels'] and by[6]['ancillary_panels'][0]['kind']=='MRI'
    assert 'following day' in by[6]['original_caption'] and 'not registered' in by[6]['ancillary_panels'][0]['limits']
    assert 'timeAttenuationCurve' not in by[8]['clinical_panels']
    assert by[8]['source_context']['panel_types']['timeAttenuationCurve']=='Haemodynamic tracing'
    assert by[8]['source_context']['cohort_statistics_artwork'] is False
    roles=by[13]['source_context']['original_panel_source_roles']
    assert list(roles)==['A','B','C','D','E','F','G','H','I','K','L','M']
    assert 'different_timepoint_with_motion' in roles['B'] and 'automated_MIP' in roles['C'] and 'manual_MIP' in roles['D']
    for row,asset in zip(rows,assets):
        catalog._validate_source_panel_roles(row);assert inspect_binding(asset,{'modality_scope':['CT','MRI'],'context_requirements':[]})==[]
        assert row['source_context']['numeric_perfusion_map_arrays_supplied'] is False
        assert row['source_context']['patient_3D_supplied'] is False


def test_five_real_report_actions_are_unfilled_and_scope_fields_match(state):
    _,ref,inventory,scope,*_=state;walk=ref['walkthrough'];assert walk['preset_mode']=='assessment-prompts' and len(walk['steps'])==5
    for s in walk['steps']:
        assert s['parts']==[] and s['images'] and all(i.startswith(integration.PREFIX) for i in s['images'])
        assert list(s['normal'])==s['sections']
        assert all('[ ]' in text and 'No ' not in text for text in s['normal'].values())
        assert all('[ ]' in text or '__' in text for text in s['findings'])
    assert walk['start']['module_illustrations'] is False and ref['key_images']==[]
    bodies={s['heading']:s['body'] for s in ref['report_templates'][0]['sections']}
    assert 'CTV/MRV' in bodies['ARTERIAL FINDINGS'] and 'unassessed' in bodies['ARTERIAL FINDINGS']
    assert 'Software/version' in bodies['COLLATERALS AND PERFUSION'] and 'thresholds/units' in bodies['COLLATERALS AND PERFUSION']
    assert 'level' in bodies['MASS EFFECT AND OTHER FINDINGS'] and 'method' in bodies['MASS EFFECT AND OTHER FINDINGS']
    validate_reporting_snapshots({'investigations':[scope]},{INV:ref['reporting']})
    assert scope['source_contract_sha256']==digest({k:ref[k] for k in scope['source_contract_definition']})
    assert {r['url'] for r in integration.PRIMARY}.issubset({r['url'] for r in ref['reading']})


def test_every_named_scope_and_current_quiz_remains_unfulfilled(state):
    c,ref,inventory,scope,rows,assets,receipt=state
    original=json.loads((ROOT/integration.FOLDER/'structure-requirements-proposal.json').read_text())
    assert [g['id'] for g in scope['structures']]==[g['id'] for g in original['structures']]
    assert len(scope['structures'])==369 and len(requirements_for(scope))==3692
    assert scope['shared_curriculum_quiz_sha256']==digest(c.node(integration.MODULE)['quiz'])
    quizzes=[g for g in scope['structures'] if g['tissue_class']=='curriculum_quiz_dependency']
    assert len(quizzes)==12
    for i,g in enumerate(quizzes):assert g['literal_curriculum_quiz']==c.node(integration.MODULE)['quiz'][i] and g['original_literal_curriculum_quiz']==[x for x in original['structures'] if x['tissue_class']=='curriculum_quiz_dependency'][i]['literal_curriculum_quiz']
    assert all(g[k] is False for g in scope['structures'] for k in ('clinical_approval','fine_anatomical_approval','structure_coverage_granted'))
    result=audit({'investigations':[scope],'scope':{'catalog_investigation_ids':[INV]},'clinical_validation_status':'draft_requires_neuroradiologist_review'},{'assets':assets},ROOT,expected_catalog_ids={INV})
    assert result['counts']=={'verified':0,'unverified':0,'missing':11076}
    assert receipt['full_patient_denominator_known'] is False
    for g in scope['structures']:
        if g['tissue_class']=='MCA_ASPECTS_region':assert g['walkthrough_step_indices']==[0] and [r['checklist_index'] for r in g['report_refs']]==[1]
        if g['tissue_class']=='haemorrhage_compartment':assert g['walkthrough_step_indices']==[1,4] and [r['checklist_index'] for r in g['report_refs']]==[0,4]


def test_all_unrelated_values_and_effective_nonstroke_reports_are_unchanged(state):
    c,ref,inventory,scope,rows,assets,receipt=state;ids={r['id'] for r in rows}
    for p in integration.DATA_PATHS:
        raw=before_current_labs_bytes(str(p),(ROOT/p).read_bytes()).decode()
        _,tokens=restore_prior_view(p,json.loads(raw),integration.unrelated_tokens(raw,p,ids))
        assert tokens==receipt['unrelated_token_fingerprints'][str(p)]
    assert restore_prior_contracts(integration.nonstroke_contracts(c))==receipt['nonstroke_effective_contract_digests']
    assert receipt['nonstroke_effective_contracts_unchanged']==135==len(catalog.catalogue()['investigations'])-1
    assert receipt['all_unrelated_JSON_value_tokens_unchanged'] is True


def test_negative_current_report_snapshot_and_source_panel_promotion_are_rejected(state):
    _,ref,inventory,scope,rows,assets,receipt=state
    bad=copy.deepcopy(scope);bad['structures'][0]['report_refs'][0]['detail']='silently changed'
    with pytest.raises(ValueError,match='stale'):validate_reporting_snapshots({'investigations':[bad]},{INV:ref['reporting']})
    mixed=copy.deepcopy(next(r for r in rows if r['figure_number']==6));mixed['source_context']['selected_panels'].append('F');mixed['clinical_panels'].append('F')
    with pytest.raises(ValueError,match='modality'):catalog._validate_source_panel_roles(mixed)
    graph=copy.deepcopy(next(r for r in rows if r['figure_number']==8));graph['source_context']['panel_types']['timeAttenuationCurve']='CT'
    with pytest.raises(ValueError,match='contradict'):catalog._validate_source_panel_roles(graph)
    changed=copy.deepcopy(scope);changed['reporting_template_sections'][0]['body']='incorrect full normal report'
    with pytest.raises(ValueError,match='fields changed'):validate_reporting_snapshots({'investigations':[changed]},{INV:ref['reporting']})
