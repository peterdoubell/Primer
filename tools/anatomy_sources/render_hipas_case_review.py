#!/usr/bin/env python3
"""Show original array-index planes; no patient orientation, clinical approval or geometry repair."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def render(root,out):
    files={'CT':root/'case-001/ct/001.npz','artery':root/'case-001/annotation/artery/001.npz','vein':root/'case-001/annotation/vein/001.npz'}
    arrays={}
    for name,path in files.items():
        with np.load(path,allow_pickle=False) as source:arrays[name]=source['data']
    ct=arrays['CT'];a=arrays['artery']!=0;v=arrays['vein']!=0;overlap=a&v
    fig,axes=plt.subplots(3,2,figsize=(12,14),facecolor='white');panels=[]
    for axis in range(3):
        other=tuple(i for i in range(3) if i!=axis);index=int(np.argmax(overlap.sum(axis=other)));image=np.take(ct,index,axis=axis).T;artery=np.take(a,index,axis=axis).T;vein=np.take(v,index,axis=axis).T;both=artery&vein
        axes[axis,0].imshow(image,cmap='gray',vmin=-1000,vmax=600,origin='lower');axes[axis,0].set_title(f'Original CT array axis {axis} index {index}\nDisplay window -1000 to 600 source scalar units; HU unverified')
        axes[axis,1].imshow(image,cmap='gray',vmin=-1000,vmax=600,origin='lower');rgba=np.zeros(image.shape+(4,),dtype=float);rgba[artery]=[0,1,0,.7];rgba[vein]=[1,0,0,.7];rgba[both]=[1,.65,0,1];axes[axis,1].imshow(rgba,origin='lower');axes[axis,1].set_title('Original artery green / vein red / overlapping labels orange\nAll original components retained')
        for col in range(2):axes[axis,col].set_xlabel(f'Array axis {other[0]} index');axes[axis,col].set_ylabel(f'Array axis {other[1]} index')
        panels.append({'source_array_axis':axis,'source_array_index':index,'plane_overlap_voxels':int(both.sum()),'source_indices_not_patient_orientation':True})
    fig.suptitle('HiPaS released case 001 — source array review only\nNo affine/laterality, HU calibration, commercial reuse or clinical accuracy approval',fontsize=14);fig.tight_layout(rect=[0,0,1,.94]);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=140);plt.close(fig)
    proof={'file':out.name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'source_file_sha256':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in files.items()},'panels':panels,'source_samples_changed':False,'display_window_source_scalar_units':[-1000,600],'patient_orientation_verified':False,'clinical_approval':False,'runtime_promoted':False};out.with_suffix('.json').write_text(json.dumps(proof,indent=2)+'\n');print(out)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();render(args.source_root,args.output)
