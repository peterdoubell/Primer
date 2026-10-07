#!/usr/bin/env python3
"""Render original paired CT/mask planes without anatomical relabelling, resampling or operative claims."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tools.anatomy_sources.review_nasalseg_case import parse,LABELS

def render(root,out):
    image,ip=parse((root/'P001/P001_img.nrrd').read_bytes());mask,mp=parse((root/'P001/P001_seg.nrrd').read_bytes());pitch=ip['source_pitch_mm'];centre=[int(np.median(v)) for v in np.where(mask>0)];fig,axes=plt.subplots(3,2,figsize=(14,16));colors={1:'#f4a261',2:'#2a9d8f',3:'#e76f51',4:'#457b9d',5:'#aa66cc'};planes=[]
    for row,axis in enumerate([0,1,2]):
        other=[i for i in range(3) if i!=axis];spacing_zyx=list(reversed(pitch));aspect=spacing_zyx[other[0]]/spacing_zyx[other[1]];idx=centre[axis];ct=np.take(image,idx,axis=axis);labels=np.take(mask,idx,axis=axis);axes[row,0].imshow(ct,cmap='gray',vmin=-1000,vmax=1500,origin='lower',aspect=aspect);axes[row,1].imshow(ct,cmap='gray',vmin=-1000,vmax=1500,origin='lower',aspect=aspect)
        for label,color in colors.items():
            if (labels==label).any():axes[row,1].contour(labels==label,levels=[.5],colors=[color],linewidths=.8)
        for col in [0,1]:axes[row,col].set_xlabel('Original in-plane source index');axes[row,col].set_ylabel('Original in-plane source index')
        axes[row,0].set_title(f'Original CT: zyx axis {axis}, index {idx}\nWindow −1000..1500 source units\nHU calibration unverified');axes[row,1].set_title('Original source labels\nComponents and boundary contacts retained')
        planes.append({'array_normal_axis_zyx':axis,'source_index':idx,'source_samples_resampled':False,'display_pixel_aspect_from_declared_source_pitch':aspect})
    legend=' / '.join(str(k)+': '+v for k,v in LABELS.items());fig.suptitle('NasalSeg P001 source-grid review only\n0.586×0.586×1.5 mm declared sampling; region, not full thin-bone operative anatomy\n'+legend,fontsize=11);fig.subplots_adjust(hspace=.35,wspace=.25,top=.9,bottom=.07);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=120);plt.close(fig);proof={'file':out.name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'source_CT_sha256':hashlib.sha256((root/'P001/P001_img.nrrd').read_bytes()).hexdigest(),'source_mask_sha256':hashlib.sha256((root/'P001/P001_seg.nrrd').read_bytes()).hexdigest(),'planes':planes,'display_window_source_scalar_units':[-1000,1500],'source_resampling_or_registration':False,'source_mask_repair_filter_or_relabelling':False,'independent_anatomical_label_or_clinical_approval':False,'runtime_promoted':False};out.with_suffix('.json').write_text(json.dumps(proof,indent=2)+'\n');print(out)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();render(args.source_root,args.output)
