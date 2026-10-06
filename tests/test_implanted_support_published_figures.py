"""Historical support-device projections cannot establish present function, circuit roles or geometry."""
import hashlib,json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/implanted-support-published-source-review';PREFIX='open-implanted-support-pmc6837777-fig'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_complete_original_pixels_and_grant_are_preserved():
    p=json.loads((OUT/'original-source-review.json').read_text());pack=json.loads((OUT/'packaged-source-images.json').read_text());assert p['original_license']=='CC BY 4.0' and len(p['figures'])==len(pack['figures'])==11
    for s,r in zip(p['figures'],pack['figures']):
        path=ROOT/r['local_path'];assert sha(path.read_bytes())==s['sha256']==r['sha256']
        with Image.open(path) as im:assert im.mode==s['pixel_mode'] and im.size==(s['width'],s['height']) and sha(im.tobytes())==s['decoded_pixel_sha256']
        assert s['publisher_md5_verified'] and not s['source_pixels_changed']
    assert 'June 3, 2021' in p['historical_regulatory_context']['scope'] and not pack['model_promoted'] and not pack['structure_coverage_granted']
def test_source_historical_and_intentionally_inactive_states_are_explicit():
    ref=detail(Curriculum(),resolve('ra.cardiovascular-devices'))['radiology_reference'];rows={r['figure_number']:r for r in ref['structure_atlas'] if r['id'].startswith(PREFIX)};assert set(rows)==set(range(1,12))
    assert 'not a current repositioning instruction' in rows[1]['limits']
    assert rows[5]['clinical_panels']==list('ab') and 'recirculation' in rows[2]['limits']
    assert 'not independently calibrated' in rows[7]['limits'] and 'universal acceptable values' in rows[7]['limits'] and rows[8]['source_context']['source_reported_same_case_as_figure']==7
    assert rows[9]['source_context']['source_historical_hvad'] and 'existing implants' in rows[9]['limits']
    assert rows[11]['source_context']['source_intentionally_decommissioned'] and 'not automatically' in rows[11]['limits']
    for row in rows.values():
        for k in ['full_acquired_series_included','independent_calibrated_measurements_verified','same_series_registration_verified','cross_figure_patient_identity_verified','full_device_native_geometry_verified','current_system_function_or_mri_conditions_verified','measured_circuit_flow_or_recirculation_verified']:assert row['source_context'][k] is False
    assert 'Identify actual ECMO drainage and return' in ref['walkthrough']['steps'][1]['tip']
    assert 'documented decommissioning' in ref['walkthrough']['steps'][4]['tip']
    assert {PREFIX+'7',PREFIX+'8',PREFIX+'9',PREFIX+'11'}.issubset(ref['walkthrough']['steps'][4]['images'])
def test_rights_do_not_approve_circuit_or_native_device_anatomy():
    assets=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'];rows=[r for r in assets if r['id'].startswith(PREFIX)];assert len(rows)==11
    for row in rows:
        license=row['source']['license'];assert license['commercial_use'] and license['redistribution'] and license['name']=='CC BY 4.0'
        assert sha((ROOT/license['evidence_path']).read_bytes())==license['evidence_sha256']
        assert not row['structure_ids'] and not row['requirement_coverage'] and row['anatomical_review']['status']=='pending'
