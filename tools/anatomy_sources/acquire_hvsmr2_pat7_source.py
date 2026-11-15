#!/usr/bin/env python3
"""Acquire actual bilateral-SVC pat7 from pinned source ZIP ranges with resumable chunks."""
import argparse,csv,hashlib,json,re,struct,urllib.request,zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
META_SHA='605e1e5f4f0028f2ad859d2e7cf10d583afd52a5d18611d366f39274835fd5f0'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def acquire(root):
    root.mkdir(parents=True,exist_ok=True);mp=root/'figshare-25226360-v2.json'
    if not mp.exists():mp.write_bytes(urllib.request.urlopen('https://api.figshare.com/v2/articles/25226360/versions/2',timeout=45).read())
    meta=mp.read_bytes()
    if sha(meta)!=META_SHA:raise ValueError('Reviewed figshare v2 metadata differs')
    m=json.loads(meta)
    if m['license']['name']!='CC BY 4.0':raise ValueError('Dataset grant differs')
    for f in m['files']:
        if f['name'].endswith('.csv'):
            path=root/f['name']
            if not path.exists():path.write_bytes(urllib.request.urlopen(f['download_url'],timeout=45).read())
            if hashlib.md5(path.read_bytes()).hexdigest()!=f['computed_md5']:raise ValueError('Original CSV checksum differs')
    article_pins={'PMC11219801.1.json':'2685d3fcb484f9b63e47418414b06f08361099715325fd0222c08be1a1130a95','PMC11219801.1.xml':'7a01aae052a07f0af3ecb035252323a61485c299f616177d3f2f9b833c9a774c'}
    for name,pin in article_pins.items():
        path=root/name
        if not path.exists():path.write_bytes(urllib.request.urlopen('https://pmc-oa-opendata.s3.amazonaws.com/PMC11219801.1/'+name,timeout=45).read())
        if sha(path.read_bytes())!=pin:raise ValueError('Pinned source article snapshot differs')
    archive=next(f for f in m['files'] if f['name']=='orig.zip');total=archive['size'];url=archive['download_url'];requests=[]
    def fetch(a,b):
        req=urllib.request.Request(url,headers={'Range':f'bytes={a}-{b}'})
        with urllib.request.urlopen(req,timeout=60) as response:
            if response.status!=206 or response.headers['Content-Range']!=f'bytes {a}-{b}/{total}':raise ValueError('Source range differs')
            data=response.read(b-a+2);record={'start':a,'end':b,'etag':response.headers.get('ETag')}
        if len(data)!=b-a+1:raise ValueError('Source range length differs')
        requests.append(record);return data,record
    clinical=list(csv.DictReader((root/'hvsmr_clinical.csv').read_text().splitlines()));case=next(r for r in clinical if r['Pat']=='7')
    if [k for k,v in case.items() if v=='X']!=['BilateralSVC']:raise ValueError('Actual source case selection differs')
    tail,_=fetch(total-65557,total-1);loc=tail.rfind(b'PK\x05\x06');h=struct.unpack_from('<4s4H2LH',tail,loc)
    if h[1:3]!=(0,0) or h[3]!=h[4] or h[4]!=362:raise ValueError('Original directory changed')
    central,_=fetch(h[6],h[6]+h[5]-1);pos=0;entries=[]
    while pos<len(central):
        f=struct.unpack_from('<4s6H3L5H2L',central,pos)
        if f[0]!=b'PK\x01\x02':raise ValueError('Invalid central directory')
        name=central[pos+46:pos+46+f[10]].decode('utf-8' if f[3]&0x800 else 'cp437')
        entries.append({'name':name,'method':f[4],'flags':f[3],'crc32':f[7],'compressed_bytes':f[8],'bytes':f[9],'offset':f[16]});pos+=46+f[10]+f[11]+f[12]
    selected=[r for r in entries if r['name'].startswith('orig/pat7_orig')]
    if len(selected)!=3 or any(r['flags']&1 or r['method']!=8 for r in selected):raise ValueError('Selection/method changed')
    chunks=root/'pat7-range-chunks';chunks.mkdir(exist_ok=True);records=[]
    for record in selected:
        fn=record['name'].split('/')[-1];path=root/fn
        header,_=fetch(record['offset'],record['offset']+29);n,e=struct.unpack_from('<HH',header,26)
        if header[:4]!=b'PK\x03\x04' or fetch(record['offset']+30,record['offset']+29+n)[0].decode()!=record['name']:raise ValueError('Original member identity differs')
        start=record['offset']+30+n+e;size=record['compressed_bytes'];parts=[(a,min(a+2*1024*1024-1,start+size-1)) for a in range(start,start+size,2*1024*1024)]
        def part(bounds):
            a,b=bounds;p=chunks/f'{a}-{b}.bin';proof=p.with_suffix('.json')
            if p.exists() and proof.exists():
                r=json.loads(proof.read_text());raw=p.read_bytes()
                if len(raw)!=b-a+1 or sha(raw)!=r['sha256'] or r['start']!=a or r['end']!=b:raise ValueError('Cached source chunk differs')
                requests.append({k:r[k] for k in ['start','end','etag']});return raw
            raw,r=fetch(a,b);p.write_bytes(raw);r['sha256']=sha(raw);proof.write_text(json.dumps(r));print('Verified source chunk',a,b,flush=True);return raw
        if not path.exists():
            with ThreadPoolExecutor(max_workers=4) as pool:encoded=b''.join(pool.map(part,parts))
            raw=zlib.decompress(encoded,-15)
            if len(raw)!=record['bytes'] or zlib.crc32(raw)!=record['crc32']:raise ValueError('Original member CRC differs')
            path.write_bytes(raw)
        raw=path.read_bytes()
        if len(raw)!=record['bytes'] or zlib.crc32(raw)!=record['crc32']:raise ValueError('Cached original payload differs')
        records.append({**record,'file':fn,'sha256':sha(raw)});print('Verified original member',fn,sha(raw),flush=True)
        if len({r['etag'] for r in requests})!=1:raise ValueError('Archive changed during reads')
        (root/'pat7-acquisition-progress.json').write_text(json.dumps({'records':records,'requests':requests,'full_archive_md5_verified':False},indent=2)+'\n')
    patient_ids=sorted(int(re.fullmatch(r'orig/pat(\d+)_orig\.nii\.gz',r['name']).group(1)) for r in entries if re.fullmatch(r'orig/pat(\d+)_orig\.nii\.gz',r['name']))
    proof={'patient_image_ids':patient_ids,'archive':{'url':url,'archive_bytes':total,'source_md5':archive['computed_md5'],'central_sha256':sha(central)},'records':records,'requests':requests,'full_archive_md5_verified':False}
    (root/'pat7-acquisition.json').write_text(json.dumps(proof,indent=2)+'\n');print('Three complete original pat7 volumes acquired; whole-archive MD5 not claimed.',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);acquire(p.parse_args().source_root)
