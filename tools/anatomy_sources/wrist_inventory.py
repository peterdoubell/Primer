#!/usr/bin/env python3
"""Inspect publicly licensed wrist-source candidates without publishing meshes."""
import hashlib,json,pathlib,urllib.request,zipfile
import numpy as np
import trimesh
ROOT=pathlib.Path('/tmp/primer-msk-sources/wrist-next')

def main():
 metadata=json.loads((ROOT/'zenodo-3728255.json').read_text());assert metadata['metadata']['license']['id']=='cc-by-4.0'
 record=metadata['files'][0];archive=ROOT/'forearm_model.zip'
 if not archive.exists():archive.write_bytes(urllib.request.urlopen(record['links']['self'],timeout=60).read())
 raw=archive.read_bytes();assert len(raw)==record['size'] and hashlib.md5(raw).hexdigest()==record['checksum'].split(':')[1]
 folder=ROOT/'hamze-2020';folder.mkdir(exist_ok=True)
 with zipfile.ZipFile(archive) as z:
  for i in z.infolist():
   target=(folder/i.filename).resolve();assert folder.resolve() in target.parents
   if i.is_dir():target.mkdir(parents=True,exist_ok=True);continue
   target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(i))
 rows=[]
 for p in sorted(folder.rglob('*')):
  if p.suffix not in ['.obj','.ply','.stl']:continue
  obj=trimesh.load(p,force='mesh',process=False)
  rows.append({'path':str(p),'name':p.stem,'kind':'landmark marker mesh' if 'landmarks' in p.parts else p.parent.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'vertices':len(obj.vertices),'triangles':len(obj.faces),'bounds':obj.bounds.tolist(),'finite':bool(np.isfinite(obj.vertices).all()),'watertight_raw':bool(obj.is_watertight),'header':p.read_bytes()[:180].decode('utf8','replace')})
 report={'dataset':'A 3D geometric model for the human forearm','doi':'10.5281/zenodo.3728255','license':'CC BY 4.0','license_evidence':str(ROOT/'zenodo-3728255.json'),'archive_sha256':hashlib.sha256(raw).hexdigest(),'published_md5_verified':True,'members':rows,'clinical_fidelity_approval':False}
 (ROOT/'hamze-inventory.json').write_text(json.dumps(report,indent=2)+'\n')
 for row in rows:print(row['kind'],row['name'],row['vertices'],row['triangles'],np.round(row['bounds'],2).tolist())

if __name__=='__main__':main()
