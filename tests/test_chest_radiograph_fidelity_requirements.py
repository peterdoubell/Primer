"""Chest radiograph reporting must use actual projection/interfaces, not normal or physiological invention."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import requirements_for,validate_reporting_snapshots
from tools.anatomy_sources.expand_chest_radiograph_requirements import build
ROOT=Path(__file__).resolve().parents[1]
def test_full_covered_structure_floor_and_actual_source_contract():
    item=build();stored=next(i for i in json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())['investigations'] if i['investigation_id']=='ra.chest-radiography')
    assert item==stored and item['module_id']==resolve('ra.chest-radiography')['module_id']=='rad.3.chest-xray'
    assert len(item['structures'])==114 and len(requirements_for(item))==698
    ids={s['id'] for s in item['structures']}
    for key in ['trachea_carina','aortopulmonary_window','azygos_oesophageal','retrosternal','retrocardiac','right_subdiaphragmatic_zone','left_additional_region','right_rib1','left_rib12','vertebra_C7','vertebra_T12','sternum','additional_bone','vascular_device','upper_abdomen','comparison']:assert 'cxr.'+key in ids
    assert all(s['requires_site_instantiation'] and s['report_refs'] and s['modality_scope']==['Radiography'] for s in item['structures'])
def test_projection_quality_and_all_normal_fields_remain_unanswered():
    ref=detail(Curriculum(),resolve('ra.chest-radiography'))['radiology_reference']
    assert all(not s['normal'] for s in ref['walkthrough']['steps'])
    assert 'No view is assumed' in ref['walkthrough']['steps'][0]['look']
    assert 'AP/supine magnification' in ref['walkthrough']['steps'][1]['tip']
    assert 'No device' in ref['walkthrough']['steps'][4]['tip']
    assert ref['reporting']['classification'] is None and 'Partial thoracic orientation' in ref['spatial_model']['reporting_aim']
    assert 'complete3D anatomy' in ref['reporting']['protocol'][1]
def test_projection_measurement_and_native_route_limits_are_explicit():
    ref=detail(Curriculum(),resolve('ra.chest-radiography'))['radiology_reference'];m={r['name']:r for r in ref['reporting']['measurements']}
    assert set(m)=={'Cardiothoracic ratio','Device tip distance'}
    assert 'actual' in m['Cardiothoracic ratio']['method'] and 'measured cardiac function' in m['Cardiothoracic ratio']['pitfall']
    assert 'single view' in m['Device tip distance']['pitfall'] and 'full3D' in m['Device tip distance']['pitfall']
    for s in ref['reporting']['template_sections']:assert '[ ]' in s['body']
