import gzip
import hashlib
import json
import struct
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/prostate-native-source-review/case0001'

def test_original_surfaces_retain_every_ordered_corner_and_do_not_upgrade_ROI_to_tumour():
    review=json.loads((OUT/'original-source-review.json').read_text())
    assert review['original_objects_verified']==106 and review['original_scalar_samples_independently_decoded']==71479680
    expected={'prostate':1198,'suspicious_target1':4280}
    for row in review['original_surfaces']:
        raw=(OUT/(row['role']+'-original.stl')).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==row['source_STL_sha256']
        count=struct.unpack_from('<I',raw,80)[0]
        assert count==expected[row['role']] and len(raw)==84+count*50
        corners=b''.join(raw[84+i*50+12:84+i*50+48] for i in range(count))
        assert gzip.decompress((OUT/(row['role']+'-original-face-corners.f32.gz')).read_bytes())==corners
        assert hashlib.sha256(corners).hexdigest()==row['source_face_corners_sha256']
        assert row['component_triangle_counts']==[count]
        assert not row['source_positions_normals_faces_or_attributes_changed']
    assert not review['source_ROI_is_proven_tumour_or_current_patient_histology']
    assert not review['prostate_outline_is_every_prostate_zone_capsule_nerve_vessel_or_duct']
    assert not review['clinical_anatomical_or_full_reporting_approval_granted'] and not review['runtime_promoted']

def test_original_MRI_SEG_and_US_roles_preserve_source_grids_and_unresolved_calibration():
    review=json.loads((OUT/'original-source-review.json').read_text())
    assert {r['role'] for r in review['MRI_series']}=={'T2','producer_ADC','producer_calculated_DWI'}
    assert sorted(r['geometry']['shape'] for r in review['MRI_series'])==[[20,132,160],[20,132,160],[60,256,256]]
    for row in review['derived_segmentations']:
        assert row['all_60_T2_SOP_references_exactly_verified']
        assert not row['derived_rasterization_is_original_manual_voxel_segmentation']
        assert not row['clinical_tumour_boundary_or_all_prostate_tissues_approved']
    us=review['original_US_series']
    assert len(us)==2 and {float(r['private_voxel_size']) for r in us}=={0.178,0.356}
    assert all(not r['standard_ImagePositionPatient_present'] and not r['standard_ImageOrientationPatient_present'] and not r['physical_axes_or_native_MRI_US_registration_verified'] for r in us)
    roles=json.loads((OUT/'publisher-roles-and-rights-review.json').read_text())
    assert roles['source_US_transform']!=roles['source_US_inverse_transform']
    assert roles['source_US_registration_average_accuracy_mm']==[3,4]
    assert roles['commercial_reuse_grant']=='CC BY 4.0'

def test_independent_scalar_and_STL_readers_reject_malformed_source_values():
    pytest.importorskip('numpy');pydicom=pytest.importorskip('pydicom')
    from tools.anatomy_sources.review_prostate_biopsy0001 import binary_stl,decode_scalar
    raw=(OUT/'prostate-original.stl').read_bytes()
    with pytest.raises(ValueError,match='Incomplete'):binary_stl(raw[:-1])
    ds=pydicom.dcmread(OUT/'prostate-original-SEG.dcm')
    assert decode_scalar(ds).shape==(60,256,256)
    ds.HighBit=1
    with pytest.raises(ValueError,match='bit field'):decode_scalar(ds)
