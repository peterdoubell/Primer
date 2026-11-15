#!/usr/bin/env python3
"""Acquire the pinned licensed source archive with a full publisher checksum."""
import argparse
import hashlib
import json
from pathlib import Path
import time
from urllib.request import urlopen

URL='https://zenodo.org/api/records/10047263'


def acquire(root):
    root.mkdir(parents=True,exist_ok=True)
    metadata_raw=urlopen(URL,timeout=60).read();metadata=json.loads(metadata_raw)
    if metadata['id']!=10047263 or metadata['metadata']['license']['id']!='cc-by-4.0':raise ValueError('Pinned source or licence changed')
    entry=metadata['files'][0]
    if entry['key']!='Totalsegmentator_dataset_small_v201.zip':raise ValueError('Unexpected archive')
    expected_md5=entry['checksum'].removeprefix('md5:');path=root/entry['key'];temporary=path.with_name(path.name+'.part')
    def inspect(candidate):
        if not candidate.is_file() or candidate.stat().st_size!=entry['size']:return None
        md5=hashlib.md5();sha=hashlib.sha256()
        with candidate.open('rb') as stream:
            for chunk in iter(lambda:stream.read(8*1024*1024),b''):md5.update(chunk);sha.update(chunk)
        return (md5.hexdigest(),sha.hexdigest())
    checked=inspect(path)
    if checked is None or checked[0]!=expected_md5:
        md5=hashlib.md5();sha=hashlib.sha256();received=0;last=time.monotonic()
        with urlopen(entry['links']['self'],timeout=60) as response,temporary.open('wb') as out:
            for chunk in iter(lambda:response.read(4*1024*1024),b''):
                out.write(chunk);md5.update(chunk);sha.update(chunk);received+=len(chunk)
                if time.monotonic()-last>=20:
                    print('Downloaded bytes:',received,'of',entry['size'],flush=True);last=time.monotonic()
        if received!=entry['size'] or md5.hexdigest()!=expected_md5:raise ValueError('Publisher full archive size/checksum mismatch')
        temporary.replace(path);checked=(md5.hexdigest(),sha.hexdigest())
    (root/'metadata.json').write_bytes(metadata_raw)
    record={'source_metadata_url':URL,'source_metadata_sha256':hashlib.sha256(metadata_raw).hexdigest(),'record_id':metadata['id'],
            'doi':metadata['metadata'].get('doi'),'license':metadata['metadata']['license'],'creators':metadata['metadata']['creators'],
            'archive':entry['key'],'archive_size':entry['size'],'md5':checked[0],'sha256':checked[1],'publisher_checksum_passed':True,
            'source_values_changed':False,'clinical_approval':False,'runtime_promoted':False}
    (root/'acquisition.json').write_text(json.dumps(record,indent=2)+'\n');print('Full source archive verified:',path,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--destination',type=Path,required=True);args=parser.parse_args();acquire(args.destination)
