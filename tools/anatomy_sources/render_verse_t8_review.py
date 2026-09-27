from pathlib import Path
import json,hashlib
import numpy as np,nibabel as nib
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path('/tmp/primer-msk-sources/verse/verse521');out=Path('docs/msk-verse-source-review')
ct=nib.load(root/'sub-verse521_dir-ax_ct.nii.gz');seg=nib.load(root/'sub-verse521_dir-ax_seg-vert_msk.nii.gz')
v=np.asanyarray(ct.dataobj);mask=np.asanyarray(seg.dataobj)
assert v.shape==mask.shape and np.isfinite(v).all()
points=np.argwhere(mask==15);lo=points.min(0);hi=points.max(0);center=((lo+hi)//2).astype(int);spacing=np.array(ct.header.get_zooms())
fig,axes=plt.subplots(3,3,figsize=(12,11),facecolor='white');records=[]
for row,axis in enumerate([2,0,1]):
 for col,fraction in enumerate([.25,.5,.75]):
  index=int(round(lo[axis]+fraction*(hi[axis]-lo[axis])));slices=[slice(max(0,int(lo[a])-12),min(v.shape[a],int(hi[a])+13)) for a in range(3)];slices[axis]=index
  im=v[tuple(slices)].T;binary=(mask[tuple(slices)]==15).T;remaining=[a for a in range(3) if a!=axis]
  ax=axes[row,col];ax.imshow(im,cmap='gray',vmin=-200,vmax=1000,origin='lower',interpolation='nearest',aspect=spacing[remaining[1]]/spacing[remaining[0]])
  if binary.any() and not binary.all():ax.contour(np.arange(binary.shape[1]),np.arange(binary.shape[0]),binary,levels=[.5],colors=['#00e5ff'],linewidths=.6)
  codes=nib.aff2axcodes(ct.affine);opposite={'L':'R','R':'L','A':'P','P':'A','S':'I','I':'S'}
  for x,y,text in [(.02,.5,opposite[codes[remaining[0]]]),(.98,.5,codes[remaining[0]]),(.5,.98,codes[remaining[1]]),(.5,.02,opposite[codes[remaining[1]]])]:
   ax.text(x,y,text,transform=ax.transAxes,color='#ffed80',ha='center',va='center',fontsize=9,bbox={'facecolor':'black','alpha':.65,'pad':1})
  ax.set_title(f"{'Axial' if axis==2 else 'Sagittal' if axis==0 else 'Coronal'} · voxel {index}");ax.set_axis_off();records.append({'axis':axis,'index':index,'crop':[[s.start,s.stop] if isinstance(s,slice) else s for s in slices]})
fig.suptitle('VerSe sub-verse521 · T8 (label 15) · CT and original segmentation boundary',fontsize=14)
fig.text(.5,.015,'Native voxel planes; nearest-neighbour display. Display range −200 to 1000 scaled CT values. Cyan: T8 only; adjacent levels remain visible.\nArray-axis orientation retained; this is source inspection, not clinical approval.',ha='center',fontsize=10)
fig.tight_layout(rect=(0,.06,1,.95));fig.savefig(out/'t8-orthogonal-review.png',dpi=170);plt.close(fig)
report={'case':'sub-verse521','label':15,'ct_voxel_range':[int(v.min()),int(v.max())],'ct_dtype':str(v.dtype),'ct_scaling':[float(ct.dataobj.slope),float(ct.dataobj.inter)],'mask_bounds':[lo.tolist(),hi.tolist()],'voxel_spacing_mm':spacing.tolist(),'planes':records,'display_range_scaled_ct_values':[-200,1000],'voxel_resampling':False,'display_interpolation':'nearest','contour_coordinates':'Explicit integer pixel centres, matching imshow; no half-pixel offset','clinical_approval':False}
(out/'t8-review-planes.json').write_text(json.dumps(report,indent=2)+'\n');print('CT fully decoded; saved nine native-plane comparisons.')
