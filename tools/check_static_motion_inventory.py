#!/usr/bin/env python3
"""Bind static movie declarations to actual released bytes and container tables."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from primer.source_motion_contract import parse_motion_contract

def inventory():
    registry=json.loads((ROOT/'data/radiology/source-motion-references.json').read_text());rows={}
    for entries in registry.values():
        for item in entries:
            for field,digest in [('src','sha256'),('original_src','original_sha256')]:
                src=item[field];prefix='/app/reference-media/radiology-motion/'
                if not src.startswith(prefix) or '/' in src.removeprefix(prefix) or '%' in src or '\\' in src:raise ValueError('Invalid motion path')
                path=ROOT/'web'/src.removeprefix('/app/');raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest()
                if sha!=item[digest]:raise ValueError('Motion source changed')
                row={'sha256':sha,'bytes':len(raw),'contract':parse_motion_contract(raw)}
                if src in rows and rows[src]!=row:raise ValueError('Conflicting motion source')
                rows[src]=row
    return {'schema_version':1,'scope':'Release byte/container integrity only; no anatomical or physiological approval.','files':dict(sorted(rows.items()))}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args();data=inventory();path=ROOT/'data/radiology/radiology-static-motion.json'
    if args.write:path.write_text(json.dumps(data,indent=2)+'\n')
    elif json.loads(path.read_text())!=data:raise SystemExit('Static motion inventory differs from actual files')
    print(len(data['files']),'original motion byte/container contracts verified')
