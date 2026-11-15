"""An intact cine file is not proof of stone mobility, pressure response or tenderness."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/gallbladder-dynamic-source-review'


def test_original_clip_provider_hash_and_every_decoded_timestamp_are_preserved():
    proof=json.loads((REVIEW/'original-cine-source-review.json').read_text());raw=(REVIEW/proof['file']).read_bytes()
    assert len(raw)==proof['bytes']==2015031
    assert hashlib.sha1(raw).hexdigest()==proof['publisher_sha1']=='67fa5a5456e9b5ae288975d1cae9cb2934bc87a5'
    assert hashlib.sha256(raw).hexdigest()==proof['sha256']
    assert proof['source_rights_metadata']['LicenseShortName']=='CC BY-SA 4.0'
    assert proof['decoded_frame_count']==len(proof['decoded_frames'])==150
    timestamps=[float(r['source_timestamp_seconds']) for r in proof['decoded_frames']]
    assert timestamps[0]==0 and timestamps[-1]==5.067
    assert all(b>a for a,b in zip(timestamps,timestamps[1:]))
    assert proof['unrepresented_nominal_30fps_slots']==[149,150,151]
    assert abs(timestamps[-1]-timestamps[-2]-.134)<1e-12
    assert proof['original_frame_intervals_preserved_without_interpolation'] is True
    assert proof['original_encoded_clip_altered'] is False


def test_cine_integrity_does_not_approve_required_dynamic_clinical_observations():
    proof=json.loads((REVIEW/'original-cine-source-review.json').read_text())
    for field in ['actual_patient_position_independently_verified','stone_mobility_verified','compression_response_verified',
                  'tenderness_response_verified','doppler_flow_verified','native_acquisition_resolution_verified',
                  'clinical_diagnosis_verified','clinical_approval','runtime_promoted']:
        assert proof[field] is False
    assert proof['nominal_slots_are_not_asserted_missing_clinical_acquisition_frames'] is True
    assert proof['access_holds'][0]['source_media_or_grant_acquired'] is False
    assert proof['access_holds'][0]['indefinite_unavailability_inferred'] is False
