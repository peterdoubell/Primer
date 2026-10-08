"""Local source viewer bytes or release-verified CDN identity; no anatomy approval."""
import hashlib,json,os
from pathlib import Path
CDN_VOLUME_FILES={'totalseg-v3-esophagus-s0358':'ct-reference.html','ispy1-expert1002':'mri-reference.html','prostate-biopsy0001':'mri-reference.html'}
CDN_VOLUME_ATLASES=frozenset(CDN_VOLUME_FILES)
def verified_volume_identity(volume,web,data_dir):
    src=volume.get('src');prefix='/app/anatomy/'
    if not isinstance(src,str) or not src.startswith(prefix) or '%' in src or '\\' in src:
        raise ValueError('Invalid source volume path')
    parts=src.removeprefix(prefix).split('/')
    if len(parts)!=2 or parts[0] in {'','.','..'} or parts[1]!=CDN_VOLUME_FILES.get(parts[0],'ct-reference.html'):
        raise ValueError('Source volume must use its canonical atlas viewer')
    root=Path(web).resolve();path=(root/src.removeprefix('/app/')).resolve()
    if not path.is_relative_to(root):raise ValueError('Source volume leaves its workspace')
    if path.is_file():
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=volume.get('sha256'):raise ValueError('Source volume viewer changed')
        return len(raw)
    if not os.environ.get('VERCEL') or parts[0] not in CDN_VOLUME_ATLASES:
        raise ValueError('Source volume viewer missing')
    inventory=json.loads((Path(data_dir)/'radiology-static-source-volumes.json').read_text())
    if inventory.get('schema_version')!=1 or not isinstance(inventory.get('files'),dict):
        raise ValueError('Invalid verified static source volume inventory')
    row=inventory['files'].get(src)
    if (not isinstance(row,dict) or row.get('sha256')!=volume.get('sha256')
            or row.get('script_sha256')!=volume.get('script_sha256')
            or type(row.get('bytes')) is not int or row['bytes']<=0):
        raise ValueError('Hosted source volume differs from verified release inventory')
    return row['bytes']
