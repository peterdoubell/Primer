"""Inventory all T1-L5 foreground components without modifying labels."""
from pathlib import Path
import json,hashlib
import nibabel as nib
import numpy as np
from scipy import ndimage
root=Path('/tmp/primer-msk-sources/verse');path=root/'verse521/sub-verse521_dir-ax_seg-vert_msk.nii.gz';acq=json.loads((root/'case-acquisition.json').read_text());record=next(x for x in acq['files'] if x['file']==str(path));assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256']
img=nib.load(path);mask=np.asanyarray(img.dataobj);boxes=ndimage.find_objects(mask,max_label=24);rows=[]
for value in range(8,25):
 box=boxes[value-1]
 if box is None:raise ValueError('Missing required source level')
 field=mask[box]==value;checks={}
 for conn in [1,3]:
  components,count=ndimage.label(field,ndimage.generate_binary_structure(3,conn));sizes=np.bincount(components.ravel())[1:];checks[str(6 if conn==1 else 26)]={'components':int(count),'sizes_voxels':sorted(map(int,sizes),reverse=True)}
 rows.append({'label':value,'level':('T'+str(value-7)) if value<20 else ('L'+str(value-19)),'foreground_voxels':int(field.sum()),'bbox':[[s.start,s.stop] for s in box],'touches_array_boundary':any(s.start==0 or s.stop==mask.shape[a] for a,s in enumerate(box)),'connectivity':checks})
result={'source_mask_sha256':record['sha256'],'shape':list(mask.shape),'levels':rows,'voxel_edits':False,'clinical_approval':False,'limits':'Component connectivity is a label property, not proof that an island is artifact, fracture fragment or correctly segmented anatomy.'}
Path('docs/msk-verse-source-review/all-level-components.json').write_text(json.dumps(result,indent=2)+'\n')
for r in rows:print(r['level'],r['connectivity']['6']['components'],r['connectivity']['26']['components'],r['foreground_voxels'])
