#!/usr/bin/env python3
"""Compare every original display-mesh vertex to explicit native labelled voxel-cell faces."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import zipfile


def cell_faces(mask,spacing):
    import numpy as np
    # Input array order K/J/I; output centers are native I/J/K physical-axis lengths.
    rows=[];axes=[];voxels=[];exterior=[]
    padded=np.pad(mask,1)
    for axis in range(3):
        array_axis=2-axis
        for sign in [-1,1]:
            slices=[slice(1,-1)]*3;slices[array_axis]=slice(0,-2) if sign<0 else slice(2,None)
            exposed=mask & ~padded[tuple(slices)]
            indices=np.argwhere(exposed)[:,::-1]
            centers=indices.astype(float);centers[:,axis]+=sign*.5
            rows.append(centers*spacing);axes.extend([axis]*len(indices));voxels.append(indices)
            exterior.extend((indices[:,axis]==(0 if sign<0 else mask.shape[array_axis]-1)).tolist())
    return np.concatenate(rows),np.asarray(axes),np.concatenate(voxels),np.asarray(exterior)


def closest_faces(points,centers,axes,spacing,prepared=None):
    import numpy as np
    from scipy.spatial import cKDTree
    if prepared is None:
        tree=cKDTree(centers);half=np.tile(spacing*.5,(len(centers),1));half[np.arange(len(centers)),axes]=0
        radius=float(np.linalg.norm(half,axis=1).max())
    else:tree,half,radius=prepared
    _,initial=tree.query(points)
    upper=np.linalg.norm(np.maximum(np.abs(points-centers[initial])-half[initial],0),axis=1)
    all_ids=tree.query_ball_point(points,upper+radius+1e-10)
    rows=[]
    for p,ids in zip(points,all_ids):
        ids=np.asarray(sorted(ids),dtype=np.int64)
        delta=np.maximum(np.abs(p-centers[ids])-half[ids],0);dist=np.linalg.norm(delta,axis=1);slot=int(np.argmin(dist));fid=int(ids[slot])
        nearest=np.minimum(np.maximum(p,centers[fid]-half[fid]),centers[fid]+half[fid])
        rows.append({'distance_mm':float(dist[slot]),'native_boundary_face_index':fid,'nearest_boundary_point_native_axis_mm':nearest.tolist(),
                     'conservatively_tested_faces':len(ids)})
    return rows,radius


def compare(archive,output):
    import numpy as np
    from tools.anatomy_sources.review_spl_wall_source import vtk,nrrd
    raw=(output/'independent-wall-source-review.json').read_bytes();review=json.loads(raw)
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=review['archive_sha256']:raise ValueError('Original source archive differs')
    summaries=[]
    with zipfile.ZipFile(archive) as z:
        fields,labels=nrrd(z.read('abdomen-2016-09/Data/seg.nrrd'))
        origin=np.asarray([float(v) for v in fields['space origin'].strip('()').split(',')])
        directions=np.asarray([[float(v) for v in s.split(',')] for s in re.findall(r'\(([^)]+)\)',fields['space directions'])]).T
        spacing=np.linalg.norm(directions,axis=0);basis=directions/spacing
        if not np.allclose(basis.T@basis,np.eye(3),rtol=0,atol=1e-12):raise ValueError('Oblique/sheared cell boundary requires separate review')
        for model in review['records']:
            source=z.read(model['source_member'])
            if hashlib.sha256(source).hexdigest()!=model['source_vtk_sha256']:raise ValueError('Original mesh differs')
            points,*_=vtk(source);ijk=np.linalg.solve(directions,(points.astype(float)*[-1,-1,1]-origin).T).T
            centers,axes,voxels,exterior=cell_faces(labels==model['label_value'],spacing)
            rows,radius=closest_faces(ijk*spacing,centers,axes,spacing)
            for i,row in enumerate(rows):row['source_vertex_index']=i
            distances=np.asarray([r['distance_mm'] for r in rows])
            proof={'label_value':model['label_value'],'source_name':model['source_name'],'source_vtk_sha256':model['source_vtk_sha256'],
                'source_review_sha256':hashlib.sha256(raw).hexdigest(),'native_spacing':spacing.tolist(),
                'boundary_centers_native_axis_mm':centers.tolist(),'boundary_normal_axis':axes.tolist(),'boundary_source_voxel_ijk':voxels.tolist(),
                'boundary_is_at_delivered_grid_exterior':exterior.tolist(),'vertex_comparisons':rows,'maximum_face_half_diagonal_mm':radius,
                'continuous_anatomical_surface_is_voxel_cell_union':False,'source_voxels_or_geometry_changed':False,'clinical_approval':False}
            payload=(json.dumps(proof,indent=2)+'\n').encode();packed=gzip.compress(payload,mtime=0);name='label-'+str(model['label_value'])+'-complete-vertex-boundary-comparison.json.gz';(output/name).write_bytes(packed)
            summaries.append({'label_value':model['label_value'],'source_name':model['source_name'],'file':name,
                'compressed_sha256':hashlib.sha256(packed).hexdigest(),'uncompressed_sha256':hashlib.sha256(payload).hexdigest(),
                'all_original_vertices_compared':len(rows)==model['position_records'],'vertices':len(rows),'boundary_faces':len(centers),
                'boundary_faces_at_grid_exterior':int(exterior.sum()),'maximum_vertex_distance_mm':float(distances.max()),
                'mean_vertex_distance_mm':float(distances.mean()),'distance_percentiles_mm':{str(q):float(np.percentile(distances,q)) for q in [50,90,95,99]},
                'vertex_distance_is_full_surface_hausdorff_distance':False,'anatomical_accuracy_or_acceptance_threshold_verified':False})
            print(model['source_name'],len(rows),'original vertices; max cell-boundary distance',distances.max(),flush=True)
    (output/'label-boundary-comparison-summary.json').write_text(json.dumps({'source_review_sha256':hashlib.sha256(raw).hexdigest(),'records':summaries,
        'source_geometry_changed':False,'clinical_approval':False,'runtime_promoted':False,
        'limits':['Native labelled voxel-cell unions are explicit discrete reference geometry, not independently established continuous tissue surfaces.',
            'Every source vertex is compared using a conservative face-center radius bound and exact rectangular-face distance. Triangle interiors and reverse surface distance remain separate requirements.',
            'Model smoothing, display decimation, voxel discretization and field-of-view clipping can contribute differences; no clinical error or acceptance threshold is inferred.',
            'No fitting, resampling, label relabelling, vertex movement, source-side splitting or missing-layer reconstruction is introduced.']},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();compare(a.archive,a.output)
