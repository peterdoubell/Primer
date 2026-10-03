from copy import deepcopy
import pytest
from tools.anatomy_sources.acquire_cptac_pancreatic_case import validate_selection


def selection():
    pairs=[]
    for i,role in enumerate(['arterial-labelled','venous-labelled']):
        common={'PatientID':'C3L-02112','StudyInstanceUID':'study','Collection':'CPTAC-PDA','LicenseURI':'https://creativecommons.org/licenses/by/4.0/'}
        pairs.append({'role':role,'annotation_row':{'PatientID':'C3L-02112','StudyInstanceUID':'study','Tracking UID':'same-observation','ClinicalTrialTimePointID':'Pre-Dose',
                    'Annotation Type':'Segmentation','Modality':'RTSTRUCT','ReferencedSeriesModality':'CT','SeriesInstanceUID':'annotation'+str(i),'ReferencedSeriesInstanceUID':'ct'+str(i)},
                    'original_ct_series':{**common,'Modality':'CT','SeriesInstanceUID':'ct'+str(i)},'annotation_series':{**common,'Modality':'RTSTRUCT','SeriesInstanceUID':'annotation'+str(i)}})
    return {'case_id':'C3L-02112','source_pairs':pairs}


def test_both_explicit_ct_and_annotation_references_remain_distinct():
    objects=validate_selection(selection());assert len(objects)==4
    assert len({s['SeriesInstanceUID'] for _,s in objects})==4


@pytest.mark.parametrize('target,key,value',[
 ('annotation_row','Tracking UID','different-observation'),('annotation_row','Annotation Type','Seed point'),
 ('annotation_row','ClinicalTrialTimePointID','Post-Chemotherapy'),('annotation_row','ReferencedSeriesInstanceUID','unrelated-ct'),
 ('original_ct_series','PatientID','C3L-00000'),('annotation_series','StudyInstanceUID','other-study'),
 ('original_ct_series','Collection','CPTAC-CCRCC'),('annotation_series','LicenseURI','https://creativecommons.org/licenses/by-nc/4.0/')])
def test_reference_treatment_and_original_data_scope_cannot_be_substituted(target,key,value):
    s=deepcopy(selection());s['source_pairs'][1][target][key]=value
    with pytest.raises(ValueError):validate_selection(s)


def test_one_source_series_cannot_be_duplicated_as_two_contrast_references():
    s=selection();s['source_pairs'][1]['original_ct_series']['SeriesInstanceUID']='ct0';s['source_pairs'][1]['annotation_row']['ReferencedSeriesInstanceUID']='ct0'
    with pytest.raises(ValueError,match='distinct references'):validate_selection(s)
