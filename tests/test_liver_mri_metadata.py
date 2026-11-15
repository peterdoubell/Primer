import pytest
from tools.anatomy_sources.review_liver_mri_metadata import readings


def test_repeated_header_is_retained_as_structure_instead_of_a_patient():
    headers=('PatientID','StudyDate','Comments')
    result=readings(headers,[('TCGA-BC-A3KG',None,None),headers,(None,None,None)])
    assert result['source_patient_ids']==['TCGA-BC-A3KG']
    assert result['repeated_header_rows']==[3] and result['empty_source_rows']==[4]
    assert not result['source_readings'][0]['diagnostic_eligibility_verified']


def test_treated_or_incomplete_source_comments_are_not_rewritten_into_normal_anatomy():
    result=readings(('PatientID','Comments'),[('TCGA-BC-A216','No residual tumor; incomplete acquisition')])
    assert result['source_readings'][0]['source_values']['Comments']=='No residual tumor; incomplete acquisition'
    assert not result['source_readings'][0]['clinical_approval']


def test_header_like_record_with_different_fields_is_rejected():
    with pytest.raises(ValueError,match='Ambiguous header'):
        readings(('PatientID','Comments'),[('PatientID','Changed field')])
