#!/usr/bin/env python3
"""Compare independent source raters on original arterial MRI without averaging labels."""
import argparse
import hashlib
import json
from pathlib import Path


def review(source_root,inventory_path,output):
    import numpy as np
    import nibabel as nib
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    inventory=json.loads(inventory_path.read_text());entries={r['filename']:r for r in inventory['records']}
    names=['art.nii.gz','rater1_liver.nii.gz','rater2_liver.nii.gz','rater1_tumor1.nii.gz','rater2_tumor1.nii.gz']
    images=[]
    for name in names:
        path=source_root/name
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entries[name]['sha256']:raise ValueError('Source case file changed')
        images.append(nib.load(path))
    arterial=images[0];volume=np.asanyarray(arterial.dataobj)
    if any(im.shape!=arterial.shape or not np.array_equal(im.affine,arterial.affine) for im in images[1:]):raise ValueError('Rater masks do not share arterial source geometry')
    if any(set(np.unique(np.asanyarray(im.dataobj)))!={0,1} for im in images[1:]):raise ValueError('Expected original binary rater masks')
    masks=[np.asanyarray(im.dataobj)>0 for im in images[1:]]
    rows=[]
    for roi,a,b in [('liver',masks[0],masks[1]),('tumor1',masks[2],masks[3])]:
        overlap=int(np.count_nonzero(a&b));aonly=int(np.count_nonzero(a&~b));bonly=int(np.count_nonzero(b&~a))
        rows.append({'roi':roi,'rater1_voxels':int(a.sum()),'rater2_voxels':int(b.sum()),'overlap_voxels':overlap,
                     'rater1_only_voxels':aonly,'rater2_only_voxels':bonly,'dice_rater_agreement':2*overlap/(int(a.sum())+int(b.sum())),
                     'rater_agreement_is_independent_anatomical_accuracy':False})
    tumour_points=np.argwhere(masks[2]|masks[3]);centre=np.rint(tumour_points.mean(0)).astype(int)
    # Union is used only to select a review centre; neither source mask is merged or exported as a new boundary.
    spacing=arterial.header.get_zooms()[:3];window=np.percentile(volume[np.isfinite(volume)],(2,98)).tolist()
    if nib.aff2axcodes(arterial.affine)!=('R','A','S') or not np.array_equal(arterial.affine[:3,:3],np.diag(spacing)):
        raise ValueError('Source direction needs separate physical display review')
    i,j,k=map(int,centre)
    x=arterial.affine[0,3]+np.arange(volume.shape[0])*spacing[0]
    y=arterial.affine[1,3]+np.arange(volume.shape[1])*spacing[1]
    z=arterial.affine[2,3]+np.arange(volume.shape[2])*spacing[2]
    def extent(horizontal,vertical,hs,vs):
        return [float(horizontal[-1]+hs/2),float(horizontal[0]-hs/2),float(vertical[0]-vs/2),float(vertical[-1]+vs/2)]
    views=[(volume[:,:,k].T[:,::-1],[m[:,:,k].T[:,::-1] for m in masks],'Axial',x[::-1],y,extent(x,y,spacing[0],spacing[1]),'RAS X mm (R → L)','RAS Y mm (P → A)'),
     (volume[:,j,:].T[:,::-1],[m[:,j,:].T[:,::-1] for m in masks],'Coronal',x[::-1],z,extent(x,z,spacing[0],spacing[2]),'RAS X mm (R → L)','RAS Z mm (I → S)'),
     (volume[i,:,:].T[:,::-1],[m[i,:,:].T[:,::-1] for m in masks],'Sagittal',y[::-1],z,extent(y,z,spacing[1],spacing[2]),'RAS Y mm (A → P)','RAS Z mm (I → S)')]
    figures=[];output.mkdir(parents=True,exist_ok=True)
    for name,indices,title in [('unmarked',[],'Unmarked original MRI'),('liver-raters',[0,1],'Independent liver raters'),('tumor-raters',[2,3],'Independent tumour raters')]:
        fig,axes=plt.subplots(1,3,figsize=(15,6))
        for ax,(pixels,planes,plane,horizontal,vertical,bounds,xlabel,ylabel) in zip(axes,views):
            ax.imshow(pixels,cmap='gray',vmin=window[0],vmax=window[1],interpolation='nearest',extent=bounds,aspect='equal',origin='lower')
            for index,colour in zip(indices,['#ecb453','#65b6dc']):
                mask=planes[index]
                if mask.any():ax.contour(horizontal,vertical,mask,levels=[.5],colors=[colour],linewidths=.8)
            ax.set_title(plane,fontsize=10);ax.set_xlabel(xlabel,fontsize=8);ax.set_ylabel(ylabel,fontsize=8)
        fig.suptitle(f'TCGA-BC-A3KG | original arterial T1 MRI | {title}\n'
                     'Original 1.406 × 1.406 × 2.5 mm sampling; rater 1 amber / rater 2 blue; no merged boundary or clinical approval',fontsize=11)
        fig.tight_layout(rect=(0,0,1,.88));path=output/(name+'.png');fig.savefig(path,dpi=150);plt.close(fig)
        figures.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rater_indices_overlaid':indices})
    result={'case_id':inventory['case_id'],'source_doi':inventory['source_doi'],'source_inventory_sha256':hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
      'source_arterial_sha256':entries['art.nii.gz']['sha256'],'original_index_axes':list(nib.aff2axcodes(arterial.affine)),
      'source_review_indices_ijk':centre.tolist(),'display_window_source_percentiles_2_98':window,'display_window_is_calibrated_measurement':False,
      'rater_comparisons':rows,'source_rater_masks_changed':False,'rater_boundaries_averaged':False,'source_voxels_resampled':False,
      'registered_derivatives_overlaid':False,'display_convention':'Explicit radiological horizontal order with physical RAS axes; source arrays unchanged','figures':figures,'clinical_approval':False,'runtime_promoted':False,
      'limits':['Difference counts quantify observer/source variability, not a reason to choose either rater as truth.',
                'Selected sections do not establish complete boundary accuracy or sequence/eligibility/treatment scope.',
                'A common arterial display window does not prove dynamic enhancement or washout.']}
    (output/'rater-review.json').write_text(json.dumps(result,indent=2)+'\n');print('Rater agreement:',[(r['roi'],r['dice_rater_agreement']) for r in rows])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case-root',type=Path,required=True);p.add_argument('--inventory',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();review(a.case_root,a.inventory,a.output)
