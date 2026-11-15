#!/usr/bin/env python3
"""Render native HOA phase-contrast source planes with explicit local micrometre axes and scalar windows."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def render(root,out):
    sources=[]
    for name in ['LADAF-2020-27_lung_left_VOI-03b-interlobular-fissure_6.5um_bm05','LADAF-2020-27_lung_left_VOI-03-upper-lobe-apical_2.5um_bm05']:
        p=root/'chunks'/name/'original-chunk-acquisition.json';proof=json.loads(p.read_text());row=proof['chunks'][0];file=root/row['derived_array_file']
        if hashlib.sha256(file.read_bytes()).hexdigest()!=row['derived_array_file_sha256']:raise ValueError('Original decoded source samples changed')
        volume=np.load(file,allow_pickle=False);sources.append((name,proof,row,volume))
    fig,axes=plt.subplots(2,3,figsize=(14,10));panels=[]
    for line,(name,proof,row,a) in enumerate(sources):
        pitch=row['pitch_um'];lo,hi=np.percentile(a,[1,99]);planes=[('z',a[a.shape[0]//2,:,:],('x','y')),('y',a[:,a.shape[1]//2,:],('x','z')),('x',a[:,:,a.shape[2]//2],('y','z'))]
        for col,(normal,image,coords) in enumerate(planes):
            ax=axes[line,col];ax.imshow(image,cmap='gray',vmin=lo,vmax=hi,origin='lower',extent=[-.5*pitch,(image.shape[1]-.5)*pitch,-.5*pitch,(image.shape[0]-.5)*pitch]);ax.set_xlabel('Local '+coords[0]+' (µm)');ax.set_ylabel('Local '+coords[1]+' (µm)');ax.set_title(f'{pitch:g}µm source pitch / {normal}-normal midpoint\nScalar window {lo:.0f} to {hi:.0f}; not HU')
            panels.append({'dataset':name,'source_index_normal':normal,'source_plane_local_index':64,'source_index_origin_xyz':row['source_index_origin_xyz'],'source_pitch_um':pitch,'display_window_original_scalar_units':[float(lo),float(hi)],'display_voxel_center_convention':'index0 center at0µm; outer edges at -pitch/2 and (count-.5)*pitch','local_plane_dimensions_um':[image.shape[1]*pitch,image.shape[0]*pitch],'source_array_file_sha256':row['derived_array_file_sha256']})
    fig.suptitle('Original human left-lung phase-contrast source blocks\nFixed ex-vivo tissue / local ROI / no anatomical labels or clinical diagnosis approval',fontsize=14);fig.subplots_adjust(hspace=.42,wspace=.30,top=.86,bottom=.08);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=140);plt.close(fig);p={'file':out.name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'source_volumes_resampled_or_registered':False,'scalar_samples_changed':False,'display_contrast_window_disclosed':True,'panels':panels,'complete_VOI_organ_or_secondary_lobule_verified':False,'anatomical_labels_or_source_segmentation_supplied':False,'clinical_approval':False,'runtime_promoted':False};out.with_suffix('.json').write_text(json.dumps(p,indent=2)+'\n');print(out)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();render(a.source_root,a.output)
