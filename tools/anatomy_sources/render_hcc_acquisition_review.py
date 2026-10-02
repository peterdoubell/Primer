#!/usr/bin/env python3
"""Show separate original HCC acquisitions without phase inference or mask overlay."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.anatomy_sources.review_tcia_lung_case import read_series
from tools.anatomy_sources.audit_hcc_source_acquisitions import acquisition_groups


def render(root,audit_path,output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    proof=json.loads(audit_path.read_text());path=root/'hcc-003-multiphase.zip'
    if hashlib.sha256(path.read_bytes()).hexdigest()!=proof['contrast_archive_sha256']:raise ValueError('Source CT changed')
    groups=acquisition_groups(read_series(path));fig,axes=plt.subplots(len(groups),3,figsize=(15,9),squeeze=False)
    rows=[]
    for row,(number,images) in enumerate(sorted(groups.items())):
        positions=np.asarray([d.ImagePositionPatient for d in images],float)
        if not np.allclose(np.diff(positions,axis=0),[0,0,2.5],rtol=0,atol=1e-9):raise ValueError('Unsupported source section geometry')
        if any(list(map(float,d.ImageOrientationPatient))!=[1,0,0,0,1,0] or list(map(float,d.PixelSpacing))!=[.703125,.703125] for d in images):raise ValueError('Source orientation/spacing changed')
        volume=np.stack([d.pixel_array.astype(float)*float(d.RescaleSlope)+float(d.RescaleIntercept) for d in images])
        if not np.isfinite(volume).all():raise ValueError('Nonfinite source CT')
        z,y,x=[n//2 for n in volume.shape];spacing=list(map(float,images[0].PixelSpacing))
        if volume.shape!=(95,512,512):raise ValueError('Unexpected source dimensions')
        views=[(volume[z],spacing[0]/spacing[1],'Axial',z),(volume[:,y,:],2.5/spacing[1],'Coronal',y),(volume[:,:,x],2.5/spacing[0],'Sagittal',x)]
        for ax,(pixels,aspect,name,index) in zip(axes[row],views):
            ax.imshow(pixels,cmap='gray',vmin=-160,vmax=240,origin='upper' if name=='Axial' else 'lower',interpolation='nearest',aspect=aspect)
            ax.set_title(f'Acquisition {number} | {name} native index {index}',fontsize=10);ax.set_xticks([]);ax.set_yticks([])
        rows.append({'source_acquisition_number':number,'native_shape_zyx':list(volume.shape),'selected_indices_zyx':[z,y,x],
                     'phase_name':None,'rescale_slopes':sorted({float(d.RescaleSlope) for d in images}),
                     'rescale_intercepts':sorted({float(d.RescaleIntercept) for d in images})})
    fig.suptitle('HCC_003 | two separate source CT acquisitions, identical grid indices\n'
                 'Unmarked source pixels; phase identity and anatomical cross-acquisition registration unresolved',fontsize=12)
    fig.tight_layout(rect=(0,0,1,.93));output.mkdir(parents=True,exist_ok=True)
    name='hcc-003-separate-acquisition-ct.png';fig.savefig(output/name,dpi=150);plt.close(fig)
    result={'case_id':'HCC_003','source_doi':proof['source_doi'],'source_acquisition_audit_sha256':hashlib.sha256(audit_path.read_bytes()).hexdigest(),
            'source_ct_archive_sha256':proof['contrast_archive_sha256'],'figure_sha256':hashlib.sha256((output/name).read_bytes()).hexdigest(),
            'acquisitions':rows,'display_window':[-160,240],'source_resampling':False,'source_voxels_changed':False,
            'phase_names_assigned':False,'mask_or_model_overlaid':False,'clinical_approval':False,'runtime_promoted':False,
            'limits':'Same numeric indices are not validated anatomical correspondence. These central views do not prove whole lesion extent, enhancement, phase identity or SEG registration.'}
    (output/'hcc-003-separate-acquisition-view-review.json').write_text(json.dumps(result,indent=2)+'\n');print('Rendered separate source acquisitions:',list(groups))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--audit',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();render(a.source_root,a.audit,a.output)
