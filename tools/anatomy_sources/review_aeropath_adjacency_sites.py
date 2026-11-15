#!/usr/bin/env python3
"""Review original CT/label patches at recorded topology-sensitive sites."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import nibabel as nib
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt


def review(root,locations,output):
    output.mkdir(parents=True,exist_ok=True);acq=json.loads((root/'acquisition.json').read_text());evidence=json.loads((locations/'adjacency-review.json').read_text())
    path=locations/'adjacency-dependent-cubes.npz'
    if hashlib.sha256(path.read_bytes()).hexdigest()!=evidence['location_array_sha256']:raise ValueError('Candidate locations changed')
    with np.load(path) as arrays:origins=arrays['native_origins'].copy();codes=arrays['configuration_codes'].copy()
    images=[]
    for name in ('1_CT_HR.nii.gz','1_CT_HR_label_airways.nii.gz'):
        path=root/name;entry=next(e for e in acq['files'] if e['name']==name)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:raise ValueError('Original source changed')
        images.append(nib.load(path))
    ct,labels=images
    if ct.shape!=labels.shape or not np.array_equal(ct.affine,labels.affine):raise ValueError('Original grids differ')
    plane_values,plane_counts=np.unique(origins[:,2],return_counts=True)
    top_planes=plane_values[np.argsort(-plane_counts)[:3]]
    chosen=[]
    for z in top_planes:
        indices=np.flatnonzero(origins[:,2]==z);chosen.append(int(indices[0]))
        if len(indices)>1:chosen.append(int(indices[-1]))
    fig,axes=plt.subplots(len(chosen),2,figsize=(9,3*len(chosen)),layout='constrained');records=[]
    for row,index in enumerate(chosen):
        origin=origins[index];lo=np.maximum(origin-6,0);hi=np.minimum(origin+8,np.array(ct.shape));z=int(origin[2])
        selection=(slice(lo[0],hi[0]),slice(lo[1],hi[1]),z)
        raw=np.asarray(ct.dataobj[selection]).T;mask=np.asarray(labels.dataobj[selection]).T
        x=ct.affine[0,0]*np.arange(lo[0],hi[0])+ct.affine[0,3];y=ct.affine[1,1]*np.arange(lo[1],hi[1])+ct.affine[1,3]
        if x[0]>x[-1]:x=x[::-1];raw=raw[:,::-1];mask=mask[:,::-1]
        if y[0]>y[-1]:y=y[::-1];raw=raw[::-1];mask=mask[::-1]
        half_x=abs(ct.affine[0,0])/2;half_y=abs(ct.affine[1,1])/2;extent=[x[0]-half_x,x[-1]+half_x,y[0]-half_y,y[-1]+half_y]
        for column in range(2):
            ax=axes[row,column];ax.imshow(raw,origin='lower',extent=extent,cmap='gray',vmin=-1000,vmax=400,interpolation='nearest')
            if column:
                if mask.any() and not mask.all():ax.contour(x,y,mask,levels=[.5],colors=['#f3b943'],linewidths=.9)
                point=nib.affines.apply_affine(ct.affine,origin+.5);ax.plot(point[0],point[1],'r+',markersize=8)
            ax.set_title(f'Native cube {origin.tolist()} | code {int(codes[index])}\n'+('source annotation + projected cube centre' if column else 'unmarked source CT'))
            ax.set_xlabel('RAS X mm');ax.set_ylabel('RAS Y mm')
        support=tuple(slice(int(a),int(a)+2) for a in origin)
        records.append({'native_cube_origin':origin.tolist(),'configuration_code':int(codes[index]),'ct_patch_xy_start':lo[:2].tolist(),'ct_patch_xy_stop_exclusive':hi[:2].tolist(),'displayed_native_z':z,'marker_basis':'3D source cube centre projected onto the displayed base-Z plane' ,'native_label_cube_xyz':np.asarray(labels.dataobj[support]).astype(int).tolist(),'native_ct_cube_xyz':np.asarray(ct.dataobj[support]).tolist(),'display_window':[-1000,400],'source_resampling':False})
    fig.suptitle('AeroPath case 1 — representative adjacency-sensitive native sites\nCandidate-site review only; no artefact/diagnosis/repair determination',fontsize=12)
    fig.savefig(output/'case-1-adjacency-source-patches.png',dpi=160,bbox_inches='tight');plt.close(fig)
    result={'source_dataset_doi':acq['source_dataset_doi'],'complete_candidate_sites':len(origins),'selection':'First and last indexed cube in each of the three most populated native-Z candidate planes; full location array retained separately','selected_records':records,'source_voxels_changed':False,'clinical_approval':False,'limits':'Native CT and 2x2x2 source label data at selected sites. A selected axial patch does not establish complete 3D local topology, clinical cause or correspondence with a specific surface handle.'}
    (output/'case-1-adjacency-site-review.json').write_text(json.dumps(result,indent=2)+'\n');print('Native sites reviewed:',len(records))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--locations',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();review(args.source,args.locations,args.output)
