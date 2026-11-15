#!/usr/bin/env python3
"""Review actual same-case CT and every original selected annotation; preserve all source surfaces."""
import argparse,gzip,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import nibabel as nib,numpy as np
from scipy import ndimage
from skimage.measure import marching_cubes
from tools.anatomy_sources.review_hvsmr2_pat7_source import read_nifti

def sha(raw):return hashlib.sha256(raw).hexdigest()
def review(source,out):
    out.mkdir(parents=True,exist_ok=True);a=json.loads((source/'acquisition.json').read_text());records=[];targets=[];reference=None
    for row in a['records']:
        path=source/row['file'];raw=path.read_bytes()
        if sha(raw)!=row['sha256']:raise ValueError('Original acquired member changed')
        array,A,h=read_nifti(path);independent=nib.load(path)
        if not np.array_equal(array,independent.dataobj.get_unscaled()) or not np.allclose(A,independent.affine,rtol=0,atol=1e-7):raise ValueError('Independent sample/transform check differs')
        if reference is None:reference=(array.shape,A)
        if array.shape!=reference[0] or not np.array_equal(A,reference[1]):raise ValueError('Same-case declared grids differ')
        records.append({'file':row['file'],'source_file_sha256':sha(raw),'all_original_samples_match_independent_reader':True,**h})
        if row['file']=='ct.nii.gz':continue
        if not set(np.unique(array)).issubset({0,1}):raise ValueError('Original annotation is not binary')
        mask=array!=0;components,count=ndimage.label(mask,ndimage.generate_binary_structure(3,1));sizes=np.bincount(components.ravel())[1:];locations=np.where(mask);bounds=[[int(x.min()),int(x.max())] for x in locations] if mask.any() else None
        target={'file':row['file'],'foreground_voxels':int(mask.sum()),'components_6_connected':int(count),'component_sizes_descending':sorted(sizes.tolist(),reverse=True),'native_bounds_xyz_inclusive':bounds,'source_volume_boundary_axes':[i for i,x in enumerate(bounds or []) if x[0]==0 or x[1]==mask.shape[i]-1],'source_components_deleted_or_repaired':False}
        if mask.any():
            vertices,faces,_,_=marching_cubes(mask.astype(np.uint8),level=.5,allow_degenerate=True);positions=vertices.astype(np.float64)@A[:3,:3].T+A[:3,3];edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1);_,counts=np.unique(edges,axis=0,return_counts=True)
            p=positions.astype('<f8').tobytes();f=faces.astype('<u4').tobytes();stem=row['file'].removesuffix('.nii.gz')
            for suffix,data in [('positions.f64.gz',p),('triangles.u32.gz',f)]:
                destination=out/(stem+'-'+suffix);destination.write_bytes(gzip.compress(data,mtime=0))
                if gzip.decompress(destination.read_bytes())!=data:raise ValueError('Derived geometry write/readback differs')
            target.update(vertices=len(vertices),triangles=len(faces),positions_sha256=sha(p),triangles_sha256=sha(f),boundary_edges=int((counts==1).sum()),nonmanifold_edges=int((counts>2).sum()),world_bounds=np.stack([positions.min(0),positions.max(0)]).tolist())
        targets.append(target);del components,array,mask,locations
    result={'source_doi':a['source_doi'],'actual_dataset_license':a['actual_dataset_license'],'case':a['case'],'source_acquisition_sha256':sha((source/'acquisition.json').read_bytes()),'source_metadata_rows':a['source_metadata_rows'],'original_files':records,'all_selected_source_grids_identical':True,'source_axes':list(nib.aff2axcodes(reference[1])),'targets':targets,'derivation':'Full original selected binary masks; 0.5 Lewiner isosurfaces transformed only by original sform. No source padding, fitting, smoothing, decimation, class merging or deletion of original components. Boundary openings remain source coverage limits.',
        'single_thyroid_class_independently_identifies_lobes_isthmus_capsule_internal_nodules_or_every_interface':False,'source_CT_annotations_supply_US_echogenicity_Doppler_or_matched_published_US_cases':False,'native_DICOM_physical_calibration_contrast_phase_or_tiny_wall_resolution_verified':False,'source_study_type_is_dedicated_neck_CT':False,'clinical_approval':False,'structure_coverage_granted':False,'runtime_promoted':False}
    (out/'native-source-review.json').write_text(json.dumps(result,indent=2)+'\n');(out/'original-acquisition.json').write_bytes((source/'acquisition.json').read_bytes());print('Nine original arrays independently checked; eight source annotation surfaces retained',[(x['file'],x.get('triangles',0),x['source_volume_boundary_axes']) for x in targets])
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--proof-dir',type=Path,required=True);a=p.parse_args();review(a.source_root,a.proof_dir)
