import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import requirements_for
ROOT=Path(__file__).resolve().parents[1];INV='ra.mri-neck-spaces'
def item():return next(x for x in json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())['investigations'] if x['investigation_id']==INV)
def test_every_compartment_content_and_critical_interface_stays_in_scope():
    r=item();assert r['module_id']=='rad.5.deep-neck-spaces' and len(r['structures'])==107 and len(requirements_for(r))==642
    ids={x['id'] for x in r['structures']}
    for side in ['left','right']:
        for key in ['parapharyngeal_prestyloid_region','carotid_poststyloid_region_if_named','parotid_space','sublingual_space','submandibular_space','posterior_cervical_space','covered_retropharyngeal_region','covered_danger_space_region','prevertebral_region','thyroid_lobe_and_encountered_parathyroid','carotid_sheath_vagus_sympathetic_and_encountered_IX_XI_XII','each_actual_skull_base_neural_or_visceral_spread_connection']:
            assert 'neck_spaces.'+side+'_'+key in ids
    for key in ['alar_or_intercarotid_fascia_if_named','buccopharyngeal_fascia','prevertebral_fascia_and_actual_compartments','danger_space_and_obtained_mediastinal_connection','laryngeal_mucosal_cartilage_and_paraglottic_interfaces','tracheal_wall_lumen_and_source_air_interface','esophageal_wall_lumen_and_surrounding_planes']:
        assert 'neck_spaces.not_applicable_'+key in ids
    assert all(x['requires_site_instantiation'] and x['modality_scope']==['MRI'] for x in r['structures'])
    assert all(0<=ref['checklist_index']<5 for x in r['structures'] for ref in x['report_refs'])
def test_displacement_contact_and_static_signal_do_not_preset_tissue_or_function():
    r=detail(Curriculum(),resolve(INV))['radiology_reference'];w=r['walkthrough']
    assert all(x['normal']=={} for x in w['steps'])
    assert w['spatial_model']['family']=='neck' and 'Partial neck compartment orientation' in w['spatial_model']['reporting_aim']
    assert 'not unique proof' in w['steps'][2]['tip']
    assert 'not an independently seen fascial layer' in w['steps'][0]['tip']
    assert 'does not certify thrombosis' in w['steps'][4]['tip']
    functional=' '.join(item()['functional_evidence_requirements'])
    for term in ['Airway compromise','Histology','microscopic invasion','vessel patency']:assert term in functional
