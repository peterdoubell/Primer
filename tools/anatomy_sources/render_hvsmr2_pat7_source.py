#!/usr/bin/env python3
"""Render retained native source masks and geometry without fitting or anatomy repairs."""
import argparse,gzip,json
from pathlib import Path
from tools.anatomy_sources.review_hvsmr2_pat7_source import read_nifti,OUTPUT,LABELS
COLORS=['#eb78ae','#467ee4','#61c6c6','#54b970','#e69b36','#ba72d9','#243cd1','#afb94a']
def render(root):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    image,A,_=read_nifti(root/'pat7_orig.nii.gz');mask,_,_=read_nifti(root/'pat7_orig_seg.nii.gz');optional,_,_=read_nifti(root/'pat7_orig_seg_endpoints.nii.gz')
    coords=np.argwhere(mask==7);centre=np.rint(np.median(coords,axis=0)).astype(int);low,high=np.percentile(image,[1,99.5]);fig,axs=plt.subplots(1,3,figsize=(15,6),layout='constrained')
    for axis,ax in enumerate(axs):
        plane=np.take(image,int(centre[axis]),axis=axis).T;labels=np.take(mask,int(centre[axis]),axis=axis).T;ends=np.take(optional,int(centre[axis]),axis=axis).T
        ax.imshow(plane,cmap='gray',vmin=low,vmax=high,origin='lower',interpolation='nearest')
        for label,color in zip(LABELS,COLORS):
            if (labels==label).any():ax.contour(labels==label,levels=[.5],colors=[color],linewidths=.65)
        if (ends>0).any():ax.contour(ends>0,levels=[.5],colors=['white'],linewidths=.7,linestyles='dashed')
        ax.set_title(f'Native index axis {axis}, slice {centre[axis]}');ax.set_xlabel('Original in-plane voxel index');ax.set_ylabel('Original in-plane voxel index')
    fig.suptitle('HVSMR-2.0 pat7: source MRI planes and original label contours\nWhite dashed = source optional zones; source index orientation retained, no new anatomy or temporal data',fontsize=13)
    fig.legend(handles=[Patch(color=c,label=f'{n}: {name}') for (n,name),c in zip(LABELS.items(),COLORS)],loc='outside lower center',ncol=4,fontsize=8)
    fig.savefig(OUTPUT/'pat7-native-mri-label-context.png',dpi=140);plt.close(fig)
    meshes=[]
    for label in LABELS:
        p=np.frombuffer(gzip.decompress((OUTPUT/f'label{label}-positions.f64.gz').read_bytes()),dtype='<f8').reshape(-1,3)
        f=np.frombuffer(gzip.decompress((OUTPUT/f'label{label}-triangles.u32.gz').read_bytes()),dtype='<u4').reshape(-1,3);meshes.append((label,p,f))
    allpoints=np.concatenate([p for _,p,_ in meshes]);lo=allpoints.min(0);hi=allpoints.max(0);fig=plt.figure(figsize=(15,7),layout='constrained')
    for number,(azim,title) in enumerate([(-75,'All 8 original source classes'),(115,'SVC source channels with faint atrial/arterial context')],1):
        ax=fig.add_subplot(1,2,number,projection='3d')
        for label,p,f in meshes:
            if number==2 and label not in [3,4,5,6,7,8]:continue
            alpha=1 if number==1 or label==7 else .1
            ax.add_collection3d(Poly3DCollection(p[f],facecolors=COLORS[label-1],edgecolors='none',alpha=alpha))
        ax.set_xlim(lo[0],hi[0]);ax.set_ylim(lo[1],hi[1]);ax.set_zlim(lo[2],hi[2]);ax.set_box_aspect(hi-lo);ax.view_init(elev=20,azim=azim)
        ax.set_xlabel('Source sform X');ax.set_ylabel('Source sform Y');ax.set_zlabel('Source sform Z');ax.set_title(title)
    fig.suptitle('Native mask-derived surfaces — no smoothing, fitting, decimation, padding or component deletion\nNIfTI-declared coordinates; optional/benchmark boundaries do not establish complete wall, valve, airway or venous anatomy',fontsize=12)
    fig.legend(handles=[Patch(color=c,label=f'{n}: {name}') for (n,name),c in zip(LABELS.items(),COLORS)],loc='outside lower center',ncol=4,fontsize=8)
    fig.savefig(OUTPUT/'pat7-source-bilateral-svc-surfaces.png',dpi=140);plt.close(fig)
    (OUTPUT/'render-review.json').write_text(json.dumps({'native_indices':centre.tolist(),'display_percentile_window':[float(low),float(high)],
        'source_voxels_modified':False,'source_surfaces_modified':False,'raster_figures_are_mesh_geometry':False,'clinical_approval':False},indent=2)+'\n')
    print('Two source MRI/model review worksheets rendered without source edits.')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);render(p.parse_args().source_root)
