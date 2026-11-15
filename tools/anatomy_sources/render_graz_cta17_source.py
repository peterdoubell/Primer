#!/usr/bin/env python3
"""Render unchanged native paired-lumen labels and their separate source-grid surfaces."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from tools.anatomy_sources.review_graz_cta17_source import OUTPUT,HASHES
from tools.anatomy_sources.review_avt_r6_source import read_nrrd

def render(root):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    import numpy as np
    proof_raw=(OUTPUT/'paired-lumen-source-review.json').read_bytes();proof=json.loads(proof_raw)
    raw=(root/'cta17s.nrrd').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=HASHES['cta17s.nrrd']:raise ValueError('Original CT differs')
    _,ct=read_nrrd(raw);masks={};arrays={}
    colours={'true':'#80ae80','false':'#d8654f'}
    for r in proof['records']:
        kind=r['lumen'];raw=(OUTPUT/(kind+'lumen17.seg.nrrd')).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=r['source_mask_sha256']:raise ValueError('Original mask differs')
        _,values=read_nrrd(raw);masks[kind]=values==r['source_label_value']
        pbytes=gzip.decompress((OUTPUT/(kind+'-positions.f64.gz')).read_bytes())
        tbytes=gzip.decompress((OUTPUT/(kind+'-triangles.u32.gz')).read_bytes())
        if hashlib.sha256(pbytes).hexdigest()!=r['positions_sha256'] or hashlib.sha256(tbytes).hexdigest()!=r['triangles_sha256']:raise ValueError('Native derivative arrays differ')
        arrays[kind]=(np.frombuffer(pbytes,'<f8').reshape(-1,3),np.frombuffer(tbytes,'<u4').reshape(-1,3))
    slices=[150,200,250,300,350,400]
    fig,axes=plt.subplots(2,3,figsize=(13,8.8))
    for ax,k in zip(axes.flat,slices):
        ax.imshow(ct[k],cmap='gray',vmin=-150,vmax=500,origin='lower',interpolation='nearest')
        for kind in ('true','false'):
            if masks[kind][k].any():ax.contour(masks[kind][k],levels=[.5],colors=[colours[kind]],linewidths=.7)
        ax.set_xlim(100,400);ax.set_ylim(110,410);ax.set_title(f'Original axial plane k={k}',fontsize=9)
        ax.set_xlabel('Native i (LPS −L)',fontsize=8);ax.set_ylabel('Native j (LPS −P)',fontsize=8)
    fig.suptitle('Graz cta17 · expert-source True Lumen (green, label 1) / False Lumen (red, label 2)',fontsize=12)
    fig.text(.02,.022,'Native CT display window −150..500 stored values; source labels unchanged. No independent DICOM calibration, flap/wall thickness, entry/re-entry or flow inference.',fontsize=8)
    fig.tight_layout(rect=(0,.075,1,.96));name='cta17-native-paired-ct-planes.png';fig.savefig(OUTPUT/name,dpi=180);plt.close(fig)
    fig=plt.figure(figsize=(12,9))
    bounds=np.concatenate([arrays[k][0] for k in arrays]);lo=bounds.min(0);hi=bounds.max(0);pad=(hi-lo)*.08
    for column,shown in enumerate([('true',),('false',),('true','false')],1):
        ax=fig.add_subplot(1,3,column,projection='3d')
        for kind in shown:
            positions,triangles=arrays[kind]
            ax.add_collection3d(Poly3DCollection(positions[triangles],facecolors=colours[kind],edgecolors='none',linewidths=0,alpha=1))
        ax.set_xlim(lo[0]-pad[0],hi[0]+pad[0]);ax.set_ylim(lo[1]-pad[1],hi[1]+pad[1]);ax.set_zlim(lo[2]-pad[2],hi[2]+pad[2])
        ax.set_box_aspect(hi-lo);ax.view_init(elev=12,azim=-65)
        ax.set_xticks(np.linspace(lo[0],hi[0],3));ax.set_yticks(np.linspace(lo[1],hi[1],3));ax.set_zticks(np.linspace(lo[2],hi[2],5))
        ax.tick_params(labelsize=7)
        ax.set_xlabel('R',labelpad=7);ax.set_ylabel('A',labelpad=7);ax.set_zlabel('S',labelpad=18)
        ax.set_title(' / '.join(k.capitalize()+' lumen' for k in shown),fontsize=10)
    fig.suptitle('cta17 · separate native-grid lumen isosurfaces, same patient frame',fontsize=12)
    fig.text(.02,.04,'All source components and voxel anisotropy retained; no merging, smoothing, decimation, fitting or invented flap. Colour denotes source labels, not tissue biology.',fontsize=8)
    fig.text(.02,.02,'Closed source-label boundaries are not complete vascular walls or haemodynamic models. Source thrombosed regions/entries are excluded or unlabelled; clinical review remains outstanding.',fontsize=8)
    fig.tight_layout(rect=(0,.15,1,.94));surface='cta17-separate-native-lumen-surfaces.png';fig.savefig(OUTPUT/surface,dpi=180);plt.close(fig)
    report={'source_review_sha256':hashlib.sha256(proof_raw).hexdigest(),'original_ct_sha256':HASHES['cta17s.nrrd'],
        'native_axial_plane_indices':slices,'stored_value_display_window':[-150,500],
        'source_masks_or_geometry_edited':False,'source_geometry_fitted_or_rescaled':False,
        'colour_camera_and_window_are_review_choices':True,'clinical_approval':False,'runtime_promoted':False,
        'images':[{'file':n,'sha256':hashlib.sha256((OUTPUT/n).read_bytes()).hexdigest()} for n in [name,surface]]}
    (OUTPUT/'render-review.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Rendered six native paired-label CT contexts and two separate unfitted source-grid lumen surfaces.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    render(p.parse_args().source_root)
