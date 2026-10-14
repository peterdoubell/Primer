"""Source-bound same-case basal lung/organ inspection; anatomical approval remains pending."""
import hashlib,json,os
from functools import lru_cache
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PREFIX='/app/anatomy/totalseg-s0028-basal-context/'
REGISTRY=ROOT/'data/radiology/thoracic-basal-context-inspector.json'
REGISTRY_SHA256='be32dd4f9d0a3d546bdbdecf27948a6808314e6a78df587df9c252fd559d2df5'
AUTHORED=frozenset({'index.html','viewer.css','volume-review.js','surface-review.js','viewer-manifest.json','basal-source-correspondence.png'})
LABELS=frozenset({'lung_upper_lobe_left','lung_lower_lobe_left','lung_upper_lobe_right','lung_middle_lobe_right','lung_lower_lobe_right','liver','spleen'})


@lru_cache(maxsize=1)
def registry():
    raw=REGISTRY.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=REGISTRY_SHA256:raise ValueError('Lung source registry changed')
    data=json.loads(raw);expected=set(AUTHORED)|{'originals/ct.nii.gz'}|{'originals/'+label+'.nii.gz' for label in LABELS}|{'surfaces/'+label+'-review-buffer.bin.gz' for label in LABELS}
    if data.get('schema_version')!=1 or data.get('source_case')!='s0028' or set(data.get('files',{}))!=expected or data.get('source_triangles')!=486984 or data.get('bindings')!={'ra.thoracic-ultrasound':['totalseg-s0028-basal-context']} or set(data.get('inspectors',{}))!={'totalseg-s0028-basal-context'}:raise ValueError('Lung source scope differs')
    return data


def validate_file(asset):
    data=registry()
    if asset not in data['files']:raise ValueError('Unknown lung source asset')
    path=ROOT/'web/anatomy/totalseg-s0028-basal-context'/asset;row=data['files'][asset]
    if path.is_symlink():raise ValueError('Lung source must be a regular file')
    if path.is_file():
        raw=path.read_bytes()
        if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Lung source bytes changed')
    elif asset in AUTHORED or not os.environ.get('VERCEL'):raise ValueError('Lung source file missing')
    return path


@lru_cache(maxsize=1)
def references():
    data=registry()
    for asset in data['files']:validate_file(asset)
    item=data['inspectors']['totalseg-s0028-basal-context']
    if item.get('id')!='totalseg-s0028-basal-context' or item.get('src')!=PREFIX+'index.html' or item.get('manifest_url')!=PREFIX+'viewer-manifest.json' or item.get('modality')!='CT' or item.get('bound_source_ids')!=['totalseg-s0028-basal-context'] or any(item.get(flag) is not False for flag in ['clinical_approval','fine_anatomical_approval','current_patient_registration','normal_anatomical_atlas_approval','complete_reporting_anatomy_approved']):raise ValueError('Lung source identity or approval differs')
    manifest=json.loads(validate_file('viewer-manifest.json').read_text())
    if manifest.get('case')!='s0028' or manifest.get('shape')!=[299,299,394] or manifest.get('spacing')!=[1.5,1.5,1.5] or {p['id'] for p in manifest['parts']}!=LABELS or sum(p['triangles'] for p in manifest['parts'])!=486984 or any(manifest.get(flag) is not False for flag in ['clinical_approval','source_dicom_calibration_verified','current_patient_registration','normal_anatomical_atlas_approval']):raise ValueError('Lung source manifest scope differs')
    if manifest['ct_file']!='originals/ct.nii.gz' or manifest['ct_file_sha256']!=data['files']['originals/ct.nii.gz']['sha256']:raise ValueError('Original CT source binding differs')
    for part in manifest['parts']:
        if part['mask_file']!='originals/'+part['id']+'.nii.gz' or part['buffer_file']!='surfaces/'+part['id']+'-review-buffer.bin.gz' or part['mask_file_sha256']!=data['files'][part['mask_file']]['sha256'] or part['buffer_sha256']!=data['files'][part['buffer_file']]['sha256']:raise ValueError('Lung source array binding differs')
    return {'ra.thoracic-ultrasound':[item]}
