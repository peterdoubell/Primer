"""CMR figure pixels, source graph roles and held upstream credits remain explicit."""
import hashlib,json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/cmr-published-source-review';PREFIX='open-cmr-source-'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_original_grants_samples_and_upstream_holds_are_preserved():
    p=json.loads((OUT/'original-source-review.json').read_text());pack=json.loads((OUT/'packaged-source-images.json').read_text());assert len(pack['figures'])==13
    originals={PREFIX+s['pmcid'].lower()+'-fig'+str(f['figure_number']):f for s in p['sources'] for f in s['figures']};assert len(originals)==13
    for row in pack['figures']:
        s=originals[row['id']];path=ROOT/row['local_path'];assert sha(path.read_bytes())==s['sha256']==row['sha256']
        with Image.open(path) as im:assert im.mode==s['pixel_mode'] and im.size==(s['width'],s['height']) and sha(im.tobytes())==s['decoded_pixel_sha256']
        assert s['publisher_md5_verified'] and not s['source_pixels_changed']
    assert all(s['original_license']=='CC BY 4.0' for s in p['sources'])
    held=next(s for s in p['sources'] if s['pmcid']=='PMC7066763')['upstream_credit_figures_held'];assert {h['figure_number'] for h in held}=={5,10} and all(not h['reused'] for h in held)
    assert not pack['structure_coverage_granted'] and not pack['model_promoted']
def test_still_grids_maps_graphs_and_normal_case_labels_are_not_raw_results():
    ref=detail(Curriculum(),resolve('ra.mri-cardiomyopathy'))['radiology_reference'];rows={r['id']:r for r in ref['structure_atlas'] if r['id'].startswith(PREFIX)};sc=lambda n:rows[PREFIX+'pmc7066763-fig'+str(n)];ca=lambda n:rows[PREFIX+'pmc11084160-fig'+str(n)]
    assert len(rows)==13 and sc(1)['clinical_panels']==list('abcd')
    assert sc(4)['clinical_panels']==['left','right'] and sc(4)['source_context']['source_layout_schemes']=='unlettered_left_right'
    assert sc(7)['clinical_panels']==['A','C'] and sc(7)['source_context']['source_graphical_panels']==list('BDE')
    assert sc(8)['clinical_panels']==['top'] and sc(8)['source_context']['source_graphical_panels']==['bottom'] and 'representative/grouped' in sc(8)['limits']
    assert ca(5)['clinical_panels']==list('abcdeghi') and ca(5)['source_context']['source_graphical_panels']==['f'] and ca(5)['source_context']['source_caption_metric_context_ambiguity']
    assert 'mg/g' in ca(5)['limits'] and 'not independently validated' in ca(1)['limits']
    assert 'genetic record is not supplied' in ca(3)['limits']
    for row in rows.values():
        for k in ['source_native_temporal_or_quantitative_data_included','full_original_acquisition_verified','independent_calibrated_function_or_mapping_verified','source_case_diagnosis_independently_verified','patient_phase_or_series_registration_verified','full_myocardial_layer_geometry_verified']:assert row['source_context'][k] is False
        if row['source_context']['source_graphical_panels']:assert row['contains_schematic_panels'] and row['schematic_structures_visible']
    assert ref['walkthrough']['start']['images']==[PREFIX+'pmc7066763-fig1',PREFIX+'pmc7066763-fig4'] and ref['walkthrough']['start']['module_illustrations'] is False
    assert PREFIX+'pmc7066763-fig2' in ref['walkthrough']['steps'][0]['images'] and PREFIX+'pmc11084160-fig5' in ref['walkthrough']['steps'][2]['images']
def test_rights_do_not_approve_source_contours_or_case_diagnoses():
    a=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'];rows=[r for r in a if r['id'].startswith(PREFIX)];assert len(rows)==13
    for r in rows:
        l=r['source']['license'];assert l['commercial_use'] and l['redistribution'] and l['name']=='CC BY 4.0'
        assert sha((ROOT/l['evidence_path']).read_bytes())==l['evidence_sha256'] and not r['structure_ids'] and not r['requirement_coverage'] and r['anatomical_review']['status']=='pending'
