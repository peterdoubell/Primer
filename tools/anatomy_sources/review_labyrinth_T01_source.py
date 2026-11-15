#!/usr/bin/env python3
"""Audit original labyrinth NIfTI qforms and identical published meshes without repairing sources."""
import argparse,hashlib,json,math,struct,zipfile
from pathlib import Path
import numpy as np
import nibabel as nib
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

def sha(raw):return hashlib.sha256(raw).hexdigest()

def read(raw):
    if struct.unpack_from('<i',raw)[0]!=348 or raw[344:348]!=b'n+1\0':raise ValueError('Original little-endian NIfTI-1 required')
    dims=struct.unpack_from('<8h',raw,40);code,bits=struct.unpack_from('<2h',raw,70);offset_float=struct.unpack_from('<f',raw,108)[0];offset=int(offset_float);dtype={2:'u1',4:'<i2'}.get(code)
    if dims[0]!=3 or min(dims[1:4])<1 or dtype is None or bits!=np.dtype(dtype).itemsize*8 or offset<352 or offset!=offset_float or any(d not in [0,1] for d in dims[4:]):raise ValueError('Unexpected source scalar interpretation')
    count=math.prod(dims[1:4]);payload=raw[offset:]
    if len(payload)!=count*np.dtype(dtype).itemsize:raise ValueError('Original payload count differs')
    values=np.frombuffer(payload,dtype=dtype).reshape(dims[1:4],order='F')
    # Independent scalar byte-order/index reader, separate from NumPy and nibabel.
    scalar=np.fromiter((v[0] for v in struct.iter_unpack('<B' if code==2 else '<h',payload)),dtype=np.dtype(dtype),count=count)
    if not np.array_equal(values.ravel(order='F'),scalar):raise ValueError('Scalar readback differs')
    pix=struct.unpack_from('<8f',raw,76);qcode,scode=struct.unpack_from('<2h',raw,252)
    if qcode<=0 or scode!=0:raise ValueError('Original qform-only source required')
    b,c,d=struct.unpack_from('<3f',raw,256);norm=b*b+c*c+d*d
    if norm>1+1e-6:raise ValueError('Invalid source quaternion')
    a=math.sqrt(max(0,1-norm));R=np.array([[a*a+b*b-c*c-d*d,2*b*c-2*a*d,2*b*d+2*a*c],[2*b*c+2*a*d,a*a+c*c-b*b-d*d,2*c*d-2*a*b],[2*b*d-2*a*c,2*c*d+2*a*b,a*a+d*d-c*c-b*b]])
    affine=np.eye(4);affine[:3,:3]=R@np.diag([pix[1],pix[2],pix[3]*(-1 if pix[0]<0 else 1)]);affine[:3,3]=struct.unpack_from('<3f',raw,268)
    if not np.isfinite(affine).all() or abs(np.linalg.det(affine[:3,:3]))<1e-12:raise ValueError('Invalid source geometry')
    return values,affine,{'shape_xyz':list(dims[1:4]),'datatype_code':code,'bits':bits,'qform_code':qcode,'sform_code':scode,'declared_xyzt_units':raw[123],'pixdim':list(pix),'declared_qform':affine.tolist(),'slope_intercept':list(struct.unpack_from('<2f',raw,112)),'sample_sha256':sha(payload),'independent_scalar_samples_checked':count,'scalar_range':[int(values.min()),int(values.max())]}

def review(root,out):
    m=json.loads((root/'zenodo-3355272.json').read_text());f=next(f for f in m['files'] if f['key']=='T01.zip');raw=(root/'T01.zip').read_bytes()
    if len(raw)!=f['size'] or hashlib.md5(raw).hexdigest()!=f['checksum'].split(':')[1]:raise ValueError('Original full archive checksum differs')
    files=[];arrays={};meshes={};descriptor=None
    with zipfile.ZipFile(root/'T01.zip') as z:
        for info in z.infolist():
            if info.is_dir():continue
            data=z.read(info.filename);destination=(root/info.filename).resolve()
            if not destination.is_relative_to(root.resolve()):raise ValueError('Original archive member escapes source cache')
            destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)
            row={'member':info.filename,'bytes':len(data),'sha256':sha(data),'ZIP_CRC_verified':True,'crc32':f'{info.CRC:08x}'}
            if info.filename.endswith('.nii'):
                values,affine,header=read(data);path=root/info.filename;library=nib.load(path)
                if not np.array_equal(values,library.dataobj.get_unscaled()) or not np.allclose(affine,library.get_qform(),rtol=0,atol=1e-7):raise ValueError('Independent NIfTI read differs')
                row.update(header);row['all_samples_and_qform_match_nibabel']=True;arrays[info.filename]=(values,affine)
            elif info.filename.endswith('.ply'):
                header,body=data.split(b'end_header\n',1);lines=body.decode().splitlines();n=int(next(l.split()[-1] for l in header.decode().splitlines() if l.startswith('element vertex ')));k=int(next(l.split()[-1] for l in header.decode().splitlines() if l.startswith('element face ')))
                vertices=np.array([[float(v) for v in l.split()] for l in lines[:n]]);face_rows=[list(map(int,l.split())) for l in lines[n:n+k]]
                if vertices.shape!=(n,3) or not np.isfinite(vertices).all() or any(len(t)!=5 or t[0]!=3 or min(t[1:4])<0 or max(t[1:4])>=n for t in face_rows):raise ValueError('Original PLY geometry interpretation differs')
                faces=np.array([t[1:4] for t in face_rows]);edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1);unique,counts=np.unique(edges,axis=0,return_counts=True)
                graph=coo_matrix((np.ones(len(unique)),(unique[:,0],unique[:,1])),shape=(n,n));component_count,_=connected_components(graph,directed=False)
                tri=vertices[faces];area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
                row.update(surface_components=int(component_count),zero_area_triangles=int((area==0).sum()),original_header=header.decode(),vertices=n,triangles=k,source_bounds=[vertices.min(0).tolist(),vertices.max(0).tolist()],boundary_edges=int((counts==1).sum()),nonmanifold_edges=int((counts>2).sum()),uninterpreted_original_trailing_lines=len(lines)-n-k);meshes[info.filename]=data
            else:descriptor=json.loads(data);row['original_descriptor']=descriptor
            files.append(row)
    differences=[]
    for mode in ['CT','uCT']:
        image,A=arrays[f'T01/{mode}/T01_{mode}_RAW.nii'];mask,B=arrays[f'T01/{mode}/T01_{mode}_LABELS.nii']
        if image.shape!=mask.shape:raise ValueError('Paired source shapes differ')
        corners=np.array([[x,y,z,1] for x in [0,image.shape[0]-1] for y in [0,image.shape[1]-1] for z in [0,image.shape[2]-1]])
        labels,component_count=ndimage.label(mask!=0,ndimage.generate_binary_structure(3,1));sizes=np.bincount(labels.ravel())[1:]
        differences.append({'six_neighbour_components':int(component_count),'component_sizes_descending':sorted(sizes.tolist(),reverse=True),'source_components_repaired_or_filtered':False,'mode':mode,'image_mask_equal_shape':True,'image_mask_qforms_exactly_equal':bool(np.array_equal(A,B)),'maximum_image_mask_corner_qform_displacement_declared_units':float(np.linalg.norm(corners@A.T-corners@B.T,axis=1).max()),'original_labels':np.unique(mask).tolist(),'foreground_samples':int((mask!=0).sum())})
    identical=len({sha(data) for data in meshes.values()})==1
    proof={'record_id':3355272,'case':'T01','actual_dataset_license':m['metadata']['license'],'metadata_sha256':sha((root/'zenodo-3355272.json').read_bytes()),'archive':{'file':f['key'],'bytes':len(raw),'publisher_checksum':f['checksum'],'publisher_MD5_verified':True,'sha256':sha(raw)},'files':files,'paired_source_grid_comparisons':differences,'CT_and_microCT_surface_files_byte_identical':identical,'original_descriptor':descriptor,'source_registration_resampling_repair_or_mesh_changes_applied':False,'independent_raw_DICOM_geometry_HU_or_effective_resolution_verified':False,'source_surface_anatomical_identity_full_extent_and_registration_approved':False,'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False}
    out.mkdir(parents=True,exist_ok=True);(out/'T01-original-source-review.json').write_text(json.dumps(proof,indent=2)+'\n');print('Independent scalar samples',sum(r.get('independent_scalar_samples_checked',0) for r in files));print(differences);print('Original mesh copies byte-identical',identical)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();review(a.source_root,a.output)
