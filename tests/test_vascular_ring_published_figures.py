"""Ring/slings source panels remain original and cannot confer complete anatomy or function."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'docs/vascular-ring-published-source-review'
PREFIX='open-vascular-ring-pmc4141344-fig'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_original_pixels_rights_and_complete_panels_are_preserved():
    proof=json.loads((FOLDER/'original-source-review.json').read_text());pack=json.loads((FOLDER/'packaged-source-images.json').read_text())
    assert proof['original_license']=='CC BY 4.0' and proof['original_license_url']=='https://creativecommons.org/licenses/by/4.0/'
    assert proof['source_caption_side_ambiguity_figures']==[7] and proof['source_reported_multiple_patient_figures']==[2]
    assert len(proof['figures'])==len(pack['figures'])==11
    for s,r in zip(proof['figures'],pack['figures']):
        path=ROOT/r['local_path'];assert sha(path.read_bytes())==s['sha256']==r['sha256']
        with Image.open(path) as im:
            assert im.mode==s['pixel_mode'] and im.size==(s['width'],s['height'])
            assert sha(im.tobytes())==s['decoded_pixel_sha256']
        assert s['publisher_md5_verified'] and not s['source_pixels_changed']
    assert not pack['clinical_approval'] and not pack['model_promoted'] and not pack['structure_coverage_granted']
def test_mixed_patient_schematic_and_flat_panels_do_not_become_geometry():
    ref=detail(Curriculum(),resolve('ra.vascular-anomalies'))['radiology_reference'];rows={r['figure_number']:r for r in ref['structure_atlas'] if r['id'].startswith(PREFIX)}
    assert set(rows)==set(range(1,12))
    assert rows[1]['kind']=='schematic' and rows[1]['modality']=='Schematic' and rows[1]['clinical_panels']==[]
    assert 'not present simultaneously' in rows[1]['limits'] and not rows[1]['contains_schematic_panels']
    assert rows[2]['clinical_panels']==list('bcde') and rows[2]['source_context']['source_ct_volume_rendering_panels']==list('fgh')
    assert 'another patient' in rows[2]['limits']
    assert rows[3]['source_context']['virtual_bronchoscopy_panels']==['d']
    assert rows[4]['clinical_panels']==[] and rows[4]['source_context']['all_panels_flat_renderings_only']
    assert rows[7]['clinical_panels']==list('abc') and 'ambiguous side wording' in rows[7]['limits']
    assert rows[11]['clinical_panels']==list('bc') and rows[11]['source_context']['source_schematic_panels']==['a']
    for r in rows.values():
        for key in ['flat_renderings_are_spatial_geometry','full_acquired_series_included','independent_calibrated_measurements_verified',
            'complete_ring_components_directly_visualised','cross_figure_patient_identity_verified','same_series_registration_verified',
            'dynamic_airway_or_haemodynamic_function_verified','complete_structure_coverage_verified']:
            assert r['source_context'][key] is False
        if r['contains_schematic_panels']: assert r['schematic_structures_visible']
    assert ref['walkthrough']['start']['images']==[PREFIX+'1',PREFIX+'11']
    assert ref['walkthrough']['start']['module_illustrations'] is False
    assert {PREFIX+'6',PREFIX+'11'}.issubset(ref['walkthrough']['steps'][2]['images'])
    assert not any(i.startswith(PREFIX) for step in ref['walkthrough']['steps'][3:] for i in step['images'])
def test_rights_clearance_does_not_grant_anatomy_or_reuse_other_articles():
    assets=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'];rows=[r for r in assets if r['id'].startswith(PREFIX)]
    assert len(rows)==11
    for r in rows:
        license=r['source']['license'];assert license['name']=='CC BY 4.0' and license['commercial_use'] and license['redistribution']
        assert sha((ROOT/license['evidence_path']).read_bytes())==license['evidence_sha256']
        assert not r['structure_ids'] and not r['requirement_coverage'] and r['anatomical_review']['status']=='pending'
    assert json.loads((FOLDER/'original-source-review.json').read_text())['noncommercial_other_article_images_not_reused']=='PMC9705143'
