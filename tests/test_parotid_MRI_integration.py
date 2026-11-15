import copy,hashlib,json
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];INV='ra.head-neck-malignancy'
def rows():return json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text())[INV]
def test_adult_adolescent_and_sequence_roles_are_preserved_without_classifier_approval():
    r=rows();assert len(r)==3
    assert [x['source_context']['population']['age_years'] for x in r]==[54,65,15]
    assert [x['source_context']['laterality'] for x in r]==['left','right','right']
    assert r[2]['source_context']['population']['life_stage']=='child'
    from primer.radiology_catalog import _validate_source_panel_roles
    ledger=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets']
    for row in r:
        _validate_source_panel_roles(row)
        assert row['clinical_panels']==list('abcde') and row['ancillary_panels'][0]['kind']=='MRI-derived plot' and row['ancillary_panels'][0]['panels']==['f']
        assert row['source_context']['panel_types']['f']=='MRI-derived plot'
        assert row['source_context']['source_sequence_roles']['d']=='MRI DWI' and row['source_context']['source_sequence_roles']['e']=='MRI ADC map'
        assert not row['source_context']['different_figures_assumed_same_patient'] and not row['source_context']['source_panels_independently_registered']
        assert not row['source_context']['source_classifier_is_current_patient_diagnostic_guarantee']
        assert not row['source_context']['source_normalized_signal_or_ADC_are_independent_new_measurements']
        assert hashlib.sha256((ROOT/'web'/row['src'].removeprefix('/app/')).read_bytes()).hexdigest()==row['sha256']
        asset=next(x for x in ledger if x['id']==row['id']);assert asset['anatomical_review']['status']=='pending' and not asset['structure_ids'] and not asset['requirement_coverage']
    node=json.loads((ROOT/'data/radiology/reporting-steps/head-neck.json').read_text())['investigations'][INV]
    assert node['start']['images']==[] and all(x['normal']=={} for x in node['steps'])
    assert not any(x['images'] for x in node['steps'][2:])
@pytest.mark.parametrize('change',['plot_as_MRI','plot_as_tissue','plot_primary_overlap'])
def test_derived_plot_role_cannot_silently_become_acquired_anatomy(change):
    from primer.radiology_catalog import _validate_source_panel_roles
    row=copy.deepcopy(rows()[0])
    if change=='plot_as_MRI':row['source_context']['panel_types']['f']='MRI'
    if change=='plot_as_tissue':row['ancillary_panels'][0]['kind']='Histology'
    if change=='plot_primary_overlap':row['clinical_panels'].append('f');row['source_context']['selected_panels'].append('f')
    with pytest.raises(ValueError):_validate_source_panel_roles(row)
