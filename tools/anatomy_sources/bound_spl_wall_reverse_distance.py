#!/usr/bin/env python3
"""Bound every native labelled-cell boundary face against complete original display meshes."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import zipfile


def triangle_distances(point,triangles):
    import numpy as np
    a=triangles[:,0];u=triangles[:,1]-a;v=triangles[:,2]-a
    n=np.cross(u,v);square=np.einsum('ij,ij->i',n,n)
    if np.any(square<=0):raise ValueError('Degenerate reference triangle needs separate hold')
    signed=np.einsum('ij,ij->i',point-a,n)/square
    projected=point-signed[:,None]*n;w=projected-a
    d00=np.einsum('ij,ij->i',u,u);d01=np.einsum('ij,ij->i',u,v);d11=np.einsum('ij,ij->i',v,v)
    d20=np.einsum('ij,ij->i',w,u);d21=np.einsum('ij,ij->i',w,v)
    s=(d11*d20-d01*d21)/square;t=(d00*d21-d01*d20)/square
    inside=(s>=0)&(t>=0)&(s+t<=1)
    best=np.where(inside,np.linalg.norm(point-projected,axis=1),np.inf)
    for i,j in [(0,1),(1,2),(2,0)]:
        edge=triangles[:,j]-triangles[:,i];length=np.einsum('ij,ij->i',edge,edge)
        fraction=np.clip(np.einsum('ij,ij->i',point-triangles[:,i],edge)/length,0,1)
        candidate=triangles[:,i]+fraction[:,None]*edge
        best=np.minimum(best,np.linalg.norm(point-candidate,axis=1))
    return best


def mesh_oracle(triangles):
    import numpy as np
    from scipy.spatial import cKDTree
    centers=triangles.mean(1);tree=cKDTree(centers);radius=float(np.linalg.norm(triangles-centers[:,None],axis=2).max())
    def distance(points):
        _,initial=tree.query(points);upper=np.asarray([triangle_distances(p,triangles[[i]])[0] for p,i in zip(points,initial)])
        candidates=tree.query_ball_point(points,upper+radius+1e-10)
        return np.asarray([float(triangle_distances(p,triangles[np.asarray(ids,dtype=np.int64)]).min()) for p,ids in zip(points,candidates)])
    return distance,radius


def rectangle_triangles(centers,axes,spacing):
    import numpy as np
    result=[]
    for center,axis in zip(centers,axes):
        other=[a for a in range(3) if a!=axis];corners=[]
        for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]:
            p=center.copy();p[other[0]]+=a*spacing[other[0]]/2;p[other[1]]+=b*spacing[other[1]]/2;corners.append(p)
        result.extend([[corners[0],corners[1],corners[2]],[corners[0],corners[2],corners[3]]])
    return np.asarray(result)


def bound(archive,output,error):
    import numpy as np
    from tools.anatomy_sources.review_spl_wall_source import vtk,nrrd
    from tools.anatomy_sources.compare_spl_wall_label_boundaries import cell_faces
    from tools.anatomy_sources.bound_spl_wall_triangle_interiors import certify
    source_raw=(output/'independent-wall-source-review.json').read_bytes();source=json.loads(source_raw);forward=json.loads((output/'triangle-distance-bound-summary.json').read_text());rows=[]
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=source['archive_sha256']:raise ValueError('Original archive differs')
    if not forward['all_five_original_models_complete']:raise ValueError('Full forward evidence incomplete')
    with zipfile.ZipFile(archive) as z:
        fields,labels=nrrd(z.read('abdomen-2016-09/Data/seg.nrrd'));origin=np.asarray([float(v) for v in fields['space origin'].strip('()').split(',')])
        directions=np.asarray([[float(v) for v in s.split(',')] for s in re.findall(r'\(([^)]+)\)',fields['space directions'])]).T;spacing=np.linalg.norm(directions,axis=0)
        if not np.allclose((directions/spacing).T@(directions/spacing),np.eye(3),rtol=0,atol=1e-12):raise ValueError('Unreviewed native cell basis')
        for model in source['records']:
            raw=z.read(model['source_member'])
            if hashlib.sha256(raw).hexdigest()!=model['source_vtk_sha256']:raise ValueError('Original model differs')
            v,n,f,*_=vtk(raw);points=np.linalg.solve(directions,(v.astype(float)*[-1,-1,1]-origin).T).T*spacing
            triangles=points[f];distance,radius=mesh_oracle(triangles)
            centers,axes,voxels,exterior=cell_faces(labels==model['label_value'],spacing);cells=rectangle_triangles(centers,axes,spacing)
            result=certify(cells,distance,error)
            fwd=next(r for r in forward['records'] if r['label_value']==model['label_value'])
            if fwd['source_review_sha256']!=hashlib.sha256(source_raw).hexdigest() or fwd['source_vtk_sha256']!=model['source_vtk_sha256']:raise ValueError('Forward certificate/source identity differs')
            result.update({'label_value':model['label_value'],'source_name':model['source_name'],'native_boundary_faces':len(centers),
                'reference_original_mesh_triangles':len(triangles),'reference_triangle_maximum_centroid_radius_mm':radius,
                'boundary_source_voxel_ijk':voxels.tolist(),'boundary_normal_axis':axes.tolist(),'boundary_face_centers_native_axis_mm':centers.tolist(),
                'boundary_faces_at_grid_exterior':int(exterior.sum()),'source_vtk_sha256':model['source_vtk_sha256'],
                'source_review_sha256':hashlib.sha256(source_raw).hexdigest(),'clinical_approval':False,
                'reverse_source_is_discrete_cell_union':True,'source_voxels_or_model_changed':False,
                'bidirectional_lower_bound_mm':max(result['lower_bound_mm'],fwd['lower_bound_mm']),
                'bidirectional_upper_bound_mm':max(result['upper_bound_mm'],fwd['upper_bound_mm'])})
            payload=(json.dumps(result,indent=2)+'\n').encode();packed=gzip.compress(payload,mtime=0);file='label-'+str(model['label_value'])+'-complete-reverse-distance-bounds.json.gz';(output/file).write_bytes(packed)
            rows.append({k:v for k,v in result.items() if k not in ['terminal_cells','boundary_source_voxel_ijk','boundary_normal_axis','boundary_face_centers_native_axis_mm']}|{
                'file':file,'compressed_sha256':hashlib.sha256(packed).hexdigest(),'uncompressed_sha256':hashlib.sha256(payload).hexdigest(),'terminal_cell_count':len(result['terminal_cells'])})
            (output/'reverse-distance-bound-summary.json').write_text(json.dumps({'records':rows,'all_five_original_models_complete':len(rows)==5,
                'forward_summary_sha256':hashlib.sha256((output/'triangle-distance-bound-summary.json').read_bytes()).hexdigest(),
                'source_geometry_changed':False,'clinical_approval':False,'runtime_promoted':False,
                'limits':['Bidirectional intervals compare continuous original mesh triangles with explicit discrete labelled voxel-cell surfaces, not anatomical ground truth.',
                    'Every native boundary rectangle is split into two coplanar analysis triangles and fully covered by Lipschitz cells. Original label voxels and source meshes are unchanged.',
                    'Numerical interval width, annotation authority and source conservation do not supply clinical accuracy, acceptance thresholds, missing layers or patient registration.']},indent=2)+'\n')
            print(model['source_name'],'reverse interval',result['lower_bound_mm'],result['upper_bound_mm'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--error-mm',type=float,default=.05)
    a=p.parse_args();bound(a.archive,a.output,a.error_mm)
