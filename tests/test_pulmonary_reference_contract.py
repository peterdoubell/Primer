"""The native companion allowance cannot migrate to another source or claim."""
import copy
import pytest
from primer.curriculum import Curriculum
from primer import radiology_catalog
from tools.pulmonary_reference_contract import assert_native_pulmonary_reference


@pytest.fixture(scope='module')
def reference():
    return radiology_catalog.detail(Curriculum(), radiology_catalog.resolve('ra.ct-pulmonary-nodules'))['radiology_reference']


def test_exact_native_reference_and_shared_lesson_are_checked(reference):
    assert_native_pulmonary_reference(reference)
    assert_native_pulmonary_reference(Curriculum().node('rad.4.pulmonary-nodule')['radiology_reference'])


@pytest.mark.parametrize('change', ['missing_native_mode', 'wrong_source', 'clinical_credit',
                                   'procedural_fallback', 'wrong_scene', 'invented_landmark'])
def test_native_allowance_rejects_changed_scope_or_missing_companion(reference, change):
    bad = copy.deepcopy(reference)
    if change == 'missing_native_mode': bad['source_native_only'] = False
    elif change == 'wrong_source': bad['source_native_inspectors'][0]['id'] = 'unknown-source'
    elif change == 'clinical_credit': bad['source_native_inspectors'][0]['clinical_approval'] = True
    elif change == 'procedural_fallback': bad['key_images'] = [{'id': 'invented-fallback'}]
    elif change == 'wrong_scene': bad['spatial_model']['scenario'] = 'radiology-reference:rad.5.sella'
    else: bad['walkthrough']['steps'][0]['landmark'] = 'imagined-lobe'
    with pytest.raises(AssertionError): assert_native_pulmonary_reference(bad)


def test_unknown_or_ordinary_reference_cannot_receive_native_allowance():
    ref = radiology_catalog.detail(Curriculum(), radiology_catalog.resolve('ra.mri-shoulder'))['radiology_reference']
    with pytest.raises(AssertionError): assert_native_pulmonary_reference(ref)
