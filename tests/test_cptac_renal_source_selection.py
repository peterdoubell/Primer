from copy import deepcopy
import pytest
from tools.anatomy_sources.acquire_cptac_renal_case import validate_selection


def selection():
    common={'PatientID':'source-case','StudyInstanceUID':'source-study','Collection':'CPTAC-CCRCC',
            'LicenseURI':'https://creativecommons.org/licenses/by/4.0/'}
    return {'case_id':'source-case','annotation_row':{'PatientID':'source-case','StudyInstanceUID':'source-study',
            'SeriesInstanceUID':'annotation-series','ReferencedSeriesInstanceUID':'ct-series','Annotation Type':'Segmentation','Modality':'RTSTRUCT'},
            'original_ct_series':{**common,'SeriesInstanceUID':'ct-series','Modality':'CT'},
            'annotation_series':{**common,'SeriesInstanceUID':'annotation-series','Modality':'RTSTRUCT'}}


def test_explicit_original_image_reference_preserved():
    s=selection();pair=validate_selection(s)
    assert pair[0][1]['SeriesInstanceUID']=='ct-series'
    assert pair[1][1]['SeriesInstanceUID']=='annotation-series'


@pytest.mark.parametrize('target,field,value', [('annotation_row','Annotation Type','Seed point'),
 ('annotation_row','ReferencedSeriesInstanceUID','unrelated-ct'),('annotation_series','PatientID','other-case'),
 ('original_ct_series','StudyInstanceUID','other-study'),('annotation_series','LicenseURI','https://creativecommons.org/licenses/by-nc-sa/4.0/'),
 ('original_ct_series','Collection','unrelated-collection')])
def test_source_references_or_rights_cannot_be_substituted(target,field,value):
    s=deepcopy(selection());s[target][field]=value
    with pytest.raises(ValueError):validate_selection(s)
