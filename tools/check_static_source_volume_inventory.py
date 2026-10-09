#!/usr/bin/env python3
"""Bind CDN source volume identities to actual complete source viewer files."""
import argparse,gzip,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from primer.source_volume_integrity import CDN_VOLUME_ATLASES,CDN_VOLUME_FILES

def inventory():
    files={}
    for entries in json.loads((ROOT/'data/radiology/source-anatomy-references.json').read_text()).values():
        for entry in entries:
            if entry['atlas'] not in CDN_VOLUME_ATLASES:continue
            volume=entry.get('source_volume')
            if not volume or volume.get('src')!='/app/anatomy/'+entry['atlas']+'/'+CDN_VOLUME_FILES[entry['atlas']]:raise ValueError('Unregistered source volume')
            root=(ROOT/'web/anatomy'/entry['atlas']).resolve();path=(ROOT/'web'/volume['src'].removeprefix('/app/')).resolve()
            if not path.is_relative_to(root) or not path.is_file():raise ValueError('Source volume missing or outside atlas')
            raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest();script=hashlib.sha256(path.with_suffix('.js').read_bytes()).hexdigest()
            if sha!=volume['sha256'] or script!=volume['script_sha256']:raise ValueError('Reviewed source volume/script changed')
            row={'sha256':sha,'script_sha256':script,'bytes':len(raw)}
            if volume.get('data_files'):
                for item in volume['data_files']:
                    if item.get('file') not in {'source-image.bin.gz','source-label.bin.gz'}:raise ValueError('Unregistered source array filename')
                    encoded=(root/item['file']).read_bytes();decoded=gzip.decompress(encoded)
                    if (len(encoded)!=item['compressed_bytes'] or hashlib.sha256(encoded).hexdigest()!=item['compressed_sha256']
                            or len(decoded)!=item['bytes'] or hashlib.sha256(decoded).hexdigest()!=item['raw_source_voxel_sha256']):
                        raise ValueError('Complete original array differs')
                row['data_files']=volume['data_files']
            if volume['src'] in files and files[volume['src']]!=row:raise ValueError('Conflicting source volume identity')
            files[volume['src']]=row
    return {'schema_version':1,'scope':'Configured CDN source CT viewers; release integrity only, not anatomical approval.','files':dict(sorted(files.items()))}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');args=p.parse_args();data=inventory();path=ROOT/'data/radiology/radiology-static-source-volumes.json'
    if args.write:path.write_text(json.dumps(data,indent=2)+'\n')
    elif json.loads(path.read_text())!=data:raise SystemExit('Static source volume inventory differs from reviewed source bytes')
    print(len(data['files']),'complete source volume viewer hashes verified')
