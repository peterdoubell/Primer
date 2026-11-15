"""Verified native Contact source reference, without clinical approval transfer."""
from functools import lru_cache
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
ATLAS='spl-source-contacts'
IDENTIFIER='spl-cortical-source-contacts-reference'
PREFIX='/app/anatomy/'+ATLAS+'/'
BLOB_HOST='https://ja2lsnp9uca4bivw.public.blob.vercel-storage.com'
BLOB_PREFIX=BLOB_HOST+'/radiology-native/spl-source-contacts-v1/runtime/'
REGISTRY=ROOT/'web/anatomy'/ATLAS/'registry.json'
REGISTRY_SHA256='37ea1098bb7cebce4539f98e66308797f3a8939beaa2a963077321605f3d561f'
AUTHORED=frozenset(['ATTRIBUTION.txt', 'LICENSE.txt', 'index.html', 'manifest.json', 'mesh.js', 'transport.js', 'viewer.js', 'mri.js', 'mri-source.json'])
MANIFEST_SHA256='c5ca712f4ee1a0b92f97e2ca50c8260f2dc09ad6669556835cfeef4703b31c2e'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def regular(path):
    if not path.is_file() or any(p.is_symlink() for p in [path,*path.parents] if p==ROOT or ROOT in p.parents):
        raise ValueError('Contact source file missing or symlinked')
@lru_cache(maxsize=1)
def registry():
    regular(REGISTRY);raw=REGISTRY.read_bytes()
    if sha(raw)!=REGISTRY_SHA256:raise ValueError('Contact registry changed')
    data=json.loads(raw)
    if set(data['files'])!=AUTHORED or data['bindings']!=['ra.brain-anatomy','ra.mri-epilepsy']:raise ValueError('Contact scope changed')
    return data
@lru_cache(maxsize=32)
def _check(path,size,modified,digest):
    raw=Path(path).read_bytes()
    if len(raw)!=size or sha(raw)!=digest:raise ValueError('Contact source bytes changed')
def validate_file(name):
    if name not in AUTHORED:raise ValueError('Unknown Contact source asset')
    path=ROOT/'web/anatomy'/ATLAS/name;regular(path);stat=path.stat();row=registry()['files'][name]
    if stat.st_size!=row['bytes']:raise ValueError('Contact source length changed')
    _check(str(path),stat.st_size,stat.st_mtime_ns,row['sha256']);return path
@lru_cache(maxsize=1)
def references():
    data=registry()
    for name in AUTHORED:validate_file(name)
    if data['files']['manifest.json']['sha256']!=MANIFEST_SHA256:raise ValueError('Contact manifest changed')
    manifest=json.loads(validate_file('manifest.json').read_bytes());delivery=data['delivery']
    expected={}
    for p in manifest['meshes'].values():expected[p['file']]={'bytes':p['compressedBytes'],'sha256':p['compressedSHA256']}
    if manifest['clinicalApproval'] is not False or manifest['anatomicalBoundaryValidated'] is not False or manifest['contactFaces']!=274109 or len(manifest['groups'])!=77:raise ValueError('Contact interpretation changed')
    if not delivery['allRemoteHashesMatch'] or delivery['manifestSHA256']!=MANIFEST_SHA256 or set(delivery['files'])!=set(expected):raise ValueError('Contact delivery incomplete')
    for name,row in expected.items():
        if delivery['files'][name]!=dict(row,url=BLOB_PREFIX+row['sha256']+'/'+name,remoteHashVerified=True):raise ValueError('Contact hosted identity changed')
    native=data['native_mri']
    if native!={'manifest_path':'web/anatomy/spl-nac-limbic/manifest.json','manifest_sha256':'204f87b6d88a9570eb34664497a1462a5d8bba1afa0c2f7abe1cdf11082de2e6','config_sha256':data['files']['mri-source.json']['sha256'],'source_pairs':77,'source_anchor_samples':308,'resampled':False,'anatomical_visibility_verified':False,'clinical_approval':False}:raise ValueError('Contact MRI scope changed')
    source_path=ROOT/native['manifest_path'];regular(source_path);source_raw=source_path.read_bytes()
    if sha(source_raw)!=native['manifest_sha256']:raise ValueError('Contact native MRI identity differs')
    source=json.loads(source_raw);config=json.loads(validate_file('mri-source.json').read_bytes())
    if config['volumes']!=source['volumes'] or config['labelVolume']!=source['labelVolume']:raise ValueError('Contact MRI sample metadata changed')
    if [(p['whiteCode'],p['corticalCode'])for p in config['pairs']]!=[(g['whiteCode'],g['corticalCode'])for g in manifest['groups']]:raise ValueError('Contact MRI pair coverage changed')
    for pair in config['pairs']:
        for side in ['white','cortical']:
            anchor=pair['anchors'][side]
            if anchor['sourceLabelCode']!=pair['whiteCode' if side=='white'else 'corticalCode']:raise ValueError('Contact MRI anchor label differs')
            for contrast,row in config['volumes'].items():
                point=anchor['nativeMRI'][contrast]
                if point['nearestSourceLabelCode']!=anchor['sourceLabelCode'] or any(not isinstance(v,int)or v<0 or v>=row['shape'][i]for i,v in enumerate(point['sourceIJK'])):raise ValueError('Contact MRI anchor leaves source class')
    item=data['inspector']
    if item['src']!=PREFIX+'index.html' or item['sha256']!=data['files']['index.html']['sha256'] or item['manifest_sha256']!=MANIFEST_SHA256:raise ValueError('Contact descriptor changed')
    for key in ['clinical_approval','fine_anatomical_approval','current_patient_registration','normal_anatomical_atlas_approval','complete_reporting_anatomy_approved']:
        if item.get(key) is not False:raise ValueError('Contact approval scope changed')
    return {key:[item] for key in ['ra.brain-anatomy','ra.mri-epilepsy']}
