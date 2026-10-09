"""Local source viewer bytes or release-verified CDN identity; no anatomy approval."""
import gzip,hashlib,json,os,re
from pathlib import Path
CDN_VOLUME_FILES={'totalseg-v3-esophagus-s0358':'ct-reference.html','ispy1-expert1002':'mri-reference.html','prostate-biopsy0001':'mri-reference.html'}
CDN_VOLUME_FILES.update({'fedbca-' + case: 'mri-reference.html' for case in ['center1-001', 'center2-01', 'center3-01', 'center4-01']})
CDN_VOLUME_ATLASES=frozenset(CDN_VOLUME_FILES)
def _hosted_identity(volume,data_dir,atlas):
    if not os.environ.get('VERCEL') or atlas not in CDN_VOLUME_ATLASES:
        raise ValueError('Source volume viewer/array missing')
    inventory=json.loads((Path(data_dir)/'radiology-static-source-volumes.json').read_text())
    if inventory.get('schema_version')!=1 or not isinstance(inventory.get('files'),dict):
        raise ValueError('Invalid verified static source volume inventory')
    row=inventory['files'].get(volume['src'])
    if (not isinstance(row,dict) or row.get('sha256')!=volume.get('sha256')
            or row.get('script_sha256')!=volume.get('script_sha256')
            or row.get('data_files')!=volume.get('data_files')
            or type(row.get('bytes')) is not int or row['bytes']<=0):
        raise ValueError('Hosted source volume differs from verified release inventory')
    return row
def verified_volume_identity(volume,web,data_dir):
    src=volume.get('src');prefix='/app/anatomy/'
    if not isinstance(src,str) or not src.startswith(prefix) or '%' in src or '\\' in src:
        raise ValueError('Invalid source volume path')
    parts=src.removeprefix(prefix).split('/')
    if len(parts)!=2 or parts[0] in {'','.','..'} or parts[1]!=CDN_VOLUME_FILES.get(parts[0],'ct-reference.html'):
        raise ValueError('Source volume must use its canonical atlas viewer')
    if parts[0].startswith('fedbca-'):
        payloads=volume.get('data_files')
        if (not isinstance(payloads,list) or len(payloads)!=2
                or any(not isinstance(p,dict) for p in payloads)
                or {p.get('file') for p in payloads}!={'source-image.bin.gz','source-label.bin.gz'}):
            raise ValueError('Source volume needs both complete original array identities')
        for payload in payloads:
            if (any(type(payload.get(k)) is not int or payload[k]<=0 for k in ['bytes','compressed_bytes'])
                    or any(not re.fullmatch(r'[0-9a-f]{64}',payload.get(k,'')) for k in ['compressed_sha256','raw_source_voxel_sha256'])):
                raise ValueError('Invalid complete source array identity')
    root=Path(web).resolve();path=(root/src.removeprefix('/app/')).resolve()
    if not path.is_relative_to(root):raise ValueError('Source volume leaves its workspace')
    if path.is_file():
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=volume.get('sha256'):raise ValueError('Source volume viewer changed')
        for row in volume.get('data_files', []):
            if row.get('file') not in {'source-image.bin.gz', 'source-label.bin.gz'}:
                raise ValueError('Unknown source volume array filename')
            payload=path.parent/row['file']
            if not payload.is_file():
                _hosted_identity(volume,data_dir,parts[0])
                continue
            encoded=payload.read_bytes();decoded=gzip.decompress(encoded)
            if (len(encoded)!=row.get('compressed_bytes') or hashlib.sha256(encoded).hexdigest()!=row.get('compressed_sha256')
                    or len(decoded)!=row.get('bytes') or hashlib.sha256(decoded).hexdigest()!=row.get('raw_source_voxel_sha256')):
                raise ValueError('Complete source volume array changed')
        return len(raw)
    return _hosted_identity(volume,data_dir,parts[0])['bytes']
