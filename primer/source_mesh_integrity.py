"""Validate local source geometry or release-verified CDN metadata; no anatomy approval."""
import gzip
import hashlib
import json
import os
import struct
from functools import lru_cache
from pathlib import Path

# These registered source-reference atlases have mesh bytes excluded from the
# Python bundle and delivered by the configured static builder. Other sources
# must keep local bytes, even in hosted mode.
CDN_ATLASES = frozenset(('bodyparts3d', 'liu-lumbosacral-sub03', 'verse521', 'hvsmr2-pat7', 'openear-zeta'))


@lru_cache(maxsize=1)
def _inventory(path):
    data = json.loads(Path(path).read_text())
    if data.get('schema_version') != 1 or not isinstance(data.get('files'), dict):
        raise ValueError('Invalid verified static source mesh inventory')
    return data['files']


def verified_mesh_contract(part, atlas_root, data_dir):
    """Return the actual header and decoded byte count checked in release QA."""
    root = Path(atlas_root).resolve()
    prefix = '/app/anatomy/'+root.name+'/'
    src = part.get('file')
    if not isinstance(src, str) or not src.startswith(prefix) or '%' in src or '\\' in src:
        raise ValueError('Source anatomy mesh must remain in its atlas')
    path = (root/src.removeprefix(prefix)).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Source anatomy mesh leaves its atlas')
    if path.is_file():
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != part['sha256']:
            raise ValueError('Source anatomy mesh changed')
        decoded = gzip.decompress(raw) if src.endswith('.gz') else raw
        if 'decoded_sha256' in part and hashlib.sha256(decoded).hexdigest() != part['decoded_sha256']:
            raise ValueError('Source anatomy decoded geometry changed')
        return decoded[:12], len(decoded)
    if not os.environ.get('VERCEL') or root.name not in CDN_ATLASES:
        raise ValueError('Source anatomy mesh missing from its atlas')
    entry = _inventory(str(Path(data_dir)/'radiology-static-source-meshes.json')).get(src)
    if (not isinstance(entry, dict) or entry.get('sha256') != part.get('sha256')
            or entry.get('vertices') != part.get('vertices')
            or entry.get('triangles') != part.get('triangles')
            or ('decoded_sha256' in part and entry.get('decoded_sha256') != part['decoded_sha256'])
            or type(entry.get('decoded_bytes')) is not int
            or entry['decoded_bytes'] != 12+part['vertices']*24+part['triangles']*12):
        raise ValueError('Hosted source mesh differs from verified release inventory')
    try:
        header = bytes.fromhex(entry['header_hex'])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError('Hosted source mesh header is invalid') from exc
    if len(header) != 12 or struct.unpack('<4sII', header) != (b'BP3D', part['vertices'], part['triangles']*3):
        raise ValueError('Hosted source mesh header differs')
    return header, entry['decoded_bytes']
