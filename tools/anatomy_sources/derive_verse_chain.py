"""Derive every T1-L5 source label without voxel edits or mesh cleanup."""
from pathlib import Path
import sys,json,hashlib
import numpy as np,nibabel as nib,skimage
from skimage.measure import marching_cubes
from scipy import ndimage
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.anatomy_sources.check_atlantoaxial_topology import topology
root=Path('/tmp/primer-msk-sources/verse');case=root/'verse521';out=Path('output/msk-verse521/t1-l5');out.mkdir(parents=True,exist_ok=True)
acq=json.loads((root/'case-acquisition.json').read_text());sources={Path(x['file']).name:x['sha256'] for x in acq['files'] if x['member'].endswith('.nii.gz')}
for name,digest in sources.items():
 if hashlib.sha256((case/name).read_bytes()).hexdigest()!=digest:raise ValueError('Changed source')
ct=nib.load(case/'sub-verse521_dir-ax_ct.nii.gz');seg=nib.load(case/'sub-verse521_dir-ax_seg-vert_msk.nii.gz');assert ct.shape==seg.shape and np.allclose(ct.affine,seg.affine,rtol=0,atol=1e-6)
assert ct.header.get_xyzt_units()[0]=='mm' and seg.header.get_xyzt_units()[0] in ['unknown','mm']
mask=np.asanyarray(seg.dataobj);components=json.loads(Path('docs/msk-verse-source-review/all-level-components.json').read_text());assert components['source_mask_sha256']==sources['sub-verse521_dir-ax_seg-vert_msk.nii.gz'];rows=[]
for entry in components['levels']:
 value=entry['label'];name=entry['level'];start=np.array([a for a,b in entry['bbox']])-1;stop=np.array([b for a,b in entry['bbox']])+1
 assert not entry['touches_array_boundary'] and np.all(start>=0) and np.all(stop<=mask.shape)
 field=(mask[tuple(slice(a,b) for a,b in zip(start,stop))]==value).astype(np.uint8);assert int(field.sum())==entry['foreground_voxels']
 vertices,faces,_,_=marching_cubes(field,level=.5,step_size=1,allow_degenerate=True,method='lewiner')
 voxel=vertices.astype(np.float64)+start;world=nib.affines.apply_affine(ct.affine,voxel);centered=world-world.mean(0);tri=centered[faces];signed=float(np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])).sum()/6);flipped=signed<0
 if flipped:faces=faces[:,[0,2,1]]
 recovered=np.linalg.solve(ct.affine[:3,:3],(world-ct.affine[:3,3]).T).T;assert np.max(np.abs(recovered-voxel))<1e-6
 values=ndimage.map_coordinates(field.astype(float),(recovered-start).T,order=1,mode='constant',cval=0);residual=float(np.max(np.abs(values-.5)))
 fractions=vertices-np.floor(vertices);halves=np.isclose(fractions,.5,rtol=0,atol=1e-6);integers=np.isclose(fractions,0,rtol=0,atol=1e-6)
 half_count=halves.sum(axis=1);centers=half_count==3;edges=half_count==1
 assert np.all(halves|integers) and np.all(centers|edges)
 edge_residual=float(np.max(np.abs(values[edges]-.5))) if edges.any() else 0.;assert edge_residual<1e-6
 for index in np.flatnonzero(centers):
  corner=np.floor(vertices[index]).astype(int);cube=field[tuple(slice(x,x+2) for x in corner)]
  assert cube.shape==(2,2,2) and abs(float(cube.mean())-float(values[index]))<1e-6
 helper_values=sorted(set(map(float,values[centers])))
 check=topology(world.tolist(),faces.tolist());path=out/(name.lower()+'.npz');np.savez_compressed(path,vertices_world_mm=world,faces=faces.astype(np.uint32),vertices_voxel=voxel,affine=ct.affine)
 if name=='T8':
  previous=np.load('output/msk-verse521/t8-surface.npz')
  assert all(np.array_equal(previous[key],array) for key,array in [('vertices_world_mm',world),('faces',faces),('vertices_voxel',voxel),('affine',ct.affine)])
 rows.append({'level':name,'label':value,'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'vertices':len(world),'triangles':len(faces),'source_voxels':entry['foreground_voxels'],'source_connectivity':entry['connectivity'],'crop_start':start.tolist(),'crop_stop':stop.tolist(),'world_bounds_mm':[world.min(0).tolist(),world.max(0).tolist()],'world_winding_reversed':bool(flipped),'maximum_saved_vertex_isovalue_residual':residual,'edge_vertex_isovalue_residual':edge_residual,'cell_center_helper_vertices':int(centers.sum()),'helper_vertex_sampled_values':helper_values,'topology':check})
 print(name,len(faces),'components',check['edge_connected_components'],'boundary',check['boundary_edges'],'nonmanifold',check['nonmanifold_edges'],flush=True)
assert [x['label'] for x in rows]==list(range(8,25))
report={'case':'sub-verse521','source_files':sources,'affine':ct.affine.tolist(),'world_coordinates':'CT RAS millimetres; mask unit flag unknown, numerical selected affine matches CT','method':'Lewiner isovalue 0.5, step 1; no smoothing, decimation, filling or component removal','skimage_version':skimage.__version__,'levels':rows,'total_triangles':sum(x['triangles'] for x in rows),'clinical_approval':False,'runtime_promoted':False,'limits':['Lewiner cell-centre helper vertices can lie off the trilinear 0.5 boundary; their counts and sampled values are explicitly reported.','All source-labelled components retained; label connectivity is not a clinical interpretation.','Mesh fidelity to segmentation is not independent validation of anatomical boundaries.','No registration to or replacement within another atlas.']}
Path('docs/msk-verse-source-review/chain-surface-audit.json').write_text(json.dumps(report,indent=2)+'\n');(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
