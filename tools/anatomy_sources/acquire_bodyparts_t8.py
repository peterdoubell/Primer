import urllib.request,struct,zlib,json,hashlib
from pathlib import Path
url='https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/isa_BP3D_4.0_obj_99.zip';out=Path('/tmp/primer-msk-sources/bodyparts-t8');seen=[]
def fetch(rng):
 req=urllib.request.Request(url,headers={'Range':rng})
 with urllib.request.urlopen(req,timeout=30) as r:
  if r.status!=206:raise ValueError('Server did not honor bounded range')
  seen.append({'range':rng,'content_range':r.headers.get('Content-Range'),'etag':r.headers.get('ETag')})
  data=r.read()
 if len(data)>1000000:raise ValueError('Unexpected response size')
 return data
tail=fetch('bytes=-65557');pos=tail.rfind(b'PK\x05\x06');assert pos>=0
end=struct.unpack_from('<4s4H2LH',tail,pos);size,offset=end[5:7];assert size<1000000 and offset!=0xffffffff
cd=fetch(f'bytes={offset}-{offset+size-1}');cursor=0;target='isa_BP3D_4.0_obj_99/FJ3174.obj';entry=None
while cursor<len(cd):
 h=struct.unpack_from('<4s6H3L5H2L',cd,cursor);assert h[0]==b'PK\x01\x02';name=cd[cursor+46:cursor+46+h[10]].decode()
 if name==target:entry={'name':name,'method':h[4],'crc32':h[7],'compressed_size':h[8],'size':h[9],'offset':h[16]}
 cursor+=46+h[10]+h[11]+h[12]
assert entry
start=entry['offset'];header=fetch(f'bytes={start}-{start+29}');h=struct.unpack('<4s5H3L2H',header);assert h[0]==b'PK\x03\x04' and not h[2]&1
name=fetch(f'bytes={start+30}-{start+29+h[9]}').decode();assert name==target
start+=30+h[9]+h[10];compressed=fetch(f"bytes={start}-{start+entry['compressed_size']-1}");data=zlib.decompress(compressed,-15) if entry['method']==8 else compressed
assert len(data)==entry['size'] and zlib.crc32(data)==entry['crc32'];assert len({s['etag'] for s in seen})==1
(out/'FJ3174.obj').write_bytes(data);record={'archive_url':url,'member':entry,'requests':seen,'obj_sha256':hashlib.sha256(data).hexdigest(),'central_directory_sha256':hashlib.sha256(cd).hexdigest(),'license':'CC BY 4.0','license_evidence':'https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html','reduction':'Publisher-labelled 99% polygon reduction','runtime_promoted':False};(out/'acquisition.json').write_text(json.dumps(record,indent=2)+'\n');print(entry,'sha256',record['obj_sha256'])
