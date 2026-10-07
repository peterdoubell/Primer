import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];INV='ra.mri-trigeminal';PREFIX='open-trigeminal-pmc6420596-fig'
def test_source_roles_normality_and_timeline_are_not_borrowed_across_panels():
    rows=json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text())[INV];by={x['figure_number']:x for x in rows};assert len(by)==9
    assert by[1]['clinical_panels']==['E'] and by[1]['image_state']=='normal_anatomical_reference'
    assert not by[1]['source_context']['normal_panels_assumed_same_patient']
    assert by[6]['kind']=='schematic' and by[6]['modality']=='Schematic' and by[6]['clinical_panels']==[] and by[6]['schematic_panels']==['full_figure']
    assert by[13]['modality']=='MRI' and by[13]['clinical_panels']==['C']
    assert by[13]['ancillary_panels'][0]['kind']=='CT' and by[13]['ancillary_panels'][0]['panels']==['A','B']
    assert by[19]['modality']=='CT' and by[19]['source_context']['source_followup_months']=={'A':0,'B':6,'C':12}
    assert by[21]['source_context']['source_branch_caption_discrepancy']=={'division_name':'mandibular','source_division_number':'V2','resolved':False}
    for n in [22,28]:assert by[n]['clinical_panels']==['A'] and 'B' in by[n]['source_context']['nonselected_panels']
def test_every_packaged_source_master_has_exact_pixels_and_pending_anatomy():
    rows=json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text())[INV]
    ledger=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets']
    from primer.radiology_catalog import _validate_source_panel_roles
    for row in rows:
        _validate_source_panel_roles(row)
        assert hashlib.sha256((ROOT/'web'/row['src'].removeprefix('/app/')).read_bytes()).hexdigest()==row['sha256']
        assert 'Nicola Romano, Margherita Federici, Antonio Castaldi' in row['attribution']
        asset=next(x for x in ledger if x['id']==row['id']);assert not asset['structure_ids'] and not asset['requirement_coverage']
        assert asset['anatomical_review']['status']=='pending' and not asset['pixel_provenance']['source_pixels_changed']
    node=json.loads((ROOT/'data/radiology/reporting-steps/head-neck.json').read_text())['investigations'][INV]
    assert node['start']['images']==[PREFIX+'6'] and all(s['normal']=={} for s in node['steps'])
