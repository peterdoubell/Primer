from pathlib import Path
import concurrent.futures,hashlib,json,re,urllib.request
R=Path.cwd();D=R/'.research/spl-additional-source-models-20261101';candidates=R/'.research/spl-additional-source-candidates-20261101/candidates.json';rows=json.loads(candidates.read_bytes())['rows'];commit='bec24db25aad5f7600e2df3becfb1f883e61ff56';prefix='https://raw.githubusercontent.com/mhalle/spl-brain-atlas/'+commit+'/slicer/models/';tasks=[];missing=[]
for row in rows:
 if not row['publisherLUTName']:continue
 if not row['originalSurfaceRecords']:missing.append(row['code'])
 for model in row['originalSurfaceRecords']:tasks.append((row['code'],model))
def acquire(task):
 code,model=task;url=model['source_url'];assert url.startswith(prefix)and model['tree_entry_present'];name=url.rsplit('/',1)[1];assert re.fullmatch(r'[A-Za-z0-9_.-]+\.vtk',name);path=D/'originals'/name
 if path.is_file():raw=path.read_bytes();downloaded=False
 else:
  with urllib.request.urlopen(url,timeout=90)as response:assert response.status==200;raw=response.read()
  downloaded=True
 assert len(raw)==model['source_bytes'];assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==model['source_blob_sha1']
 if downloaded:path.write_bytes(raw)
 return {'code':code,'file':str(path.relative_to(D)),'sourceURL':url,'sourcePath':model['source_path'],'bytes':len(raw),'gitBlobSHA1':model['source_blob_sha1'],'sha256':hashlib.sha256(raw).hexdigest(),'parentTransform':model['parent_transform'],'downloadedThisRun':downloaded,'allSourceBytesExact':True,'geometryReviewed':False,'clinicalApproval':False}
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:results=list(pool.map(acquire,tasks))
proof={'sourceRepository':'https://github.com/mhalle/spl-brain-atlas','sourceCommit':commit,'sourceCandidateFileSHA256':hashlib.sha256(candidates.read_bytes()).hexdigest(),'allOriginalBytesMatchPinnedGitTree':True,'surfaceFiles':len(results),'sourceCodesWithSurfaces':len({r['code']for r in results}),'namedRawCodesWithoutOriginalSurfaces':missing,'totalBytes':sum(r['bytes']for r in results),'rows':results,'clinicalApproval':False,'anatomicalVisibilityVerified':False};(D/'acquisition.json').write_text(json.dumps(proof,indent=2)+'\n');print({k:proof[k]for k in ['surfaceFiles','sourceCodesWithSurfaces','namedRawCodesWithoutOriginalSurfaces','totalBytes','allOriginalBytesMatchPinnedGitTree']})
