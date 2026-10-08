import base64,copy,gzip,hashlib,json,re,struct
from pathlib import Path
import pytest
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
ROOT=Path(__file__).resolve().parents[1];PROOF=ROOT/'docs/breast-native-MRI-source-review/ISPY1_1002-expert';OUT=ROOT/'web/anatomy/ispy1-expert1002';ATLAS='ispy1-expert1002'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_source_tumour_all_faces_components_and_coordinates_survive_transport():
    m=json.loads((OUT/'manifest.json').read_text());p=m['parts'][ATLAS+'-expert-structural-tumour'];encoded=(ROOT/'web'/p['file'].removeprefix('/app/')).read_bytes();raw=gzip.decompress(encoded);magic,n,indices=struct.unpack('<4sII',raw[:12]);assert magic==b'BP3D' and indices==5144*3 and sha(encoded)==p['sha256'] and sha(raw)==p['decoded_sha256'];faces=raw[12+n*24:];assert faces==gzip.decompress((PROOF/'masks_stv_manual-triangles.u32.gz').read_bytes());v=gzip.decompress((PROOF/'masks_stv_manual-positions.f64.gz').read_bytes());assert max(abs(x[0]-struct.unpack_from('<f',raw,12+i*4)[0]) for i,x in enumerate(struct.iter_unpack('<d',v)))<=4e-5
    assert p['source_components']==2 and p['source_component_triangle_counts']==[5100,44] and not m['complete_breast_geometry_verified'] and not m['clinical_approval']
def test_all_three_processed_MRI_arrays_and_original_mask_are_exact_recoveries():
    data=json.loads(re.search(r'<script id="dataset" type="application/json">(.*?)</script>',(OUT/'mri-reference.html').read_text(),re.S).group(1));native=json.loads((PROOF/'original-source-review.json').read_text());records={r['file']:r for r in native['source_records']};assert data['shape']==[200,200,120] and len(data['phases'])==3
    for p in data['phases']:
        raw=gzip.decompress(base64.b64decode(p['samples']));assert len(raw)==4800000*4 and sha(raw)==p['sha256']==records[p['source_file']]['payload_sha256'];assert data['affine']==records[p['source_file']]['affine']
    mask=gzip.decompress(base64.b64decode(data['mask']));assert len(mask)==4800000 and mask.count(b'\x01')==5091 and set(mask)=={0,1}
    # Rebuild the source float32 values byte-exactly, including their original zero representation.
    original=b''.join(struct.pack('<f',v) for v in mask);row=next(r for r in records.values() if r['file'].startswith('masks_stv_manual/'));assert sha(original)==row['payload_sha256'] and data['affine']==row['affine']
def test_reader_and_CDN_identity_require_MRI_metadata_and_exact_pairing(monkeypatch,tmp_path):
    from primer.source_volume_integrity import verified_volume_identity
    ref=catalog.detail(Curriculum(),catalog.resolve('ra.mri-breast'))['radiology_reference'];entry=next(r for r in ref['source_anatomy_references'] if r['atlas']==ATLAS);v=entry['source_volume'];assert v['modality']=='MRI' and v['src'].endswith('/mri-reference.html');monkeypatch.setenv('VERCEL','1');assert verified_volume_identity(v,tmp_path,ROOT/'data/radiology')==(OUT/'mri-reference.html').stat().st_size
    changed=dict(v,sha256='0'*64)
    with pytest.raises(ValueError,match='release inventory'):verified_volume_identity(changed,tmp_path,ROOT/'data/radiology')
    original_read=catalog._read
    def bad(name,default=None):
        data=copy.deepcopy(original_read(name,default))
        if name=='source-anatomy-references.json':next(r for r in data['ra.mri-breast'] if r['atlas']==ATLAS)['source_volume']['modality']='CT'
        return data
    catalog._source_anatomy_references.cache_clear();monkeypatch.setattr(catalog,'_read',bad)
    try:
        with pytest.raises(ValueError,match='MRI modality'):catalog._source_anatomy_references()
    finally:catalog._source_anatomy_references.cache_clear()
def test_expert_case_is_not_registered_to_unrelated_US_or_threshold_sources():
    data=json.loads((ROOT/'data/radiology/source-anatomy-references.json').read_text());assert any(r['atlas']==ATLAS for r in data['ra.mri-breast']) and any(r['atlas']==ATLAS for r in data['ra.breast-cancer-staging']);assert not any(r['atlas']==ATLAS for r in data.get('ra.ultrasound-breast',[]));assets=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'];row=next(r for r in assets if r['id']==ATLAS+'-expert-structural-tumour');assert not row['structure_ids'] and not row['requirement_coverage'] and row['anatomical_review']['status']=='pending'
