#!/usr/bin/env python3
"""Preserve a same-case CT/lobe source and derive unmodified 0.5 label interfaces."""
import argparse,gzip,hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import nibabel as nib
import numpy as np
from scipy import ndimage
from skimage.measure import marching_cubes
from tools.anatomy_sources.review_hvsmr2_pat7_source import read_nifti


def sha(raw):return hashlib.sha256(raw).hexdigest()


def package(source,output):
    acquisition=json.loads((source/'CT-acquisition.json').read_text());screen=json.loads((source/'mask-screen.json').read_text())
    if acquisition['case']!='s0028' or screen['case']!='s0028' or not acquisition['original_CT_member_CRC_verified']:
        raise ValueError('Explicit source case and original-member proof required')
    output.mkdir(parents=True,exist_ok=True);originals=output/'originals';surfaces=output/'surfaces';originals.mkdir(exist_ok=True);surfaces.mkdir(exist_ok=True)
    entries=[{'file':'ct.nii.gz','sha256':acquisition['CT']['sha256']}]+[{'file':r['label']+'.nii.gz','sha256':r['sha256']} for r in screen['labels']]
    grid=None;records=[];masks=[]
    for entry in entries:
        path=source/entry['file'];raw=path.read_bytes()
        if sha(raw)!=entry['sha256']:raise ValueError('Original source member changed')
        independent,A,header=read_nifti(path);image=nib.load(path);array=np.asarray(image.dataobj.get_unscaled())
        if not np.array_equal(array,independent) or not np.array_equal(A,image.affine):raise ValueError('Independent NIfTI readers disagree')
        if grid is None:grid=(array.shape,A)
        if array.shape!=grid[0] or not np.array_equal(A,grid[1]):raise ValueError('Source grids differ')
        shutil.copyfile(path,originals/entry['file']);row={'file':'originals/'+entry['file'],'sha256':entry['sha256'],'bytes':len(raw),'independent_reader_samples_exact':True,'independent_reader_affine_exact':True,'shape':list(array.shape),'affine':A.tolist(),'source_header':header}
        if entry['file']!='ct.nii.gz':
            if not set(np.unique(array))<={0,1}:raise ValueError('Mask is not binary')
            mask=array.astype(bool);masks.append(mask);components,n=ndimage.label(mask,ndimage.generate_binary_structure(3,1));coords=np.where(mask);bounds=[[int(a.min()),int(a.max())] for a in coords]
            v,f,_,_=marching_cubes(array,level=.5,allow_degenerate=True)
            v=v.astype(np.float64)
            world=np.column_stack([v[:,0]*A[i,0]+v[:,1]*A[i,1]+v[:,2]*A[i,2]+A[i,3] for i in range(3)]).astype('<f8');faces=f.astype('<u4')
            edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1);_,counts=np.unique(edges,axis=0,return_counts=True)
            name=entry['file'].removesuffix('.nii.gz');payloads={}
            for suffix,body in [('positions.f64.gz',world.tobytes()),('triangles.u32.gz',faces.tobytes())]:
                dest=surfaces/(name+'-'+suffix);encoded=gzip.compress(body,mtime=0);dest.write_bytes(encoded);assert gzip.decompress(dest.read_bytes())==body;payloads[suffix]={'file':str(dest.relative_to(output)),'sha256':sha(encoded),'decoded_sha256':sha(body),'decoded_bytes':len(body)}
            row.update(label=name,foreground_voxels=int(mask.sum()),components_6=int(n),bounds_voxel_xyz=bounds,touches_scan_boundary=any(lo==0 or hi==array.shape[i]-1 for i,(lo,hi) in enumerate(bounds)),vertices=len(world),triangles=len(faces),boundary_edges=int((counts==1).sum()),nonmanifold_edges=int((counts>2).sum()),world_bounds=[world.min(0).tolist(),world.max(0).tolist()],surfaces=payloads)
        records.append(row);print('Preserved',entry['file'],row.get('triangles','CT'),flush=True)
    overlaps=[int(np.logical_and(masks[i],masks[j]).sum()) for i in range(5) for j in range(i+1,5)]
    result={'source_case':'s0028','source_doi':'10.5281/zenodo.22688904','license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/','records':records,'pairwise_lobe_overlap_voxels':overlaps,'all_source_arrays_and_affines_preserved':True,'source_masks_relabelled_or_components_deleted':False,'derivation':'Full original masks, 0.5 Lewiner isosurfaces, original sform. No padding, smoothing, capping, decimation, fitting or component deletion.','source_dicom_HU_calibration_or_patient_orientation_independently_verified':False,'clinical_approval':False,'normal_anatomical_atlas_approval':False,'structure_coverage_granted':False,'runtime_promoted':False}
    (output/'source-review.json').write_text(json.dumps(result,indent=2)+'\n')
    for name in ['CT-acquisition.json','mask-screen.json','lung-mask-review.json','lung-source-correspondence.png']:shutil.copy2(source/name,output/name)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();package(a.source_root,a.output)
