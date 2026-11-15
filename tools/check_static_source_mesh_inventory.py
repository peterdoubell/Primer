#!/usr/bin/env python3
"""Bind excluded source-reference mesh contracts to actual reviewed runtime bytes."""
import argparse
import gzip
import hashlib
import json
import struct
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from primer.source_mesh_integrity import CDN_ATLASES


def inventory():
    sources = json.loads((ROOT/'data/radiology/source-anatomy-references.json').read_text())
    files = {}
    for entries in sources.values():
        for entry in entries:
            if entry['atlas'] not in CDN_ATLASES: continue
            root = (ROOT/'web/anatomy'/entry['atlas']).resolve()
            manifest_raw = (root/'manifest.json').read_bytes()
            if hashlib.sha256(manifest_raw).hexdigest() != entry['manifest_sha256']:
                raise ValueError('Source manifest changed')
            manifest = json.loads(manifest_raw)
            for selected in manifest['regions'][entry['family']]['parts']:
                part = manifest['parts'][selected['id']]; src = part['file']; prefix = '/app/anatomy/'+entry['atlas']+'/'
                if not src.startswith(prefix) or '%' in src or '\\' in src: raise ValueError('Source path invalid')
                path = (root/src.removeprefix(prefix)).resolve()
                if not path.is_relative_to(root): raise ValueError('Source path escaped')
                raw = path.read_bytes(); sha = hashlib.sha256(raw).hexdigest()
                if sha != part['sha256']: raise ValueError('Reviewed source mesh bytes changed')
                decoded = gzip.decompress(raw) if src.endswith('.gz') else raw
                header = decoded[:12]
                if len(header) != 12: raise ValueError('Source mesh header truncated')
                magic, vertices, indices = struct.unpack('<4sII',header)
                if magic != b'BP3D' or (vertices, indices) != (part['vertices'], part['triangles']*3) or len(decoded) != 12+vertices*24+indices*4:
                    raise ValueError('Source mesh contract invalid')
                decoded_sha = hashlib.sha256(decoded).hexdigest()
                if 'decoded_sha256' in part and decoded_sha != part['decoded_sha256']: raise ValueError('Reviewed decoded mesh changed')
                item = {'sha256':sha,'decoded_sha256':decoded_sha,'bytes':len(raw),'decoded_bytes':len(decoded),
                        'vertices':vertices,'triangles':indices//3,'header_hex':header.hex()}
                if src in files and files[src] != item: raise ValueError('Conflicting source geometry')
                files[src] = item
    return {'schema_version':1,'scope':'Configured CDN source-reference geometry only; release byte integrity, not anatomical approval.',
            'files':dict(sorted(files.items()))}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--write',action='store_true'); args = parser.parse_args()
    data = inventory(); path = ROOT/'data/radiology/radiology-static-source-meshes.json'
    if args.write: path.write_text(json.dumps(data,indent=2)+'\n')
    elif json.loads(path.read_text()) != data: raise SystemExit('Static source mesh inventory differs from reviewed actual files')
    print(len(data['files']),'source-reference mesh file contracts verified')
