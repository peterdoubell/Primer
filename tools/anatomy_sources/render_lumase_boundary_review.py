"""Render native CT/mask planes at all six source crop boundaries."""
from pathlib import Path
import hashlib,json
import numpy as np
import nibabel as nib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap,BoundaryNorm
from matplotlib.patches import Patch
ROOT=Path(__file__).resolve().parents[2];DOC=ROOT/'docs/msk-vertebral-substructure-source-review'
def main():
 acquisition=json.loads((DOC/'lumase-case-acquisition.json').read_text());images=[]
 for entry in acquisition['files']:
  path=ROOT/entry['local_path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'];images.append(nib.load(path))
 assert images[0].shape==images[1].shape and np.array_equal(images[0].affine,images[1].affine)
 ct=np.asanyarray(images[0].dataobj);mask=np.asanyarray(images[1].dataobj);assert np.equal(mask,np.floor(mask)).all()
 spacing=np.array(images[0].header.get_zooms());axes=nib.aff2axcodes(images[0].affine);opposite={'L':'R','R':'L','P':'A','A':'P','S':'I','I':'S'}
 colors=['#00000000','#f6bd60','#84a59d','#f28482','#b8a5d1','#9fc8df','#f2c57c','#a3bf85'];cmap=ListedColormap(colors);norm=BoundaryNorm(np.arange(-.5,8),8)
 fig,plots=plt.subplots(6,3,figsize=(15,22));rows=[]
 for row,(axis,maximum) in enumerate((a,m) for a in range(3) for m in [False,True]):
  boundary=ct.shape[axis]-1 if maximum else 0;direction=-1 if maximum else 1;remaining=[a for a in range(3) if a!=axis];a,b=remaining
  face_mask=np.take(mask,boundary,axis=axis);labels,counts=np.unique(face_mask,return_counts=True)
  face={'axis':axis,'edge':'maximum' if maximum else 'minimum','boundary_slice':boundary,'label_counts':{str(int(v)):int(c) for v,c in zip(labels,counts) if v},'planes':[]}
  for column,offset in enumerate([0,1,4]):
   position=boundary+direction*offset;values=np.take(ct,position,axis=axis).T;labels=np.take(mask,position,axis=axis).T;plot=plots[row,column]
   origin='upper' if axes[b]=='P' else 'lower';aspect=spacing[b]/spacing[a]
   plot.imshow(values,cmap='gray',vmin=-200,vmax=1000,origin=origin,interpolation='nearest',aspect=aspect)
   plot.imshow(np.ma.masked_where(labels==0,labels),cmap=cmap,norm=norm,alpha=.38,origin=origin,interpolation='nearest',aspect=aspect)
   plot.set_title(('Native boundary' if offset==0 else str(offset)+' voxels inward')+' · '+['Sagittal','Coronal','Axial'][axis]+' '+str(position),fontsize=11)
   plot.set_xticks([]);plot.set_yticks([])
   plot.text(-.035,.5,opposite[axes[a]],transform=plot.transAxes,ha='right',va='center',color='#825a00')
   plot.text(1.035,.5,axes[a],transform=plot.transAxes,ha='left',va='center',color='#825a00')
   plot.text(.5,.96,opposite[axes[b]] if origin=='upper' else axes[b],transform=plot.transAxes,ha='center',color='#ffdf78',fontweight='bold')
   plot.text(.5,.015,axes[b] if origin=='upper' else opposite[axes[b]],transform=plot.transAxes,ha='center',color='#ffdf78',fontweight='bold')
   point=np.array([n//2 for n in ct.shape]);point[axis]=position
   face['planes'].append({'source_slice':position,'inward_offset_voxels':offset,'source_center_ras_mm':nib.affines.apply_affine(images[0].affine,point).tolist(),'display_physical_pixel_aspect':float(aspect),'visible_labels':list(map(int,np.unique(labels[labels>0])))})
  rows.append(face)
 fig.suptitle('LumASe original L3 · native CT / numeric-label crop boundaries',fontsize=17)
 fig.legend(handles=[Patch(facecolor=colors[i],label='Source label '+str(i)) for i in range(1,8)],loc='lower center',ncol=7,bbox_to_anchor=(.5,.045))
 fig.text(.5,.022,'Original labels retained. Numeric-to-anatomical meanings remain unverified. Boundary contact does not establish complete anatomical endpoints.\nNative planes; no source resampling, mask edits, filling or component removal. Display window −200 to 1000 scaled CT values.\nLiu et al. (2022), LumASe, doi:10.5281/zenodo.7181338, CC BY 4.0. Adaptation: native-plane display and numeric label overlays.',ha='center',fontsize=10)
 fig.subplots_adjust(top=.95,bottom=.085,left=.07,right=.93,hspace=.30,wspace=.20)
 out=DOC/'lumase-native-boundary-review.png';fig.savefig(out,dpi=150);plt.close(fig)
 report={'source_files':acquisition['files'],'faces':rows,'source_values_modified':False,'label_meanings_verified':False,'source_voxels_resampled':False,'clinical_approval':False,'runtime_promoted':False,'image':str(out.relative_to(ROOT)),'image_sha256':hashlib.sha256(out.read_bytes()).hexdigest()};(DOC/'lumase-native-boundary-review.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Rendered 18 native planes across all six crop faces; source labels unchanged.')
if __name__=='__main__':main()
