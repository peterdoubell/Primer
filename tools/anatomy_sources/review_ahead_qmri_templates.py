#!/usr/bin/env python3
"""Inspect native qMRI template grids and explicit source-label overlays."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import nibabel as nib
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection
from tools.anatomy_sources.audit_massp_mesh_voxels import section
from tools.anatomy_sources.massp_probability_mesh import load_verified


def review(root, atlas_root, output, mesh_root=None):
    output.mkdir(parents=True, exist_ok=True)
    acquisition = json.loads((root/'acquisition.json').read_text())
    atlas_source = json.loads((atlas_root/'acquisition.json').read_text())
    labels_image = load_verified(atlas_root,'ahead-massp2_avg-bestlabel_decade-18to80.nii.gz',atlas_source)
    labels = np.asarray(labels_image.dataobj)
    mesh_triangles={};mesh_manifest_digest=None
    if mesh_root:
        manifest_path=mesh_root/'surface-review.json';manifest=json.loads(manifest_path.read_text())
        if manifest['source_doi']!=atlas_source['doi'] or manifest['publisher_selection_file']!='ahead-massp2_avg-bestlabel_decade-18to80.nii.gz':
            raise ValueError('MRI comparison uses an unrelated model source')
        mesh_manifest_digest=hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        for row in manifest['records']:
            path=mesh_root/row['mesh_file']
            if hashlib.sha256(path.read_bytes()).hexdigest()!=row['mesh_sha256']:raise ValueError('Comparison mesh changed')
            with np.load(path) as mesh:mesh_triangles[row['label_id']]=mesh['vertices'][mesh['faces']]
        if set(mesh_triangles)!={9,10,11,12,38,39}:raise ValueError('Incomplete anatomical model comparison')
    prefix='native-qmri-joint' if mesh_root else 'native-qmri'
    planes=[(2,-3,'Axial'),(1,0,'Coronal'),(0,-20,'Sagittal left')]
    if mesh_root:planes.append((0,20,'Sagittal right'))
    records = []
    figures = {stat: plt.subplots(len(planes),3,figsize=(12,4*len(planes)),layout='constrained') for stat in ('med','iqr','med-unmarked')}
    colors = {9:'#bd39d4',10:'#bd39d4',11:'#1fe1a0',12:'#1fe1a0',38:'#ffad38',39:'#ffad38'}
    for entry in acquisition['files']:
        image = load_verified(root,entry['name'],acquisition)
        data = np.asarray(image.dataobj)
        affine = image.affine
        exact_grid = image.shape == labels_image.shape and np.array_equal(affine,labels_image.affine)
        record = {'source_file':entry['name'],'sha256':entry['sha256'],'shape':list(image.shape),
                  'affine':affine.tolist(),'qform_code':int(image.header['qform_code']),
                  'sform_code':int(image.header['sform_code']),'spatial_temporal_units':image.header.get_xyzt_units(),
                  'axis_codes':list(nib.aff2axcodes(affine)),'stored_dtype':str(data.dtype),
                  'exact_shape_and_affine_match_with_atlas':bool(exact_grid),
                  'nonfinite_voxels':int(np.count_nonzero(~np.isfinite(data))),
                  'finite_range':[float(np.nanmin(data)),float(np.nanmax(data))],
                  'clinical_registration_approval':False,'displayed_planes':[]}
        records.append(record)
        if not exact_grid or nib.aff2axcodes(affine) != ('R','P','S') or not np.allclose(affine[:3,:3],np.diag(np.diag(affine[:3,:3])),rtol=0,atol=1e-12):
            raise ValueError('Native planes do not support an unresampled source-label overlay')
        stat = 'med' if '_med_' in entry['name'] else 'iqr'
        contrast = next(c for c in ('r1map','r2map','qsmap') if '_'+c+'_' in entry['name'])
        column = ('r1map','r2map','qsmap').index(contrast)
        lo = np.floor(nib.affines.apply_affine(np.linalg.inv(affine),[-45,40,-25])).astype(int)
        hi = np.ceil(nib.affines.apply_affine(np.linalg.inv(affine),[45,-35,35])).astype(int)+1
        if np.any(lo<0) or np.any(hi>np.array(data.shape)):
            raise ValueError('Requested native review region outside source field')
        for row,(axis,value,title) in enumerate(planes):
            index = int(round((value-affine[axis,3])/affine[axis,axis]))
            selection=[slice(a,b) for a,b in zip(lo,hi)];selection[axis]=index
            plane=data[tuple(selection)].T; label_plane=labels[tuple(selection)].T
            horizontal,vertical={2:(0,1),1:(0,2),0:(1,2)}[axis]
            xcoords = affine[horizontal,horizontal]*np.arange(lo[horizontal],hi[horizontal])+affine[horizontal,3]
            ycoords = affine[vertical,vertical]*np.arange(lo[vertical],hi[vertical])+affine[vertical,3]
            if xcoords[0]>xcoords[-1]:
                plane=plane[:,::-1];label_plane=label_plane[:,::-1];xcoords=xcoords[::-1]
            if ycoords[0]>ycoords[-1]:
                plane=plane[::-1];label_plane=label_plane[::-1];ycoords=ycoords[::-1]
            finite=plane[np.isfinite(plane)];window=np.percentile(finite,[2,98])
            ax=figures[stat][1][row,column]
            ax.imshow(plane,origin='lower',extent=[xcoords[0]-.25,xcoords[-1]+.25,ycoords[0]-.25,ycoords[-1]+.25],cmap='gray',vmin=window[0],vmax=window[1],interpolation='nearest')
            model_section_counts={}
            if stat=='med':
                plain_ax=figures['med-unmarked'][1][row,column]
                plain_ax.imshow(plane,origin='lower',extent=[xcoords[0]-.25,xcoords[-1]+.25,ycoords[0]-.25,ycoords[-1]+.25],cmap='gray',vmin=window[0],vmax=window[1],interpolation='nearest')
                plain_ax.set_title(f'{title} | {contrast} med\nRAS {"XYZ"[axis]}={affine[axis,axis]*index+affine[axis,3]:.1f} mm')
                plain_ax.set_xlabel(f'RAS {"XYZ"[horizontal]} mm');plain_ax.set_ylabel(f'RAS {"XYZ"[vertical]} mm')
                for label,color in colors.items():
                    if mesh_root:
                        lines=section(mesh_triangles[label],axis,float(affine[axis,axis]*index+affine[axis,3]),horizontal,vertical)
                        model_section_counts[str(label)]=len(lines)
                        if len(lines):ax.add_collection(LineCollection(lines,colors=[color],linewidths=.8))
                    else:
                        mask=label_plane==label
                        if mask.any() and not mask.all():ax.contour(xcoords,ycoords,mask.astype(float),levels=[.5],colors=[color],linewidths=.8)
            ax.set_title(f'{title} | {contrast} {stat}\nRAS {"XYZ"[axis]}={affine[axis,axis]*index+affine[axis,3]:.1f} mm')
            ax.set_xlabel(f'RAS {"XYZ"[horizontal]} mm');ax.set_ylabel(f'RAS {"XYZ"[vertical]} mm')
            record['displayed_planes'].append({'axis':axis,'native_index':index,'ras_mm':float(affine[axis,axis]*index+affine[axis,3]),'native_roi_start':lo.tolist(),'native_roi_stop_exclusive':hi.tolist(),'display_window_percentiles':[2,98],'display_window_source_values':window.tolist(),'source_resampling':False,'direct_mesh_section_segments_by_label':model_section_counts})
        print(entry['name'],'native grid checked',flush=True)
    for stat,(fig,_) in figures.items():
        overlay_name='direct joint-model sections' if mesh_root else 'source best-label contours'
        fig.suptitle('AHEAD native '+('median qMRI with MASSP '+overlay_name+'\nGPi purple / GPe green / putamen amber' if stat=='med' else 'unmarked median qMRI' if stat=='med-unmarked' else 'qMRI interquartile ranges — source population variability')+'\nGroup templates, not individual MRI; shared grid does not prove clinical boundary accuracy',fontsize=13)
        fig.savefig(output/f'{prefix}-{stat}-review.png',dpi=160,bbox_inches='tight');plt.close(fig)
    report={'source_doi':acquisition['doi'],'atlas_doi':atlas_source['doi'],'records':records,'mesh_manifest_sha256':mesh_manifest_digest,'overlay_method':'Direct triangle/plane intersections in original RAS millimetres' if mesh_root else 'Source label-mask contour',
            'source_intensities_or_coordinates_changed':False,'runtime_binding_added':False,'clinical_approval':False,
            'limits':'105-subject qMRI group templates compared with 97-subject label atlas. Identical array grid and declared affine establish sampling correspondence only; independent source registration accuracy, individual anatomy and intensity units remain unverified.'}
    (output/(prefix+'-review.json')).write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--atlas-source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--mesh-source',type=Path)
    args=parser.parse_args();review(args.source,args.atlas_source,args.output,args.mesh_source)
