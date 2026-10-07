#!/usr/bin/env python3
"""Acquire exact public HOA N5 lung chunks; retain original scalar layout and missing-data/source limits."""
import argparse,base64,hashlib,json,struct,urllib.request,urllib.parse
from pathlib import Path
import numpy as np
from numcodecs import Blosc

def sha(raw):return hashlib.sha256(raw).hexdigest()
def decode_n5(raw):
    if len(raw)<16:raise ValueError('Truncated original N5 header')
    mode,rank=struct.unpack_from('>HH',raw)
    if mode!=0 or rank!=3:raise ValueError('Unsupported N5 mode or dimensionality')
    xyz=struct.unpack_from('>III',raw,4)
    if any(n<1 or n>128 for n in xyz):raise ValueError('Unsupported original block dimensions')
    decoded=Blosc().decode(raw[16:]);expected=2*np.prod(xyz)
    if len(decoded)!=expected:raise ValueError('N5 source sample length differs')
    # N5 samples are big endian with x the fastest-changing index.
    zyx=np.frombuffer(decoded,dtype='>u2').reshape(tuple(reversed(xyz)))
    # Independent scalar readback binds all positions/endian order, not appearance.
    scalar=np.fromiter((n[0] for n in struct.iter_unpack('>H',decoded)),dtype=np.uint16,count=int(np.prod(xyz)))
    if not np.array_equal(zyx.ravel(order='C'),scalar):raise ValueError('Independent scalar samples differ')
    return zyx,{'mode':mode,'block_dimensions_xyz':list(xyz),'array_shape_zyx':list(zyx.shape),'decoded_big_endian_sample_sha256':sha(decoded),'every_scalar_sample_independently_verified':len(scalar)}
def acquire(root,name,centre):
    metadata_path=root/(name+'.json');meta=json.loads(metadata_path.read_text());base=meta['data']['gcs_url']
    if not base.startswith('n5://gs://ucl-hip-ct-35a68e99feaae8932b1d44da0358940b/'):raise ValueError('Unexpected original publisher bucket')
    bucket,key=base.removeprefix('n5://gs://').split('/',1);attrs=json.loads((root/(name+'-s0-attributes.json')).read_text());top=json.loads((root/(name+'-attributes.json')).read_text())
    if attrs['dataType']!='uint16' or attrs['blockSize']!=[128]*3 or attrs['compression']['type']!='blosc':raise ValueError('Original scalar storage differs')
    if top['axes']!=['x','y','z'] or top['units']!=['um']*3 or top['resolution']!=[meta['data']['voxel_size_um']]*3:raise ValueError('Source pitch/axes differ')
    out=root/'chunks'/name;out.mkdir(parents=True,exist_ok=True);rows=[]
    for coordinate in [tuple(centre)]:
        if any(c<0 or c*128>=attrs['dimensions'][i] for i,c in enumerate(coordinate)):raise ValueError('Chunk outside source dimensions')
        suffix='s0/'+'/'.join(map(str,coordinate));object_key=key+suffix;url=f'https://storage.googleapis.com/{bucket}/{object_key}';filename='-'.join(map(str,coordinate));path=out/(filename+'.n5')
        info_url=f'https://storage.googleapis.com/storage/v1/b/{bucket}/o/'+urllib.parse.quote(object_key,safe='');info_raw=urllib.request.urlopen(info_url,timeout=30).read();info=json.loads(info_raw);(out/(filename+'-object.json')).write_bytes(info_raw)
        if not path.exists():path.write_bytes(urllib.request.urlopen(url,timeout=45).read())
        raw=path.read_bytes();expected=base64.b64decode(info['md5Hash'])
        if len(raw)!=int(info['size']) or hashlib.md5(raw).digest()!=expected:raise ValueError('Publisher object bytes or MD5 differ')
        array,proof=decode_n5(raw);array_file=out/(filename+'-source-zyx.npy');np.save(array_file,array,allow_pickle=False)
        rows.append({'grid_coordinate_xyz':list(coordinate),'source_index_origin_xyz':[128*c for c in coordinate],'source_object_url':url,'source_object_generation':info['generation'],'source_md5_base64':info['md5Hash'],'source_encoded_sha256':sha(raw),'source_object_metadata_sha256':sha(info_raw),'source_bytes':len(raw),'n5_header_and_samples':proof,'scalar_range':[int(array.min()),int(array.max())],'derived_array_file':str(array_file.relative_to(root)),'derived_array_file_sha256':sha(array_file.read_bytes()),'pitch_um':meta['data']['voxel_size_um'],'source_samples_changed':False})
        print(name,coordinate,'original samples',array.shape,'source MD5 and every scalar matched',flush=True)
    review={'source_dataset':name,'source_metadata_sha256':sha(metadata_path.read_bytes()),'metadata_repository_revision':'f8dc2928234ac46a6d126cc293aab7ddbd446f61','source_citation_doi':meta['citation']['doi'],'source_object_layout':'N5 big endian uint16, x fastest; derived array zyx','source_level':0,'source_preparation':meta['sample'],'source_registration_to_parent':meta['registration'],'registration_independently_verified':False,'intensity_is_clinical_HU':False,'in_vivo_clinical_CT':False,'acquired_whole_VOI_or_organ':False,'highest_original_TIFF_sample_identity_verified':False,'article_JPEG2000_and_current_N5_conversion_identity_verified':False,'data_license_independently_verified':False,'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False,'chunks':rows};(out/'original-chunk-acquisition.json').write_text(json.dumps(review,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--dataset',required=True);p.add_argument('--chunk',type=int,nargs=3,required=True);args=p.parse_args();acquire(args.source_root,args.dataset,args.chunk)
