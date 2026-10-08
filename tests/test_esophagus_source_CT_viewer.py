"""All source voxels survive; none of this grants anatomy or US approval."""
import base64,copy,gzip,hashlib,json,re
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];PROOF=ROOT/'docs/esophagus-native-context-review/s0358';OUT=ROOT/'web/anatomy/totalseg-v3-esophagus-s0358'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_every_CT_sample_and_all_overlapping_masks_match_independent_original_digests():
    html=(OUT/'ct-reference.html').read_text();data=json.loads(re.search(r'<script id="dataset" type="application/json">(.*?)</script>',html,re.S).group(1));native=json.loads((PROOF/'native-source-review.json').read_text());proof=json.loads((PROOF/'CT-reader-array-review.json').read_text());records={r['file']:r for r in native['original_files']};ct=gzip.decompress(base64.b64decode(data['ct']));mask=gzip.decompress(base64.b64decode(data['mask']));assert data['shape']==[255,255,523] and len(mask)==34008075*4 and data['mask_bytes_per_voxel']==4 and len(data['levels'])==27 and len(ct)==68016150
    assert sha(ct)==records['ct.nii.gz']['raw_voxel_sha256']==data['ct_sha256']==proof['CT_payload_sha256'];assert sha(mask)==data['mask_sha256']==proof['mask_payload_sha256'];assert data['affine']==records['ct.nii.gz']['sform']
    for row in proof['binary_mask_readback']:
        component=mask[row['bit']//8::4];recovered=component.translate(bytes((value>>(row['bit']%8))&1 for value in range(256)))
        assert sha(recovered)==records[row['file']]['raw_voxel_sha256']==row['original_payload_sha256'];assert recovered.count(b'\x01')==row['foreground_voxels']
    assert proof['overlap_voxels']==2666
    assert max(row['bit'] for row in proof['binary_mask_readback'])==26
    assert next(row for row in proof['binary_mask_readback'] if row['bit']==26)['file']=='vertebrae_T12.nii.gz'
    assert not proof['source_voxels_resampled_relabelled_cropped_or_repaired'] and not proof['clinical_approval'] and not proof['independent_physical_calibration']
    assert '<script>' not in html and 'Raw DICOM/HU calibration' in html
@pytest.mark.parametrize('mutation',['hash','script','label'])
def test_source_volume_or_part_pairing_cannot_change_silently(monkeypatch,mutation):
    from primer import radiology_catalog as catalog
    original=catalog._read
    def changed(name,default=None):
        data=copy.deepcopy(original(name,default))
        if name=='source-anatomy-references.json':
            volume=next(r for r in data['ra.esophagus'] if r['atlas']=='totalseg-v3-esophagus-s0358')['source_volume']
            if mutation=='hash':volume['sha256']='0'*64
            if mutation=='script':volume['script_sha256']='0'*64
            if mutation=='label':volume['level_by_part']['totalseg-v3-esophagus-s0358-esophagus']='trachea'
        return data
    catalog._source_anatomy_references.cache_clear();monkeypatch.setattr(catalog,'_read',changed)
    try:
        with pytest.raises(ValueError):catalog._source_anatomy_references()
    finally:catalog._source_anatomy_references.cache_clear()

@pytest.mark.parametrize('mutation',['html_hash','script_hash','missing_local','unregistered_hosted','escaped_path'])
def test_missing_source_volume_only_uses_exact_verified_CDN_identity(monkeypatch,tmp_path,mutation):
    from primer.source_volume_integrity import verified_volume_identity
    registry=json.loads((ROOT/'data/radiology/source-anatomy-references.json').read_text());v=copy.deepcopy(next(r for r in registry['ra.esophagus'] if r['atlas']=='totalseg-v3-esophagus-s0358')['source_volume']);monkeypatch.setenv('VERCEL','1')
    assert verified_volume_identity(v,tmp_path,ROOT/'data/radiology')==(OUT/'ct-reference.html').stat().st_size
    if mutation=='html_hash':v['sha256']='0'*64
    elif mutation=='script_hash':v['script_sha256']='0'*64
    elif mutation=='missing_local':monkeypatch.delenv('VERCEL')
    elif mutation=='unregistered_hosted':v['src']='/app/anatomy/unknown/ct-reference.html'
    elif mutation=='escaped_path':v['src']='/app/anatomy/../ct-reference.html'
    with pytest.raises(ValueError):verified_volume_identity(v,tmp_path,ROOT/'data/radiology')
