#!/usr/bin/env python3
"""Review original lobe labels in their supplied coarse CT grid, without repair."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import nibabel as nib
from scipy import ndimage
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt

NAMES=['lung_upper_lobe_left','lung_lower_lobe_left','lung_upper_lobe_right','lung_middle_lobe_right','lung_lower_lobe_right']
COLORS=['#38b8b6','#a66fdb','#e59f3b','#de5968','#74b747']


def review(root,output):
    output.mkdir(parents=True,exist_ok=True);acq=json.loads((root/'acquisition.json').read_text());sources={e['file']:e for e in acq['files']}
    images={}
    for name in ['ct.nii.gz',*[n+'.nii.gz' for n in NAMES],'trachea.nii.gz']:
        path=root/name
        if hashlib.sha256(path.read_bytes()).hexdigest()!=sources[name]['sha256']:raise ValueError('Source member changed')
        images[name]=nib.load(path)
    ct=images['ct.nii.gz'];occupancy=np.zeros(ct.shape,dtype=np.uint8);masks=[];records=[]
    for name in NAMES:
        image=images[name+'.nii.gz']
        if image.shape!=ct.shape or not np.array_equal(image.affine,ct.affine):raise ValueError('Coarse source grids differ')
        mask=np.asarray(image.dataobj)>0;masks.append(mask);occupancy+=mask
        coords=np.argwhere(mask);components,count=ndimage.label(mask)
        component_sizes=np.bincount(components.ravel())[1:]
        records.append({'source_label':name,'sha256':sources[name+'.nii.gz']['sha256'],'foreground_voxels':len(coords),
                        'source_components_6_connected':count,'component_voxel_sizes':component_sizes.tolist(),
                        'singleton_component_native_indices':[np.argwhere(components==int(component+1))[0].tolist() for component in np.flatnonzero(component_sizes==1)],
                        'native_foreground_bounds':[coords.min(0).tolist(),coords.max(0).tolist()],
                        'world_foreground_bounds':[nib.affines.apply_affine(ct.affine,coords).min(0).tolist(),nib.affines.apply_affine(ct.affine,coords).max(0).tolist()],
                        'positive_source_boundary_faces':sum(int(np.count_nonzero(mask.take(i,axis=a))) for a in range(3) for i in (0,-1))})
    total_coords=np.argwhere(occupancy>0);centre=((total_coords.min(0)+total_coords.max(0))/2).astype(int)
    # Representative native planes across the whole combined lung extent.
    plans=[(2,int(centre[2]),'Axial'),(1,int(centre[1]),'Coronal'),(0,int(centre[0]),'Sagittal')]
    figures={mode:plt.subplots(1,3,figsize=(15,6),layout='constrained') for mode in ['unmarked','labels']};planes=[]
    for column,(axis,index,title) in enumerate(plans):
        select=[slice(None)]*3;select[axis]=index;plane=np.asarray(ct.dataobj[tuple(select)]).T
        horizontal,vertical={2:(0,1),1:(0,2),0:(1,2)}[axis];x=ct.affine[horizontal,horizontal]*np.arange(ct.shape[horizontal])+ct.affine[horizontal,3];y=ct.affine[vertical,vertical]*np.arange(ct.shape[vertical])+ct.affine[vertical,3]
        if x[0]>x[-1] or y[0]>y[-1]:raise ValueError('Unexpected source display axes')
        extent=[x[0]-.75,x[-1]+.75,y[0]-.75,y[-1]+.75]
        for mode,(fig,axes) in figures.items():
            ax=axes[column];ax.imshow(plane,origin='lower',extent=extent,cmap='gray',vmin=-1000,vmax=400,interpolation='nearest')
            if mode=='labels':
                for mask,color in zip(masks,COLORS):
                    region=mask[tuple(select)].T
                    if region.any() and not region.all():ax.contour(x,y,region,levels=[.5],colors=[color],linewidths=.8)
            ax.set_title(f'{title} | index {index}\nRAS {"XYZ"[axis]}={ct.affine[axis,axis]*index+ct.affine[axis,3]:.1f} mm');ax.set_xlabel(f'RAS {"XYZ"[horizontal]} mm');ax.set_ylabel(f'RAS {"XYZ"[vertical]} mm')
        planes.append({'axis':axis,'index':index,'display_window':[-1000,400],'source_resampling':False})
    for mode,(fig,_) in figures.items():
        fig.suptitle('TotalSegmentator s0011 — supplied 1.5 mm source grid\n'+('LUL cyan / LLL purple / RUL orange / RML red / RLL green' if mode=='labels' else 'Unmarked source CT')+'\nCoarse lobe context only; no source branch, segment, wall or clinical accuracy approval',fontsize=12)
        fig.savefig(output/f's0011-lobe-{mode}.png',dpi=160,bbox_inches='tight');plt.close(fig)
    result={'source_doi':acq['source_doi'],'source_archive_sha256':acq['source_archive_sha256'],'ct_sha256':sources['ct.nii.gz']['sha256'],
            'shape':list(ct.shape),'spacing':[float(v) for v in ct.header.get_zooms()],'affine':ct.affine.tolist(),
            'lobes':records,'overlapping_lobe_voxels':int(np.count_nonzero(occupancy>1)),'combined_lobe_voxels':int(np.count_nonzero(occupancy)),
            'planes':planes,'source_data_changed':False,'clinical_approval':False,'runtime_promoted':False,
            'limits':'Same-case masks/CT only. Coarse source labels do not identify fissure thickness, bronchopulmonary segments or named bronchial branches. Label completeness, normality, original acquisition resolution and clinical anatomical accuracy are unproven.'}
    (output/'s0011-lobe-review.json').write_text(json.dumps(result,indent=2)+'\n');print('Overlapping source lobe voxels:',result['overlapping_lobe_voxels'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();review(args.source,args.output)
