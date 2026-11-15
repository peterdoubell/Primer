"""Byte-pinned published dissection figures with explicit source limitations."""
from functools import lru_cache
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
ATLAS='cavernous-source-photographs'
IDENTIFIER='mosteiro-cavernous-dissection-reference'
PREFIX='/app/anatomy/'+ATLAS+'/'
BINDINGS=['ra.mri-sella']
REGISTRY=ROOT/'data/radiology/cavernous-photo-reference.json'
REGISTRY_SHA256='442de252ecb764b5604a05e02b3eec5432e8000a1492e8019f3ad3e0447fe32e'
FLAGS=('clinical_approval','fine_anatomical_approval','current_patient_registration','normal_anatomical_atlas_approval','complete_reporting_anatomy_approved')
def digest(raw):return hashlib.sha256(raw).hexdigest()
@lru_cache(maxsize=1)
def registry():
    raw=REGISTRY.read_bytes()
    if REGISTRY.is_symlink()or digest(raw)!=REGISTRY_SHA256:raise ValueError('Dissection registry identity differs')
    data=json.loads(raw)
    if data['bindings']!=BINDINGS or data['sourceDOI']!='10.3389/fnana.2024.1367533'or len(data['files'])!=9:raise ValueError('Dissection scope differs')
    if any(data[k]is not False for k in ['clinicalApproval','completeReportingCoverage','wholeGoalComplete']):raise ValueError('Dissection approval differs')
    return data

def validate_file(asset):
    row=registry()['files'][asset];base=ROOT/'web/anatomy'/ATLAS;path=base/asset
    if any(p.is_symlink()for p in [path,*path.parents]if p==ROOT or ROOT in p.parents)or not path.is_file()or base not in path.parents:raise ValueError('Invalid dissection source path')
    raw=path.read_bytes()
    if len(raw)!=row['bytes']or digest(raw)!=row['sha256']:raise ValueError('Dissection source bytes differ')
    return path

@lru_cache(maxsize=1)
def references():
    data=registry()
    for asset in data['files']:validate_file(asset)
    meta=json.loads(validate_file('figure-review.json').read_bytes());item=data['inspector']
    if len(meta['authors'])!=8 or len(meta['figures'])!=5 or meta['raw3DCoordinatesOrMeshesProvided']is not False:raise ValueError('Dissection source grain differs')
    for figure in meta['figures']:
        row=data['files'][figure['file']]
        if row['sha256']!=figure['sha256']or row['bytes']!=figure['bytes']or figure['sourcePixelsAltered']is not False:raise ValueError('Dissection figure identity differs')
    if not all(meta['figures'][i]['captionDiscrepancy']for i in [1,2]):raise ValueError('Source discrepancies missing')
    if item['id']!=IDENTIFIER or item['src']!=PREFIX+'viewer/index.html'or item['manifest_url']!=PREFIX+'figure-review.json'or any(item[k]is not False for k in FLAGS):raise ValueError('Dissection descriptor differs')
    if item['sha256']!=data['files']['viewer/index.html']['sha256']or item['manifest_sha256']!=data['files']['figure-review.json']['sha256']:raise ValueError('Dissection descriptor hashes differ')
    return {key:[item]for key in BINDINGS}
