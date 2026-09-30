"""Read the public LumASe ZIP directory without downloading its 2.9 GB body."""
from pathlib import Path
import urllib.request,struct,json,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/msk-vertebral-substructure-source-review';CACHE=ROOT/'.research/anatomy-sources/lumase'
def fetch(url,first,last,total):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'Range':f'bytes={first}-{last}'}),timeout=40) as r:
  if r.status!=206 or r.headers.get('Content-Range')!=f'bytes {first}-{last}/{total}':raise ValueError('Archive range mismatch')
  data=r.read(last-first+2)
 if len(data)!=last-first+1:raise ValueError('Unexpected range size')
 return data
def main():
 info=json.loads((OUT/'lumase-archive-index-location.json').read_text());start=info['central_offset'];data=fetch(info['url'],start,start+info['central_bytes']-1,info['archive_bytes']);CACHE.mkdir(parents=True,exist_ok=True);(CACHE/'central-directory.bin').write_bytes(data)
 rows=[];pos=0
 while pos<len(data):
  h=struct.unpack_from('<4s6H3L5H2L',data,pos);assert h[0]==b'PK\x01\x02'
  name=data[pos+46:pos+46+h[10]].decode('utf-8' if h[3]&0x800 else 'cp437')
  rows.append({'name':name,'method':h[4],'flags':h[3],'crc32':h[7],'compressed_size':h[8],'size':h[9],'offset':h[16]});pos+=46+h[10]+h[11]+h[12]
 assert len(rows)==info['entries'];report={**info,'central_sha256':hashlib.sha256(data).hexdigest(),'entries':rows,'clinical_approval':False,'runtime_promoted':False};(OUT/'lumase-archive-inventory.json').write_text(json.dumps(report,indent=2)+'\n');print(len(rows),'entries');print('\n'.join(r['name'] for r in rows[:25]))
if __name__=='__main__':main()
