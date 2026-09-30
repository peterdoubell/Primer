"""Preserve numeric LumASe label surfaces without inventing crop closure caps."""
from pathlib import Path
import json,hashlib
import numpy as np
import nibabel as nib
import skimage,scipy
from scipy import ndimage
from skimage.measure import marching_cubes
ROOT=Path(__file__).resolve().parents[2];DOC=ROOT/'docs/msk-vertebral-substructure-source-review';OUT=ROOT/'output/msk-lumase-l3'
def main():
 acquisition=json.loads((DOC/'lumase-case-acquisition.json').read_text());entry=next(e for e in acquisition['files'] if '_seg' in e['member']);source=ROOT/entry['local_path'];assert hashlib.sha256(source.read_bytes()).hexdigest()==entry['sha256']
 image=nib.load(source);labels=np.asanyarray(image.dataobj);assert np.isfinite(labels).all() and np.equal(labels,np.floor(labels)).all() and set(np.unique(labels))==set(range(8))
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 for value in range(1,8):
  mask=np.asarray(labels==value,dtype=np.uint8)
  vertices,faces,_,_=marching_cubes(mask,level=.5,method='lewiner',allow_degenerate=True)
  sampled=ndimage.map_coordinates(mask.astype(np.float32),vertices.T,order=1,prefilter=False,mode='nearest')
  assert np.isfinite(sampled).all()
  world=nib.affines.apply_affine(image.affine,vertices.astype(np.float64));faces=faces.astype(np.uint32)
  edges=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]);edges.sort(axis=1);unique,counts=np.unique(edges,axis=0,return_counts=True);boundary=unique[counts==1]
  edge_points=vertices[boundary.ravel()];on_crop=np.any(np.isclose(edge_points,0)|(np.isclose(edge_points,np.array(mask.shape)-1)),axis=1)
  assert not len(edge_points) or on_crop.all()
  triangles=world[faces];area2=np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1)
  path=OUT/f'source-label-{value}.npz';np.savez_compressed(path,vertices_voxel=vertices,vertices_world_mm=world,faces=faces,source_label=np.array(value),affine=image.affine)
  restored=np.load(path);assert np.array_equal(restored['vertices_voxel'],vertices) and np.array_equal(restored['vertices_world_mm'],world) and np.array_equal(restored['faces'],faces)
  row={'numeric_label':value,'trilinear_mask_at_vertices':{'minimum':float(sampled.min()),'maximum':float(sampled.max()),'max_deviation_from_0_5':float(np.max(np.abs(sampled-.5))),'vertices_off_0_5_above_1e_6':int(np.count_nonzero(np.abs(sampled-.5)>1e-6))},'meaning':'unverified','source_voxels':int(mask.sum()),'vertices':len(vertices),'triangles':len(faces),'boundary_edges':len(boundary),'all_boundary_vertices_on_original_crop':bool(not len(edge_points) or on_crop.all()),'nonmanifold_edges':int(np.count_nonzero(counts>2)),'zero_area_triangles':int(np.count_nonzero(area2==0)),'surface_area_mm2':float(area2.sum()/2),'world_bounds_mm':[world.min(0).tolist(),world.max(0).tolist()],'file':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()};rows.append(row);print('Label',value,len(faces),'triangles,',len(boundary),'source-crop boundary edges',flush=True)
 report={'software_versions':{'numpy':np.__version__,'nibabel':nib.__version__,'scikit_image':skimage.__version__,'scipy':scipy.__version__},'limitations':['Anatomical meanings of numeric labels 1–7 are unverified.','Four label surfaces retain open source-crop edges; anatomical endpoint completeness is unproved.','Marching-cubes interpolation is a derived voxel-scale approximation, not a measured biological boundary.','Basic edge/area checks do not prove freedom from self-intersections or clinical fidelity.'],'source_mask_sha256':entry['sha256'],'source_ct_sha256':next(e['sha256'] for e in acquisition['files'] if '_seg' not in e['member']),'coordinate_system':'Original NIfTI affine to RAS millimetres; no registration to another case.','method':'Lewiner marching cubes at 0.5 on each original numeric binary label. All generated positions/topology retained, including zero-area faces if present.','zero_padding':False,'caps_added':False,'smoothing':False,'decimation':False,'source_voxels_modified':False,'label_meanings_verified':False,'clinical_approval':False,'runtime_promoted':False,'parts':rows};(DOC/'lumase-numeric-surface-audit.json').write_text(json.dumps(report,indent=2)+'\n');(OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
