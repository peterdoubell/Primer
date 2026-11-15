#!/usr/bin/env python3
"""Validate research-stage geometry and report defects without repairing sources."""
import hashlib,json,pathlib,struct
import numpy as np

CACHE=pathlib.Path('/tmp/primer-msk-sources')

def read(path):
 raw=pathlib.Path(path).read_bytes()
 assert raw[:4]==b'BP3D'
 nv,ni=struct.unpack_from('<II',raw,4)
 assert len(raw)==12+nv*24+ni*4
 p=np.frombuffer(raw,dtype='<f4',count=nv*3,offset=12).reshape(-1,3)
 n=np.frombuffer(raw,dtype='<f4',count=nv*3,offset=12+nv*12).reshape(-1,3)
 ix=np.frombuffer(raw,dtype='<u4',count=ni,offset=12+nv*24).reshape(-1,3)
 return raw,p,n,ix

def main():
 manifest=json.loads((CACHE/'staged/manifest.json').read_text())
 results=[]
 for item in manifest['parts'].values():
  assert not item['name'].endswith(('.i','.j','.ir','.or','.er','.il','.ol','.el'))
  for sub in [item,*item.get('material_submeshes',[])]:
   raw,p,n,ix=read(sub['file'])
   assert np.isfinite(p).all() and np.isfinite(n).all()
   assert ix.max()<len(p)
   assert len(ix)==sub['triangles']
   assert hashlib.sha256(raw).hexdigest()==sub['sha256']
   norm=np.linalg.norm(n,axis=1)
   assert ((norm<1e-6)|(abs(norm-1)<1e-5)).all()
   face=np.cross(p[ix[:,1]]-p[ix[:,0]],p[ix[:,2]]-p[ix[:,0]])
   area=np.linalg.norm(face,axis=1)
   nondegenerate=area>1e-10
   dot=np.sum(face*n[ix].sum(axis=1),axis=1)
   active=np.unique(ix)
   actual=np.array([p[active].min(axis=0),p[active].max(axis=0)])
   assert np.allclose(actual,np.array(sub['bounds']),atol=1e-4,rtol=1e-5)
   results.append({'name':item['name']+((' / '+sub['name']) if sub is not item else ''),'file':sub['file'],'triangles':len(ix),'degenerate_triangles':int((~nondegenerate).sum()),'face_normal_disagreement':int(((dot<0)&nondegenerate).sum()),'normal_count_zero':int((norm<1e-6).sum())})
 result={'files_checked':len(results),'objects':len(manifest['parts']),'finite_geometry':True,'valid_indices':True,'source_bounds_match':True,'results':results}
 (CACHE/'staged/geometry-validation.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='results'}))
 print('Source irregularities:',json.dumps([r for r in results if r['degenerate_triangles'] or r['face_normal_disagreement'] or r['normal_count_zero']][:20]))

if __name__=='__main__':main()
