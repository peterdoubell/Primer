from pathlib import Path
import io,json,urllib.request,zipfile,hashlib,zlib
D=Path.cwd()/'.research/pituitary-case-source-20261101';index=json.loads((D/'archive-index.json').read_bytes());metadata=json.loads((D/'figshare-27894084-v1.json').read_bytes());url=index['sourceURL'];size=index['sourceArchiveBytes'];etag=index['sourceETag'];reads=[]
class Source(io.RawIOBase):
 def __init__(self):self.position=0
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
  if n>16*1024*1024:raise ValueError('Unexpected large source range')
  start=self.position;end=start+n-1
  with urllib.request.urlopen(urllib.request.Request(url,headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity','If-Range':etag}),timeout=180)as response:
   assert response.status==206 and response.headers['Content-Range']==f'bytes {start}-{end}/{size}'and response.headers.get('ETag')==etag
   raw=response.read(n+1);assert len(raw)==n
  self.position+=n;reads.append({'start':start,'end':end,'bytes':n,'sha256':hashlib.sha256(raw).hexdigest()});return raw
out=D/'case-1';out.mkdir(exist_ok=True);records=[];source=Source()
with zipfile.ZipFile(source)as archive:
 for name in ['1_carotids_f.nii.gz','1_tumor_f.nii.gz','1_T1.nii.gz','1_T2_f.nii.gz']:
  info=archive.getinfo(name);expected=next(r for r in index['entries']if r['name']==name);assert info.header_offset==expected['headerOffset']and info.CRC==int(expected['CRC32'],16)and info.file_size==expected['decodedBytes'];target=out/name;hasher=hashlib.sha256();crc=0;total=0
  with archive.open(info)as member,target.open('wb')as f:
   while True:
    data=member.read(8*1024*1024)
    if not data:break
    f.write(data);total+=len(data);crc=zlib.crc32(data,crc);hasher.update(data)
  assert total==info.file_size and crc==info.CRC;records.append({'sourceFile':name,'bytes':total,'sha256':hasher.hexdigest(),'ZIPCRC32':format(crc,'08x'),'sourceArchiveHeaderOffset':info.header_offset});(D/'case-1-acquisition.partial.json').write_text(json.dumps({'completed':records,'ranges':reads},indent=2)+'\n');print({'file':name,'bytes':total,'ZIPCRCverified':True},flush=True)
proof={'sourceDatasetDOI':metadata['doi'],'sourceFileId':50793273,'sourceArchiveBytes':size,'sourceETag':etag,'sourceLicense':metadata['license'],'caseId':'1','selectionReason':'First numbered source case has both supplied contrasts and both original annotation files; not claimed representative or clinically validated by Primer','files':records,'rangeReads':reads,'totalBytesTransferred':sum(r['bytes']for r in reads),'fullArchiveDownloaded':False,'sourceFilesChanged':False,'sourceImagesAreAcquisitionNative':False,'sourceRegistrationOrPreprocessingUndone':False,'clinicalApproval':False};(D/'case-1-acquisition.json').write_text(json.dumps(proof,indent=2)+'\n');print({'allSourceFilesAcquired':True,'files':len(records),'bytesTransferred':proof['totalBytesTransferred']})
