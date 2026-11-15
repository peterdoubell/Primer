"""Audit native LumASe arrays; retain numeric labels until semantics are verified."""
from pathlib import Path
import json,hashlib
import numpy as np
import nibabel as nib
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[2];DOC=ROOT/'docs/msk-vertebral-substructure-source-review'
def main():
 acquisition=json.loads((DOC/'lumase-case-acquisition.json').read_text());rows=[];images=[]
 for entry in acquisition['files']:
  path=ROOT/entry['local_path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'];image=nib.load(path);arr=np.asanyarray(image.dataobj);images.append(image)
  row={'file':entry['local_path'],'sha256':entry['sha256'],'shape':list(image.shape),'spacing_mm':[float(v) for v in image.header.get_zooms()],'affine':image.affine.tolist(),'axis_codes':list(nib.aff2axcodes(image.affine)),'dtype':str(arr.dtype),'finite':bool(np.isfinite(arr).all()),'range':[float(arr.min()),float(arr.max())],'header_description':bytes(image.header['descrip']).rstrip(b'\x00').decode(errors='replace'),'extensions':len(image.header.extensions)}
  assert row['finite']
  if '_seg' in path.name:
   assert np.equal(arr,np.floor(arr)).all();values,counts=np.unique(arr,return_counts=True);row['labels']=[]
   for value,count in zip(values,counts):
    part={'value':int(value),'voxels':int(count),'meaning':'unresolved_numeric_label' if value else 'background'}
    if value:
     mask=arr==value;points=np.argwhere(mask);lo=points.min(0);hi=points.max(0);part['voxel_bounds_inclusive']=[lo.tolist(),hi.tolist()];part['volume_mm3']=float(count*abs(np.linalg.det(image.affine[:3,:3])))
     part['array_boundary_voxels']=int(np.count_nonzero(np.any((points==0)|(points==np.array(arr.shape)-1),axis=1)))
     for connectivity in [1,3]:
      components,n=ndimage.label(mask,ndimage.generate_binary_structure(3,connectivity));sizes=np.bincount(components.ravel())[1:];part['components_'+str(6 if connectivity==1 else 26)]={'count':int(n),'sizes_descending':sorted(map(int,sizes),reverse=True)}
    row['labels'].append(part)
  rows.append(row)
 assert images[0].shape==images[1].shape and np.array_equal(images[0].affine,images[1].affine)
 report={'paired_grid_and_affine_equal':True,'label_meanings_verified':False,'source_arrays_modified':False,'boundary_contact_interpretation':'Array contact is a source-scope warning, not independent proof of anatomical truncation; do not invent caps or claim complete endpoints.','clinical_approval':False,'runtime_promoted':False,'files':rows};(DOC/'lumase-case-audit.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Native CT/label grid verified; seven numeric classes retained without anatomical names.')
 print([(p['value'],p['array_boundary_voxels'],p['components_26']['count']) for p in rows[1]['labels'] if p['value']])
if __name__=='__main__':main()
