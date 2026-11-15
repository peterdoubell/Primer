#!/usr/bin/env python3
"""Acquire pinned, bounded upstream atlas files for research staging only."""
import concurrent.futures, hashlib, json, pathlib, subprocess, urllib.parse, urllib.request

CACHE=pathlib.Path('/tmp/primer-msk-sources')
ROOT=pathlib.Path(__file__).resolve().parents[2]
COMMIT='6c7f9016bd5899ac8edafd31b9900c151df42ed6'
UFBX_COMMIT='26a482ae66871d7de36eb722aa060bce95bce274'
FILES={
 'Joints100.fbx':('Resources/Models/FBX/Joints100.fbx',9804796,'f4ba7a910cdaef99e31530f368628780d9f06b5d77853f8b721f47f67137e823'),
 'SkeletalSystem100.fbx':('Resources/Models/FBX/SkeletalSystem100.fbx',41339660,'294a649765cd060a62a4095da52b9c8ef2d97769aa447e196448aa5f7d596dea'),
 'MuscularSystem100.fbx':('Resources/Models/FBX/MuscularSystem100.fbx',37343180,'4c19df534d5d84aabbce08604306aa0485b43e8a2483c72a95b569e1dfea2279'),
 'NervousSystem100.fbx':('Resources/Models/FBX/NervousSystem100.fbx',53887724,'3ea1aad64956cad27348a27b8fb50494b7cc307c6bc77bee0810ec2a67dff2b1'),
 'License.txt':('Resources/Models/License.txt',1514,'af62c06f620b9da20138e4c22a3f56565482dd058266540994ace97a4e24b693'),
 'LICENSE':('LICENSE',20559,'5e7dd512c01cfb822e3253f8f8df923103a64e269deb9bb5303f23b2376cad46'),
}

def fetch(url,path,expected_size=None,expected_sha=None):
 if not path.exists():
  req=urllib.request.Request(url,headers={'User-Agent':'Primer-anatomy-source-audit'})
  with urllib.request.urlopen(req,timeout=120) as stream:
   length=int(stream.headers.get('Content-Length','0'))
   if length>500_000_000:raise ValueError('Source exceeds authorized per-asset budget')
   payload=stream.read(500_000_001)
   if len(payload)>500_000_000:raise ValueError('Source exceeds authorized per-asset budget')
  path.write_bytes(payload)
 data=path.read_bytes();digest=hashlib.sha256(data).hexdigest()
 if expected_size is not None and len(data)!=expected_size:raise ValueError('Size mismatch: '+str(path))
 if expected_sha is not None and digest!=expected_sha:raise ValueError('Hash mismatch: '+str(path))
 return {'path':str(path),'url':url,'bytes':len(data),'sha256':digest}

def main():
 CACHE.mkdir(exist_ok=True)
 def atlas(item):
  name,(path,size,digest)=item
  url='https://raw.githubusercontent.com/LluisV/Z-Anatomy/'+COMMIT+'/'+urllib.parse.quote(path)
  return fetch(url,CACHE/('z-anatomy-'+name),size,digest)
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(atlas,FILES.items()))
 for name in ['ufbx.h','ufbx.c','LICENSE']:
  url='https://raw.githubusercontent.com/ufbx/ufbx/'+UFBX_COMMIT+'/'+name
  records.append(fetch(url,CACHE/('ufbx-LICENSE' if name=='LICENSE' else name)))
 (CACHE/'acquisition.json').write_text(json.dumps(records,indent=2)+'\n')
 subprocess.run(['clang','-O2','-I'+str(CACHE),str(ROOT/'tools/anatomy_sources/export_ufbx.c'),str(CACHE/'ufbx.c'),'-lm','-o',str(CACHE/'export_ufbx')],check=True)
 for category,source in [('bones','SkeletalSystem100'),('joints','Joints100'),('muscles','MuscularSystem100'),('nerves','NervousSystem100')]:
  with (CACHE/(category+'-world-inventory.json')).open('w') as output:
   subprocess.run([str(CACHE/'export_ufbx'),str(CACHE/('z-anatomy-'+source+'.fbx'))],stdout=output,check=True)
 print('Pinned source files and native world-coordinate inventories acquired in',CACHE)

if __name__=='__main__':main()
