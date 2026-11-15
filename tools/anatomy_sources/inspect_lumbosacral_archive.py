"""Inspect the public MRI ZIP directory with bounded, version-checked ranges."""
import io,json,urllib.request,zipfile
from pathlib import Path
root=Path('/tmp/primer-msk-sources/lumbosacral2024');record=json.load(urllib.request.urlopen('https://api.figshare.com/v2/articles/26403595'));f=record['files'][0]
class Remote(io.RawIOBase):
 def __init__(self):self.pos=0;self.etag=None;self.requests=[];self.total=0
 def seekable(self):return True
 def readable(self):return True
 def tell(self):return self.pos
 def seek(self,offset,whence=0):
  self.pos=offset if whence==0 else self.pos+offset if whence==1 else f['size']+offset
  if not 0<=self.pos<=f['size']:raise ValueError('Out-of-bounds seek')
  return self.pos
 def read(self,n=-1):
  n=f['size']-self.pos if n<0 else min(n,f['size']-self.pos)
  if not n:return b''
  if n>2_000_000 or self.total+n>5_000_000:raise ValueError('Metadata range budget exceeded')
  first,last=self.pos,self.pos+n-1
  with urllib.request.urlopen(urllib.request.Request(f['download_url'],headers={'Range':f'bytes={first}-{last}'}),timeout=30) as r:
   if r.status!=206 or r.headers.get('Content-Range')!=f"bytes {first}-{last}/{f['size']}":raise ValueError('Unexpected range response')
   etag=r.headers.get('ETag');assert etag
   if self.etag is not None and self.etag!=etag:raise ValueError('Archive version changed')
   self.etag=etag;raw=r.read(n+1)
  assert len(raw)==n;self.pos+=n;self.total+=n;self.requests.append([first,last]);return raw
remote=Remote()
with zipfile.ZipFile(remote) as z:
 entries=[{'name':i.filename,'size':i.file_size,'compressed_size':i.compress_size,'offset':i.header_offset,'crc32':i.CRC,'method':i.compress_type} for i in z.infolist()]
result={'url':f['download_url'],'archive_bytes':f['size'],'advertised_archive_md5':f['computed_md5'],'whole_archive_md5_verified':False,'etag':remote.etag,'metadata_range_bytes':remote.total,'requests':remote.requests,'entries':entries}
(root/'rawdata-inventory.json').write_text(json.dumps(result,indent=2)+'\n')
print('Members:',len(entries),'range bytes:',remote.total)
for e in entries:
 if 'sub-03' in e['name'] or e['name'].endswith('participants.tsv'):print(e)
