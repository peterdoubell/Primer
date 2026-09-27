from pathlib import Path
import json,hashlib
import numpy as np,nibabel as nib
from scipy.ndimage import map_coordinates
report=json.load(open('docs/msk-verse-source-review/t8-surface-audit.json'))
for name,expected in report['source_files'].items():
 source=Path('/tmp/primer-msk-sources/verse/verse521')/name
 if hashlib.sha256(source.read_bytes()).hexdigest()!=expected:raise ValueError('Changed source file: '+name)
path=Path(report['preserved_surface_file']);assert hashlib.sha256(path.read_bytes()).hexdigest()==report['surface_sha256'];surface=np.load(path);world=surface['vertices_world_mm'];faces=surface['faces'];ct=nib.load('/tmp/primer-msk-sources/verse/verse521/sub-verse521_dir-ax_ct.nii.gz');seg=nib.load('/tmp/primer-msk-sources/verse/verse521/sub-verse521_dir-ax_seg-vert_msk.nii.gz')
# Solve the coordinate equations rather than use the generator's inverse helper.
voxel=np.linalg.solve(ct.affine[:3,:3],(world-ct.affine[:3,3]).T).T
assert np.max(np.abs(voxel-surface['vertices_voxel']))<1e-7
mask=np.asanyarray(seg.dataobj);start=np.maximum(0,np.floor(voxel.min(0)).astype(int)-1);stop=np.minimum(mask.shape,np.ceil(voxel.max(0)).astype(int)+2);field=(mask[tuple(slice(a,b) for a,b in zip(start,stop))]==15).astype(np.float32)
values=map_coordinates(field,(voxel-start).T,order=1,mode='constant',cval=0);residual=float(np.max(np.abs(values-.5)));assert residual<1e-6
# Independent divergence-theorem form, centered for numerical stability.
v=world-world.mean(0);tri=v[faces];area_vectors=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])/2;centers=tri.mean(1);volume=float(np.sum(centers*area_vectors)/3)
mask_volume=float(np.count_nonzero(mask==15)*abs(np.linalg.det(ct.affine[:3,:3])))
result={'surface_sha256':report['surface_sha256'],'vertices_checked':len(world),'triangles_checked':len(faces),'maximum_saved_vertex_mask_isovalue_residual':residual,'independent_mesh_volume_mm3':volume,'mask_occupied_volume_mm3':mask_volume,'relative_volume_difference':(volume-mask_volume)/mask_volume,'voxel_coordinate_roundtrip_maximum':float(np.max(np.abs(voxel-surface['vertices_voxel']))),'clinical_approval':False,'limits':['Volume agreement is mask-to-mesh consistency, not biological bone-volume accuracy.','Vertex isovalue checks do not establish every triangle interior or segmentation boundary is clinically correct.']}
Path('docs/msk-verse-source-review/t8-saved-surface-check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
