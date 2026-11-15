"""All source voxels survive; none of this grants anatomy or US approval."""
import base64,copy,gzip,hashlib,json,re
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];PROOF=ROOT/'docs/thyroid-native-source-review/s0358';OUT=ROOT/'web/anatomy/totalseg-v3-s0358'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_every_CT_sample_and_all_overlapping_masks_match_independent_original_digests():
    html=(OUT/'ct-reference.html').read_text();data=json.loads(re.search(r'<script id="dataset" type="application/json">(.*?)</script>',html,re.S).group(1));native=json.loads((PROOF/'native-source-review.json').read_text());proof=json.loads((PROOF/'CT-reader-array-review.json').read_text());records={r['file']:r for r in native['original_files']};ct=gzip.decompress(base64.b64decode(data['ct']));mask=gzip.decompress(base64.b64decode(data['mask']));assert data['shape']==[255,255,523] and len(mask)==34008075 and len(ct)==68016150
    assert sha(ct)==records['ct.nii.gz']['raw_voxel_sha256']==data['ct_sha256']==proof['CT_payload_sha256'];assert sha(mask)==data['mask_sha256']==proof['mask_payload_sha256'];assert data['affine']==records['ct.nii.gz']['sform']
    for row in proof['binary_mask_readback']:
        recovered=mask.translate(bytes((value>>row['bit'])&1 for value in range(256)))
        assert sha(recovered)==records[row['file']]['raw_voxel_sha256']==row['original_payload_sha256'];assert recovered.count(b'\x01')==row['foreground_voxels']
    counts=mask.translate(bytes(int(bool(value&(value-1))) for value in range(256)));assert counts.count(b'\x01')==proof['overlap_voxels']==22
    assert not proof['source_voxels_resampled_relabelled_cropped_or_repaired'] and not proof['clinical_approval'] and not proof['independent_physical_calibration']
    assert '<script>' not in html and 'Raw DICOM/HU calibration' in html
@pytest.mark.parametrize('mutation',['hash','script','label'])
def test_source_volume_or_part_pairing_cannot_change_silently(monkeypatch,mutation):
    from primer import radiology_catalog as catalog
    original=catalog._read
    def changed(name,default=None):
        data=copy.deepcopy(original(name,default))
        if name=='source-anatomy-references.json':
            volume=data['ra.ultrasound-thyroid'][0]['source_volume']
            if mutation=='hash':volume['sha256']='0'*64
            if mutation=='script':volume['script_sha256']='0'*64
            if mutation=='label':volume['level_by_part']['totalseg-v3-s0358-thyroid_gland']='trachea'
        return data
    catalog._source_anatomy_references.cache_clear();monkeypatch.setattr(catalog,'_read',changed)
    try:
        with pytest.raises(ValueError):catalog._source_anatomy_references()
    finally:catalog._source_anatomy_references.cache_clear()
