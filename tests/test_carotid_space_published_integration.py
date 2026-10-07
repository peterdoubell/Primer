import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];INV='ra.mri-neck-spaces';PREFIX='open-neck-spaces-pmc6377693-fig'
def rows():return json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text())[INV]
def test_conceptual_layers_and_mixed_acquisitions_have_actual_roles():
    by={r['figure_number']:r for r in rows()};assert len(by)==23
    assert {n for n,r in by.items() if r['kind']=='schematic'}=={1,6,11,13}
    for n in [1,6,11,13]:assert by[n]['modality']=='Schematic' and not by[n]['clinical_panels'] and by[n]['schematic_panels']
    assert by[2]['clinical_panels']==['b'] and by[2]['modality']=='MRI'
    assert {a['kind']:a['panels'] for a in by[2]['ancillary_panels']}=={'CT':['a'],'Radiography':['c'],'Ultrasound':['d']}
    assert by[2]['source_context']['source_panel_d_contains_spectral_Doppler_tracing']
    assert by[12]['modality']=='CT' and by[12]['ancillary_panels'][0]['kind']=='Ultrasound'
    assert by[18]['modality']=='CT' and by[18]['ancillary_panels'][0]['kind']=='Ultrasound'
    assert by[17]['source_context']['source_followup_months']=={'c':4} and by[17]['source_context']['followup_interval_approximate']
    assert by[19]['source_context']['source_followup_days']=={'a':0,'b':3} and by[19]['source_context']['panel_c_chronology_not_independently_supplied']
    assert 'not a new independent biopsy' in by[21]['source_context']['source_supplied_biopsy_site']
    assert 'static vocal-fold medialisation' in by[14]['limits']
def test_original_samples_and_pending_anatomy_are_retained_for_every_figure():
    ledger=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets']
    from primer.radiology_catalog import _validate_source_panel_roles
    for r in rows():
        _validate_source_panel_roles(r)
        assert hashlib.sha256((ROOT/'web'/r['src'].removeprefix('/app/')).read_bytes()).hexdigest()==r['sha256']
        assert 'Harris U. Chengazi, Alok A. Bhatt' in r['attribution']
        a=next(a for a in ledger if a['id']==r['id']);assert a['anatomical_review']['status']=='pending' and not a['structure_ids'] and not a['requirement_coverage']
        assert not a['pixel_provenance']['source_pixels_changed']
    n=json.loads((ROOT/'data/radiology/reporting-steps/head-neck.json').read_text())['investigations'][INV]
    assert n['start']['images']==[PREFIX+'1'] and all(s['normal']=={} for s in n['steps'])
