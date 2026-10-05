#!/usr/bin/env python3
"""Reconstruct all independent strip-model self-crossings against native CT/labels."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re
import zipfile


def review(archive,output):
    import numpy as np
    from tools.anatomy_sources.review_spl_wall_source import vtk,nrrd
    from tools.anatomy_sources.review_zanatomy_wall_self_crossings import barycentric
    summary=json.loads((output/'independent-wall-contact-summary.json').read_text());packed=(output/summary['file']).read_bytes();raw=gzip.decompress(packed)
    if hashlib.sha256(raw).hexdigest()!=summary['uncompressed_sha256'] or hashlib.sha256(packed).hexdigest()!=summary['compressed_sha256']:raise ValueError('Complete contact evidence differs')
    evidence=json.loads(raw);source_raw=(output/'independent-wall-source-review.json').read_bytes();source=json.loads(source_raw)
    if hashlib.sha256(source_raw).hexdigest()!=evidence['source_review_sha256']:raise ValueError('Original source review differs')
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=source['archive_sha256']:raise ValueError('Original independent archive differs')
    rows=[];models={};geometry={}
    with zipfile.ZipFile(archive) as z:
        fields,labels=nrrd(z.read('abdomen-2016-09/Data/seg.nrrd'));ct_fields,ct=nrrd(z.read('abdomen-2016-09/Data/I.nrrd'))
        if fields!=ct_fields:raise ValueError('Native source grids differ')
        origin=np.asarray([float(v) for v in fields['space origin'].strip('()').split(',')]);directions=np.asarray([[float(v) for v in s.split(',')] for s in re.findall(r'\(([^)]+)\)',fields['space directions'])]).T
        for model in source['records']:
            raw=z.read(model['source_member'])
            if hashlib.sha256(raw).hexdigest()!=model['source_vtk_sha256']:raise ValueError('Original VTK differs')
            v,n,f,*_=vtk(raw);key=str(model['label_value']);geometry[key]=(v.astype(float),f);models[key]=model
        for c in evidence['contacts']:
            if not c['within_original_model']:continue
            faces=c['original_source_faces'];key=faces[0]['source_part'];v,f=geometry[key];ids=[a['source_face_index'] for a in faces];triangles=v[f[ids]];points=np.asarray(c['contact_points_ras_mm'])
            if points.shape!=(2,3):raise ValueError('Nonsegment contact needs separate classification')
            normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]);normals/=np.linalg.norm(normals,axis=1)[:,None]
            midpoint=points.mean(0);weights=[];errors=[];endpoints=[]
            for triangle in triangles:
                w,error=barycentric(triangle,midpoint);weights.append(w.tolist());errors.append(error)
                endpoints.append([{'weights':barycentric(triangle,p)[0].tolist(),'plane_reconstruction_error_mm':barycentric(triangle,p)[1]} for p in points])
            cross=float(np.linalg.norm(np.cross(normals[0],normals[1])));length=float(np.linalg.norm(points[1]-points[0]));inside=all(min(w)>1e-9 for w in weights) and max(errors)<1e-9
            ijk=np.linalg.solve(directions,(midpoint*[-1,-1,1]-origin));nearest=np.floor(ijk+.5).astype(int)
            if np.any(nearest<0) or np.any(nearest>=np.asarray(ct.shape[::-1])):raise ValueError('Source contact midpoint outside delivered grid')
            i,j,k=nearest
            rows.append({'label_value':int(key),'source_name':models[key]['source_name'],'source_vtk_sha256':models[key]['source_vtk_sha256'],
                'original_source_faces':faces,'original_source_vertex_indices':f[ids].tolist(),'original_triangles_ras':triangles.tolist(),
                'contact_points_ras':points.tolist(),'contact_segment_length_mm':length,'unit_normal_cross_norm':cross,
                'midpoint_barycentric_weights':weights,'midpoint_reconstruction_errors_mm':errors,'endpoint_barycentric_coordinates':endpoints,
                'midpoint_ras':midpoint.tolist(),'midpoint_native_ijk':ijk.tolist(),'nearest_native_voxel_ijk':nearest.tolist(),
                'nearest_native_label_value':int(labels[k,j,i]),'nearest_native_ct_stored_value':int(ct[k,j,i]),
                'nearest_voxel_is_anatomical_adjudication':False,
                'classification':'nonparallel_original_strip_triangle_interior_crossing' if inside and cross>1e-12 and length>1e-9 else 'unresolved_numerical_contact',
                'source_geometry_changed':False,'anatomical_tissue_or_pathology_classified':False,'clinical_approval':False})
    regions=[]
    for key in sorted({r['label_value'] for r in rows}):
        remaining={i for i,r in enumerate(rows) if r['label_value']==key}
        while remaining:
            indices={remaining.pop()};affected={f['source_face_index'] for i in indices for f in rows[i]['original_source_faces']}
            while True:
                joined={i for i in remaining if affected&{f['source_face_index'] for f in rows[i]['original_source_faces']}}
                if not joined:break
                remaining-=joined;indices|=joined;affected|={f['source_face_index'] for i in joined for f in rows[i]['original_source_faces']}
            regions.append({'label_value':key,'source_name':models[str(key)]['source_name'],'contact_record_indices':sorted(indices),'original_triangle_indices':sorted(affected)})
    if len(rows)!=summary['within_model_contacts']:raise ValueError('Full original self-contact set differs')
    result={'complete_contact_evidence_sha256':summary['uncompressed_sha256'],'source_review_sha256':hashlib.sha256(source_raw).hexdigest(),
        'records':rows,'regions':regions,'classifications':dict(Counter(r['classification'] for r in rows)),
        'model_quality_holds':[{'label_value':key,'source_name':models[str(key)]['source_name'],'original_crossing_count':sum(r['label_value']==key for r in rows),
            'status':'original_surface_crossings_require_resolution_and_anatomical_review_before_clinical_promotion'} for key in sorted({r['label_value'] for r in rows})],
        'source_geometry_changed':False,'clinical_approval':False,'runtime_promoted':False,
        'limits':['All contact triangles are expanded from original native strips; no new tessellation, source vertex/index changes, repair or clinical inference.',
            'Nearest source voxel and displayed CT are context, not calibrated HU/phase or a definitive continuous anatomical boundary.',
            'No-contact source labels are not automatically approved for tissue accuracy, complete course, missing-layer coverage or clinical registration.']}
    (output/'original-self-crossing-review.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Reconstructed',len(rows),'original independent strip contacts in',len(regions),'regions.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();review(a.archive,a.output)
