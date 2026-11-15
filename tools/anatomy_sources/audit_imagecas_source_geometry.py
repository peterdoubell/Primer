#!/usr/bin/env python3
"""Inspect supplied coronary geometry against native labels; no mesh repair."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import numpy as np
import nibabel as nib
from tools.anatomy_sources.audit_massp_mesh_voxels import section,raster_section


def vtk_points(path):
    raw=path.read_bytes();lines=raw.splitlines()[:4]
    if len(lines)<4 or lines[3]!=b'DATASET POLYDATA' or lines[2] not in (b'ASCII',b'BINARY'):
        raise ValueError('Unsupported declared VTK format')
    match=re.search(rb'(?m)^POINTS (\d+) (float|double) *\r?\n',raw)
    if not match:raise ValueError('Missing supported VTK point array')
    count=int(match[1]);start=match.end()
    if lines[2]==b'ASCII':
        tokens=raw[start:].decode('ascii').split()
        points=np.array([float(v) for v in tokens[:count*3]],dtype=np.float64).reshape(count,3)
    else:
        dtype='>f4' if match[2]==b'float' else '>f8'
        points=np.frombuffer(raw,dtype=dtype,count=count*3,offset=start).reshape(count,3).astype(np.float64)
    if not np.isfinite(points).all():raise ValueError('Nonfinite source VTK points')
    return points,lines[2].decode(),raw


def ascii_surface(path):
    points,encoding,raw=vtk_points(path)
    if encoding!='ASCII':raise ValueError('Only declared ASCII source polygons implemented')
    text=raw.decode('ascii');match=re.search(r'(?m)^POLYGONS (\d+) (\d+)\s*\nOFFSETS (\w+)\s*\n',text)
    if not match:raise ValueError('Unsupported source polygon encoding')
    count,total=int(match[1]),int(match[2]);tail=text[match.end():];marker=re.search(r'\bCONNECTIVITY (\w+)\s*\n',tail)
    if not marker:raise ValueError('Missing source connectivity')
    offsets=np.array([int(v) for v in tail[:marker.start()].split()],dtype=np.int64)
    if len(offsets)!=count or offsets[0]!=0 or offsets[-1]!=total or np.any(np.diff(offsets)!=3):raise ValueError('Source polygons are not a complete triangle table')
    faces=np.array([int(v) for v in tail[marker.end():].split()[:total]],dtype=np.int64).reshape(-1,3)
    if np.any(faces<0) or np.any(faces>=len(points)):raise ValueError('Invalid source point indices')
    return points,faces


def audit(root,output,code_evidence,baseline=None):
    acquisition=json.loads((root.parent/'imagecas-x-case-134-acquisition.json').read_text())
    expected={Path(e['name']).name:e['sha256'] for e in acquisition['files']}
    for name,digest in expected.items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('Acquired annotation changed')
    image=nib.load(root/'134.coronary.nii.gz');labels=np.asarray(image.dataobj)
    q,qcode=image.get_qform(coded=True);s,scode=image.get_sform(coded=True)
    if not qcode or not scode or not np.allclose(q,s,rtol=0,atol=1e-5):raise ValueError('Ambiguous source label affine')
    if baseline:
        baseline_manifest=json.loads((baseline/'surface-review.json').read_text());part=baseline_manifest['records'][0]
        baseline_path=baseline/part['mesh_file']
        if hashlib.sha256(baseline_path.read_bytes()).hexdigest()!=part['mesh_sha256']:raise ValueError('Baseline model changed')
        if baseline_manifest['source_label_sha256']!=expected['134.coronary.nii.gz']:raise ValueError('Baseline uses another annotation')
        with np.load(baseline_path) as mesh:points_ras=mesh['vertices'].copy();faces=mesh['faces'].copy()
        points_lps=points_ras*np.array([-1.,-1.,1.])
        geometry_digest=part['mesh_sha256'];geometry_origin='Derived unsmoothed original-label isosurface in NIfTI RAS'
    else:
        points_lps,faces=ascii_surface(root/'134.coronary_surface.vtk')
        points_ras=points_lps*np.array([-1.,-1.,1.])
        geometry_digest=expected['134.coronary_surface.vtk'];geometry_origin='Supplied archival VTK surface'
    native=nib.affines.apply_affine(np.linalg.inv(image.affine),points_ras);triangles=native[faces]
    lo=np.floor(native.min(0)).astype(int)-1;hi=np.ceil(native.max(0)).astype(int)+2
    if np.any(lo<0) or np.any(hi>labels.shape):raise ValueError('Source geometry beyond label field')
    xs=np.arange(lo[0],hi[0]);ys=np.arange(lo[1],hi[1]);records=[];fp=fn=total=expected_count=predicted_count=0
    omissions_by_label={int(v):0 for v in np.unique(labels) if v>0}
    for z in range(lo[2],hi[2]):
        predicted=raster_section(section(triangles,2,z,0,1),xs,ys)
        actual=labels[lo[0]:hi[0],lo[1]:hi[1],z].T>0
        a=int(np.count_nonzero(predicted & ~actual));b=int(np.count_nonzero(actual & ~predicted))
        source_plane=labels[lo[0]:hi[0],lo[1]:hi[1],z].T
        for label in omissions_by_label:omissions_by_label[label]+=int(np.count_nonzero((source_plane==label)&~predicted))
        fp+=a;fn+=b;total+=actual.size;expected_count+=int(actual.sum());predicted_count+=int(predicted.sum())
        records.append({'native_z_index':z,'source_foreground':int(actual.sum()),'source_surface_interior':int(predicted.sum()),'false_positive':a,'false_negative':b})
    full=int(np.count_nonzero(labels));omitted=full-expected_count
    edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1);_,counts=np.unique(edges,axis=0,return_counts=True)
    result={'case':'134','source_label_sha256':expected['134.coronary.nii.gz'],'analysed_geometry_sha256':geometry_digest,'geometry_origin':geometry_origin,'original_supplied_surface_sha256':expected['134.coronary_surface.vtk'],
            'source_code_evidence_path':str(code_evidence),'source_code_sha256':hashlib.sha256(code_evidence.read_bytes()).hexdigest(),
            'coordinate_comparison':('Original NIfTI affine applied directly; no fitted registration' if baseline else 'Publisher code documents original physical LPS mm. Standard LPS-to-NIfTI-RAS basis conversion [-X,-Y,+Z] used for analysis only; no fitted registration.'),
            'archival_generation_version_and_parameters_verified':False,'vertices':len(points_lps),'triangles':len(faces),
            'source_surface_edge_boundary_count':int((counts==1).sum()),'source_surface_nonmanifold_edge_count':int((counts>2).sum()),
            'comparison_start':lo.tolist(),'comparison_stop_exclusive':hi.tolist(),'compared_voxel_centres':total,
            'full_source_foreground_voxels':full,'source_foreground_in_compared_bounds':expected_count,'source_foreground_outside_compared_bounds':omitted,
            'source_surface_interior_voxels':predicted_count,'false_positive_interiors':fp,'false_negative_source_voxels':fn,'false_negative_voxels_by_label':omissions_by_label,
            'foreground_dice':float(2*(expected_count-fn)/(full+predicted_count)),'planes':records,
            'source_files_changed':False,'clinical_approval':False,'runtime_promoted':False,
            'limits':'Geometric consistency comparison conditional on publisher-documented coordinate convention. Current source script describes smoothing, but archival construction parameters are not independently attested. No original CT images acquired; no clinical anatomy, branch-label or commercial image permission verified.'}
    output.write_text(json.dumps(result,indent=2)+'\n');print('Comparisons',total,'false positive',fp,'false negative',fn,'source outside bounds',omitted)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--source-code-evidence',type=Path,required=True)
    parser.add_argument('--baseline',type=Path)
    args=parser.parse_args();audit(args.source,args.output,args.source_code_evidence,args.baseline)
