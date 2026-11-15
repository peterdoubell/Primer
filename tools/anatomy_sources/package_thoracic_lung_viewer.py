#!/usr/bin/env python3
"""Prepare source-bound CT/mask and label-interface buffers for correspondence review."""
import argparse,gzip,hashlib,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))


def sha(raw):return hashlib.sha256(raw).hexdigest()


def package(root):
    proof=json.loads((root/'source-review.json').read_text());records=proof['records'];ct=records[0];origin=np.mean([np.min([r['world_bounds'][0] for r in records[1:]],axis=0),np.max([r['world_bounds'][1] for r in records[1:]],axis=0)],axis=0);parts=[]
    for r in records:
        h=r['source_header'];raw=gzip.decompress((root/r['file']).read_bytes());count=int(np.prod(r['shape']));body=raw[int(h['voxel_offset']):int(h['voxel_offset'])+count*h['bits']//8]
        if h['endian']!='<' or h['slope']!=1 or h['intercept']!=0 or sha(body)!=h['raw_voxel_sha256']:raise ValueError('Unsupported source sample layout')
        if 'label' not in r:continue
        p=r['surfaces']['positions.f64.gz'];f=r['surfaces']['triangles.u32.gz'];positions=np.frombuffer(gzip.decompress((root/p['file']).read_bytes()),dtype='<f8').reshape(-1,3);faces=np.frombuffer(gzip.decompress((root/f['file']).read_bytes()),dtype='<u4').reshape(-1,3)
        relative=(positions-origin).astype('<f4');error=float(np.abs(relative.astype(float)+origin-positions).max());tri=positions[faces];face_normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normals=np.zeros_like(positions)
        for corner in range(3):np.add.at(normals,faces[:,corner],face_normals)
        length=np.linalg.norm(normals,axis=1);normals[length>0]/=length[length>0,None];normal=normals.astype('<f4');data=relative.tobytes()+normal.tobytes()+faces.astype('<u4').tobytes();path=root/'surfaces'/(r['label']+'-review-buffer.bin.gz');encoded=gzip.compress(data,mtime=0);path.write_bytes(encoded)
        parts.append({'id':r['label'],'label':r['label'].replace('_',' '),'mask_file':r['file'],'mask_file_sha256':r['sha256'],'mask_file_decoded_sha256':sha(gzip.decompress((root/r['file']).read_bytes())),'mask_payload_sha256':h['raw_voxel_sha256'],'mask_voxel_offset':h['voxel_offset'],'buffer_file':str(path.relative_to(root)),'buffer_sha256':sha(encoded),'buffer_decoded_sha256':sha(data),'vertices':len(positions),'triangles':len(faces),'bounds':r['world_bounds'],'max_centered_float32_position_error_source_mm':error,'normals':'Area-weighted display normals derived from retained original interface triangles; not authored tissue measurements.','center_indices':[int((a+b)//2) for a,b in r['bounds_voxel_xyz']],'foreground_voxels':r['foreground_voxels']})
    viewer={'case':'s0028','shape':ct['shape'],'spacing':[1.5,1.5,1.5],'affine':ct['affine'],'ct_file':ct['file'],'ct_file_sha256':ct['sha256'],'ct_file_decoded_sha256':sha(gzip.decompress((root/ct['file']).read_bytes())),'ct_voxel_offset':ct['source_header']['voxel_offset'],'ct_payload_sha256':ct['source_header']['raw_voxel_sha256'],'parts':parts,'mesh_origin_source_mm':origin.tolist(),'clinical_approval':False,'source_dicom_calibration_verified':False,'current_patient_registration':False,'normal_anatomical_atlas_approval':False,'runtime_promoted':False}
    (root/'viewer-manifest.json').write_text(json.dumps(viewer,indent=2)+'\n');print('Prepared',len(parts),'source-bound review buffers; max coordinate error',max(p['max_centered_float32_position_error_source_mm'] for p in parts))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--review-root',type=Path,default=ROOT/'docs/thoracic-lung-source-review-s0028');package(p.parse_args().review_root)
