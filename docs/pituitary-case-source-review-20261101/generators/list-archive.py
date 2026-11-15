from pathlib import Path
import json,urllib.request,zipfile,io,hashlib
D=Path.cwd()/'.research/pituitary-case-source-20261101';metadata=json.loads((D/'figshare-27894084-v1.json').read_bytes());f=next(f for f in metadata['files']if f['id']==50793273);size=f['size'];url=f['download_url'];reads=[]
class Source(io.RawIOBase):
 def __init__(self):self.position=0;self.etag=None
 def readable(self):return True
 def seekable(self):return True
 def tell(self):return self.position
 def seek(self,offset,whence=0):
  self.position=offset if whence==0 else self.position+offset if whence==1 else size+offset
  if not 0<=self.position<=size:raise ValueError('Archive seek escaped source')
  return self.position
 def read(self,n=-1):
  if n<0:n=size-self.position
  n=min(n,size-self.position)
  if not n:return b''
  if n>16*1024*1024:raise ValueError('Unexpected large archive metadata read')
  start=self.position;end=start+n-1;headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'}
  if self.etag:headers['If-Range']=self.etag
  request=urllib.request.Request(url,headers=headers)
  with urllib.request.urlopen(request,timeout=90)as response:
   assert response.status==206,(response.status,'Server did not honour bounded range')
   assert response.headers['Content-Range']==f'bytes {start}-{end}/{size}'
   etag=response.headers.get('ETag')
   if self.etag:assert etag==self.etag,'Archive object identity changed'
   else:self.etag=etag
   raw=response.read(n+1);assert len(raw)==n
  self.position+=n;reads.append({'start':start,'end':end,'bytes':n,'sha256':hashlib.sha256(raw).hexdigest(),'etag':etag});return raw
source=Source()
with zipfile.ZipFile(source)as archive:rows=[{'name':i.filename,'compressedBytes':i.compress_size,'decodedBytes':i.file_size,'CRC32':format(i.CRC,'08x'),'compression':i.compress_type,'headerOffset':i.header_offset,'directory':i.is_dir()}for i in archive.infolist()]
(D/'archive-index.json').write_text(json.dumps({'sourceFileId':50793273,'sourceArchiveBytes':size,'sourceURL':url,'sourceETag':source.etag,'rangeReads':reads,'entries':rows,'fullArchiveDownloaded':False,'license':metadata['license']},indent=2)+'\n');print({'archiveBytes':size,'metadataBytesRead':sum(r['bytes']for r in reads),'entries':len(rows),'etag':source.etag});print(json.dumps(rows[:14],indent=2))
