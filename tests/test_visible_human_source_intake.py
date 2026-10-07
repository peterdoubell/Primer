import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/visible-human-source-review'
def test_current_rights_and_original_encoding_are_not_conflated_with_old_readmes():
    r=json.loads((OUT/'rights-and-grid-intake.json').read_text())
    assert r['female_nominal_sampling_mm']==[.33,.33,.33] and r['female_raw_shape_xy']==[2048,1216]
    assert r['female_full_head_neck_frame_count']==855
    assert r['mandatory_attribution']=='Courtesy of the U.S. National Library of Medicine'
    assert 'no access licence is required since 2019' in r['rights_basis']
    assert not r['NLM_endorsement_implied'] and not r['source_3D_registration_independently_verified']
    assert not r['original_cadaver_RGB_is_current_patient_or_functional_evidence']
    assert not r['third_party_lower_extremity_geometry_is_neck_data']
    head=r['additional_head_source'];assert head['provider_synthetic_average_slice_ids']==[172,173,174,1395]
    assert head['nominal_sampling_mm']==[.147,.147,.147] and not head['individual_source_grant_independently_cleared']
    for flag in ['clinical_approval','structure_coverage_granted','runtime_promoted']:assert r[flag] is False
def test_sampled_original_planar_rgb_matches_every_published_png_sample():
    rows=json.loads((OUT/'paired-original-samples.json').read_text())
    assert [r['file'] for r in rows]==['avf1240a','avf1260a','avf1280a']
    assert all(r['all_original_RGB_channels_equal_published_PNG'] and r['raw_Z_single_object_MD5_verified'] for r in rows)
    for row in rows:
        assert len(row['decoded_planar_source_sha256'])==len(row['decoded_RGB_sha256'])==64

def test_complete_original_sequence_preserves_every_frame_without_registration_claims():
    r=json.loads((OUT/'female-head-original-acquisition.json').read_text());rows=r['records']
    assert len(rows)==855 and [x['frame'] for x in rows]==[f'avf{n}{c}' for n in range(1001,1286) for c in 'abc']
    assert r['source_grid']==[2048,1216,855]
    assert all(x['all_original_RGB_samples_match_PNG'] and x['original_PNG']['single_object_MD5_verified'] and x['original_raw_Z']['single_object_MD5_verified'] for x in rows)
    assert r['every_original_raw_RGB_sample_matches_PNG'] and not r['source_RGB_samples_repaired_cropped_or_enhanced']
    assert not r['raw_photos_independently_registered_or_physically_calibrated']
    assert not r['source_cadaver_photos_are_living_patient_US_CT_or_functional_evidence']
    assert not r['clinical_approval'] and not r['structure_coverage_granted'] and not r['runtime_promoted']
