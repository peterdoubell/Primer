"""Interpret legacy CT rescale units from PS3.3 C.8.2, not pixel appearance."""
CT_IMAGE_STORAGE = '1.2.840.10008.5.1.4.1.1.2'
STANDARD = 'https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.8.2.html'


def resolve_ct_units(sop_class_uid, image_type, rescale_type=None, multi_energy=None):
    result = dict(units=None, basis='unresolved', standard=STANDARD,
                  independent_physical_calibration_verified=False)
    if sop_class_uid != CT_IMAGE_STORAGE:
        result['basis'] = 'outside_legacy_ct_scope'
        return result
    if multi_energy not in (None, 'NO', 'YES'):
        raise ValueError('Invalid multi-energy CT declaration')
    if rescale_type is not None and (not isinstance(rescale_type,str) or not rescale_type.strip()):
        raise ValueError('Empty or invalid Rescale Type')
    declared = rescale_type.strip() if rescale_type is not None else None
    original = (isinstance(image_type,(list,tuple)) and len(image_type)>=3
                and image_type[0]=='ORIGINAL' and bool(image_type[2])
                and image_type[2]!='LOCALIZER' and multi_energy in (None,'NO'))
    if original:
        if declared is not None and declared != 'HU':
            raise ValueError('Original non-localizer CT contradicts required HU units')
        result.update(units='HU',basis='explicit_rescale_type' if declared else 'ct_image_module_original_default')
    elif declared:
        result.update(units=declared,basis='explicit_rescale_type')
    else:
        result['basis'] = 'missing_units_for_nonqualifying_ct'
    return result
