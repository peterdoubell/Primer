#!/usr/bin/env python3
"""Acquire a complete licensed OpenEar case, with resumable bytes and full publisher checksum."""
import argparse
import hashlib
import json
import urllib.request
import zipfile
from pathlib import Path


def hashes(path):
    md5=hashlib.md5();sha=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024*1024),b''):md5.update(block);sha.update(block)
    return md5.hexdigest(),sha.hexdigest()


def acquire(root,output,case):
    metadata_path=root/'zenodo-1473724.json';m=json.loads(metadata_path.read_text())
    if m['id']!=1473724 or m['metadata']['license']['id']!='cc-by-4.0':raise ValueError('Original dataset identity/grant differs')
    f=next(f for f in m['files'] if f['key']==case+'.zip');target=root/f['key'];partial=target.with_suffix('.zip.part')
    if not target.exists():
        offset=partial.stat().st_size if partial.exists() else 0
        if offset>f['size']:raise ValueError('Partial acquisition exceeds publisher size')
        if offset<f['size']:
            req=urllib.request.Request(f['links']['self'],headers={'Range':f'bytes={offset}-'} if offset else {})
            with urllib.request.urlopen(req,timeout=45) as response:
                if offset and (response.status!=206 or not response.headers.get('Content-Range','').startswith(f'bytes {offset}-')):
                    raise ValueError('Server did not honour exact resumed byte range; retained partial untouched')
                received=offset;last=received
                with partial.open('ab' if offset else 'wb') as stream:
                    while True:
                        block=response.read(4*1024*1024)
                        if not block:break
                        stream.write(block);received+=len(block)
                        if received>f['size']:raise ValueError('Publisher byte count exceeded')
                        if received-last>=128*1024*1024:print(f'{case}: {received}/{f["size"]} original bytes received',flush=True);last=received
        if partial.stat().st_size!=f['size']:raise ValueError('Complete publisher archive not yet acquired; retained partial')
        md5,sha=hashes(partial)
        if md5!=f['checksum'].split(':')[1]:raise ValueError('Publisher MD5 differs; partial retained for investigation')
        partial.rename(target)
    md5,sha=hashes(target)
    if target.stat().st_size!=f['size'] or md5!=f['checksum'].split(':')[1]:raise ValueError('Cached archive differs from publisher')
    members=[]
    with zipfile.ZipFile(target) as archive:
        for info in archive.infolist():
            if info.is_dir():continue
            # Read every original member to verify ZIP CRC without extracting paths.
            digest=hashlib.sha256()
            with archive.open(info) as stream:
                for block in iter(lambda:stream.read(4*1024*1024),b''):digest.update(block)
            members.append({'member':info.filename,'uncompressed_bytes':info.file_size,'CRC32':f'{info.CRC:08x}',
                            'ZIP_CRC_verified':True,'sha256':digest.hexdigest()})
    output.mkdir(parents=True,exist_ok=True)
    proof={'record_id':1473724,'case':case,'metadata_sha256':hashlib.sha256(metadata_path.read_bytes()).hexdigest(),
        'actual_dataset_license':m['metadata']['license'],'archive':{'file':f['key'],'bytes':target.stat().st_size,
            'publisher_checksum':f['checksum'],'publisher_MD5_verified':True,'sha256':sha},'members':members,
        'all_original_members_CRC_and_SHA_checked':True,'source_coordinates_registration_colour_and_anatomy_independently_reviewed':False,
        'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False}
    (output/(case+'-original-acquisition.json')).write_text(json.dumps(proof,indent=2)+'\n')
    print('Complete original archive and',len(members),'member CRCs checked',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--case',choices=['ALPHA','BETA','GAMMA','DELTA','EPSILON','ZETA','ETA','THETA'],required=True);a=p.parse_args();acquire(a.source_root,a.output,a.case)
