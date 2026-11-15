"""Acquire only selected small metadata members from the author-linked archive."""
from pathlib import Path
import json,urllib.request,struct,zlib,hashlib
ROOT=Path('/tmp/primer-msk-sources/verse')
inventory=json.loads((ROOT/'training-inventory.json').read_text());requests=[]
def fetch(first,last):
    if last-first>100000:raise ValueError('Metadata request too large')
    req=urllib.request.Request(inventory['url'],headers={'Range':f'bytes={first}-{last}'})
    with urllib.request.urlopen(req,timeout=30) as r:
        if r.status!=206 or r.headers.get('ETag')!=inventory['etag'] or r.headers.get('Content-Range')!=f"bytes {first}-{last}/{inventory['archive_bytes']}":raise ValueError('Archive range or version changed')
        data=r.read(last-first+2)
    if len(data)!=last-first+1:raise ValueError('Unexpected range length')
    requests.append([first,last]);return data
records=[]
for subject in ['verse506','verse521','verse542']:
    for entry in inventory['entries']:
        name=entry['name']
        if '__MACOSX' in name or '/sub-'+subject+'/' not in name or not name.endswith('.json'):continue
        if entry['size']>10000:raise ValueError('Unexpected metadata size')
        start=entry['offset'];header=struct.unpack('<4s5H3L2H',fetch(start,start+29));assert header[0]==b'PK\x03\x04' and not header[2]&1
        actual=fetch(start+30,start+29+header[9]).decode();assert actual==name
        start+=30+header[9]+header[10];raw=fetch(start,start+entry['compressed_size']-1)
        data=zlib.decompress(raw,-15) if entry['method']==8 else raw
        assert len(data)==entry['size'] and zlib.crc32(data)==entry['crc32']
        destination=ROOT/subject/Path(name).name;destination.parent.mkdir(exist_ok=True);destination.write_bytes(data)
        parsed=json.loads(data)
        records.append({'archive_member':name,'file':str(destination),'sha256':hashlib.sha256(data).hexdigest(),'crc32':entry['crc32'],'size':len(data)})
        if 'ctd' in name:print(subject,'labels',[x.get('label') for x in parsed if isinstance(x,dict) and 'label' in x])
        else:print(subject,'metadata',parsed)
(ROOT/'metadata-acquisition.json').write_text(json.dumps({'archive_url':inventory['url'],'etag':inventory['etag'],'requests':requests,'files':records,'runtime_promoted':False},indent=2)+'\n')
