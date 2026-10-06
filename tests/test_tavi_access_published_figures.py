"""Historical access workspaces and flat VR cannot be treated as current device models or calibrated routes."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'docs/tavi-access-published-source-review'
PREFIX='open-tavi-access-pmc3948900-fig'

def sha(raw):return hashlib.sha256(raw).hexdigest()

def test_complete_original_access_jpegs_and_cc_by_2_grant_are_preserved():
    p=json.loads((FOLDER/'original-source-review.json').read_text());package=json.loads((FOLDER/'packaged-source-images.json').read_text())
    assert p['original_license']=='CC BY 2.0' and p['original_license_url']=='https://creativecommons.org/licenses/by/2.0/'
    assert p['separately_credited_manufacturer_figures_not_acquired']==[4,6,7]
    assert len(p['figures'])==len(package['figures'])==4
    for s,row in zip(p['figures'],package['figures']):
        path=ROOT/row['local_path'];assert sha(path.read_bytes())==s['sha256']==row['sha256']
        with Image.open(path) as im:
            assert im.mode==s['pixel_mode'] and im.size==(s['width'],s['height'])
            assert sha(im.tobytes())==s['decoded_pixel_sha256']
        assert s['publisher_md5_verified'] and not s['source_pixels_changed']
    assert not package['clinical_approval'] and not package['model_promoted'] and not package['structure_coverage_granted']

def test_flat_renderings_and_mixed_workspaces_keep_explicit_scope():
    ref=detail(Curriculum(),resolve('ra.ct-tavi'))['radiology_reference'];rows={r['figure_number']:r for r in ref['structure_atlas'] if r['id'].startswith(PREFIX)}
    assert set(rows)=={21,22,23,24}
    assert rows[21]['clinical_panels']==list('adef') and rows[21]['source_context']['workspace_panels_with_mixed_2D_3D_subviews']==list('def')
    assert rows[21]['source_context']['source_projected_ct_panels']==['c']
    assert not rows[22]['clinical_panels'] and rows[22]['source_context']['all_panels_flat_renderings_only']
    assert rows[22]['source_context']['source_ct_volume_rendering_panels']==list('abc')
    assert '98-degree' in rows[22]['limits'] and 'not an independently calibrated' in rows[22]['limits']
    assert rows[23]['clinical_panels']==list('abde') and rows[23]['source_context']['source_ct_volume_rendering_panels']==list('cf')
    assert rows[24]['clinical_panels']==list('cd') and 'not a current universal safe access rule' in rows[24]['limits']
    for row in rows.values():
        for key in ['flat_renderings_are_spatial_geometry','full_acquired_series_included','complete_access_route_or_minimum_lumen_verified',
                    'independent_calibrated_measurements_verified','cross_figure_patient_identity_verified',
                    'current_device_suitability_or_procedural_safety_verified']:
            assert row['source_context'][key] is False
    assert set(ref['walkthrough']['steps'][4]['images']) >= {r['id'] for r in rows.values()}
    assert not any(i.startswith(PREFIX) for i in ref['walkthrough']['start']['images'])

def test_access_figure_rights_do_not_borrow_manufacturer_or_anatomical_approval():
    assets=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'];rows=[r for r in assets if r['id'].startswith(PREFIX)]
    assert len(rows)==4
    assert len([r for r in assets if r['id'].startswith('open-tavi-pmc9743261-fig')])==8
    for row in rows:
        licence=row['source']['license'];assert licence['name']=='CC BY 2.0' and licence['commercial_use'] and licence['redistribution']
        assert sha((ROOT/licence['evidence_path']).read_bytes())==licence['evidence_sha256']
        assert not row['structure_ids'] and not row['requirement_coverage'] and row['anatomical_review']['status']=='pending'
