#!/usr/bin/env python3
"""Acquire complete original SC-HF-I-01 members from the author's Part3 ZIP with checked ranges/CRCs."""
import argparse,hashlib,json,re,struct,urllib.request,zlib
from pathlib import Path
URL='https://sourceforge.net/projects/cardiac-mr/files/Sunnybrook%20Cardiac%20MR%20Database%20DICOMPart3.zip/download'
TOTAL=208345315
PUBLISHER_SHA='b0a54336316e09e801e8175edaa01a75c108bcfb87be7cacc16d5d044e01bd38'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def acquire(root):
    root.mkdir(parents=True,exist_ok=True);requests=[];etag=None;resolved_url=URL
    def fetch(start,end):
        nonlocal etag,resolved_url
        with urllib.request.urlopen(urllib.request.Request(resolved_url,headers={'Range':f'bytes={start}-{end}'}),timeout=60) as response:
            if response.status!=206 or response.headers.get('Content-Range')!=f'bytes {start}-{end}/{TOTAL}':raise ValueError('Original ZIP range/length differs')
            current=response.headers.get('ETag');resolved_url=response.url
            if current is None or etag is not None and current!=etag:raise ValueError('Original archive changed between reads')
            etag=current;raw=response.read(end-start+2)
        if len(raw)!=end-start+1:raise ValueError('Original range byte length differs')
        requests.append({'start':start,'end':end,'etag':etag,'sha256':sha(raw)});return raw
    tail=fetch(TOTAL-65557,TOTAL-1);offset=tail.rfind(b'PK\x05\x06')
    if offset<0:raise ValueError('Original archive directory missing')
    end=struct.unpack_from('<4s4H2LH',tail,offset)
    if end[1:3]!=(0,0) or end[3]!=end[4]:raise ValueError('Unsupported multi-volume original archive')
    central=fetch(end[6],end[6]+end[5]-1);entries=[];position=0
    while position<len(central):
        row=struct.unpack_from('<4s6H3L5H2L',central,position)
        if row[0]!=b'PK\x01\x02':raise ValueError('Original directory entry differs')
        name=central[position+46:position+46+row[10]].decode('utf-8' if row[3]&0x800 else 'cp437');entries.append({'member':name,'flags':row[3],'compression':row[4],'crc32':row[7],'compressed_bytes':row[8],'bytes':row[9],'offset':row[16]});position+=46+row[10]+row[11]+row[12]
    selected=[row for row in entries if '/SC-HF-I-01/' in row['member'] and row['member'].endswith('.dcm')]
    if len(selected)!=240 or any(row['flags']&1 or row['compression']!=8 for row in selected):raise ValueError('Original case member selection/method differs')
    if {Path(row['member']).name for row in selected}!={f'IM-0001-{i:04d}.dcm' for i in range(1,241)}:raise ValueError('Original complete case filenames differ')
    start=min(row['offset'] for row in selected);last=max(selected,key=lambda row:row['offset']);header=fetch(last['offset'],last['offset']+29);n,e=struct.unpack_from('<HH',header,26);stop=last['offset']+30+n+e+last['compressed_bytes']-1;block=fetch(start,stop);records=[]
    output=root/'original-case-SC-HF-I-01';output.mkdir(exist_ok=True)
    for row in sorted(selected,key=lambda row:row['member']):
        relative=row['offset']-start;header=block[relative:relative+30]
        if header[:4]!=b'PK\x03\x04':raise ValueError('Original member local header differs')
        n,e=struct.unpack_from('<HH',header,26);name=block[relative+30:relative+30+n].decode()
        if name!=row['member']:raise ValueError('Original local/member name differs')
        encoded=block[relative+30+n+e:relative+30+n+e+row['compressed_bytes']];raw=zlib.decompress(encoded,-15)
        if len(raw)!=row['bytes'] or zlib.crc32(raw)!=row['crc32']:raise ValueError('Original member CRC/length differs')
        filename=Path(name).name;(output/filename).write_bytes(raw);records.append({**row,'file':'original-case-SC-HF-I-01/'+filename,'sha256':sha(raw),'zip_crc_verified':True})
    proof={'author_archive_url':URL,'author_archive_bytes':TOTAL,'publisher_full_archive_sha256':PUBLISHER_SHA,'full_archive_sha256_verified':False,'complete_selected_original_case_members_acquired':True,'case':'SC-HF-I-01','archive_etag':etag,'central_directory_sha256':sha(central),'requests':requests,'members':records,'publisher_hash_source':URL,'partial_archive_acquisition_explicit':True}
    (root/'original-case-acquisition.json').write_text(json.dumps(proof,indent=2)+'\n');print('Acquired all 240 original case members, CRCs verified; full archive hash not claimed.',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);acquire(p.parse_args().source_root)
