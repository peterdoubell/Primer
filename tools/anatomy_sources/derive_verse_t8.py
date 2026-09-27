"""Derive an offline surface from original label 15; no mask/mesh repair."""
from pathlib import Path
import sys,json,hashlib
import numpy as np,nibabel as nib,skimage
from skimage.measure import marching_cubes
from scipy import ndimage
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.anatomy_sources.check_atlantoaxial_topology import topology
root=Path('/tmp/primer-msk-sources/verse');case=root/'verse521';out=root/'derived-t8';out.mkdir(exist_ok=True)
acq=json.loads((root/'case-acquisition.json').read_text())
for item in acq['files']:
 if item['member'].endswith('.nii.gz') and hashlib.sha256(Path(item['file']).read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Source changed')
ct=nib.load(case/'sub-verse521_dir-ax_ct.nii.gz');seg=nib.load(case/'sub-verse521_dir-ax_seg-vert_msk.nii.gz')
assert ct.shape==seg.shape and np.allclose(ct.affine,seg.affine,rtol=0,atol=1e-6)
assert ct.header.get_xyzt_units()[0]=='mm' and seg.header.get_xyzt_units()[0] in ['unknown','mm']
mask=np.asanyarray(seg.dataobj);points=np.argwhere(mask==15);start=points.min(0)-1;stop=points.max(0)+2
assert np.all(start>=0) and np.all(stop<=mask.shape)
field=(mask[tuple(slice(a,b) for a,b in zip(start,stop))]==15).astype(np.uint8)
vertices,faces,_,_=marching_cubes(field,level=.5,spacing=(1,1,1),step_size=1,allow_degenerate=True,method='lewiner')
voxel=vertices.astype(np.float64)+start;world=nib.affines.apply_affine(ct.affine,voxel)
centered=world-world.mean(0);tri=centered[faces];signed=float(np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])).sum()/6)
flipped=signed<0
if flipped:faces=faces[:,[0,2,1]]
values=ndimage.map_coordinates(field.astype(float),vertices.T,order=1,mode='constant',cval=0)
residual=float(np.max(np.abs(values-.5)));assert residual<1e-6
inverse=nib.affines.apply_affine(np.linalg.inv(ct.affine),world);assert np.max(np.abs(inverse-voxel))<1e-6
check=topology(world.tolist(),faces.tolist())
components={}
for connectivity in [1,3]:
 labels,count=ndimage.label(field,ndimage.generate_binary_structure(3,connectivity));sizes=np.bincount(labels.ravel())[1:];components[str(6 if connectivity==1 else 26)]={'count':int(count),'voxel_sizes':sorted(map(int,sizes),reverse=True)}
np.savez_compressed(out/'t8-surface.npz',vertices_world_mm=world,faces=faces.astype(np.uint32),vertices_voxel=voxel,affine=ct.affine)
result={'case':'sub-verse521','label':15,'source_files':{Path(x['file']).name:x['sha256'] for x in acq['files'] if x['member'].endswith('.nii.gz')},'ct_spatial_units':ct.header.get_xyzt_units()[0],'mask_spatial_units':seg.header.get_xyzt_units()[0],'world_coordinate_authority':'CT selected affine; mask selected affine matches numerically','crop_start':start.tolist(),'crop_stop':stop.tolist(),'method':'scikit-image Lewiner marching cubes at label isovalue 0.5; step 1; no smoothing, decimation, filling or component removal','skimage_version':skimage.__version__,'numpy_version':np.__version__,'vertices':len(world),'triangles':len(faces),'world_winding_reversed':bool(flipped),'maximum_vertex_isovalue_residual':residual,'mask_components':components,'mask_occupied_volume_mm3':float(field.sum()*abs(np.linalg.det(ct.affine[:3,:3]))),'topology':check,'surface_file':str(out/'t8-surface.npz'),'surface_sha256':hashlib.sha256((out/'t8-surface.npz').read_bytes()).hexdigest(),'clinical_approval':False,'runtime_promoted':False,'limits':['Isosurface geometry approximates the original voxel labels; it does not improve annotation accuracy or CT resolution.','Mesh topology and vertex-level isovalue agreement are not independent anatomical validation.','This case-specific surface is not registered to the Z-Anatomy spine.']}
Path('docs/msk-verse-source-review/t8-surface-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['vertices','triangles','ct_spatial_units','mask_spatial_units','mask_components','topology']},indent=2))
