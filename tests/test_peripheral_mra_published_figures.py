"""Original MRA figures retain method-specific roles, source pixels and unresolved clinical geometry."""
import hashlib,json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/peripheral-mra-published-source-review';PREFIX='open-peripheral-mra-'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_original_grants_complete_pixels_and_modified_diagram_hold_are_preserved():
    proof=json.loads((OUT/'original-source-review.json').read_text());package=json.loads((OUT/'packaged-source-images.json').read_text());assert len(package['figures'])==5
    originals={PREFIX+s['pmcid'].lower()+'-fig'+str(f['figure_number']):f for s in proof['sources'] for f in s['figures']}
    for row in package['figures']:
        source=originals[row['id']];path=ROOT/row['local_path'];assert sha(path.read_bytes())==source['sha256']==row['sha256']
        with Image.open(path) as im:assert im.mode==source['pixel_mode'] and im.size==(source['width'],source['height']) and sha(im.tobytes())==source['decoded_pixel_sha256']
        assert source['publisher_md5_verified'] and not source['source_pixels_changed'] and source['complete_original_pixels_and_in_pixel_credits_inspected']
    assert all(s['original_license']=='CC BY 4.0' for s in proof['sources'])
    assert 'Ramon Andrade de Mello' not in next(s for s in proof['sources'] if s['pmcid']=='PMC3946661')['authors']
    held=next(s for s in proof['sources'] if s['pmcid']=='PMC3946661')['held_upstream_credit_figures'];assert len(held)==1 and held[0]['figure_number']==1 and not held[0]['reused']
    assert 'modified after' in held[0]['original_caption']
    assert not (ROOT/'web/reference-media/radiology-open/peripheral-mra-pmc3946661-fig1.jpg').exists()
    assert {i['id'] for i in package['replaced_unverified_investigation_images']}=={'peripheral-vascular-image-1','peripheral-vascular-image-2','peripheral-vascular-image-3'}
    assert not package['module_lesson_images_or_other_investigations_changed'] and not package['model_promoted'] and not package['structure_coverage_granted']
def test_actual_reference_keeps_CT_DSA_and_unlettered_MRA_methods_separate():
    ref=detail(Curriculum(),resolve('ra.mra-peripheral-vessels'))['radiology_reference'];rows={r['id']:r for r in ref['structure_atlas'] if r['id'].startswith(PREFIX)};q=lambda n:rows[PREFIX+'pmc5072342-fig'+str(n)];p=lambda n:rows[PREFIX+'pmc3946661-fig'+str(n)]
    assert len(rows)==5 and not ref['key_images']
    for n in [1,2,3]:assert q(n)['clinical_panels']==['b'] and q(n)['source_context']['panel_types']['a']=='CT' and q(n)['source_context']['source_MRI_sequence_types']=={'b':'noncontrast_QISS'}
    for n in [2,3]:
        assert q(n)['source_context']['panel_types']['c']=='Radiography' and q(n)['source_context']['source_projection_subtypes']['c']=='catheter_digital_subtraction_angiography'
        assert {a['kind'] for a in q(n)['ancillary_panels']}=={'CT','Radiography'}
        assert p(n)['clinical_panels']==['left','right'] and p(n)['source_context']['source_MRI_sequence_types']=={'left':'contrast_enhanced_MRA','right':'noncontrast_HR_QISS'}
    assert 'not independently calibrated severity' in p(2)['limits'] and 'flow direction' in p(3)['limits']
    assert ref['walkthrough']['start']['module_illustrations'] is False and all(not s['normal'] for s in ref['walkthrough']['steps'])
    assert p(3)['id'] in ref['walkthrough']['steps'][3]['images'] and q(2)['id'] in ref['walkthrough']['steps'][4]['images']
    assert not any(i.startswith('peripheral-vascular-image-') for s in ref['walkthrough']['steps'] for i in s['images'])
    for row in rows.values():
        for key in ['full_native_volume_and_temporal_series_included','independent_calibrated_lumen_or_lesion_measurements_verified','complete_patient_tree_wall_and_pedal_extent_verified','cross_panel_patient_series_or_phase_registration_verified','cross_figure_patient_identity_verified','flow_direction_pressure_perfusion_or_viability_verified','projection_is_actual_3D_geometry','source_diagnosis_treatment_or_outcome_independently_verified']:assert row['source_context'][key] is False

def test_cleared_rights_do_not_approve_tissue_or_complete_structure_coverage():
    assets=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'];rows=[a for a in assets if a['id'].startswith(PREFIX)];assert len(rows)==5
    for row in rows:
        grant=row['source']['license'];assert grant['commercial_use'] and grant['redistribution'] and grant['name']=='CC BY 4.0' and sha((ROOT/grant['evidence_path']).read_bytes())==grant['evidence_sha256']
        assert row['anatomical_review']['status']=='pending' and not row['structure_ids'] and not row['requirement_coverage']
