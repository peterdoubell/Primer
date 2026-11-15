#!/usr/bin/env python3
"""Serialize every original RGB frame unchanged; audit continuity without fitting or registration."""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image

def sha(raw):return hashlib.sha256(raw).hexdigest()
def build(source,proof_dir):
    proof_dir.mkdir(parents=True,exist_ok=True);acquisition_path=source/'female-head-acquisition.json';acquisition=json.loads(acquisition_path.read_text());rows=acquisition['records'];expected=[f'avf{n}{c}' for n in range(1001,1286) for c in 'abc']
    if [r['frame'] for r in rows]!=expected or not acquisition['every_original_raw_RGB_sample_matches_PNG']:raise ValueError('Full original ordered acquisition differs')
    shape=(855,1216,2048,3);path=source/'female-head-original-ordered.rgb';temporary=path.with_suffix('.partial');volume=np.memmap(temporary,dtype=np.uint8,mode='w+',shape=shape);frame_checks=[];pairs=[];previous=None;seen={};duplicate_groups=[]
    for index,row in enumerate(rows):
        png=source/'female-head-original'/(row['frame']+'.png');raw=png.read_bytes()
        if sha(raw)!=row['original_PNG']['sha256']:raise ValueError('Original PNG object changed')
        with Image.open(png) as image:
            image.load();pixels=image.tobytes()
            if image.mode!='RGB' or image.size!=(2048,1216) or sha(pixels)!=row['decoded_RGB_sha256']:raise ValueError('Original decoded source samples differ')
        array=np.frombuffer(pixels,np.uint8).reshape(1216,2048,3);volume[index]=array
        if volume[index].tobytes()!=pixels:raise ValueError('Stack sample writeback differs')
        digest=sha(pixels);seen.setdefault(digest,[]).append(row['frame']);frame_checks.append({'frame':row['frame'],'source_index':index,'decoded_RGB_sha256':digest})
        if previous is not None:
            difference=np.abs(array.astype(np.int16)-previous.astype(np.int16));pairs.append({'first_frame':rows[index-1]['frame'],'second_frame':row['frame'],'mean_absolute_RGB_difference':float(difference.mean()),'maximum_channel_difference':int(difference.max()),'fraction_pixel_locations_with_any_channel_difference':float(np.any(difference!=0,axis=2).mean()),'metric_is_anatomical_registration_or_distance':False})
        previous=array.copy()
        if (index+1)%100==0:print('Exact source frames serialized:',index+1,'of 855',flush=True)
    volume.flush();del volume;temporary.replace(path);volume=np.memmap(path,dtype=np.uint8,mode='r',shape=shape);whole=hashlib.sha256()
    for index,row in enumerate(frame_checks):
        raw=volume[index].tobytes()
        if sha(raw)!=row['decoded_RGB_sha256']:raise ValueError('Persisted complete stack differs')
        whole.update(raw)
    duplicate_groups=[frames for frames in seen.values() if len(frames)>1];del volume
    report={'original_acquisition_sha256':sha(acquisition_path.read_bytes()),'source_grid_zyx_RGB':list(shape),'dtype':'uint8','source_stack_file':path.name,'source_stack_bytes':path.stat().st_size,'source_stack_sha256':whole.hexdigest(),'all_855_original_frame_RGB_samples_written_and_read_back_exactly':True,'source_frame_checks':frame_checks,'adjacent_frame_photometric_checks':pairs,'identical_decoded_frame_groups':duplicate_groups,'largest_photometric_transitions':sorted(pairs,key=lambda x:x['mean_absolute_RGB_difference'],reverse=True)[:20],'nominal_spacing_mm':acquisition['nominal_sampling_mm'],'ordering_is_independent_physical_alignment_or_registration':False,'source_sample_resampling_fitting_gap_filling_or_enhancement':False,'source_anatomical_labels_or_full_tissue_boundary_approval':False,'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False}
    (proof_dir/'ordered-source-stack-review.json').write_text(json.dumps(report,indent=2)+'\n');print('Full original 6.39 GB RGB stack checked; identical decoded frame groups:',len(duplicate_groups));print('Largest transitions:',[(r['first_frame'],r['second_frame'],round(r['mean_absolute_RGB_difference'],2)) for r in report['largest_photometric_transitions'][:5]])
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--proof-dir',type=Path,required=True);a=p.parse_args();build(a.source_root,a.proof_dir)
