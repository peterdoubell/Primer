"""Compare native MRI with original contour control points, without fitting curves."""
from pathlib import Path
import json,hashlib,sys
import numpy as np,nibabel as nib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/msk-lumbosacral-nerve-source-review';STAGE=Path('/tmp/primer-msk-sources/lumbosacral2024')


def main():
    defaults='--default-curves' in sys.argv
    reconstructed=json.loads((OUT/'default-curve-reconstruction.json').read_text()) if defaults else None
    audit=json.loads((OUT/'cord-dura-contour-audit.json').read_text());annotations=json.loads((OUT/'annotation-and-image-audit.json').read_text());p=STAGE/'sub-03/sub-03_CISS.nii.gz';assert hashlib.sha256(p.read_bytes()).hexdigest()==audit['source_ciss_sha256'];image=nib.load(p);inv=np.linalg.inv(image.affine);records=[]
    fig,axes=plt.subplots(2,3,figsize=(14,9));limits=[]
    for col,index in enumerate([14,40,79]):
        selected={}
        for category in ['cord','dura']:
            row=next(r for r in audit['contours'] if r['category']==category and r['nearest_slice']==index);source=next(r for r in annotations['selected_case_annotations'] if r['member']==row['member']);assert source['sha256']==row['source_sha256'];xyz=nib.affines.apply_affine(inv,np.asarray(source['points_lps_mm'])*[-1,-1,1]);selected[category]=(row,xyz)
        all_points=np.concatenate([v[1] for v in selected.values()]);lo=np.maximum(0,np.floor(all_points[:,:2].min(0)-25).astype(int));hi=np.minimum(image.shape[:2],np.ceil(all_points[:,:2].max(0)+26).astype(int));plane=np.asanyarray(image.dataobj[:,:,index]);crop=plane[lo[0]:hi[0],lo[1]:hi[1]];window=list(map(float,np.percentile(crop,[1,99.5])))
        for row in range(2):
            ax=axes[row,col];ax.imshow(crop.T,cmap='gray',origin='lower',interpolation='nearest',vmin=window[0],vmax=window[1]);ax.set_axis_off();ax.set_title(f'Native CISS slice {index} · '+('MRI only' if row==0 else ('Fresh default reconstruction' if defaults else 'Original contour controls')))
            for x,y,text in [(.02,.5,'L'),(.98,.5,'R'),(.5,.98,'A'),(.5,.02,'P')]:ax.text(x,y,text,transform=ax.transAxes,color='#ffdf80',ha='center',va='center',fontsize=9)
            if row:
                for category,color in [('dura','#ffd96a'),('cord','#3ae2ff')]:
                    points=selected[category][1][:,:2]-lo;closed=np.vstack([points,points[0]]);ax.plot(closed[:,0],closed[:,1],color=color,lw=.7,linestyle='--');ax.scatter(points[:,0],points[:,1],s=9,c=color,label=category+' controls')
                    if defaults:
                        derived=next(r for r in reconstructed['curves'] if r['member']==selected[category][0]['member']);curve_path=ROOT/derived['file'];assert hashlib.sha256(curve_path.read_bytes()).hexdigest()==derived['sha256']
                        curve=np.load(curve_path)['default_curve_lps_mm'];projected=nib.affines.apply_affine(inv,curve*[-1,-1,1]);ax.plot(projected[:,0]-lo[0],projected[:,1]-lo[1],color=color,lw=1,label=category+' default')
                ax.legend(loc='lower left',fontsize=7,framealpha=.7)
        records.append({'native_slice':index,'crop_start':lo.tolist(),'crop_stop':hi.tolist(),'display_window':window,'contours':{k:{'member':v[0]['member'],'sha256':v[0]['source_sha256'],'points_voxel':v[1].tolist()} for k,v in selected.items()}})
    suffix='default-curve' if defaults else 'native-plane'
    fig.suptitle('Lumbosacral MRI sub-03 · cord and dura contour correspondence',fontsize=15)
    fig.text(.5,.025,('Solid curves: explicit fresh Slicer 5.4 default reconstruction, not proof of the original author settings. Dots: original controls.\n' if defaults else 'Dots are original control points; dashed lines are straight control polygons, not the unrecorded Slicer spline or a verified tissue boundary.\n')+'Slice 14 is the lowest supplied cord contour; slice 79 is the last native image plane. No anatomical tip or closed volume is inferred.\nLiu et al. (2024), Figshare collection 10.6084/m9.figshare.c.7372564 · CC BY 4.0. Crop, window and review overlays added.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.10,1,.95));fig.savefig(OUT/('cord-dura-'+suffix+'-review.png'),dpi=160);plt.close(fig)
    result={'source_ciss_sha256':audit['source_ciss_sha256'],'planes':records,'voxel_resampling':False,'display_interpolation':'nearest','curve_interpolation':('fresh Slicer 5.4 cardinal defaults; original author settings unproved' if defaults else 'straight control-polygon display only; not claimed as original interpolated curve'),'clinical_approval':False,'runtime_promoted':False};(OUT/('cord-dura-'+('default-' if defaults else '')+'review-planes.json')).write_text(json.dumps(result,indent=2)+'\n')
    print('Rendered source MRI and original contour controls at slices 14, 40 and 79.')


if __name__=='__main__':main()
