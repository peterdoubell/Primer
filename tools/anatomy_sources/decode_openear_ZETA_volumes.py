#!/usr/bin/env python3
"""Decode all original registered source volumes with bounded memory and independent gzip readback."""
import argparse,gzip,hashlib,json,math,re,struct,zipfile,zlib
from pathlib import Path
import numpy as np
from tools.anatomy_sources.review_openear_ZETA_geometry import header
MEMBERS=['04_Reconstruction_Microslicing/Microslicing_Zeta.nrrd','05_Registred_Slicer_Volumes/CBCT_Embedded.nrrd','05_Registred_Slicer_Volumes/CBCT_Unembedded.nrrd','06_Segmentation/Segmentation.seg.nrrd','07_3D_Models/Bone.nrrd']

def decode(path,out):
    with path.open('rb') as stream:original,fields=header(stream);offset=stream.tell()
    dtype={'unsigned char':'u1','short':'<i2'}.get(fields['type']);sizes=list(map(int,fields['sizes'].split()))
    if dtype is None or fields['encoding']!='gzip' or (dtype=='<i2' and fields.get('endian')!='little'):raise ValueError('Unexpected source scalar encoding')
    expected=math.prod(sizes)*np.dtype(dtype).itemsize;digest=hashlib.sha256();total=0
    with path.open('rb') as source,out.open('wb') as target:
        source.seek(offset)
        with gzip.GzipFile(fileobj=source) as compressed:
            while True:
                block=compressed.read(8*1024*1024)
                if not block:break
                target.write(block);digest.update(block);total+=len(block)
                if total>expected:raise ValueError('Original scalar payload exceeds declaration')
    if total!=expected:raise ValueError('Original scalar payload count differs')
    # Separate streaming API checks every decoded byte against actual written bytes.
    codec=zlib.decompressobj(31);second=hashlib.sha256();checked=0
    with path.open('rb') as source,out.open('rb') as restored:
        source.seek(offset)
        while True:
            chunk=source.read(1024*1024)
            if not chunk:break
            pending=chunk
            while pending:
                block=codec.decompress(pending,8*1024*1024);pending=codec.unconsumed_tail
                if restored.read(len(block))!=block:raise ValueError('Independent written scalar readback differs')
                second.update(block);checked+=len(block)
        tail=codec.flush()
        if restored.read(len(tail))!=tail or restored.read(1):raise ValueError('Independent scalar tail differs')
        second.update(tail);checked+=len(tail)
    if not codec.eof or codec.unused_data or checked!=expected or digest.digest()!=second.digest():raise ValueError('Independent original gzip stream differs')
    data=np.memmap(out,dtype=dtype,mode='r',shape=tuple(reversed(sizes)))
    samples=math.prod(sizes);probes=sorted({0,1,sizes[0]-1,samples//2,samples-1});fmt='<B' if dtype=='u1' else '<h'
    with out.open('rb') as stream:
        for index in probes:
            stream.seek(index*np.dtype(dtype).itemsize);value=struct.unpack(fmt,stream.read(np.dtype(dtype).itemsize))[0]
            if data.reshape(-1)[index]!=value:raise ValueError('Scalar endian/index sentinel differs')
    vectors=re.findall(r'\(([^)]+)\)',fields['space directions']);basis=np.array([[float(x) for x in v.split(',')] for v in vectors]).T
    origin=np.array([float(x) for x in fields['space origin'].strip('()').split(',')]);affine=np.eye(4);affine[:3,:3]=basis;affine[:3,3]=origin
    if basis.shape!=(3,3) or not np.isfinite(affine).all() or abs(np.linalg.det(basis))<1e-12:raise ValueError('Invalid declared spatial basis')
    if fields['space']=='left-posterior-superior':RAS=np.diag([-1.,-1.,1.,1.])@affine
    elif fields['space']=='right-anterior-superior':RAS=affine.copy()
    else:raise ValueError('Unknown original spatial convention')
    return data,{'original_header':original,'source_sizes_fastest_first':sizes,'memmap_shape_reversed_axes':list(data.shape),'dtype':dtype,'decoded_bytes':total,'decoded_scalar_samples':samples,'all_decoded_bytes_match_independent_stream_and_written_readback':True,'decoded_sha256':digest.hexdigest(),'declared_space':fields['space'],'declared_source_affine':affine.tolist(),'equivalent_RAS_affine':RAS.tolist(),'source_samples_reordered_resampled_or_repaired':False},fields

def review(root,proof_dir):
    acquisition=json.loads((proof_dir/'ZETA-original-acquisition.json').read_text());records={r['member']:r for r in acquisition['members']};out=root/'ZETA-volume-review';out.mkdir(exist_ok=True);rows=[];layers=[]
    with zipfile.ZipFile(root/'ZETA.zip') as archive:
        for member in MEMBERS:
            filename=Path(member).name;path=out/filename;sha=hashlib.sha256()
            with archive.open(member) as source,path.open('wb') as target:
                for block in iter(lambda:source.read(8*1024*1024),b''):sha.update(block);target.write(block)
            if sha.hexdigest()!=records[member]['sha256']:raise ValueError('Original acquired NRRD differs')
            data,p,fields=decode(path,out/(filename+'.raw'));p.update(member=member,original_member_sha256=sha.hexdigest(),ZIP_CRC_reverified=True)
            if member=='06_Segmentation/Segmentation.seg.nrrd':
                if data.ndim!=4 or data.shape[-1]!=13 or fields['kinds']!='list domain domain domain':raise ValueError('Original independent list layers required')
                counts=np.zeros(13,dtype=np.int64);low=np.full((13,3),np.iinfo(np.int32).max,dtype=int);high=np.full((13,3),-1,dtype=int);hist=np.zeros(256,dtype=np.int64);overlap=0
                for z in range(data.shape[0]):
                    slab=np.asarray(data[z]);hist+=np.bincount(slab.reshape(-1),minlength=256);overlap+=int((np.count_nonzero(slab,axis=2)>1).sum())
                    for i in range(13):
                        y,x=np.where(slab[:,:,i]!=0);counts[i]+=len(x)
                        if len(x):low[i]=np.minimum(low[i],[int(x.min()),int(y.min()),z]);high[i]=np.maximum(high[i],[int(x.max()),int(y.max()),z])
                for i in range(13):
                    declared=list(map(int,fields[f'Segment{i}_Extent'].split()));actual=[int(low[i,j]) if k%2==0 else int(high[i,j]) for k,j in enumerate([0,0,1,1,2,2])]
                    if actual!=declared:raise ValueError('Original layer/metadata extent disagreement')
                    layers.append({'original_list_axis_index':i,'source_name':fields[f'Segment{i}_Name'],'source_ID':fields[f'Segment{i}_ID'],'foreground_samples':int(counts[i]),'original_extent_equals_full_layer_sample_bounds':True,'source_extent_xyz_inclusive':actual,'source_Layer_or_LabelValue_fields_present':f'Segment{i}_Layer' in fields or f'Segment{i}_LabelValue' in fields})
                p.update(actual_scalar_value_counts={str(i):int(n) for i,n in enumerate(hist) if n},overlapping_foreground_positions_across_original_layers=overlap,list_axis_layers_flattened_or_overlap_removed=False)
            elif data.ndim==4:
                if data.shape[-1]!=3 or fields['kinds']!='vector domain domain domain':raise ValueError('Original colour vector interpretation differs')
                p.update(source_original_three_channel_vector_preserved=True,channel_range=[int(data.min()),int(data.max())],source_photography_is_untreated_in_vivo_colour=False)
            else:p['source_scalar_range']=[int(data.min()),int(data.max())]
            rows.append(p);print(member,'all decoded bytes checked',p['decoded_bytes'],flush=True)
    proof={'case':'ZETA','volumes':rows,'original_segmentation_layers':layers,'source_geometry_or_photographic_colour_registration_independently_approved':False,'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False}
    (proof_dir/'ZETA-original-volume-readback.json').write_text(json.dumps(proof,indent=2)+'\n');print('All original source scalar bytes checked; layered mask overlaps retained')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--proof-dir',type=Path,required=True);a=p.parse_args();review(a.source_root,a.proof_dir)
