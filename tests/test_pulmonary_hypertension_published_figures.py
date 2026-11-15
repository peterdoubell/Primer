"""Original pixels and modality distinctions must survive delivery without granting CT coverage."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.check_msk_fidelity import inspect_binding, inspect_source_context
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/pulmonary-hypertension-published-source-review'
PREFIX='open-pulmonary-htn-pmc9698386-fig'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_complete_original_pixels_and_grant_survive_packaging():
    proof=json.loads((OUT/'original-source-review.json').read_text());package=json.loads((OUT/'packaged-source-images.json').read_text());original={r['figure_number']:r for r in proof['figures']}
    assert set(original)==set(range(1,10)) and len(package['figures'])==9
    assert proof['original_license']=='CC BY 4.0' and proof['illustration_acknowledgment']=='Hyejin Kim'
    for row in package['figures']:
        p=original[int(row['id'].removeprefix(PREFIX))];path=ROOT/row['local_path']
        assert sha(path.read_bytes())==row['sha256']==p['sha256']
        with Image.open(path) as im:
            assert (im.width,im.height,im.mode)==(p['width'],p['height'],p['pixel_mode'])
            assert sha(im.tobytes())==p['decoded_pixel_sha256']
    assert not proof['clinical_approval'] and not proof['structure_coverage_granted'] and not proof['model_promoted']
def test_distinct_modalities_cannot_become_CT_requirement_evidence():
    ref=detail(Curriculum(),resolve('ra.pulmonary-hypertension'))['radiology_reference']
    rows={r['figure_number']:r for r in ref['structure_atlas'] if r['id'].startswith(PREFIX)}
    assert rows[1]['kind']=='schematic' and rows[1]['modality']=='Schematic'
    assert rows[3]['modality']=='Ultrasound' and rows[8]['modality']=='Nuclear medicine'
    assert rows[9]['modality']=='Radiography' and rows[9]['clinical_panels']==['B']
    assert rows[9]['ancillary_panels'][0]['kind']=='Haemodynamic tracing' and rows[9]['ancillary_panels'][0]['panels']==['A']
    assets=[r for r in json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if r['id'].startswith(PREFIX)]
    for asset in assets:
        assert not asset['structure_ids'] and not asset['requirement_coverage'] and asset['anatomical_review']['status']=='pending'
        grant=asset['source']['license'];assert sha((ROOT/grant['evidence_path']).read_bytes())==grant['evidence_sha256']
        if asset['modality'] in {'Ultrasound','Nuclear medicine','Radiography'}:
            assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(asset,{'modality_scope':['CT']})
    assert not ref['key_images'] and not ref['walkthrough']['start']['module_illustrations']
    assert all(not s['normal'] for s in ref['walkthrough']['steps'])
def test_original_panel_layouts_preserve_state_and_measurement_limits():
    ref=detail(Curriculum(),resolve('ra.pulmonary-hypertension'))['radiology_reference'];rows={r['figure_number']:r for r in ref['structure_atlas'] if r['id'].startswith(PREFIX)}
    assert rows[5]['source_context']['panel_states']=={'A':'source_chronic_thrombus','B':'source_acute_thrombus'}
    assert rows[6]['source_context']['panel_presentation']['F']=='flat_volume_rendering'
    assert rows[7]['source_context']['panel_presentation']['A']=='iodine_map_and_two_flat_volume_renderings'
    assert rows[8]['source_context']['scintigraphy_layout']['projections_each']==['ANT','R lat','RPO','POST','LPO','L lat']
    assert '415 cm/s' in rows[3]['limits'] and 'Acute material can also be eccentric' in rows[5]['limits']
    for row in rows.values():
        for field in ['full_native_series_and_calibration_verified','clinical_function_or_pressure_independently_verified','complete_tissue_or_branch_geometry_verified','flat_rendering_is_actual_3D_model']:
            assert row['source_context'][field] is False


def test_conceptual_drawing_does_not_satisfy_in_vivo_source_context():
    asset=next(r for r in json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if r['id']==PREFIX+'1')
    issues=inspect_source_context(asset,{'context_requirements':{'setting':'in_vivo'}})
    assert 'source_context_setting_mismatch' in issues
    assert 'source_context_setting_invalid' not in issues
