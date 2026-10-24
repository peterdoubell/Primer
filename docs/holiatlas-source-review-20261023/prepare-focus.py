from pathlib import Path
import json,zipfile,gzip,io
import numpy as np,nibabel as nib
from scipy import ndimage
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'reader-package';OUT.mkdir(exist_ok=True)
review=json.loads((ROOT/'holiatlas-label-review.json').read_text());boundary=json.loads((ROOT/'boundaries/boundary-proof.json').read_text());meshes={r['code']:r for r in boundary['rows']}
with zipfile.ZipFile(ROOT/'atlas_v1.0.zip') as z:raw=gzip.decompress(z.read('substructure_atlas.nii.gz'))
h=nib.Nifti1Header.from_fileobj(io.BytesIO(raw[:352]));data=np.frombuffer(raw,offset=int(h['vox_offset']),dtype=h.get_data_dtype()).reshape(h.get_data_shape(),order='F');boxes=ndimage.find_objects(data.astype(np.uint16));A=h.get_sform();result=[]
for row in review['classes']:
 if not row['code'] or row['name'].strip().lower()=='empty':continue
 item={**row,'sourceDefinedMeaning':('CSF territory around labelled folds; not a traced sulcal centre-line' if row['structure']=='CSF Hull' else 'Source-defined population-template categorical region; not independently validated patient anatomy')}
 if row['voxels']:
  box=boxes[row['code']-1];origin=np.array([s.start for s in box]);mask=data[box]==row['code'];components,count=ndimage.label(mask,np.ones((3,3,3),dtype=bool));componentBoxes=ndimage.find_objects(components);foci=[]
  for index,componentBox in enumerate(componentBoxes,1):
   points=np.argwhere(components[componentBox]==index)+np.array([s.start for s in componentBox]);mean=points.mean(0);focus=points[np.argmin(np.sum((points-mean)**2,axis=1))]+origin;assert data[tuple(focus)]==row['code'];world=A@np.r_[focus,1];foci.append({'id':index,'voxels':len(points),'focusSourceIJK':focus.tolist(),'focusSourceWorld':world[:3].tolist()})
  foci.sort(key=lambda f:(-f['voxels'],f['id']));assert sorted([f['voxels'] for f in foci],reverse=True)==meshes[row['code']]['componentsByConnectivity']['26'];item.update(components26=foci,focusSourceIJK=foci[0]['focusSourceIJK'],focusSourceWorld=foci[0]['focusSourceWorld'],mesh=meshes[row['code']]['mesh'],boundsSourceWorld=meshes[row['code']]['boundsSourceWorld'])
 else:item.update(components26=[],missingSourceLabel=True)
 result.append(item)
proof={'scope':'Source names and valid selected-voxel foci for all present classes and components; missing named labels remain unavailable','clinicalApproval':False,'sourceClasses':result,'presentClasses':sum(bool(r['voxels']) for r in result),'missingNamedClasses':sum(not r['voxels'] for r in result),'components26':sum(len(r['components26']) for r in result)};(OUT/'labels.json').write_text(json.dumps(proof,indent=2)+'\n');print({k:v for k,v in proof.items() if k!='sourceClasses'})
