"""Device position/appearance cannot substitute for actual components, interfaces or function."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_radiology_fidelity import digest
from tools.check_msk_fidelity import audit,requirements_for,validate_reporting_snapshots
ROOT=Path(__file__).resolve().parents[1];IDENT='ra.cardiovascular-devices'
def test_each_actual_component_route_and_reporting_field_are_bound():
    data=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text());item=next(i for i in data['investigations'] if i['investigation_id']==IDENT);ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];single={**data,'scope':{**data['scope'],'catalog_investigation_ids':[IDENT]},'investigations':[item]}
    assert item['source_contract_sha256']==digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')})
    validate_reporting_snapshots(single,{IDENT:ref['reporting']});assert len(item['structures'])==92 and len(requirements_for(item))==894
    assert {r['checklist_index'] for s in item['structures'] for r in s['report_refs']}==set(range(5))
    ids={p['id'] for p in requirements_for(item)}
    for suffix in ['generator_header.every_actual_port','coronary_sinus_lead.actual_tip_and_target_interface','conduction_system_lead.complete_visible_course',
        'lead_fragment.source_resolved_separation_or_externalisation','subcutaneous_electrode.every_electrode_or_coil',
        'tricuspid_mechanical.every_actual_leaflet_disc_or_occluder_if_resolved','appendage_occluder.every_actual_disc_waist_plug_or_anchor',
        'lvad_inflow.every_inlet_outlet_or_sidehole','lvad_outflow.every_inlet_outlet_or_sidehole','right_temporary_pump.each_native_entry_landing_and_branch_interface',
        'balloon_pump.proximal_distal_marker_and_extent','left_svc.device_to_lumen_or_wall_relation','pericardium.unavailable_functional_or_clinical_context',
        'complications.fracture_vs_projection_or_tie_down_mimic','function_and_system.current_device_specific_instructions_and_version']:
        assert 'cardiovascular_device.'+suffix in ids
    result=audit(single,{'assets':[{'id':'generic-heart','kind':'model','investigation_ids':[IDENT],'structure_ids':['cardiovascular_device.right_ventricle','cardiovascular_device.lvad_pump']}]},expected_catalog_ids={IDENT})
    assert result['counts']=={'verified':0,'unverified':0,'missing':2682}
    assert all(s['requires_site_instantiation'] for s in item['structures']) and item['clinical_validation_status'].startswith('draft_')
def test_no_normal_preset_or_generic_position_can_establish_device_safety():
    ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];s=ref['walkthrough']['steps'];r=ref['reporting']
    assert all(step['normal']=={} for step in s)
    assert 'abandoned/retained' in s[0]['tip'] and 'not automatically fracture' in s[1]['tip']
    assert 'proximal/distal markers' in s[2]['findings'][1] and 'LV-assist inflow from arterial outflow' in s[2]['tip']
    assert 'cannot exclude subtle perforation' in s[3]['tip'] and 'Generator appearance alone does not clear MRI' in s[4]['tip']
    assert any('manufacturer conditions' in line for line in r['protocol'])
    assert 'does not contain implanted generators' in ref['walkthrough']['spatial_model']['reporting_aim']
    assert any('coronary-sinus lead' in line and 'not an assumed intracavitary' in line for line in r['pitfalls'])
def test_source_license_url_and_correction_do_not_borrow_clinical_approval():
    proof=json.loads((ROOT/'docs/cardiovascular-device-source-review.json').read_text());sources={s['pmcid']:s for s in proof['sources']}
    assert sources['PMC4286824']['actual_license_url']=='https://creativecommons.org/licenses/by-nc-sa/3.0/'
    assert sources['PMC6837806']['actual_license_url']=='https://creativecommons.org/licenses/by/4.0/'
    assert not sources['PMC4286824']['commercial_images_reused'] and not proof['structure_coverage_granted']
    assert 'Review Article' in sources['PMC8661294']['correction_scope']
    assert sources['PMC11211236']['doi']=='10.1016/j.jocmr.2024.100995'
    assert not proof['unavailable_pmc7758755_snapshot']['rights_or_uninspected_contents_borrowed']
