import hashlib,json,re,gc
from pathlib import Path
import nibabel as nib
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt

def review(root, out):
    out.mkdir(parents=True, exist_ok=True)
    acq=json.loads((root/'acquisition.json').read_text()); records=[]
    fig,axs=plt.subplots(4,3,figsize=(13,15),layout='constrained');axes=iter(axs.flat)
    ref_affine=None
    for e in acq['files']:
     if not e['name'].startswith('proba_'):continue
     p=root/e['name'];raw=p.read_bytes()
     if hashlib.sha256(raw).hexdigest()!=e['sha256']:raise ValueError('Source hash changed')
     image=nib.load(p);arr=np.asarray(image.dataobj)
     if not np.isfinite(arr).all() or arr.min()<0 or arr.max()>1:raise ValueError('Invalid probability source')
     q,qcode=image.get_qform(coded=True);s,scode=image.get_sform(coded=True)
     if not scode:raise ValueError('No declared sform')
     if qcode and not np.allclose(q,s,rtol=0,atol=1e-5):raise ValueError('Conflicting declared affines')
     if not np.array_equal(image.affine,s):raise ValueError('Reader did not use declared sform')
     if ref_affine is None:ref_affine=image.affine
     elif not np.array_equal(ref_affine,image.affine):raise ValueError('Source grids differ')
     coords=np.argwhere(arr>0);lo=coords.min(0);hi=coords.max(0);nz=arr[tuple(coords.T)]
     world=nib.affines.apply_affine(image.affine,coords)
     weights=nz.astype('float64');center=np.average(world,axis=0,weights=weights)
     code,side=re.search(r'avg-(\w+)_hem-([lr])_',e['name']).groups()
     counts={str(t):int(np.count_nonzero(arr>=t)) for t in (.1,.25,.5,.75,.9)}
     record={'source_file':e['name'],'sha256':e['sha256'],'shape':list(image.shape),'stored_dtype':str(arr.dtype),'voxel_size_mm':[float(x) for x in image.header.get_zooms()], 'units':image.header.get_xyzt_units(),'axis_codes':list(nib.aff2axcodes(image.affine)),'affine':image.affine.tolist(),'qform_code':int(qcode),'sform_code':int(scode),'qform_sform_agree':True if qcode else None,'affine_basis':'declared source sform; qform absent' if not qcode else 'consistent declared qform and sform','range':[float(arr.min()),float(arr.max())],'nonzero_voxels':len(coords),'nonzero_world_bounds_mm':[world.min(0).tolist(),world.max(0).tolist()],'probability_weighted_centroid_ras_mm':center.tolist(),'threshold_voxel_counts':counts,'wrong_side_nonzero_voxels':int(np.count_nonzero(world[:,0]>0 if side=='l' else world[:,0]<0)),'wrong_side_probability_peak':float(nz[world[:,0]>0 if side=='l' else world[:,0]<0].max()) if np.any(world[:,0]>0 if side=='l' else world[:,0]<0) else 0,'clinical_approval':False}
     z=int(np.rint(np.average(coords[:,2],weights=weights))); x0,y0=np.maximum(lo[:2]-5,0);x1,y1=np.minimum(hi[:2]+6,arr.shape[:2]); ax=next(axes);extent=[image.affine[0,0]*(x0-.5)+image.affine[0,3],image.affine[0,0]*(x1-.5)+image.affine[0,3],image.affine[1,1]*(y1-.5)+image.affine[1,3],image.affine[1,1]*(y0-.5)+image.affine[1,3]]
     im=ax.imshow(arr[x0:x1,y0:y1,z].T,origin='upper',extent=extent,cmap='magma',vmin=0,vmax=1,interpolation='nearest');ax.set_title(f'{code.upper()} {side.upper()} | RAS Z={image.affine[2,2]*z+image.affine[2,3]:.1f} mm');ax.set_xlabel('RAS X (mm)');ax.set_ylabel('RAS Y (mm)');record['displayed_native_slice_index']=z;records.append(record)
     del arr,coords,world,weights;gc.collect()
    fig.suptitle('MASSP 2.0 native probability maps — independently chosen axial slices\n0–1 probability, not acquired MRI intensity; RAS coordinates, no resampling',fontsize=14)
    fig.colorbar(im,ax=list(axs.flat),label='Across-subject probability',shrink=.5)
    fig.savefig(out/'native-probability-slices.png',dpi=160);plt.close(fig)
    if len(records)!=12:raise ValueError('Incomplete source map review')
    summary={'source_acquisition':'docs/brain-massp-source-review/acquisition.json','source_grid':'MNI2009b as stated by publisher; no assumed registration to BodyParts3D','native_axis_codes':['R','P','S'],'source_probability_values_unchanged':True,'records':records,'display_changes':'Native axial slice selection and probability colour mapping only; no interpolation/resampling/smoothing or mesh extraction','clinical_approval':False,'runtime_binding_added':False}
    (out/'native-probability-review.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('Reviewed',len(records),'probability maps')


if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser(description="Review native MASSP probability grids without resampling or runtime changes")
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    review(args.source,args.output)
