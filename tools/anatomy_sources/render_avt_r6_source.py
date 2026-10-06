#!/usr/bin/env python3
"""Show native CT/mask planes and unchanged derived mask surfaces without anatomical relabelling."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from tools.anatomy_sources.review_avt_r6_source import OUTPUT,CT_SHA,MASK_SHA,read_nrrd


def render(root):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    import numpy as np
    ct_raw=(root/'R6.nrrd').read_bytes();mask_raw=(root/'R6.seg.nrrd').read_bytes()
    if hashlib.sha256(ct_raw).hexdigest()!=CT_SHA or hashlib.sha256(mask_raw).hexdigest()!=MASK_SHA:raise ValueError('Source case differs')
    _,ct=read_nrrd(ct_raw);_,mask=read_nrrd(mask_raw)
    proof_raw=(OUTPUT/'native-source-review.json').read_bytes();proof=json.loads(proof_raw)
    pos_raw=gzip.decompress((OUTPUT/'mask-isosurface-positions.f64.gz').read_bytes());tri_raw=gzip.decompress((OUTPUT/'mask-isosurface-triangles.u32.gz').read_bytes())
    if hashlib.sha256(pos_raw).hexdigest()!=proof['derived_surface']['positions_sha256'] or hashlib.sha256(tri_raw).hexdigest()!=proof['derived_surface']['triangles_sha256']:raise ValueError('Derived source-mask arrays differ')
    positions=np.frombuffer(pos_raw,'<f8').reshape(-1,3);triangles=np.frombuffer(tri_raw,'<u4').reshape(-1,3)
    selected=[100,200,300,400,500,600,700,800,900,923,950,1000]
    fig,axes=plt.subplots(3,4,figsize=(14,12))
    for ax,k in zip(axes.flat,selected):
        ax.imshow(ct[k],cmap='gray',vmin=800,vmax=1600,origin='lower',interpolation='nearest')
        ax.contour(mask[k],levels=[.5],colors=['#ffb034'],linewidths=.55)
        ax.set_xlim(90,470);ax.set_ylim(105,410);ax.set_title(f'Native plane k={k} · source label pixels {int(mask[k].sum())}',fontsize=9)
        ax.set_xlabel('Native i (LPS +L)',fontsize=8);ax.set_ylabel('Native j (LPS +P)',fontsize=8)
    fig.suptitle('AVT R6 (source directory labelled AAA) · original CTA and binary aorta mask',fontsize=12)
    calibration='matched original HU transform; bolus timing unverified' if proof.get('ct_hu_calibration_verified') else 'HU/bolus timing unverified'
    fig.text(.015,.017,'Source contours at binary level 0.5; one combined label, manual/clinical QA unverified. Stored-value display 800..1600; '+calibration+'.',fontsize=8)
    fig.tight_layout(rect=(0,.05,1,.965));image='R6-native-ct-mask-planes.png';fig.savefig(OUTPUT/image,dpi=180);plt.close(fig)
    fig=plt.figure(figsize=(9,10));ax=fig.add_subplot(111,projection='3d');facets=positions[triangles]
    ax.add_collection3d(Poly3DCollection(facets,facecolors='#aabac5',edgecolors='none',linewidths=0))
    lo=positions.min(0);hi=positions.max(0);pad=(hi-lo)*.08
    ax.set_xlim(lo[0]-pad[0],hi[0]+pad[0]);ax.set_ylim(lo[1]-pad[1],hi[1]+pad[1]);ax.set_zlim(lo[2]-pad[2],hi[2]+pad[2]);ax.set_box_aspect(hi-lo)
    suffix=' (mm)' if proof.get('physical_space_units_independently_verified') else ''
    ax.set_xlabel('R'+suffix,labelpad=10);ax.set_ylabel('A'+suffix,labelpad=10);ax.set_zlabel('S'+suffix,labelpad=18);ax.view_init(elev=10,azim=-65)
    ax.set_title('R6 source-mask isosurface · full resolution\nFour source mask components retained; no caps, smoothing or splitting',fontsize=10)
    units='RAS mm from fully matched original DICOM.' if proof.get('physical_space_units_independently_verified') else 'RAS native units; physical calibration unverified.'
    fig.text(.02,.025,'Derived from the binary source mask, not original delivered geometry or independently reviewed anatomy.\nNo separate wall/lumen/thrombus/branch identities or clinical approval. '+units,fontsize=8)
    fig.tight_layout(rect=(0,.17,1,.98));surface='R6-source-mask-isosurface.png';fig.savefig(OUTPUT/surface,dpi=180);plt.close(fig)
    report={'native_source_review_sha256':hashlib.sha256(proof_raw).hexdigest(),'ct_sha256':CT_SHA,'mask_sha256':MASK_SHA,
        'native_slice_indices':selected,'display_window_stored_values':[800,1600],'view_limits_padding_fraction':.08,
        'ct_resampled':False,'mask_edited':False,'source_surface_edited_or_decimated':False,
        'camera_colour_and_window_are_review_choices':True,'independent_anatomical_validation':False,'clinical_approval':False,
        'images':[{'file':name,'sha256':hashlib.sha256((OUTPUT/name).read_bytes()).hexdigest()} for name in [image,surface]]}
    (OUTPUT/'render-review.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Rendered twelve native R6 CT/mask contexts and the complete unchanged mask-derived surface.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    render(p.parse_args().source_root)
