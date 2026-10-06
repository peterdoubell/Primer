#!/usr/bin/env python3
"""Acquire an original HiPaS archive member with exact ranges and ZIP CRC; never infer native geometry."""
import argparse
import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path
class RemoteArchive(io.RawIOBase):
    def __init__(self, url, size):
        self.url=url;self.size=size;self.position=0;self.etag=None;self.ranges=[]
    def seekable(self):return True
    def readable(self):return True
    def tell(self):return self.position
    def seek(self, offset, whence=0):
        self.position=offset if whence==0 else self.position+offset if whence==1 else self.size+offset
        if not 0<=self.position<=self.size:raise ValueError('Outside original archive')
        return self.position
    def read(self, size=-1):
        size=min(self.size-self.position,size if size>=0 else self.size-self.position)
        if not size:return b''
        start=self.position;end=start+size-1
        headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'}
        # A distinct query prevents intermediaries reusing a cached different range.
        url=self.url+('?range='+str(start)+'-'+str(end) if '?' not in self.url else '&range='+str(start)+'-'+str(end))
        with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=60) as response:
            if response.status!=206 or response.headers.get('Content-Range')!=f'bytes {start}-{end}/{self.size}':raise ValueError('Server did not return the exact original range')
            etag=response.headers.get('ETag')
            if self.etag is not None and self.etag!=etag:raise ValueError('Original archive entity changed')
            self.etag=etag;raw=response.read()
        if len(raw)!=size:raise ValueError('Original range length differs')
        self.ranges.append({'start':start,'end':end,'bytes':size,'sha256':hashlib.sha256(raw).hexdigest()})
        self.position=end+1;return raw
def acquire(root,case='001'):
    if not case.isdigit() or len(case)!=3:raise ValueError('Explicit three-digit source case required')
    metadata=json.loads((root/'zenodo-14879605.json').read_text());file=next(f for f in metadata['files'] if f['key']=='ct_scan.zip')
    remote=RemoteArchive(file['links']['self'],file['size'])
    with zipfile.ZipFile(remote) as archive:
        matches=[n for n in archive.namelist() if n.endswith('/'+case+'.npz') or n==case+'.npz']
        if len(matches)!=1:raise ValueError('Source case member absent or ambiguous')
        name=matches[0];info=archive.getinfo(name)
        raw=archive.read(name) # ZipFile independently enforces source member CRC32.
    fresh=json.loads(urllib.request.urlopen('https://zenodo.org/api/records/14879605',timeout=30).read())
    current=next(f for f in fresh['files'] if f['key']=='ct_scan.zip')
    if (current['checksum'],current['size'])!=(file['checksum'],file['size']):raise ValueError('Repository archive identity changed during acquisition')
    path=root/('case-'+case)/'ct'/ (case+'.npz');path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    proof={'record_id':14879605,'case':case,'archive_file':file['key'],'archive_url':file['links']['self'],'archive_bytes':file['size'],'publisher_whole_archive_checksum':file['checksum'],'whole_archive_checksum_verified':False,'member':name,'member_crc32':f'{info.CRC:08x}','member_bytes':len(raw),'member_sha256':hashlib.sha256(raw).hexdigest(),'member_crc32_verified':True,'etag':remote.etag,'archive_entity_tag_available':remote.etag is not None,'ranges':remote.ranges,'original_acquisition_geometry_verified':False,'clinical_approval':False,'runtime_promoted':False,'commercial_reuse_approved':False}
    (root/('case-'+case+'-acquisition.json')).write_text(json.dumps(proof,indent=2)+'\n');print('Original complete CT case member acquired and CRC verified:',len(raw),'bytes')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-root',type=Path,required=True);parser.add_argument('--case',default='001');args=parser.parse_args();acquire(args.source_root,args.case)
