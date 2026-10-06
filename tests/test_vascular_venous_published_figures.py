"""Source venous images retain actual modalities, case boundaries, correction and flow limits."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
ROOT=Path(__file__).resolve().parents[1];FOLDER=ROOT/'docs/vascular-venous-published-source-review';PREFIX='open-vascular-venous-'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_complete_original_jpegs_and_actual_licenses_are_preserved():
    p=json.loads((FOLDER/'original-source-review.json').read_text());pack=json.loads((FOLDER/'packaged-source-images.json').read_text());sources={s['pmcid']:s for s in p['sources']}
    assert sources['PMC7561662']['original_license']=='CC BY 4.0'
    assert sources['PMC3038141']['original_license']=='CC BY 2.0'
    assert 'reference' in sources['PMC8052389']['correction_text'].lower() and 'original article has been updated' in sources['PMC8052389']['correction_text'].lower()
    assert p['caption_panel_mismatch_figures']=={'PMC7561662':[2,23]}
    original={PREFIX+s['pmcid'].lower()+'-fig'+str(f['figure_number']):f for s in p['sources'] for f in s['figures']}
    assert len(original)==len(pack['figures'])==11
    for row in pack['figures']:
        s=original[row['id']];path=ROOT/row['local_path'];assert sha(path.read_bytes())==s['sha256']==row['sha256']
        with Image.open(path) as im:
            assert im.mode==s['pixel_mode'] and im.size==(s['width'],s['height']) and sha(im.tobytes())==s['decoded_pixel_sha256']
        assert s['publisher_md5_verified'] and not s['source_pixels_changed']
    assert not p['supplementary_motion_acquired'] and not pack['model_promoted'] and not pack['structure_coverage_granted']
def test_actual_panel_letters_modalities_and_missing_source_function_are_retained():
    ref=detail(Curriculum(),resolve('ra.vascular-anomalies'))['radiology_reference'];rows={r['id']:r for r in ref['structure_atlas'] if r['id'].startswith(PREFIX)};ct=lambda n:rows[PREFIX+'pmc7561662-fig'+str(n)]
    assert len(rows)==11
    assert ct(2)['clinical_panels']==list('BDEFG') and ct(2)['source_context']['source_ct_volume_rendering_panels']==list('CH')
    assert ct(2)['ancillary_panels'][0]['kind']=='Radiography' and ct(2)['ancillary_panels'][0]['panels']==['A']
    assert 'misidentifies' in ct(2)['limits'] and 'not shown' in ct(2)['limits']
    assert 'different patients' in ct(3)['limits'] and 'same patient' in ct(21)['limits']
    assert 'omits actual panel D' in ct(23)['limits'] and 'No universal flow direction' in ct(18)['limits']
    mr=rows[PREFIX+'pmc3038141-fig1'];assert mr['modality']=='MRI' and mr['clinical_panels']==['D']
    assert mr['ancillary_panels'][0]['kind']=='Ultrasound' and mr['ancillary_panels'][0]['panels']==list('ABC')
    assert 'not independently measurable' in mr['limits'] and 'movies exist but are not acquired' in mr['limits']
    for r in rows.values():
        assert r['source_context']['source_panel_identifier_case']=='uppercase_in_original_pixels'
        for k in ['flat_renderings_are_spatial_geometry','full_acquired_series_included','independent_calibrated_measurements_verified',
            'same_series_registration_verified','cross_figure_patient_identity_verified','dynamic_flow_or_quantitative_shunt_verified',
            'complete_venous_geometry_verified','native_source_motion_acquired']:assert r['source_context'][k] is False
    assert PREFIX+'pmc3038141-fig1' in ref['walkthrough']['steps'][3]['images']
    assert all(PREFIX+'pmc7561662-fig'+str(n) in ref['walkthrough']['steps'][4]['images'] for n in [2,3,13,20,21,22,23])
    assert not any(i.startswith(PREFIX) for i in ref['walkthrough']['start']['images'])
def test_rights_do_not_confer_geometry_or_haemodynamic_approval():
    a=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'];rows=[r for r in a if r['id'].startswith(PREFIX)]
    assert len(rows)==11
    for r in rows:
        l=r['source']['license'];assert l['commercial_use'] and l['redistribution'] and l['review_status']=='verified'
        assert sha((ROOT/l['evidence_path']).read_bytes())==l['evidence_sha256']
        assert not r['structure_ids'] and not r['requirement_coverage'] and r['anatomical_review']['status']=='pending'
