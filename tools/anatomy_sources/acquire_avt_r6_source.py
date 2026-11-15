#!/usr/bin/env python3
"""Retrieve pinned public ZIP members with exact range, CRC and SHA controls; no full-archive claim."""
import argparse
import hashlib
import json
import struct
import urllib.request
import zlib
from tools.anatomy_sources.review_avt_r6_source import OUTPUT,META_SHA,CT_SHA,MASK_SHA
from pathlib import Path


def acquire(root):
    metadata=(OUTPUT/'source-metadata.json').read_bytes()
    if hashlib.sha256(metadata).hexdigest()!=META_SHA:raise ValueError('Reviewed metadata differs')
    meta=json.loads(metadata);archive=next(f for f in meta['files'] if f['name']=='Rider.zip')
    pinned=json.loads((OUTPUT/'original-range-acquisition.json').read_text());requests=[];root.mkdir(parents=True,exist_ok=True)
    allowed={'R6.nrrd':CT_SHA,'R6.seg.nrrd':MASK_SHA}
    if {e['file'] for e in pinned['records']}!=set(allowed) or len(pinned['records'])!=2:raise ValueError('Unreviewed source member set')
    for e in pinned['records']:
        if e['sha256']!=allowed[e['file']] or e['name']!='Rider/R6 (AAA)/'+e['file']:raise ValueError('Unreviewed source member identity')
    def ranged(start,end):
        if start<0 or end<start or end>=archive['size']:raise ValueError('Invalid original range')
        request=urllib.request.Request(archive['download_url'],headers={'Range':f'bytes={start}-{end}'})
        response=urllib.request.urlopen(request,timeout=60)
        if response.status!=206 or response.headers.get('Content-Range')!=f'bytes {start}-{end}/{archive["size"]}':
            response.close();raise ValueError('Server did not preserve range identity')
        requests.append({'range':f'{start}-{end}','etag':response.headers.get('ETag'),'content_range':response.headers.get('Content-Range')})
        return response
    for entry in pinned['records']:
        target=root/entry['file']
        if target.exists():
            if hashlib.sha256(target.read_bytes()).hexdigest()!=entry['sha256']:raise ValueError('Existing member differs')
            continue
        offset=entry['header_offset']
        with ranged(offset,offset+29) as r:header=r.read()
        if header[:4]!=b'PK\x03\x04' or struct.unpack_from('<H',header,6)[0]&1:raise ValueError('Unreviewed ZIP header')
        name_length,extra_length=struct.unpack_from('<HH',header,26)
        with ranged(offset+30,offset+29+name_length) as r:name=r.read().decode()
        if name!=entry['name']:raise ValueError('ZIP member name differs')
        start=offset+30+name_length+extra_length
        with ranged(start,start+entry['compressed_size']-1) as r:
            if entry['method']==8:
                raw=zlib.decompress(r.read(),-15);target.write_bytes(raw)
            elif entry['method']==0:
                with target.open('wb') as output:
                    remaining=entry['compressed_size']
                    while remaining:
                        raw=r.read(min(1024*1024,remaining))
                        if not raw:raise ValueError('Truncated range')
                        output.write(raw);remaining-=len(raw)
            else:raise ValueError('Unreviewed member compression')
        raw=target.read_bytes()
        if len(raw)!=entry['size'] or zlib.crc32(raw)!=entry['crc32'] or hashlib.sha256(raw).hexdigest()!=entry['sha256']:raise ValueError('Original member byte verification differs')
    if requests and len({r['etag'] for r in requests})!=1:raise ValueError('Original archive identity changed across requests')
    (root/'figshare-metadata.json').write_bytes(metadata)
    (root/'r6-acquisition.json').write_bytes((OUTPUT/'original-range-acquisition.json').read_bytes())
    (root/'rider-license-rows.json').write_bytes((OUTPUT/'tcia-license-row-review.json').read_bytes())
    (root/'repeat-acquisition-review.json').write_text(json.dumps({'records':pinned['records'],'new_requests':requests,
        'existing_pinned_files_verified':not requests,'archive_full_md5_verified':False,'runtime_promoted':False},indent=2)+'\n')
    print('Pinned R6 CT/mask members verified; entire archive MD5 remains unverified.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    acquire(p.parse_args().source_root)
