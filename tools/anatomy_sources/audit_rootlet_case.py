"""Check source MRI grids, manual-rater labels and consensus without modifying them."""
from pathlib import Path
import hashlib,itertools,json
import numpy as np,nibabel as nib
from scipy import ndimage
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
ROOT=Path(__file__).resolve().parents[2];STAGE=ROOT/'.research/anatomy-sources/rootlets';OUT=ROOT/'docs/msk-rootlet-source-review'


def main():
    acquisition=json.loads((STAGE/'acquisition.json').read_text())
    for record in acquisition['files']:assert hashlib.sha256(Path(record['file']).read_bytes()).hexdigest()==record['sha256']
    folder=STAGE/'sub-amu02';image=nib.load(folder/'sub-amu02_T2w.nii.gz');assert image.header.get_xyzt_units()[0]=='mm';assert np.prod(image.shape)<20_000_000
    arrays={};headers={}
    for name in ['rater1','rater2','rater3','rater4','staple']:
        volume=nib.load(folder/f'sub-amu02_T2w_desc-{name}_label-rootlets_dseg.nii.gz');assert volume.shape==image.shape and volume.header.get_xyzt_units()[0]=='mm'
        affine_error=float(np.max(np.abs(volume.affine-image.affine)));assert affine_error<1e-5
        data=np.asanyarray(volume.dataobj);assert np.isfinite(data).all() and np.all(data==np.rint(data));assert set(np.unique(data))<=set([0,*range(2,10)]);arrays[name]=data.astype(np.uint8)
        headers[name]={'dtype':str(volume.get_data_dtype()),'qform_code':int(volume.header['qform_code']),'sform_code':int(volume.header['sform_code']),'selected_affine_max_difference_mm':affine_error,'labels':np.unique(data).astype(int).tolist()}
    rows=[]
    for label in range(2,10):
        masks={k:a==label for k,a in arrays.items()};counts={k:int(v.sum()) for k,v in masks.items()};pairs=[]
        for a,b in itertools.combinations(['rater1','rater2','rater3','rater4'],2):
            denominator=counts[a]+counts[b];pairs.append({'raters':[a,b],'dice':float(2*np.count_nonzero(masks[a]&masks[b])/denominator) if denominator else None})
        p=np.argwhere(masks['staple']);lo=p.min(0);hi=p.max(0);crop=masks['staple'][tuple(slice(a,b+1) for a,b in zip(lo,hi))];component_counts={}
        for connectivity in [1,3]:
            components,n=ndimage.label(crop,ndimage.generate_binary_structure(3,connectivity));component_counts[str(6 if connectivity==1 else 26)]=sorted(np.bincount(components.ravel())[1:].astype(int).tolist(),reverse=True)
        consensus_to_raters={k:float(2*np.count_nonzero(masks[k]&masks['staple'])/(counts[k]+counts['staple'])) if counts[k]+counts['staple'] else None for k in ['rater1','rater2','rater3','rater4']}
        rows.append({'label':label,'source_level':'C'+str(label) if label<=8 else 'T1','voxels':counts,'pairwise_manual_dice':pairs,'consensus_to_manual_dice':consensus_to_raters,'consensus_bounds_voxel':[lo.tolist(),hi.tolist()],'touches_volume_edge':bool(np.any(lo==0)|np.any(hi==np.asarray(image.shape)-1)),'consensus_component_voxels':component_counts})
    target=arrays['staple']>0;index=int(np.argmax(target.sum(axis=(0,2))));p=np.argwhere(target);lo=np.maximum(0,p.min(0)-8);hi=np.minimum(image.shape,p.max(0)+9);volume=np.asanyarray(image.dataobj);plane=volume[lo[0]:hi[0],index,lo[2]:hi[2]].T;window=list(map(float,np.percentile(plane,[1,99.5])));colors=np.array([plt.get_cmap('tab10').colors[i] for i in [0,1,2,3,4,5,6,9]]);fig,axes=plt.subplots(1,6,figsize=(13,8))
    for col,(name,ax) in enumerate(zip(['MRI','rater1','rater2','rater3','rater4','staple'],axes)):
        ax.imshow(plane,cmap='gray',origin='lower',interpolation='nearest',vmin=window[0],vmax=window[1]);ax.set_title('MRI only' if name=='MRI' else name);ax.set_axis_off()
        if name!='MRI':
            labels=arrays[name][lo[0]:hi[0],index,lo[2]:hi[2]].T;rgba=np.zeros((*labels.shape,4))
            for label in range(2,10):rgba[labels==label]=[*colors[label-2],.65]
            ax.imshow(rgba,origin='lower',interpolation='nearest')
        for x,y,t in [(.03,.5,'R'),(.97,.5,'L'),(.5,.98,'S'),(.5,.02,'I')]:ax.text(x,y,t,transform=ax.transAxes,color='#ffdf80',ha='center',va='center',fontsize=9)
    fig.legend([Patch(facecolor=colors[i]) for i in range(8)],['C2','C3','C4','C5','C6','C7','C8','T1'],loc='lower center',bbox_to_anchor=(.5,.11),ncol=8,frameon=False)
    fig.suptitle(f'Spine Generic sub-amu02 · native coronal-oriented T2w plane {index}',fontsize=14)
    fig.text(.5,.035,'Only labels intersecting this plane are shown. Same MRI window and plane in every panel.\nConsensus is STAPLE, not an independent manual rater. Label disagreement is retained; no smoothing, fitting or repair.\nSource: Spine Generic (10.5281/zenodo.4299140) / Valošek et al. (10.1162/imag_a_00218). CC BY 4.0 terms retained; metadata separately says CC0.',ha='center',fontsize=8)
    fig.tight_layout(rect=(0,.16,1,.95));fig.savefig(OUT/'manual-rater-mri-comparison.png',dpi=170);plt.close(fig)
    report={'source_acquisition_sha256':hashlib.sha256((STAGE/'acquisition.json').read_bytes()).hexdigest(),'case':'sub-amu02','shape':list(image.shape),'voxel_spacing_mm':list(map(float,image.header.get_zooms())),'axis_codes':list(nib.aff2axcodes(image.affine)),'image_affine':image.affine.tolist(),'headers':headers,'levels':rows,'review_plane':{'axis':1,'index':index,'crop_start':lo.tolist(),'crop_stop':hi.tolist(),'display_window':window},'label_scope_evidence':'Author issue 17 specifies dorsal C2–T1, value 2 for C2 and sequential levels. Snapshot sidecars retain older C2–C8 text; discrepancy retained.','limits':['Voxel overlap measures annotation agreement, not anatomical truth.','No left/right or dorsal/ventral instance subdivision inferred from one level label.','The supplied cord context mask is algorithm-generated according to its sidecar, not assumed manual ground truth.','Disc dlabels are landmarks, not disc tissue volumes.'],'clinical_approval':False,'runtime_promoted':False};(OUT/'case-and-rater-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Verified common grids:',image.shape,'spacing',image.header.get_zooms())
    for r in rows:print(r['source_level'],'consensus voxels',r['voxels']['staple'],'manual Dice range',[min(p['dice'] for p in r['pairwise_manual_dice']),max(p['dice'] for p in r['pairwise_manual_dice'])],'edge',r['touches_volume_edge'])


if __name__=='__main__':main()
