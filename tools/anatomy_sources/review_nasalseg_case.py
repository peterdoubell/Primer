#!/usr/bin/env python3
"""Audit original NasalSeg NRRD samples and shared declared geometry without clinical/operative promotion."""
import argparse,gzip,hashlib,json,re,struct,zipfile
from pathlib import Path
import numpy as np
from scipy import ndimage
LABELS={1:'right_maxillary_sinus',2:'left_maxillary_sinus',3:'right_nasal_cavity',4:'left_nasal_cavity',5:'nasal_pharynx'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def parse(raw):
    header,encoded=raw.split(b'\n\n',1);fields={}
    for line in header.decode().splitlines():
        if line.startswith('#') or ': ' not in line:continue
        key,value=line.split(': ',1);fields[key]=value
    if fields.get('type')!='int16' or fields.get('dimension')!='3' or fields.get('endian')!='little' or fields.get('encoding')!='gzip' or fields.get('space')!='left-posterior-superior':raise ValueError('Unexpected original NRRD interpretation')
    size=tuple(map(int,fields['sizes'].split()));decoded=gzip.decompress(encoded)
    if len(decoded)!=2*np.prod(size):raise ValueError('Original NRRD sample count differs')
    a=np.frombuffer(decoded,dtype='<i2').reshape(tuple(reversed(size)));scalar=np.fromiter((v[0] for v in struct.iter_unpack('<h',decoded)),dtype=np.int16,count=int(np.prod(size)))
    if not np.array_equal(a.ravel(),scalar):raise ValueError('Independent scalar readback differs')
    directions=np.array([[float(n) for n in s.split(',')] for s in re.findall(r'\(([^)]+)\)',fields['space directions'])]);origin=np.array([float(n) for n in fields['space origin'].strip('()').split(',')]);affine=np.eye(4);affine[:3,:3]=directions.T;affine[:3,3]=origin
    if directions.shape!=(3,3) or not np.isfinite(affine).all() or abs(np.linalg.det(directions))<1e-12:raise ValueError('Invalid declared source geometry')
    return a,{'original_header':header.decode(),'shape_xyz':list(size),'array_shape_zyx':list(a.shape),'sample_sha256':sha(decoded),'independently_checked_scalar_samples':len(scalar),'declared_LPS_affine':affine.tolist(),'source_pitch_mm':np.linalg.norm(directions,axis=1).tolist(),'scalar_range':[int(a.min()),int(a.max())]}
def review(root,out):
    record=json.loads((root/'zenodo-13893419.json').read_text());f=record['files'][0];archive=root/'NasalSeg.zip';raw=archive.read_bytes()
    if len(raw)!=f['size'] or hashlib.md5(raw).hexdigest()!=f['checksum'].split(':')[1]:raise ValueError('Complete original archive differs')
    case=root/'P001';case.mkdir(exist_ok=True);arrays=[];files=[]
    with zipfile.ZipFile(archive) as z:
        for member in ['images/P001_img.nrrd','labels/P001_seg.nrrd']:
            data=z.read(member);path=case/Path(member).name;path.write_bytes(data);array,p=parse(data);arrays.append(array);files.append({'member':member,'bytes':len(data),'sha256':sha(data),'zip_crc32':f'{z.getinfo(member).CRC:08x}','zip_CRC_verified':True,**p})
    image,mask=arrays
    if image.shape!=mask.shape or files[0]['declared_LPS_affine']!=files[1]['declared_LPS_affine']:raise ValueError('Source CT/mask grids differ')
    if set(np.unique(mask).tolist())!=set(range(6)):raise ValueError('Original label set differs')
    labels=[]
    for label,name in LABELS.items():
        region=mask==label;locations=np.where(region);components,n=ndimage.label(region,ndimage.generate_binary_structure(3,1));counts=np.bincount(components.ravel())[1:]
        labels.append({'source_label':label,'source_name':name,'voxels':int(region.sum()),'six_neighbour_components':int(n),'component_sizes_descending':sorted(counts.tolist(),reverse=True),'source_index_bounds_zyx_inclusive':[[int(v.min()),int(v.max())] for v in locations],'source_boundary_faces_touched':[key for key,m in [('z0',region[0]),('zlast',region[-1]),('y0',region[:,0]),('ylast',region[:,-1]),('x0',region[:,:,0]),('xlast',region[:,:,-1])] if m.any()],'components_filtered_or_filled':False})
    proof={'record_id':13893419,'case':'P001','dataset_license':record['metadata']['license'],'source_record_sha256':sha((root/'zenodo-13893419.json').read_bytes()),'original_archive':{'file':f['key'],'bytes':len(raw),'publisher_MD5_verified':True,'publisher_checksum':f['checksum'],'sha256':sha(raw)},'files':files,'source_labels':labels,'original_shared_declared_grid_verified':True,'source_samples_resampled_registered_or_repaired':False,'matching_native_DICOM_acquisition_or_effective_resolution_verified':False,'independent_HU_calibration_verified':False,'fine_operative_bone_or_complete_sinonasal_anatomy_verified':False,'whole_uncropped_patient_head_verified':False,'left_right_label_anatomical_identity_independently_verified':False,'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False};out.mkdir(parents=True,exist_ok=True);(out/'original-case-grid-review.json').write_text(json.dumps(proof,indent=2)+'\n');print('Original grid',files[0]['shape_xyz'],'pitch',files[0]['source_pitch_mm'],'scalar readbacks',sum(f['independently_checked_scalar_samples'] for f in files));print('Labels',[(r['source_name'],r['voxels'],r['six_neighbour_components'],r['source_boundary_faces_touched']) for r in labels])
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();review(args.source_root,args.output)
