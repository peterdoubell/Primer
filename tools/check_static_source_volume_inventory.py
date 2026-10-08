#!/usr/bin/env python3
"""Bind CDN source volume identities to actual complete source viewer files."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from primer.source_volume_integrity import CDN_VOLUME_ATLASES

def inventory():
    files={}
    for entries in json.loads((ROOT/'data/radiology/source-anatomy-references.json').read_text()).values():
        for entry in entries:
            if entry['atlas'] not in CDN_VOLUME_ATLASES:continue
            volume=entry.get('source_volume')
            if not volume or volume.get('src')!='/app/anatomy/'+entry['atlas']+'/ct-reference.html':raise ValueError('Unregistered source volume')
            root=(ROOT/'web/anatomy'/entry['atlas']).resolve();path=(ROOT/'web'/volume['src'].removeprefix('/app/')).resolve()
            if not path.is_relative_to(root) or not path.is_file():raise ValueError('Source volume missing or outside atlas')
            raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest();script=hashlib.sha256(path.with_suffix('.js').read_bytes()).hexdigest()
            if sha!=volume['sha256'] or script!=volume['script_sha256']:raise ValueError('Reviewed source volume/script changed')
            row={'sha256':sha,'script_sha256':script,'bytes':len(raw)}
            if volume['src'] in files and files[volume['src']]!=row:raise ValueError('Conflicting source volume identity')
            files[volume['src']]=row
    return {'schema_version':1,'scope':'Configured CDN source CT viewers; release integrity only, not anatomical approval.','files':dict(sorted(files.items()))}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');args=p.parse_args();data=inventory();path=ROOT/'data/radiology/radiology-static-source-volumes.json'
    if args.write:path.write_text(json.dumps(data,indent=2)+'\n')
    elif json.loads(path.read_text())!=data:raise SystemExit('Static source volume inventory differs from reviewed source bytes')
    print(len(data['files']),'complete source CT viewer hashes verified')
