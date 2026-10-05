"""Generic pelvic anatomy cannot stand in for anal tumour layers, nodes or systemic staging."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.check_msk_fidelity import audit, inspect_binding, requirements_for, validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT = Path(__file__).resolve().parents[1]


def inventory():
    data = json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())
    item = next(i for i in data['investigations'] if i['investigation_id']=='ra.mri-anal-cancer')
    return {**data, 'investigations':[item], 'scope':{'catalog_investigation_ids':[item['investigation_id']]}}, item


def test_effective_report_layers_stations_and_conditional_sites_are_bound():
    data,item=inventory()
    ref=detail(Curriculum(),resolve(item['investigation_id']))['radiology_reference']
    validate_reporting_snapshots(data,{item['investigation_id']:ref['reporting']})
    assert item['source_contract_sha256']==digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')})
    leaves={r['id']:r for r in requirements_for(item)}
    assert len(leaves)==375
    for suffix in ['primary.complete_boundary','primary.greatest_dimension','anal_canal.dentate_line_limit',
                   'intersphincteric_plane.outer_interface','external_sphincter.lower_extent',
                   'right_puborectalis.covered_extent','left_levator_ani.covered_extent',
                   'right_obturator_nodes.each_actual_node','left_inguinal_nodes.station_landmarks',
                   'vagina.each_abutment_or_invasion_interface','distal_rectum.primary_framework_limit',
                   'nonregional_nodes.coverage_and_confirmation_limit','distant_sites.uncovered_sites',
                   'fistula_if_present.unresolved_course','treated_bed_if_applicable.treatment_interval',
                   'acquisition.dwi_adc_if_acquired']:
        assert 'anal_cancer.'+suffix in leaves
    assert {r['checklist_index'] for s in item['structures'] for r in s['report_refs']}==set(range(5))
    result=audit(data,{'assets':[{'id':'generic-pelvis','kind':'model',
        'investigation_ids':[item['investigation_id']],
        'structure_ids':['anal_cancer.primary','anal_cancer.external_sphincter']}]},
        expected_catalog_ids={item['investigation_id']})
    assert result['representation_requirements']==1125
    assert result['counts']=={'verified':0,'unverified':0,'missing':1125}


def test_source_context_cannot_borrow_normal_anatomy_side_or_systemic_coverage():
    _,item=inventory();leaves={r['id']:r for r in requirements_for(item)}
    normal={'kind':'clinical_image','modality':'MRI','source_context':{'depicted_state':'normal_anatomy'}}
    assert 'source_context_purpose_mismatch' in inspect_binding(normal,leaves['anal_cancer.primary.complete_boundary'])
    left={**normal,'source_context':{'depicted_state':'normal_anatomy','laterality':'left'}}
    assert 'source_context_laterality_mismatch' in inspect_binding(left,leaves['anal_cancer.right_puborectalis.covered_extent'])
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(normal,leaves['anal_cancer.distant_sites.lesion_boundary'])


def test_staging_and_response_are_explicitly_unapproved():
    _,item=inventory()
    assert item['clinical_validation_status'].startswith('draft_')
    issues=' '.join(item['source_scope_issues'])
    assert 'histology' in issues and 'AJCC8' in issues and 'not assumed directly visible' in issues
    assert 'full guideline review' in issues
    assert all(s['requires_site_instantiation'] for s in item['structures'])
    functional=' '.join(item['functional_evidence_requirements'])
    assert 'clinical confirmation' in functional and 'complete acquired multiplanar' in functional
