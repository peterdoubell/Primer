"""Stream only one selected VerSe case; verify archive identity and ZIP CRC."""
from pathlib import Path
import urllib.request,struct,zlib,json,hashlib
ROOT=Path('/tmp/primer-msk-sources/verse');inventory=json.loads((ROOT/'training-inventory.json').read_text());subject='verse521';out=ROOT/subject;out.mkdir(exist_ok=True)
def response(first,last):
    r=urllib.request.urlopen(urllib.request.Request(inventory['url'],headers={'Range':f'bytes={first}-{last}'}),timeout=30)
    if r.status!=206 or r.headers.get('ETag')!=inventory['etag'] or r.headers.get('Content-Range')!=f"bytes {first}-{last}/{inventory['archive_bytes']}":
        r.close();raise ValueError('Archive identity/range mismatch')
    return r
records=[]
for entry in inventory['entries']:
    name=entry['name']
    if '__MACOSX' in name or '/sub-'+subject+'/' not in name or not name.endswith(('.nii.gz','_snp.png')):continue
    if entry['size']>300_000_000:raise ValueError('Selected member exceeds planned bound')
    start=entry['offset']
    with response(start,start+29) as r:h=struct.unpack('<4s5H3L2H',r.read())
    assert h[0]==b'PK\x03\x04' and not h[2]&1
    with response(start+30,start+29+h[9]) as r:assert r.read().decode()==name
    start+=30+h[9]+h[10];path=out/Path(name).name
    if path.exists():raise ValueError('Existing member requires explicit reuse verification; refusing overwrite')
    partial=path.with_name(path.name+'.partial');crc=0;count=0;digest=hashlib.sha256();compressed=0;decoder=zlib.decompressobj(-15) if entry['method']==8 else None
    if entry['method'] not in (0,8):raise ValueError('Unsupported ZIP method')
    with response(start,start+entry['compressed_size']-1) as r,partial.open('wb') as f:
        while True:
            chunk=r.read(1024*1024)
            if not chunk:break
            compressed+=len(chunk);data=decoder.decompress(chunk) if decoder else chunk
            count+=len(data)
            if count>entry['size']:raise ValueError('Expanded size exceeds declaration')
            f.write(data);crc=zlib.crc32(data,crc);digest.update(data)
        data=decoder.flush() if decoder else b'';count+=len(data);f.write(data);crc=zlib.crc32(data,crc);digest.update(data)
    if compressed!=entry['compressed_size'] or count!=entry['size'] or crc!=entry['crc32'] or (decoder and not decoder.eof):raise ValueError('ZIP integrity check failed')
    partial.rename(path);records.append({'member':name,'size':count,'compressed_bytes':compressed,'sha256':digest.hexdigest(),'crc32':crc,'file':str(path)});print(path.name,count,'CRC verified',flush=True)
(ROOT/'case-acquisition.json').write_text(json.dumps({'archive_url':inventory['url'],'etag':inventory['etag'],'files':records,'clinical_approval':False,'runtime_promoted':False},indent=2)+'\n')
