"""Reproduce a failed T1 surface check in its single original source cell."""
from pathlib import Path
import json,hashlib
import numpy as np,nibabel as nib,skimage
from skimage.measure import marching_cubes
from scipy.ndimage import map_coordinates
path=Path('/tmp/primer-msk-sources/verse/verse521/sub-verse521_dir-ax_seg-vert_msk.nii.gz');inventory=json.load(open('docs/msk-verse-source-review/all-level-components.json'));assert hashlib.sha256(path.read_bytes()).hexdigest()==inventory['source_mask_sha256']
row=next(x for x in inventory['levels'] if x['label']==8);start=np.array([a for a,b in row['bbox']])-1;cell=start+np.array([91,65,30]);mask=np.asanyarray(nib.load(path).dataobj);cube=(mask[tuple(slice(int(x),int(x)+2) for x in cell)]==8).astype(np.uint8)
v,f,_,_=marching_cubes(cube,level=.5,method='lewiner');samples=map_coordinates(cube.astype(float),v.T,order=1,mode='nearest');bad=np.flatnonzero(np.abs(samples-.5)>1e-6)
result={'source_mask_sha256':inventory['source_mask_sha256'],'label':8,'source_cell_start_voxels':cell.tolist(),'binary_cell':cube.tolist(),'skimage_version':skimage.__version__,'vertices':v.tolist(),'sampled_values':samples.tolist(),'off_isovalue_vertex_indices':bad.tolist(),'maximum_isovalue_residual':float(np.max(np.abs(samples-.5))),'finding':'The discrepancy is reproduced within one source cell, independently of CT world-coordinate conversion.','geometry_promoted':False,'clinical_approval':False}
Path('docs/msk-verse-source-review/t1-isovalue-reproduction.json').write_text(json.dumps(result,indent=2)+'\n');print('cell',cell.tolist(),'off-isovalue',[(v[i].tolist(),float(samples[i])) for i in bad])
