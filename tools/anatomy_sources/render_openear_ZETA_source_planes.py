#!/usr/bin/env python3
"""Show original native reconstructed microscopy and registered CBCT planes; no cross-modality resampling."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tools.anatomy_sources.decode_openear_ZETA_volumes import verified_memmap

def render(root,proof_dir,out):
    proof_path=proof_dir/'ZETA-original-volume-readback.json';proof=json.loads(proof_path.read_text());volumes=proof['volumes'];figure,axes=plt.subplots(3,3,figsize=(15,15));planes=[]
    # Native nearest planes around the ossicular source region; actual world locations retained.
    world=np.array([26.,22.,32.]);modes=[('Reconstructed microscopy','04_Reconstruction_Microslicing/Microslicing_Zeta.nrrd'),('Embedded registered CBCT','05_Registred_Slicer_Volumes/CBCT_Embedded.nrrd'),('Unembedded registered CBCT','05_Registred_Slicer_Volumes/CBCT_Unembedded.nrrd')]
    for col,(title,member) in enumerate(modes):
        record=next(v for v in volumes if v['member']==member);path=root/'ZETA-volume-review'/(Path(member).name+'.raw');data=verified_memmap(path,record);A=np.array(record['equivalent_RAS_affine']);inverse=np.linalg.inv(A);indices=np.rint((inverse@np.r_[world,1])[:3]).astype(int);pitch=np.linalg.norm(A[:3,:3],axis=0);rows=[]
        for axis,index in enumerate(indices):
            array_axis=2-axis;plane=np.take(data,index,axis=array_axis);other=[x for x in range(3) if x!=axis];ax=axes[axis,col]
            # Array is z,y,x[,vector]. After slicing the remaining spatial axes are reversed.
            if data.ndim==4:ax.imshow(plane,origin='lower',aspect=pitch[other[1]]/pitch[other[0]])
            else:
                window=np.percentile(plane,[5,99.5]).tolist();ax.imshow(plane,cmap='gray',origin='lower',vmin=window[0],vmax=window[1],aspect=pitch[other[1]]/pitch[other[0]])
            actual=float(A[axis,axis]*index+A[axis,3]);ax.set_title(f'{title}\nOriginal xyz axis {axis}, index {index}; RAS location {actual:.5f}',fontsize=10);ax.set_xlabel('Original in-plane sample index');ax.set_ylabel('Original in-plane sample index')
            rows.append({'source_axis_xyz':axis,'source_index':int(index),'actual_declared_RAS_plane_coordinate':actual,'display_pixel_aspect':float(pitch[other[1]]/pitch[other[0]]),'source_samples_resampled_or_geometry_fitted':False,'source_window_units_not_verified_HU':data.ndim!=4,'display_window_source_units':window if data.ndim!=4 else None})
        planes.append({'source_member':member,'native_planes':rows,'source_original_colour_values_preserved':data.ndim==4})
    figure.suptitle('OpenEar ZETA original source planes — specimen preparation and reconstructed colour retained\nEach view uses its own native grid; nearest planes are not identical physical planes\nNo new registration, resampling or colour enhancement; CBCT sampling is not original acquisition resolution',fontsize=13);figure.tight_layout(rect=[0,0,1,.91]);out.parent.mkdir(parents=True,exist_ok=True);figure.savefig(out,dpi=120,bbox_inches='tight');plt.close(figure)
    result={'source_volume_readback_sha256':hashlib.sha256(proof_path.read_bytes()).hexdigest(),'file':out.name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'native_source_planes':planes,
        'new_registration_resampling_smoothing_or_colour_enhancement':False,'unembedded_registered_sampling_is_not_original_native_resolution':True,'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False}
    (proof_dir/'ZETA-source-plane-display-review.json').write_text(json.dumps(result,indent=2)+'\n');print(out)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--proof-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();render(a.source_root,a.proof_dir,a.output)
