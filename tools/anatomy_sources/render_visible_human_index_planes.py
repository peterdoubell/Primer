#!/usr/bin/env python3
"""Inspect raw source-index orthoplanes; do not call these registered patient planes."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def sha(raw):return hashlib.sha256(raw).hexdigest()
def render(source,proof_dir):
    report=json.loads((proof_dir/'ordered-source-stack-review.json').read_text());path=source/report['source_stack_file'];shape=tuple(report['source_grid_zyx_RGB'])
    if path.stat().st_size!=report['source_stack_bytes']:raise ValueError('Complete source stack length differs')
    volume=np.memmap(path,dtype=np.uint8,mode='r',shape=shape);check=hashlib.sha256()
    for frame in volume:check.update(frame.tobytes())
    if check.hexdigest()!=report['source_stack_sha256']:raise ValueError('Complete source stack changed')
    selections=[('source_y',500),('source_y',650),('source_y',800),('source_x',900),('source_x',1050),('source_x',1200)]
    fig,axes=plt.subplots(3,2,figsize=(16,15));rows=[]
    for ax,(axis,index) in zip(axes.ravel(),selections):
        image=volume[:,index,:,:] if axis=='source_y' else volume[:,:,index,:]
        ax.imshow(image,origin='upper',interpolation='nearest');ax.set_title(f'Unregistered original index plane: {axis}={index}');ax.set_xlabel('Original in-plane pixel index');ax.set_ylabel('Original ordered frame index');rows.append({'axis':axis,'index':index,'dimensions':list(image.shape),'all_plane_RGB_sha256':sha(image.tobytes())})
    fig.suptitle('855 original female head/neck cryosections: no fitting, gap filling or registration',fontsize=14);fig.tight_layout(rect=[0,.03,1,.96]);output=source/'original-index-plane-review.png';fig.savefig(output,dpi=120);plt.close(fig)
    proof={'source_stack_sha256':report['source_stack_sha256'],'source_stack_rehashed_before_render':True,'planes':rows,'plot_sha256':sha(output.read_bytes()),'pixels_interpolated_or_source_frames_fitted':False,'source_index_planes_are_independently_registered_patient_planes':False,'clinical_approval':False,'runtime_promoted':False};(proof_dir/'source-index-plane-review.json').write_text(json.dumps(proof,indent=2)+'\n');print(output)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--proof-dir',type=Path,required=True);a=p.parse_args();render(a.source_root,a.proof_dir)
