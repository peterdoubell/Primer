"""The shared lesson must not turn a suggestive wall pattern into universal cancer clearance."""
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve


def test_adenomyomatosis_assessment_retains_whole_lesion_and_coexistence_limits():
    node=Curriculum().nodes['rad.5.biliary']; ref=node['reference']
    assert 'coexisting or mimicking malignancy' in ref['approach'][3]['detail']
    assert 'name it and stop' not in str(ref['classify'])
    assert 'uncertainty or suspicious/coexisting features' in ref['classify']['rows'][1][2]
    assert 'do not delay urgent assessment' in ref['classify']['note']
    assert 'universal cancer exclusion' in node['quiz'][7]['explain']
    assert node['quiz'][7]['answer'] in node['quiz'][7]['choices']


def test_shared_template_does_not_invent_tenderness_mobility_or_doppler_assessment():
    ref=Curriculum().nodes['rad.5.biliary']['reference']
    template=ref['template']
    assert 'not assessed, unreliable or not applicable' in template
    assert 'not assessed or limited' in template
    assert 'Wall Doppler assessment: [not performed / adequate / limited]' in template
    assert 'Twinkling artefact distinguished from flow' in template
    assert 'Thickness alone is not a diagnosis' in ref['measure'][0]['cutoff']


def test_actual_reader_references_include_both_published_differential_reviews():
    ref=detail(Curriculum(),resolve('ra.ultrasound-gallbladder'))['radiology_reference']
    urls={r['url'] for r in ref['reporting']['sources']}
    assert {'https://doi.org/10.1007/s13244-017-0544-7','https://doi.org/10.1259/bjr.20220115'} <= urls
    assert any('single comet-tail artefact does not exclude' in p for p in ref['reporting']['pitfalls'])
