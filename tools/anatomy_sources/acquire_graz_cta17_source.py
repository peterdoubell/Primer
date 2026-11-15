#!/usr/bin/env python3
"""Acquire pinned public cta17 members; verify ranges/CRC/SHA without a full-archive MD5 claim."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import urllib.request
import zlib
from tools.anatomy_sources.review_graz_cta17_source import OUTPUT,HASHES

def acquire(root):
    metadata=(OUTPUT/'source-metadata.json').read_bytes()
    if hashlib.sha256(metadata).hexdigest()!=HASHES['figshare-metadata.json']:raise ValueError('Reviewed metadata differs')
    acquisition=(OUTPUT/'original-range-acquisition.json').read_bytes();record=json.loads(acquisition)
    expected={'cta17s.nrrd','raw-cta17.nrrd','truelumen17.seg.nrrd','falselumen17.seg.nrrd','mesh17.stl'}
    if {e['file'] for e in record['records']}!=expected or len(record['records'])!=5:raise ValueError('Unreviewed original selection')
    meta=json.loads(metadata);archives={f['download_url']:f for f in meta['files']};requests=[];root.mkdir(parents=True,exist_ok=True)
    for entry in record['records']:
        if entry['sha256']!=HASHES[entry['file']] or entry['archive_url'] not in archives:raise ValueError('Unreviewed original member identity')
        path=root/entry['file'];archive=archives[entry['archive_url']]
        def ranged(start,end):
            if start<0 or end<start or end>=archive['size']:raise ValueError('Invalid public range')
            request=urllib.request.Request(entry['archive_url'],headers={'Range':f'bytes={start}-{end}'})
            with urllib.request.urlopen(request,timeout=60) as r:
                if r.status!=206 or r.headers.get('Content-Range')!=f'bytes {start}-{end}/{archive["size"]}':raise ValueError('Range identity differs')
                raw=r.read(end-start+2);requests.append({'archive_url':entry['archive_url'],'range':f'{start}-{end}','etag':r.headers.get('ETag')})
            if len(raw)!=end-start+1:raise ValueError('Range length differs')
            return raw
        if not path.exists():
            offset=entry['offset'];h=ranged(offset,offset+29)
            if h[:4]!=b'PK\x03\x04' or struct.unpack_from('<H',h,6)[0]&1:raise ValueError('Original ZIP header differs')
            n,extra=struct.unpack_from('<HH',h,26)
            if ranged(offset+30,offset+29+n).decode()!=entry['name']:raise ValueError('Original member name differs')
            start=offset+30+n+extra;encoded=ranged(start,start+entry['compressed_bytes']-1)
            raw=zlib.decompress(encoded,-15) if entry['method']==8 else encoded
            if len(raw)!=entry['bytes'] or zlib.crc32(raw)!=entry['crc32'] or hashlib.sha256(raw).hexdigest()!=entry['sha256']:raise ValueError('Original payload differs')
            path.write_bytes(raw)
        raw=path.read_bytes()
        if len(raw)!=entry['bytes'] or zlib.crc32(raw)!=entry['crc32'] or hashlib.sha256(raw).hexdigest()!=entry['sha256']:raise ValueError('Cached original differs')
    for url in {r['archive_url'] for r in requests}:
        if len({r['etag'] for r in requests if r['archive_url']==url})!=1:raise ValueError('Original archive changed during reads')
    (root/'figshare-metadata.json').write_bytes(metadata);(root/'cta17-acquisition.json').write_bytes(acquisition)
    for name in ['PMC11156948.1.json','PMC11156948.1.xml']:
        expected=HASHES.get(name)
        if not (root/name).exists():
            with urllib.request.urlopen('https://pmc-oa-opendata.s3.amazonaws.com/PMC11156948.1/'+name,timeout=60) as r:raw=r.read()
            if expected and hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Pinned source article differs')
            (root/name).write_bytes(raw)
    (root/'repeat-acquisition-review.json').write_text(json.dumps({'new_requests':requests,'original_files_verified':True,
        'full_archive_md5_verified':False,'clinical_approval':False},indent=2)+'\n')
    print('Five pinned cta17 source members verified; full archive MD5 remains unverified.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    acquire(p.parse_args().source_root)
