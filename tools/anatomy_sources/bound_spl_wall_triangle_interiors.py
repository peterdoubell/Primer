#!/usr/bin/env python3
"""Bound all original mesh-triangle interiors against explicit labelled cell faces."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import zipfile


def certify(triangles,distance,error=.05,initial_lower=0.):
    """Distance to a closed set is 1-Lipschitz; centroid radius covers a convex cell."""
    import numpy as np
    if not np.isfinite(error) or error<=0 or not np.isfinite(triangles).all() or len(triangles)==0:raise ValueError('Invalid numerical bound request')
    original=np.arange(len(triangles),dtype=np.int64);paths=['']*len(triangles);pending=triangles.copy();lower=initial_lower
    leaves=[];depth=0;witness=None
    while len(pending):
        centers=pending.mean(1);values=distance(centers)
        index=int(np.argmax(values))
        if values[index]>lower:lower=float(values[index]);witness={'original_triangle_index':int(original[index]),'binary_refinement_path':paths[index],'point':centers[index].tolist(),'distance_mm':lower}
        radii=np.linalg.norm(pending-centers[:,None],axis=2).max(1)
        upper=values+radii+1e-10
        done=upper<=lower+error
        for i in np.flatnonzero(done):leaves.append({'original_triangle_index':int(original[i]),'binary_refinement_path':paths[i],
            'cell_centroid':centers[i].tolist(),'centroid_distance_mm':float(values[i]),'cover_radius_mm':float(radii[i]),'upper_bound_mm':float(upper[i])})
        if done.all():break
        selected=np.flatnonzero(~done);new=[];ids=[];new_paths=[]
        for i in selected:
            p=pending[i];edges=[(0,1),(1,2),(2,0)];a,b=max(edges,key=lambda e:float(np.linalg.norm(p[e[0]]-p[e[1]])));c=3-a-b;mid=(p[a]+p[b])/2
            new.extend([[p[a],mid,p[c]],[mid,p[b],p[c]]]);ids.extend([original[i],original[i]]);new_paths.extend([paths[i]+'0',paths[i]+'1'])
        pending=np.asarray(new);original=np.asarray(ids,dtype=np.int64);paths=new_paths;depth+=1
        print('Adaptive level',depth,'pending cells',len(pending),'global witness',lower,flush=True)
    final_upper=max(l['upper_bound_mm'] for l in leaves)
    return {'lower_bound_mm':lower,'upper_bound_mm':final_upper,'bound_width_mm':final_upper-lower,
        'target_bound_width_mm':error,'original_triangle_count':len(triangles),'terminal_cells':leaves,'maximum_refinement_level':depth,
        'maximum_interior_witness':witness,'source_triangles_changed':False,'analysis_subdivision_only':True}


def bound(archive,output,error):
    import numpy as np
    from scipy.spatial import cKDTree
    from tools.anatomy_sources.review_spl_wall_source import vtk,nrrd
    from tools.anatomy_sources.compare_spl_wall_label_boundaries import cell_faces,closest_faces
    native_raw=(output/'independent-wall-source-review.json').read_bytes();native=json.loads(native_raw)
    vertex_summary=json.loads((output/'label-boundary-comparison-summary.json').read_text());summaries=[]
    if vertex_summary['source_review_sha256']!=hashlib.sha256(native_raw).hexdigest():raise ValueError('Original vertex evidence is stale')
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=native['archive_sha256']:raise ValueError('Original archive differs')
    with zipfile.ZipFile(archive) as z:
        fields,labels=nrrd(z.read('abdomen-2016-09/Data/seg.nrrd'));origin=np.asarray([float(v) for v in fields['space origin'].strip('()').split(',')])
        directions=np.asarray([[float(v) for v in s.split(',')] for s in re.findall(r'\(([^)]+)\)',fields['space directions'])]).T
        spacing=np.linalg.norm(directions,axis=0)
        if not np.allclose((directions/spacing).T@(directions/spacing),np.eye(3),rtol=0,atol=1e-12):raise ValueError('Unreviewed source cell basis')
        for model in native['records']:
            raw=z.read(model['source_member'])
            if hashlib.sha256(raw).hexdigest()!=model['source_vtk_sha256']:raise ValueError('Native source mesh differs')
            v,n,f,*_=vtk(raw);points=np.linalg.solve(directions,(v.astype(float)*[-1,-1,1]-origin).T).T*spacing
            centers,axes,*_=cell_faces(labels==model['label_value'],spacing);half=np.tile(spacing*.5,(len(centers),1));half[np.arange(len(centers)),axes]=0
            prepared=(cKDTree(centers),half,float(np.linalg.norm(half,axis=1).max()))
            def distance(p):return np.asarray([r['distance_mm'] for r in closest_faces(p,centers,axes,spacing,prepared)[0]])
            previous=next(r for r in vertex_summary['records'] if r['label_value']==model['label_value'])
            result=certify(points[f],distance,error,previous['maximum_vertex_distance_mm'])
            result.update({'label_value':model['label_value'],'source_name':model['source_name'],'source_vtk_sha256':model['source_vtk_sha256'],
                'source_review_sha256':hashlib.sha256(native_raw).hexdigest(),'vertex_maximum_distance_mm':previous['maximum_vertex_distance_mm'],
                'reference_is_native_label_cell_union':True,'reverse_surface_distance_verified':False,'clinical_approval':False})
            payload=(json.dumps(result,indent=2)+'\n').encode();packed=gzip.compress(payload,mtime=0);file='label-'+str(model['label_value'])+'-complete-triangle-distance-bounds.json.gz';(output/file).write_bytes(packed)
            summaries.append({k:v for k,v in result.items() if k!='terminal_cells'}|{'file':file,'compressed_sha256':hashlib.sha256(packed).hexdigest(),'uncompressed_sha256':hashlib.sha256(payload).hexdigest(),'terminal_cell_count':len(result['terminal_cells'])})
            (output/'triangle-distance-bound-summary.json').write_text(json.dumps({'records':summaries,'all_five_original_models_complete':len(summaries)==5,
                'source_geometry_changed':False,'clinical_approval':False,'runtime_promoted':False,
                'limits':['These are bounded continuous mesh-to-discrete-cell-surface distances. Reverse distance and continuous anatomical ground truth are not proved.',
                          'Longest-edge analysis subdivision does not alter, smooth or repair source meshes. Lipschitz bounds cover unsampled cell interiors.',
                          'Numerical bound width is not native source resolution or a clinical acceptance threshold.']},indent=2)+'\n')
            print(model['source_name'],'complete forward interval',result['lower_bound_mm'],result['upper_bound_mm'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--error-mm',type=float,default=.05)
    a=p.parse_args();bound(a.archive,a.output,a.error_mm)
