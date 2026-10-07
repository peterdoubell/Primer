"""Thoracic morphology cannot supply unassessed normality, viability or microbiological resistance."""
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve

def reference():return detail(Curriculum(),resolve('ra.tuberculosis'))['radiology_reference']
def test_all_normal_findings_and_absent_history_presets_are_removed():
    r=reference();assert all(not s['normal'] for s in r['walkthrough']['steps'])
    assert r['reporting']['classification'] is None
    assert all('[ ]' in s['body'] for s in r['reporting']['template_sections'])
    assert 'Partial thoracic orientation' in r['spatial_model']['reporting_aim']
def test_morphology_and_microbiological_confirmation_remain_distinct():
    r=reference();steps=r['walkthrough']['steps'];assert 'drug resistance' in steps[1]['tip']
    assert 'tissue histology' in steps[2]['tip'] and 'coexisting active disease' in steps[4]['tip']
    assert 'Normal imaging does not exclude latent infection' in steps[4]['tip']
    section=next(s for s in r['reporting']['template_sections'] if s['heading']=='SEQUELAE AND COMPARISON')
    assert 'laboratory/molecular/culture/susceptibility' in section['body'] and 'dates' in section['body']
def test_actual_modality_measurements_and_sources_required():
    r=reference();assert 'only a radiograph' in r['reporting']['protocol'][0]
    assert r['reporting']['measurements'][0]['name']=='Cavity or collection'
    assert 'whole3D extent' in r['reporting']['measurements'][0]['pitfall']
    assert any(s['url']=='https://www.who.int/publications/i/item/9789240107984' for s in r['reporting']['sources'])
