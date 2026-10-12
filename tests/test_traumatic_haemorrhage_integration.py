"""Patient reporting, source modality/case limits and the unreconciled fine-anatomy floor."""
import copy
import hashlib
import json
from pathlib import Path
import re

import pytest

from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
from tools.anatomy_sources import integrate_traumatic_haemorrhage_sources as integration
from tools.anatomy_sources import traumatic_registry_amendment as registry_amendment
from tools.anatomy_sources import stroke_registry_amendment as stroke_amendment
from tools.pulmonary_data_compatibility import restore_prior_view
from tools.check_msk_fidelity import audit,requirements_for,validate_reporting_snapshots,inspect_binding
from tools.check_radiology_fidelity import digest
from tools.msk_runtime_rights import license_issues

ROOT=Path(__file__).resolve().parents[1]
INV='ra.ct-traumatic-haemorrhage'


@pytest.fixture(scope='module')
def state():
    integration.clear_catalog_caches()
    curriculum=Curriculum()
    reference=catalog.detail(curriculum,catalog.resolve(INV))['radiology_reference']
    nontraumatic=catalog.detail(curriculum,catalog.resolve('ra.intracranial-haemorrhage'))['radiology_reference']
    inventory=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())
    item=next(i for i in inventory['investigations'] if i['investigation_id']==INV)
    rows=json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text())[INV]
    assets=[a for a in json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if a['id'].startswith(integration.PREFIX)]
    receipt=json.loads((ROOT/integration.RECEIPT).read_text())
    return curriculum,reference,nontraumatic,inventory,item,rows,assets,receipt


def test_complete_independently_reviewed_packet_is_preserved_and_rights_scoped(state):
    *_,rows,assets,receipt=state
    proof,review,proposal,context,media=integration.validate_sources()
    assert len(media)==34 and sum(r['bytes'] for r in media)==38875353
    assert {r['id'] for r in rows}==set(review['approved_display_ids'])
    assert len(rows)==len(assets)==15
    assert {d['id'] for d in context['documents']}==set(receipt['registered_source_context_document_ids'])
    by_asset={a['id']:a for a in assets}
    for row in rows:
        raw=(ROOT/'web'/row['src'].removeprefix('/app/')).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==row['sha256']
        assert license_issues(by_asset[row['id']],ROOT)==[]
        assert row['original_publication_pdf']['unchanged_original']
        assert row['clinical_approval'] is row['fine_anatomical_approval'] is False
    assert not receipt['source_pixels_or_native_original_files_modified']
    assert not review['fine_structure_coverage_granted'] and not review['patient_specific_3D_approved']


def test_only_traumatic_investigation_receives_new_source_contract_and_shared_gallery(state):
    curriculum,ref,nontraumatic,inventory,item,rows,assets,receipt=state
    assert ref['source_context_documents']==receipt['source_context_documents']
    assert len(ref['source_context_documents'])==3 and 'source_context_documents' not in nontraumatic
    assert digest(nontraumatic)==receipt['nontraumatic_effective_reference_sha256']
    assert {r['id'] for r in ref['structure_atlas']}=={r['id'] for r in rows}
    assert all(not r['id'].startswith(integration.PREFIX) for r in nontraumatic['structure_atlas'])
    assert ref['key_images']==[]
    old_named_images={r['id'] for r in nontraumatic['key_images']}
    assert old_named_images and not any(i.startswith(integration.PREFIX) for i in old_named_images)
    galleries=[m for m in curriculum.node(integration.MODULE)['lesson_media'] if m['kind']=='source-gallery']
    assert galleries and all(g['investigation_ids']==[INV] for g in galleries)
    assert {r['url'] for r in integration.PRIMARY}.issubset({r['url'] for r in ref['reading']})
    assert {r['url'] for r in integration.PRIMARY}.isdisjoint({r['url'] for r in nontraumatic['reading']})


def test_all_five_report_actions_leave_observations_unfilled_and_do_not_highlight_fake_anatomy(state):
    _,ref,*_=state
    walk=ref['walkthrough'];guide=ref['reporting']
    assert walk['preset_mode']=='assessment-prompts' and len(walk['steps'])==5
    expected=['EXTRA-AXIAL BLOOD','PARENCHYMAL INJURY','VENTRICLES','MASS EFFECT','BONE AND COMPARISON']
    for step,heading in zip(walk['steps'],expected):
        assert step['sections']==[heading] and list(step['normal'])==[heading]
        assert re.search(r'\[(?:\s|_)*\]',step['normal'][heading])
        assert 'No ' not in step['normal'][heading]
        assert step['parts']==[]
        assert step['images'] and all(i.startswith(integration.PREFIX) for i in step['images'])
        assert all('__' in finding or '[ ]' in finding for finding in step['findings'])
    assert not walk['start'].get('module_illustrations',True)
    assert walk['start']['images']==[integration.FIG('2-panel-1'),integration.FIG('2-panel-2')]
    bodies={s['heading']:s['body'] for s in ref['report_templates'][0]['sections']}
    assert all('[' in bodies[h] for h in expected)
    assert 'level' in bodies['MASS EFFECT'] and 'method' in bodies['MASS EFFECT'] and ' mm ' in bodies['MASS EFFECT']
    assert 'Unassessed' in bodies['VENTRICLES'] and 'MRI if actually acquired' in bodies['PARENCHYMAL INJURY']
    tips=' '.join(guide['pitfalls'])
    assert 'usually' in tips and 'suture diastasis/fracture' in tips
    assert 'does not exclude nonhaemorrhagic' in tips and 'do not establish axonal histology' in tips
    assert 'does not establish mechanism or inevitable outcome' in tips


def test_full_source_panels_preserve_ct_mri_cases_serial_times_and_caliper_limits(state):
    *_,rows,assets,receipt=state
    by_figure={r['figure_identifier']:r for r in rows}
    assert sum(len(r['source_context'].get('panel_types',{})) for r in rows)==67
    assert sum(t=='MRI' for r in rows for t in r['source_context'].get('panel_types',{}).values())==4
    panel=by_figure['2-panel-2'];c=panel['source_context']
    assert panel['figure_number']=='2.2' and panel['source_figure_label']=='Figure 2 Panel 2'
    assert c['panel_types']['L4']==c['panel_types']['L5']=='MRI'
    assert set(panel['clinical_panels']).isdisjoint({'L4','L5'})
    assert panel['ancillary_panels'][0]['panels']==['L4','L5']
    assert '2 hours later' in c['time_descriptions']['J4'] and '2 days later' in c['time_descriptions']['J5']
    assert 'Likely small intracerebral haemorrhage' in c['source_reconsidered_initial_J3_diagnosis']
    assert not c['cross_modality_same_patient_registration_established']
    assert by_figure['9']['source_context']['different_patients_explicit_in_caption']==[['A'],['B']]
    calipers=by_figure['2-panel-1']['source_context']
    assert '1.94 cm' in calipers['source_caliper_claims']['F2'] and '2.09 cm' in calipers['source_caliper_claims']['F3']
    assert not calipers['source_numeric_claims_independently_calibrated']
    for row,asset in zip(rows,assets):
        assert row['id']==asset['id'] and row['source_context']==asset['source_context']
        catalog._validate_source_panel_roles(row)
        assert inspect_binding(asset,{'modality_scope':['CT','MRI'],'context_requirements':[]})==[]
        if row['modality']=='Schematic':
            assert row['source_context']['statistical_population_plot_not_patient_image']
            assert 'clinical_panels' not in row
    assert not by_figure['7']['source_context']['matching_CT_supplied']


def test_full_report_contract_and_named_fine_anatomy_floor_remain_unapproved(state):
    curriculum,ref,_,inventory,item,rows,assets,receipt=state
    validate_reporting_snapshots({'investigations':[item]},{INV:ref['reporting']})
    contract={k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']}
    assert digest(contract)==item['source_contract_sha256']==receipt['effective_report_contract_sha256']
    assert digest(ref['source_context_documents'])==item['source_context_documents_sha256']
    parts=requirements_for(item)
    assert len(item['structures'])==335 and len(parts)==3628
    names=' '.join(p['id'] for p in parts)
    for structure in ['periosteal_dura','meningeal_dura','arachnoid_mater','pia_mater','arachnoid_trabeculae','arachnoid_granulations',
                      'lateral_temporal_horn','foramen_of_luschka','cerebral_aqueduct','quadrigeminal_cistern','cribriform_plate',
                      'optic_canal','middle_meningeal_groove','cerebellar_tonsil','pons_upper','brainstem_paramedian_perforators',
                      'uncal_downward_transtentorial','subfalcine','tonsillar','midline_shift_perpendicular_falx',
                      'traumatic_arterial_dissection','traumatic_pseudoaneurysm','venous_sinus_injury_or_thrombosis',
                      'subdural_hygroma','penetrating_injury','postoperative_trauma_state','skull_base_CSF_communication']:
        assert structure in names
    assert all(s['requires_site_instantiation'] and s['site_instantiation_status']=='pending' for s in item['structures'])
    assert all(s['candidate_sources_are_partial_examples_not_coverage'] for s in item['structures'])
    assert item['scope_review_flags']['named_parts_are_a_floor_not_full_patient_denominator']
    assert not item['scope_review_flags']['unbounded_actual_patient_structure_denominator_known']
    assert not item['clinical_approval'] and not item['fine_anatomical_approval']
    assert len(item['non_anatomical_report_dependencies'])==6
    quiz=[s for s in item['structures'] if s['requirement_basis']=='literal_shared_curriculum_quiz']
    assert len(quiz)==13 and digest(curriculum.node(integration.MODULE)['quiz'])==item['shared_curriculum_quiz_sha256']
    assert all(not s['candidate_figure_ids'] for s in quiz)
    assert sum(s['source_case_context']=='nontraumatic_or_separate_shared_dependency' for s in quiz)==9
    assert 'AVM_nidus_maximum_diameter' in names and 'subependymal_vein' in names and 'chronic_hemosiderin_ferritin_rim' in names
    result=audit({'investigations':[item],'scope':{'catalog_investigation_ids':[INV]},'clinical_validation_status':'draft_requires_neuroradiologist_review'},
                 {'assets':assets},ROOT,expected_catalog_ids={INV})
    assert result['counts']=={'verified':0,'unverified':0,'missing':10884}
    assert all(a['structure_ids']==[] and a['requirement_coverage']=={} and a['anatomical_review']['status']=='pending' for a in assets)


def test_unrelated_value_tokens_and_nontraumatic_source_contract_are_preserved(state):
    *_,rows,assets,receipt=state
    ids={r['id'] for r in rows}
    for path in integration.DATA_PATHS:
        raw=(ROOT/path).read_text()
        actual=integration.unrelated_tokens(raw,path,ids)
        data,actual=restore_prior_view(path,json.loads(raw),actual)
        _,actual=stroke_amendment.restore_prior_view(path,data,actual)
        assert actual==receipt['unrelated_token_fingerprints'][str(path)]
    assert receipt['all_unrelated_JSON_value_tokens_unchanged']
    assert receipt['nontraumatic_effective_reference_unchanged']


@pytest.mark.parametrize('mutation',['cross_scope','missing_figure','invented_clinical_approval','invented_coverage','wrong_document'])
def test_cross_scope_or_unreviewed_claims_are_rejected_before_data_mutation(mutation):
    proof,review,proposal,context,_=integration.validate_sources()
    proof=copy.deepcopy(proof);review=copy.deepcopy(review);proposal=copy.deepcopy(proposal);context=copy.deepcopy(context)
    if mutation=='cross_scope':proposal['investigation_id']='ra.intracranial-haemorrhage'
    elif mutation=='missing_figure':proposal['images'].pop()
    elif mutation=='invented_clinical_approval':review['patient_specific_3D_approved']=True
    elif mutation=='invented_coverage':proposal['assets'][0]['structure_ids']=['whole_brain']
    else:context['documents'][0]['id']='unreviewed-document'
    with pytest.raises(ValueError):integration.validate_approval_contract(proof,review,proposal,context)


def test_corrupt_source_bytes_abort_before_any_shared_data_file_is_written(monkeypatch):
    before={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in integration.DATA_PATHS}
    original=Path.read_bytes;bad=ROOT/integration.SOURCE_PREFIX/'centertbi-2024-fig2-panel-2.png'
    def corrupted(path):
        raw=original(path)
        return raw[:-1]+bytes([raw[-1]^1]) if path==bad else raw
    monkeypatch.setattr(Path,'read_bytes',corrupted)
    with pytest.raises(ValueError,match='Frozen public source changed'):integration.integrate()
    assert {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in integration.DATA_PATHS}==before


def test_reporting_changes_cannot_reuse_a_stale_fine_structure_snapshot(state):
    _,ref,_,_,item,*_=state
    changed=copy.deepcopy(ref['reporting']);changed['checklist'][2]['detail']+=' Newly reported CSF pathway.'
    with pytest.raises(ValueError,match='reporting checklist changed'):
        validate_reporting_snapshots({'investigations':[item]},{INV:changed})


def test_exact_canonical_format_amendment_preserves_all_source_contract_values(state):
    path=ROOT/'data/radiology/reporting-steps/neuroradiology.json'
    restored=stroke_amendment.restore_prior_step_raw(path.read_text())
    record=registry_amendment.validate_format_amendment(raw=restored)
    assert record['semantic_values_unchanged']
    assert record['all_unrelated_value_tokens_byte_identical']
    assert record['before_raw_file_SHA256']!=record['after_raw_file_SHA256']
    assert record['source_trauma_field_before_value_token_SHA256']!=record['source_trauma_field_after_value_token_SHA256']
    ids={row['id'] for row in state[5]}
    actual=integration.unrelated_tokens(restored,Path(record['path']),ids)
    assert actual==record['unrelated_value_token_fingerprints']
