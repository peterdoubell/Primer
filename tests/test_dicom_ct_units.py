import pytest
from tools.anatomy_sources.dicom_ct_units import CT_IMAGE_STORAGE, resolve_ct_units


@pytest.mark.parametrize('multi_energy',[None,'NO'])
def test_original_axial_ct_has_standard_hu_semantics_without_optional_tag(multi_energy):
    result=resolve_ct_units(CT_IMAGE_STORAGE,['ORIGINAL','PRIMARY','AXIAL'],multi_energy=multi_energy)
    assert result['units']=='HU'
    assert result['basis']=='ct_image_module_original_default'
    assert not result['independent_physical_calibration_verified']


@pytest.mark.parametrize('types,multi', [(['DERIVED','PRIMARY','AXIAL'],None),(['ORIGINAL','PRIMARY','LOCALIZER'],None),(['ORIGINAL','PRIMARY','AXIAL'],'YES'),([],None)])
def test_other_images_do_not_inherit_hu(types,multi):
    assert resolve_ct_units(CT_IMAGE_STORAGE,types,multi_energy=multi)['units'] is None


def test_explicit_non_hu_units_are_preserved_for_derived_images():
    result=resolve_ct_units(CT_IMAGE_STORAGE,['DERIVED','PRIMARY','AXIAL'],rescale_type='MGML')
    assert result['units']=='MGML' and result['basis']=='explicit_rescale_type'


def test_contradictory_or_invalid_declarations_are_rejected():
    with pytest.raises(ValueError,match='contradicts'):
        resolve_ct_units(CT_IMAGE_STORAGE,['ORIGINAL','PRIMARY','AXIAL'],rescale_type='MGML')
    with pytest.raises(ValueError,match='multi-energy'):
        resolve_ct_units(CT_IMAGE_STORAGE,['ORIGINAL','PRIMARY','AXIAL'],multi_energy='')
    with pytest.raises(ValueError,match='Rescale Type'):
        resolve_ct_units(CT_IMAGE_STORAGE,['ORIGINAL','PRIMARY','AXIAL'],rescale_type='')


def test_non_ct_sop_class_cannot_use_the_ct_default():
    assert resolve_ct_units('1.2.840.10008.5.1.4.1.1.4',['ORIGINAL','PRIMARY','AXIAL'])['units'] is None
