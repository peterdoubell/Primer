import base64
import copy
import gzip
import hashlib
import json
import struct
from pathlib import Path

import pytest
from PIL import Image
from primer import radiology_catalog as catalog
from primer.curriculum import Curriculum
from primer.source_volume_integrity import verified_volume_identity

ROOT=Path(__file__).resolve().parents[1];ATLAS='prostate-biopsy0001';OUT=ROOT/'web/anatomy'/ATLAS;PROOF=ROOT/'docs/prostate-native-source-review/case0001'

def dataset():
    return json.loads((OUT/'mri-reference.html').read_text().split('<script id="dataset" type="application/json">',1)[1].split('</script>',1)[0])

def test_complete_original_faces_are_preserved_at_identical_float32_coordinates():
    manifest=json.loads((OUT/'manifest.json').read_text());source=json.loads((PROOF/'original-source-review.json').read_text())
    for part in manifest['parts'].values():
        role='prostate' if part['id'].endswith('-prostate') else 'suspicious_target1'
        original=(PROOF/(role+'-original.stl')).read_bytes();count=struct.unpack_from('<I',original,80)[0]
        encoded=(ROOT/'web'/part['file'].removeprefix('/app/')).read_bytes();raw=gzip.decompress(encoded)
        assert hashlib.sha256(encoded).hexdigest()==part['sha256'] and hashlib.sha256(raw).hexdigest()==part['decoded_sha256']
        magic,vertices,indices=struct.unpack_from('<4sII',raw)
        assert magic==b'BP3D' and vertices==count*3 and indices==count*3
        corners=b''.join(original[84+i*50+12:84+i*50+48] for i in range(count))
        assert raw[12:12+vertices*12]==corners
        faces=struct.unpack('<'+'I'*indices,raw[12+vertices*24:]);assert faces==tuple(range(indices))
    assert manifest['total_triangles']==5478 and not manifest['complete_prostate_reporting_geometry_verified']
    assert not manifest['clinical_approval'] and not manifest['anatomical_approval']

def test_all_separate_MRI_grids_and_both_original_masks_are_reversibly_encoded():
    data=dataset();proof=json.loads((PROOF/'original-source-review.json').read_text());transport=json.loads((PROOF/'reader-transport-review.json').read_text())
    assert {tuple(v['shape']) for v in data['volumes']}=={(60,256,256),(20,132,160)}
    assert transport['complete_MRI_stored_sample_count']==4776960
    for volume in data['volumes']:
        raw=gzip.decompress(base64.b64decode(volume['samples']));source=next(r for r in proof['MRI_series'] if r['role']==volume['role'])
        assert hashlib.sha256(raw).hexdigest()==volume['sha256']==source['stored_samples_sha256']
        assert len(raw)==source['stored_samples']*2 and volume['affine']==source['geometry']['index_to_dicom_lps_mm']
        assert len(volume['native_windows'])==volume['shape'][0]
    mask=gzip.decompress(base64.b64decode(data['mask']));assert len(mask)==3932160 and hashlib.sha256(mask).hexdigest()==data['mask_sha256']
    for level in data['levels']:
        role='prostate' if level['bit']==0 else 'suspicious_target1';source=next(r for r in proof['derived_segmentations'] if r['role']==role)
        recovered=bytes((v>>level['bit'])&1 for v in mask)
        assert hashlib.sha256(recovered).hexdigest()==source['stored_samples_sha256']
        assert sum(recovered)==source['foreground_samples']
    assert transport['no_mask_overlay_or_resampling_on_ADC_or_DWI']

def test_source_frame_correspondence_and_model_unit_defect_do_not_become_anatomical_approval():
    proof=json.loads((PROOF/'coordinate-correspondence-review.json').read_text())
    assert [r['mismatched_voxel_centres'] for r in proof['comparison']]==[480,5]
    assert sum(r['all_original_voxel_centres_compared'] for r in proof['comparison'])==7864320
    assert proof['source_original_model_measurement_units_code_missing'] and not proof['source_model_full_DICOM_IOD_conformance_claimed']
    assert proof['source_MRI_model_frame_association_numerically_verified'] and not proof['mismatch_source_masks_changed_or_replaced']
    assert not proof['source_clinical_native_registration_or_fine_tissue_accuracy_independently_approved']
    assert not proof['clinical_anatomical_or_full_reporting_approval_granted']

def test_scoped_reader_inventory_preserves_comprehensive_template_and_all_regions():
    ref=catalog.detail(Curriculum(),catalog.resolve('ra.mri-prostate'))['radiology_reference']
    assert len(ref['key_images'])==8 and len(ref['structure_atlas'])==3
    assert all(not s['normal'] for s in ref['walkthrough']['steps'])
    headings={s['heading'] for s in ref['report_templates'][0]['sections']}
    assert {'GLAND / PSA DENSITY','LESION WORKSHEET — REPEAT FOR EACH REPORTED LESION','LOCAL EXTENT','NODES / BONES / OTHER PELVIC FINDINGS'}<=headings
    requirements=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text());item=next(r for r in requirements['investigations'] if r['investigation_id']=='ra.mri-prostate')
    assert len(item['structures'])==107 and sum(s['official_idealized_sector_region'] for s in item['structures'])==41
    assert any('TZ_PZ_pseudocapsule' in s['id'] for s in item['structures'])
    assert any('anterior_apical_gaps' in s['id'] for s in item['structures'])
    for entry in ref['source_anatomy_references']:
        assert entry['atlas']==ATLAS and entry['source_volume']['modality']=='MRI'
    other=catalog.detail(Curriculum(),catalog.resolve('ra.mri-breast'))['radiology_reference']
    assert not any(e['atlas']==ATLAS for e in other['source_anatomy_references'])
    assets=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets']
    for asset in assets:
        if asset['id'].startswith((ATLAS,'open-prostate-biopsy0001')):
            assert asset['anatomical_review']['status']=='pending' and not asset['structure_ids'] and not asset['requirement_coverage']

def test_new_CDN_MRI_identity_is_specific_and_invalid_missing_contracts_are_rejected(tmp_path,monkeypatch):
    ref=catalog.detail(Curriculum(),catalog.resolve('ra.mri-prostate'))['radiology_reference'];volume=ref['source_anatomy_references'][0]['source_volume']
    assert verified_volume_identity(volume,ROOT/'web',ROOT/'data/radiology')>0
    (tmp_path/'data').mkdir();inventory=json.loads((ROOT/'data/radiology/radiology-static-source-volumes.json').read_text())
    (tmp_path/'data/radiology-static-source-volumes.json').write_text(json.dumps(inventory));monkeypatch.setenv('VERCEL','1')
    assert verified_volume_identity(volume,tmp_path/'web',tmp_path/'data')>0
    bad=copy.deepcopy(volume);bad['sha256']='0'*64
    with pytest.raises(ValueError,match='differs'):verified_volume_identity(bad,tmp_path/'web',tmp_path/'data')
    bad=copy.deepcopy(volume);bad['src']=bad['src'].replace('mri-reference','ct-reference')
    with pytest.raises(ValueError,match='canonical'):verified_volume_identity(bad,tmp_path/'web',tmp_path/'data')

def test_native_T2_display_files_are_windowed_source_planes_not_fabricated_publication_figures():
    proof=json.loads((PROOF/'source-T2-display-stills-review.json').read_text());ref=catalog.detail(Curriculum(),catalog.resolve('ra.mri-prostate'))['radiology_reference']
    for row,record in zip(ref['structure_atlas'],proof['figures']):
        assert row['origin']=='native-volume-sections' and 'figure_number' not in row
        assert row['source_context']['population']['age_years']==64
        path=ROOT/'web'/row['src'].removeprefix('/app/')
        with Image.open(path) as im:assert im.size==(256,256) and hashlib.sha256(im.tobytes()).hexdigest()==record['display_pixel_sha256']
        assert not record['source_plane_matrix_cropped_resampled_or_relabelled']
        bad=copy.deepcopy(row);bad['modality']='CT'
        with pytest.raises(ValueError,match='modality'):catalog._validate_native_volume_figure(bad,path.parent)
