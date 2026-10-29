"""Verified native FCD source reference, without clinical approval transfer."""
from functools import lru_cache
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
ATLAS='bonn-fcd-case4'
IDENTIFIER='bonn-fcd-case4-native-reference'
PREFIX='/app/anatomy/'+ATLAS+'/'
BLOB_HOST='https://ja2lsnp9uca4bivw.public.blob.vercel-storage.com'
BLOB_PREFIX=BLOB_HOST+'/radiology-native/bonn-fcd-case4-v1.0.6/runtime/'
REGISTRY=ROOT/'web/anatomy'/ATLAS/'registry.json'
REGISTRY_SHA256='d060496a8dbe27a3a346704b61397f50644c65fc55ff7bfa36ae7ab0e910d54a'
AUTHORED=frozenset(['ATTRIBUTION.txt', 'index.html', 'manifest.json', 'mesh.js', 'native-core.js', 'transport.js', 'viewer.css', 'viewer.js'])
MANIFEST_SHA256='17c57029b09ab6eddfb9648dfdc4df3d570a04d778a90fa37aedec42e39fde6b'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def regular(path):
    if not path.is_file() or any(p.is_symlink() for p in [path,*path.parents] if p==ROOT or ROOT in p.parents):
        raise ValueError('FCD source file missing or symlinked')
@lru_cache(maxsize=1)
def registry():
    regular(REGISTRY);raw=REGISTRY.read_bytes()
    if sha(raw)!=REGISTRY_SHA256:raise ValueError('FCD registry changed')
    data=json.loads(raw)
    if set(data['files'])!=AUTHORED or data['bindings']!=['ra.mri-epilepsy']:raise ValueError('FCD scope changed')
    return data
@lru_cache(maxsize=32)
def _check(path,size,modified,digest):
    raw=Path(path).read_bytes()
    if len(raw)!=size or sha(raw)!=digest:raise ValueError('FCD source bytes changed')
def validate_file(name):
    if name not in AUTHORED:raise ValueError('Unknown FCD source asset')
    path=ROOT/'web/anatomy'/ATLAS/name;regular(path);stat=path.stat();row=registry()['files'][name]
    if stat.st_size!=row['bytes']:raise ValueError('FCD source length changed')
    _check(str(path),stat.st_size,stat.st_mtime_ns,row['sha256']);return path
@lru_cache(maxsize=1)
def references():
    data=registry()
    for name in AUTHORED:validate_file(name)
    if data['files']['manifest.json']['sha256']!=MANIFEST_SHA256:raise ValueError('FCD manifest changed')
    manifest=json.loads(validate_file('manifest.json').read_bytes());delivery=data['delivery']
    expected={p['file']:{'bytes':p['bytes'],'sha256':p['sha256']} for v in manifest['volumes'].values() for p in v['planes'].values()}
    for p in manifest['meshes'].values():expected[p['file']]={'bytes':p['compressedBytes'],'sha256':p['compressedSHA256']}
    if not delivery['allRemoteHashesMatch'] or delivery['manifestSHA256']!=MANIFEST_SHA256 or set(delivery['files'])!=set(expected):raise ValueError('FCD delivery incomplete')
    for name,row in expected.items():
        if delivery['files'][name]!=dict(row,url=BLOB_PREFIX+row['sha256']+'/'+name,remoteHashVerified=True):raise ValueError('FCD hosted identity changed')
    item=data['inspector']
    if item['src']!=PREFIX+'index.html' or item['sha256']!=data['files']['index.html']['sha256'] or item['manifest_sha256']!=MANIFEST_SHA256:raise ValueError('FCD descriptor changed')
    for key in ['clinical_approval','fine_anatomical_approval','current_patient_registration','normal_anatomical_atlas_approval','complete_reporting_anatomy_approved']:
        if item.get(key) is not False:raise ValueError('FCD approval scope changed')
    return {'ra.mri-epilepsy':[item]}
