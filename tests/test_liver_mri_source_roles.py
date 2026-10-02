import pytest
from tools.anatomy_sources.inventory_liver_mri_case import role


def test_original_and_registered_phase_names_cannot_be_combined():
    assert role('pv.nii.gz')['kind']=='original_phase'
    assert role('pv.nii.gz')['source_registered'] is False
    assert role('art_pv.nii.gz')['kind']=='registered_derivative'
    assert role('art_pv.nii.gz')['source_registered'] is True


def test_rater_and_observation_identifiers_are_retained():
    result=role('rater2_tumor3.nii.gz')
    assert result['rater']==2 and result['roi']=='tumor3'
    assert result['source_mask_combined'] is False


def test_unlabelled_or_unknown_sequence_names_are_not_guessed():
    with pytest.raises(ValueError):role('T2.nii.gz')
    with pytest.raises(ValueError):role('rater3_liver.nii.gz')
