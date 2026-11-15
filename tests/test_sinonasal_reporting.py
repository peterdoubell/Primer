"""Acquired MRI and thin-bone sources cannot be replaced by normal/patency/benignity assumptions."""
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
def reference():return detail(Curriculum(),resolve('ra.mri-sinuses'))['radiology_reference']
def test_no_unassessed_normal_or_patency_presets():
    r=reference();assert all(not s['normal'] for s in r['walkthrough']['steps'])
    assert all('[ ]' in s['body'] for s in r['reporting']['template_sections'])
    assert r['reporting']['classification'] is None and 'Partial sinonasal orientation' in r['spatial_model']['reporting_aim']
def test_CT_MRI_and_sequence_limits_are_explicit():
    r=reference();assert 'only used when actually acquired' in r['reporting']['protocol'][0]
    assert 'thin-bone' in r['walkthrough']['steps'][2]['tip'] and 'unacquired' in r['walkthrough']['steps'][2]['tip']
    assert 'actual ADC' in r['walkthrough']['steps'][3]['tip']
    assert 'low-signal MRI sinus is not automatically aerated' in r['walkthrough']['steps'][0]['tip']
def test_signal_and_bone_morphology_do_not_uniquely_diagnose_or_exclude_spread():
    r=reference();assert 'Hyperdensity or high T2 signal alone' in r['walkthrough']['steps'][0]['tip']
    assert 'No extrasinus extension is asserted absent' in r['walkthrough']['steps'][4]['tip']
    measurements={m['name']:m for m in r['reporting']['measurements']}
    assert set(measurements)=={'Focal lesion extent','Surgical defect/variant'}
    assert 'Unacquired or unresolved thin-bone' in measurements['Surgical defect/variant']['pitfall']
