import hashlib,json
import copy
import pytest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ID='open-cervical-nodes-pmc13049566-fig3';INV='ra.cervical-lymph-nodes'
def test_published_figure_preserves_layout_roles_and_no_native_rights_inference():
    rows=json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text())[INV];r=next(x for x in rows if x['id']==ID)
    proof=json.loads((ROOT/'docs/lymphus-published-source-review/original-source-review.json').read_text())
    raw=(ROOT/'web'/r['src'].removeprefix('/app/')).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['sha256']==proof['source_master_sha256']
    assert (r['width'],r['height'])==(1490,555) and r['license']==proof['original_article_grant']=='CC BY 4.0'
    assert proof['PDF_page']==7 and proof['PDF_image_object']==53 and proof['HTML_and_PDF_original_encoded_contrast_differ']
    assert not proof['native_dataset_commercial_grant_verified'] and not proof['source_pixels_changed']
    c=r['source_context'];assert c['source_caption_layout_discrepancy'] and len(c['source_case_groups'])==4
    assert len(r['clinical_panels'])==4 and c['selected_panels']==r['clinical_panels']
    assert [x['kind'] for x in r['ancillary_panels']]==['Segmentation mask','Masked ultrasound']
    assert all(len(x['panels'])==4 for x in r['ancillary_panels'])
    from primer.radiology_catalog import _validate_source_panel_roles
    _validate_source_panel_roles(r)
    evidence=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text());a=next(x for x in evidence['assets'] if x['id']==ID)
    assert a['source']['license']['commercial_use'] and a['anatomical_review']['status']=='pending'
    assert not a['structure_ids'] and not a['requirement_coverage']
    steps=json.loads((ROOT/'data/radiology/reporting-steps/head-neck.json').read_text())['investigations'][INV]
    assert ID not in steps['start']['images']
    assert [i for i,s in enumerate(steps['steps']) if ID in s.get('images',[])]==[1,2]

@pytest.mark.parametrize('change',['missing_grid_role','invalid_grid_size','unknown_grid_panel','mask_as_CT'])
def test_unlettered_grid_rejects_missing_or_contradictory_roles(monkeypatch,change):
    from primer import radiology_catalog as catalog
    original_read=catalog._read
    rows=json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text())
    row=next(r for r in rows[INV] if r['id']==ID);context=row['source_context']
    if change=='missing_grid_role':context['panel_types'].pop('r2c6')
    if change=='invalid_grid_size':context['panel_grid_rows']=True
    if change=='unknown_grid_panel':row['ancillary_panels'][0]['panels'][0]='r9c1'
    if change=='mask_as_CT':row['ancillary_panels'][0]['kind']='CT'
    monkeypatch.setattr(catalog,'_read',lambda name,default=None:copy.deepcopy(rows) if name=='radiology-open-images.json' else original_read(name,default))
    catalog._structure_atlases.cache_clear()
    try:
        with pytest.raises(ValueError):catalog._structure_atlases()
    finally:catalog._structure_atlases.cache_clear()
