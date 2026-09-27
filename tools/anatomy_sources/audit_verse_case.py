"""Inspect original VerSe NIfTI geometry and mask coverage; no resampling."""
from pathlib import Path
import json,hashlib
import nibabel as nib
import numpy as np
from scipy import ndimage
ROOT=Path('/tmp/primer-msk-sources/verse');CASE=ROOT/'verse521';OUT=Path('docs/msk-verse-source-review')
acquisition=json.loads((ROOT/'case-acquisition.json').read_text())
for f in acquisition['files']:
 if hashlib.sha256(Path(f['file']).read_bytes()).hexdigest()!=f['sha256']:raise ValueError('Acquired file changed')
ct=nib.load(CASE/'sub-verse521_dir-ax_ct.nii.gz');seg=nib.load(CASE/'sub-verse521_dir-ax_seg-vert_msk.nii.gz');centroids=json.loads((CASE/'sub-verse521_dir-ax_seg-subreg_ctd.json').read_text())
if ct.shape!=seg.shape or not np.allclose(ct.affine,seg.affine,rtol=0,atol=1e-6):raise ValueError('CT/mask grid mismatch')
if tuple(centroids[0]['direction'])!=nib.aff2axcodes(ct.affine):raise ValueError('Centroid orientation needs explicit transformation')
mask=np.asanyarray(seg.dataobj);counts=np.zeros(256,dtype=np.int64)
for start in range(0,mask.shape[2],16):counts+=np.bincount(mask[:,:,start:start+16].ravel(),minlength=256)
labels=[int(x) for x in np.flatnonzero(counts) if x];boxes=ndimage.find_objects(mask,max_label=255);rows=[]
for label in labels:
 box=boxes[label-1];c=next(x for x in centroids[1:] if x['label']==label);point=[float(c[k]) for k in ['X','Y','Z']];voxel=tuple(int(round(x)) for x in point)
 rows.append({'label':label,'voxel_count':int(counts[label]),'bounding_box_voxels':[[s.start,s.stop] for s in box],'touches_volume_boundary':[axis for axis,s in enumerate(box) if s.start==0 or s.stop==mask.shape[axis]],'centroid_voxels':point,'centroid_inside_grid':all(0<=x<ct.shape[a] for a,x in enumerate(voxel)),'mask_at_rounded_centroid':int(mask[voxel])})
def describe(img):
 return {'shape':list(img.shape),'voxel_spacing_mm':[float(x) for x in img.header.get_zooms()],'axis_codes':list(nib.aff2axcodes(img.affine)),'dtype':str(img.get_data_dtype()),'selected_affine':img.affine.tolist(),'qform_code':int(img.header['qform_code']),'sform_code':int(img.header['sform_code']),'qform':img.get_qform().tolist(),'sform':img.get_sform().tolist()}
r={'subject':'sub-verse521','ct':describe(ct),'mask':describe(seg),'affines_match':True,'centroid_orientation_matches':True,'labels':rows,'source_acquisition_slice_thickness_mm':1.5,'stored_slice_spacing_mm':1.0,'limits':['Matching grids and centroids do not establish segmentation accuracy or normal anatomy.','Mask label boundary contact requires source-image review before claiming a complete vertebra.','No voxel resampling, mask repair, mesh generation or runtime promotion performed.'],'clinical_approval':False}
OUT.mkdir(exist_ok=True);(OUT/'case-geometry.json').write_text(json.dumps(r,indent=2)+'\n');print('labels',labels);print('boundary contacts',[(x['label'],x['touches_volume_boundary']) for x in rows if x['touches_volume_boundary']]);print('centroid mismatch',[(x['label'],x['mask_at_rounded_centroid']) for x in rows if x['label']!=x['mask_at_rounded_centroid']])
