"""Complete source case matching does not approve nodal interiors, physical scale or commercial reuse."""
import hashlib,json
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/lymphus-native-source-review'
def test_original_archive_member_inventory_and_case_identity():
    a=json.loads((OUT/'original-acquisition.json').read_text());r=json.loads((OUT/'original-image-review.json').read_text())
    assert hashlib.sha256((OUT/'original-acquisition.json').read_bytes()).hexdigest()==r['acquisition_sha256']
    assert [(x['bytes'],len(x['members'])) for x in a['archives']]==[(21867173,541),(29108550,475)]
    assert all(x['all_original_members_CRC_verified'] and not x['publisher_checksum_supplied'] for x in a['archives'])
    assert [x['case_count'] for x in r['centres']]==[180,158]
    assert [x['group_counts'] for x in r['centres']]==[{'Benign':99,'Malignant':81},{'Benign':76,'Malignant':82}]
    for centre in r['centres']:
        cases=centre['cases'];assert len({x['source_case'] for x in cases})==len(cases)
        assert len({x['spreadsheet_row'] for x in cases})==len(cases)
        assert all(x['source_lesion_is_exact_original_image_times_mask'] for x in cases)
        for case in cases:
            assert case['source_case']==f'centre{centre["centre"]}-{case["group"].lower()}-{case["index_within_group"]}'
            assert case['mask_foreground_pixels']>0
            assert set(case['original_decoded_sha256'])=={'image','mask','lesion'}
    for key in ['publisher_archive_checksum_supplied','commercial_native_dataset_clearance_verified','original_native_US_DICOM_or_cine_available','physical_pixel_spacing_independently_verified','source_3D_geometry_acquired','individual_source_case_age_sex_plane_level_laterality_or_ENE_assumed','source_samples_repaired_resampled_or_relabelled','clinical_approval','structure_coverage_granted','runtime_promoted']:
        assert r[key] is False
    assert r['mask_is_node_envelope_not_independent_cortex_hilum_capsule_annotation']
def test_original_complete_case_review_is_reproducible_when_cache_exists(tmp_path):
    pytest.importorskip('numpy');pytest.importorskip('openpyxl');pytest.importorskip('PIL')
    from tools.anatomy_sources.review_LymphUs_original import review
    source=ROOT.parent/'cervical-node-native-source-review/LymphUs-original'
    if not source.is_dir():pytest.skip('Author acquisition cache unavailable')
    review(source,tmp_path)
    assert (tmp_path/'original-image-review.json').read_bytes()==(OUT/'original-image-review.json').read_bytes()
