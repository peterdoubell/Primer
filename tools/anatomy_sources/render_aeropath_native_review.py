#!/usr/bin/env python3
"""Render native CT/label sections without source resampling or anatomy approval."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import nibabel as nib
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt


def render(root,output):
    output.mkdir(parents=True,exist_ok=True);acquisition=json.loads((root/'acquisition.json').read_text())
    entries={x['name']:x for x in acquisition['files']};images={}
    for name,entry in entries.items():
        path=root/name
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:raise ValueError('Source bytes changed')
        images[name]=nib.load(path)
    ct=images['1_CT_HR.nii.gz'];air=images['1_CT_HR_label_airways.nii.gz'];lung=images['1_CT_HR_label_lungs.nii.gz']
    if any(i.shape!=ct.shape or not np.array_equal(i.affine,ct.affine) for i in (air,lung)):raise ValueError('CT/label grids differ')
    if nib.aff2axcodes(ct.affine)!=('L','P','S'):raise ValueError('Unexpected source storage axes')
    # Native selected planes; display flips change presentation only, not data.
    plans=[(2,400,'Axial'),(1,270,'Coronal'),(0,256,'Sagittal')]
    figures={key:plt.subplots(1,3,figsize=(15,6),layout='constrained') for key in ('unmarked','labels')};records=[]
    for column,(axis,index,title) in enumerate(plans):
        selection=[slice(None)]*3;selection[axis]=index
        plane=np.asarray(ct.dataobj[tuple(selection)]).T;am=np.asarray(air.dataobj[tuple(selection)]).T;lm=np.asarray(lung.dataobj[tuple(selection)]).T
        horizontal,vertical={2:(0,1),1:(0,2),0:(1,2)}[axis]
        x=ct.affine[horizontal,horizontal]*np.arange(ct.shape[horizontal])+ct.affine[horizontal,3]
        y=ct.affine[vertical,vertical]*np.arange(ct.shape[vertical])+ct.affine[vertical,3]
        if x[0]>x[-1]:x=x[::-1];plane=plane[:,::-1];am=am[:,::-1];lm=lm[:,::-1]
        if y[0]>y[-1]:y=y[::-1];plane=plane[::-1];am=am[::-1];lm=lm[::-1]
        step_x=abs(ct.affine[horizontal,horizontal]);step_y=abs(ct.affine[vertical,vertical]);extent=[x[0]-step_x/2,x[-1]+step_x/2,y[0]-step_y/2,y[-1]+step_y/2]
        for mode,(fig,axes) in figures.items():
            ax=axes[column];ax.imshow(plane,origin='lower',extent=extent,cmap='gray',vmin=-1000,vmax=400,interpolation='nearest')
            if mode=='labels':
                if am.any() and not am.all():ax.contour(x,y,am,levels=[.5],colors=['#f2bd46'],linewidths=.7)
                if lm.any() and not lm.all():ax.contour(x,y,lm,levels=[.5],colors=['#30b2bf'],linewidths=.7)
            ax.set_title(f'{title} | native index {index}\nRAS {"XYZ"[axis]}={ct.affine[axis,axis]*index+ct.affine[axis,3]:.1f} mm');ax.set_xlabel(f'RAS {"XYZ"[horizontal]} mm');ax.set_ylabel(f'RAS {"XYZ"[vertical]} mm')
        records.append({'axis':axis,'index':index,'ras_mm':float(ct.affine[axis,axis]*index+ct.affine[axis,3]),'display_window':[-1000,400],'airway_label_pixels':int(am.sum()),'combined_lung_label_pixels':int(lm.sum()),'source_resampling':False})
    for mode,(fig,_) in figures.items():
        fig.suptitle('AeroPath case 1 — native source CT '+('and annotation contours' if mode=='labels' else 'without annotations')+'\nSource case from a lung-pathology cohort; image/label accuracy and anatomical completeness not independently approved',fontsize=13)
        fig.savefig(output/f'case-1-native-{mode}.png',dpi=160,bbox_inches='tight');plt.close(fig)
    (output/'case-1-section-review.json').write_text(json.dumps({'source_dataset_doi':acquisition['source_dataset_doi'],'source_acquisition_sha256':hashlib.sha256((root/'acquisition.json').read_bytes()).hexdigest(),'planes':records,'clinical_approval':False,'source_voxel_values_changed':False,'limits':'Selected source sections only; binary contours do not supply wall/lobar/segmental definitions. Display window and flips are disclosed; no image resampling.'},indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();render(args.source,args.output)
