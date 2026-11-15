from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve


def reference(key):
    return detail(Curriculum(), resolve(key))['radiology_reference']


def test_washout_and_capsule_phase_rules_are_kept_separate():
    ref = reference('ra.liver-lirads')
    look = ref['walkthrough']['steps'][2]['look']
    assert 'portal venous only with gadoxetate' in look
    assert 'extracellular agents or gadobenate' in look
    assert 'Transitional or hepatobiliary hypointensity is not washout' in look
    assert 'Enhancing capsule: assess separately' in look
    assert 'delayed or transitional phases as applicable' in look
    assert 'v2018' in ref['reporting']['classification']['version']
    assert any(s['url'].startswith('https://www.acr.org/') for s in ref['reporting']['sources'])


def test_category_prompt_requires_size_feature_table_instead_of_a_universal_lr5_shortcut():
    phrase = reference('ra.liver-lirads')['walkthrough']['steps'][4]['findings'][0]
    assert 'Category [ ] after applying the v2018 size/feature table' in phrase
    assert 'checking LR-M/TIV' in phrase
    assert not phrase.startswith('LR-5:')


def test_general_liver_mass_prompts_do_not_assume_eligibility_or_benignity_from_size():
    steps = reference('ra.liver-masses')['walkthrough']['steps']
    assert 'verify LI-RADS eligibility and exclusions' in steps[0]['findings'][0]
    assert 'small size alone cannot establish benignity' in steps[1]['tip']
