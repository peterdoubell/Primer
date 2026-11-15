"""Named anatomy, planes and conventions cannot be replaced by assumed normality or print callipers."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_radiology_fidelity import digest
from tools.check_msk_fidelity import requirements_for,audit,validate_reporting_snapshots

ROOT=Path(__file__).resolve().parents[1]
IDENT='ra.thoracic-aorta-measurement'
PREFIX='open-thoracic-measurement-pmc3874367-fig'
FOLDER=ROOT/'docs/thoracic-measurement-published-source-review'

def sha(raw):return hashlib.sha256(raw).hexdigest()

def test_full_effective_measurement_contract_and_all_six_fields_are_bound():
    data=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text());item=next(i for i in data['investigations'] if i['investigation_id']==IDENT)
    ref=detail(Curriculum(),resolve(IDENT))['radiology_reference']
    assert item['source_contract_sha256']==digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')})
    single={**data,'scope':{**data['scope'],'catalog_investigation_ids':[IDENT]},'investigations':[item]}
    validate_reporting_snapshots(single,{IDENT:ref['reporting']})
    assert len(item['structures'])==39 and len(requirements_for(item))==325
    assert {r['checklist_index'] for s in item['structures'] for r in s['report_refs']}==set(range(6))
    ids={r['id'] for r in requirements_for(item)}
    for suffix in ['basal_plane.each_actual_attachment_nadir','root_maximum.actual_maximum_sinus_to_sinus_axis',
        'right_sinus.each_sinus_to_sinus_pair','left_noncoronary_commissure.interleaflet_triangle_if_resolved',
        'valve_root_variants.actual_cusp_number_or_fusion','comparison.source_edge_and_axis_conventions',
        'reference_context.named_reference_population_or_guideline','abdominal_protocol_levels.unresolved_or_uncovered_extent']:
        assert 'aortic_measurement.'+suffix in ids
    result=audit(single,{'assets':[{'id':'generic-aorta','kind':'model','investigation_ids':[IDENT],
        'structure_ids':['aortic_measurement.annulus','aortic_measurement.root_maximum']}]},expected_catalog_ids={IDENT})
    assert result['representation_requirements']==975 and result['counts']=={'verified':0,'unverified':0,'missing':975}

def test_actual_methods_and_plane_landmarks_replace_unsupported_presets():
    ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];g=ref['reporting'];s=ref['walkthrough']['steps']
    for step in s:
        text=next(iter(step['normal'].values()));assert '[adequate actual' in text and 'unassessed' in text
        assert 'not dilated' not in text and 'No interval change' not in text
    assert 'virtual basal/hinge plane' in g['measurements'][0]['method']
    assert 'fixed one-slice offset' in g['measurements'][0]['pitfall']
    assert 'maximum sinus-to-sinus' in g['measurements'][1]['method'] and 'average must not' in g['measurements'][1]['pitfall']
    assert 'inner-edge' in g['measurements'][2]['method'] and 'outer-edge' in g['measurements'][2]['method']
    assert 'universal' in s[5]['tip'] and 'actual' in g['template_sections'][0]['body'].lower()

def test_complete_publisher_jpeg_samples_are_byte_identical_and_modes_are_actual():
    proof=json.loads((FOLDER/'original-source-review.json').read_text());package=json.loads((FOLDER/'packaged-source-images.json').read_text())
    assert proof['original_license']=='CC BY 3.0' and len(proof['figures'])==len(package['figures'])==3
    for source,row in zip(proof['figures'],package['figures']):
        path=ROOT/row['local_path'];assert sha(path.read_bytes())==source['sha256']==row['sha256']
        with Image.open(path) as image:
            assert image.mode==source['pixel_mode'] and image.size==(source['width'],source['height'])
            assert sha(image.tobytes())==source['decoded_pixel_sha256']
        assert not source['source_pixels_changed'] and source['method']=='original_publisher_complete_jpeg_byte_identical'
    ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];rows={r['figure_number']:r for r in ref['structure_atlas'] if r['id'].startswith(PREFIX)}
    assert rows[1]['modality']==rows[2]['modality']=='CT' and rows[3]['modality']=='MRI'
    assert rows[1]['source_context']['single_unlettered_image'] and rows[1]['clinical_panels']==['whole']
    assert rows[3]['source_context']['panel_sequences']['c']=='2D_SSFP_cine_method_static_snapshot'
    assert rows[3]['source_context']['panel_gating']['a']=='not_ECG_gated'
    for row in rows.values():
        for key in ['independent_calibrated_measurements_verified','original_acquired_voxel_series_supplied',
                    'independent_same_patient_or_phase_registration_verified','continuous_cine_supplied',
                    'independent_anatomical_review_verified','clinical_normality_or_growth_verified','patient_model_derived']:
            assert row['source_context'][key] is False

def test_cleared_figure_grants_cannot_clear_noncommercial_images_or_anatomical_coverage():
    assets=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets']
    rows=[r for r in assets if r['id'].startswith(PREFIX)];assert len(rows)==3
    for row in rows:
        license=row['source']['license'];assert license['name']=='CC BY 3.0' and license['commercial_use'] and license['redistribution']
        assert sha((ROOT/license['evidence_path']).read_bytes())==license['evidence_sha256']
        assert row['anatomical_review']['status']=='pending' and not row['structure_ids'] and not row['requirement_coverage']
    assert all('11656620' not in r['source']['url'] for r in rows)
