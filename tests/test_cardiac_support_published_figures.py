"""Support source figures preserve creator processing and conflicts, never generic device safety."""
import hashlib,json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/cardiac-support-published-source-review';PREFIX='open-cardiac-support-pmc10350447-fig'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_source_samples_credits_and_actual_grant_are_preserved():
    p=json.loads((OUT/'original-source-review.json').read_text());pack=json.loads((OUT/'packaged-source-images.json').read_text())
    assert p['original_license']=='CC BY 4.0' and p['original_license_url']=='https://creativecommons.org/licenses/by/4.0/'
    assert len(p['figures'])==len(pack['figures'])==12 and 'Medical Illustrators' in p['acknowledgements']
    for s,row in zip(p['figures'],pack['figures']):
        path=ROOT/row['local_path'];assert sha(path.read_bytes())==s['sha256']==row['sha256']
        with Image.open(path) as im:assert im.mode==s['pixel_mode'] and im.size==(s['width'],s['height']) and sha(im.tobytes())==s['decoded_pixel_sha256']
        assert s['publisher_md5_verified'] and not s['source_pixels_changed']
    assert p['caption_component_conflict_figures']==[12] and p['nonstandard_source_configuration_figures']==[11]
    assert not pack['structure_coverage_granted'] and not pack['model_promoted']
def test_ct_radiograph_schematic_and_creator_filtering_are_not_conflated():
    ref=detail(Curriculum(),resolve('ra.cardiovascular-devices'))['radiology_reference'];rows={r['figure_number']:r for r in ref['structure_atlas'] if r['id'].startswith(PREFIX)}
    assert set(rows)==set(range(1,13))
    assert rows[1]['kind']=='schematic' and rows[1]['clinical_panels']==[] and rows[1]['modality']=='Schematic'
    assert rows[2]['clinical_panels']==list('cd') and rows[2]['ancillary_panels'][0]['panels']==list('ab')
    assert rows[5]['modality']=='CT' and rows[5]['clinical_panels']==['b'] and rows[5]['ancillary_panels'][0]['kind']=='Radiography'
    for n,panels in {4:list('ab'),6:['a'],7:['a'],10:['whole'],12:['a']}.items():assert rows[n]['source_context']['source_creator_CLAHE_panels']==panels
    assert 'not a universal depth' in rows[5]['limits'] and 'nonstandard surgical configuration' in rows[11]['limits']
    assert 'conflicting' in rows[12]['limits'] and 'not adopted as a normal target' in ref['walkthrough']['steps'][2]['tip']
    for row in rows.values():
        for k in ['new_image_processing_applied','full_acquired_series_included','independent_calibrated_measurements_verified','same_series_registration_verified','cross_figure_patient_identity_verified','raw_unprocessed_acquisition_included','complete_device_tissue_geometry_verified','current_model_ifu_conformity_verified','quantitative_flow_or_function_verified']:assert row['source_context'][k] is False
    assert PREFIX+'1' in ref['walkthrough']['start']['images'] and all(PREFIX+str(n) in ref['walkthrough']['steps'][3]['images'] for n in [3,7,8,9,12])
def test_case_examples_and_artist_rights_do_not_grant_complete_geometry():
    assets=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'];rows=[r for r in assets if r['id'].startswith(PREFIX)];assert len(rows)==12
    for row in rows:
        l=row['source']['license'];assert l['commercial_use'] and l['redistribution'] and l['name']=='CC BY 4.0'
        assert sha((ROOT/l['evidence_path']).read_bytes())==l['evidence_sha256']
        assert not row['structure_ids'] and not row['requirement_coverage'] and row['anatomical_review']['status']=='pending'
    assert 'Medical Illustrators' in next(r for r in rows if r['id']==PREFIX+'1')['source']['license']['attribution']
