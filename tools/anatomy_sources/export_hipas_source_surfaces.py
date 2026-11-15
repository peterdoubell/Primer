#!/usr/bin/env python3
"""Extract untouched source-mask isosurfaces in array-index coordinates; no clinical tissue or patient affine."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy import sparse, ndimage
import skimage
from scipy.sparse.csgraph import connected_components
from skimage.measure import marching_cubes

def sha(raw):return hashlib.sha256(raw).hexdigest()
def source_edge_check(volume,vertices):
    low=np.floor(vertices).astype(np.int64);high=np.ceil(vertices).astype(np.int64)
    fractional=np.count_nonzero(high-low,axis=1)
    if not np.all(vertices*2==np.round(vertices*2)) or not np.all(np.isin(fractional,[1,3])):
        raise ValueError('Unexpected binary-mask extraction sample positions')
    if (low<0).any() or (high>=np.asarray(volume.shape)).any():raise ValueError('Surface vertex leaves source grid')
    edge=fractional==1;a=volume[tuple(low[edge].T)];b=volume[tuple(high[edge].T)]
    if not np.all((a==0)&(b==1)|(a==1)&(b==0)):raise ValueError('Edge vertex does not cross an original binary boundary')
    interior=~edge
    corners=[volume[tuple(np.where(np.asarray(bits)[None,:],high[interior],low[interior]).T)] for bits in np.ndindex(2,2,2)]
    if np.any(interior):
        samples=np.asarray(corners)
        if not np.all((samples.min(axis=0)==0)&(samples.max(axis=0)==1)):raise ValueError('Ambiguity vertex not inside an active original cell')
    values=ndimage.map_coordinates(volume.astype(np.float32),vertices.T,order=1,prefilter=False)
    return {'original_edge_midpoint_vertices':int(edge.sum()),'active_cell_interior_ambiguity_vertices':int(interior.sum()),'maximum_vertex_trilinear_level_residual':float(np.max(np.abs(values-.5)))}

def topology(vertices,faces):
    edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1);unique,counts=np.unique(edges,axis=0,return_counts=True)
    graph=sparse.coo_matrix((np.ones(len(unique),dtype=np.uint8),(unique[:,0],unique[:,1])),shape=(len(vertices),len(vertices))).tocsr();n,labels=connected_components(graph,directed=False)
    areas=np.linalg.norm(np.cross(vertices[faces[:,1]]-vertices[faces[:,0]],vertices[faces[:,2]]-vertices[faces[:,0]]),axis=1)/2
    return {'connected_surface_components':int(n),'surface_component_vertex_counts_descending':sorted(np.bincount(labels).tolist(),reverse=True),'boundary_edges':int(np.count_nonzero(counts==1)),'nonmanifold_edges':int(np.count_nonzero(counts>2)),'nonmanifold_edge_source_vertices':unique[counts>2].astype(int).tolist(),'nonmanifold_edge_incident_face_counts':counts[counts>2].astype(int).tolist(),'nonmanifold_edge_index_positions':vertices[unique[counts>2]].tolist(),'zero_area_triangles':int(np.count_nonzero(areas==0))}
def export(root,out,review):
    out.mkdir(parents=True,exist_ok=True);rows=[]
    for tissue in ['artery','vein']:
        path=root/'case-001/annotation'/tissue/'001.npz'
        with np.load(path,allow_pickle=False) as source:
            if source.files!=['data']:raise ValueError('Unexpected original NPZ keys')
            volume=source['data']
        if not np.isin(volume,[0,1]).all():raise ValueError('Original binary mask differs')
        vertices,faces,_,_=marching_cubes(volume,level=.5,spacing=(1,1,1),step_size=1,allow_degenerate=False,method='lewiner')
        _,components26=ndimage.label(volume!=0,ndimage.generate_binary_structure(3,3));verified=source_edge_check(volume,vertices);centres=vertices[faces].mean(axis=1);field=ndimage.map_coordinates(volume.astype(np.float32),centres.T,order=1,prefilter=False);face_residual=np.abs(field-.5);vp=vertices.astype('<f8').tobytes();fp=faces.astype('<u4').tobytes();vfile=out/(tissue+'-vertices-f64.bin.gz');ffile=out/(tissue+'-triangles-u32.bin.gz');vfile.write_bytes(gzip.compress(vp,mtime=0));ffile.write_bytes(gzip.compress(fp,mtime=0))
        rows.append({'source_class':tissue,'source_mask_file_sha256':sha(path.read_bytes()),'original_shape':list(volume.shape),'source_foreground_voxels':int(np.count_nonzero(volume)),'source_mask_26_neighbour_components':int(components26),'vertices':len(vertices),'triangles':len(faces),'source_vertex_samples':verified,'all_face_barycentre_trilinear_level_residual':{'maximum':float(face_residual.max()),'mean':float(face_residual.mean()),'barycentres_checked':len(faces),'not_geometric_distance_or_anatomical_accuracy':True},'vertices_file':vfile.name,'vertices_gzip_sha256':sha(vfile.read_bytes()),'vertices_uncompressed_sha256':sha(vp),'triangles_file':ffile.name,'triangles_gzip_sha256':sha(ffile.read_bytes()),'triangles_uncompressed_sha256':sha(fp),'topology':topology(vertices,faces),'mesh_bounds_source_array_indices':[vertices.min(axis=0).tolist(),vertices.max(axis=0).tolist()]})
    proof={'case':'001','skimage_version':skimage.__version__,'extraction':'skimage Lewiner marching cubes, binary level0.5, unit index spacing, step1','coordinate_system':'source_array_indices_only','units':'voxel_index','patient_coordinate_transform':None,'source_spacing_applied':False,'source_sample_resampling_or_axis_permutation':False,'source_labels_repaired_or_overlaps_removed':False,'components_removed':False,'geometry_smoothing_decimation_or_fitting':False,'surface_is_native_lumen_wall_or_complete_tissue':False,'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False,'source_array_review_sha256':sha(review.read_bytes()),'surfaces':rows}
    (out/'source-surface-review.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps([{k:r[k] for k in ['source_class','vertices','triangles','topology']} for r in rows]))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--source-review',type=Path,required=True);args=p.parse_args();export(args.source_root,args.output,args.source_review)
