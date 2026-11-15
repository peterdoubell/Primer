"""Complete ISLES'22 case0140 arrays and literal expert-mask voxel cell boundaries.

No sample resampling, smoothing, anatomy labels, pathology approval or current-patient
registration is introduced. Source geometry follows every original occupied cell.
The ISLES-specific publication entry point is withdrawn after inspection of the
archive's conflicting redistribution terms. Authored geometry helpers remain
available for independently cleared sources; historical evidence is offline.
"""
from pathlib import Path
import gzip
import hashlib
import json
import struct
import nibabel as nib
import numpy as np
from scipy import ndimage

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'web/anatomy/isles22-case0140'
REVIEW=ROOT/'docs/acute-stroke-source-review-20261011'
BASE='/app/anatomy/isles22-case0140/'
ROLES={'dwi':('dwi','<f8'),'adc':('adc','<f8'),'flair':('FLAIR','<f4'),'mask':('msk','<u2')}

def sha(raw): return hashlib.sha256(raw).hexdigest()

def cell_boundary(mask,affine):
    """Every exposed original voxel face, triangulated without shifting corners."""
    points=[];triangles=[];index={};face_records=[]
    # Counterclockwise from outside for each index-space axis/sign.
    for axis in range(3):
        remaining=[x for x in range(3) if x!=axis]
        for sign in (-1,1):
            neighbour=np.zeros_like(mask,dtype=bool)
            dest=[slice(None)]*3;src=[slice(None)]*3
            dest[axis]=slice(0,-1) if sign==1 else slice(1,None)
            src[axis]=slice(1,None) if sign==1 else slice(0,-1)
            neighbour[tuple(dest)]=mask[tuple(src)]
            for p in np.argwhere(mask & ~neighbour):
                corners=[]
                for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]:
                    q=2*p.copy();q[axis]+=sign;q[remaining[0]]+=a;q[remaining[1]]+=b
                    corners.append(tuple(int(x) for x in q))
                a=np.asarray(corners,dtype=float)/2
                normal=np.cross(a[1]-a[0],a[2]-a[0])
                if normal[axis]*sign<0: corners.reverse()
                ids=[]
                for q in corners:
                    if q not in index:index[q]=len(points);points.append(q)
                    ids.append(index[q])
                triangles.extend([(ids[0],ids[1],ids[2]),(ids[0],ids[2],ids[3])])
                face_records.append([*map(int,p),axis,sign])
    voxel=np.asarray(points,dtype='<f8')/2
    world=np.column_stack([affine[r,3]+sum(affine[r,c]*voxel[:,c] for c in range(3)) for r in range(3)]).astype('<f8')
    if not np.isfinite(world).all():raise ValueError('Source coordinates became nonfinite')
    faces=np.asarray(triangles,dtype='<u4')
    if np.linalg.det(affine[:3,:3])<0:faces=faces[:,[0,2,1]]
    return world,faces,np.asarray(face_records,dtype='<i4'),voxel

def payload(name,raw):
    b=gzip.compress(raw,mtime=0);(OUT/name).write_bytes(b)
    return {'file':BASE+name,'sha256':sha(b),'bytes':len(b),'decoded_sha256':sha(raw),'decoded_bytes':len(raw),'codec':'gzip_little_endian_original_array','source_sample_changes':False}

def build():
    raise RuntimeError('ISLES22 publication is withdrawn: archive redistribution permission is unresolved; source files are held offline')
    acquisition=json.loads((REVIEW/'source-isles22/candidate-0140-acquisition.json').read_text())
    manifest={'schema_version':1,'id':'isles22-case0140','source_case':'sub-strokecase0140_ses-0001','source_url':'https://doi.org/10.5281/zenodo.7153326',
        'license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/',
        'attribution':"Hernandez Petzsche, de la Rosa, Wiest, Hanning, Wiestler and Kirschke. ISLES 2022 dataset v2.3, Zenodo 7153326. CC BY4. Original arrays unchanged; lossless array transport and literal expert-mask cell-boundary display added.",
        'arrays':{},'clinical_approval':False,'fine_anatomical_approval':False,'structure_coverage_granted':False,'current_patient_registration':False,
        'source_skull_stripped':True,'FLAIR_registered_to_diffusion':False,'timing_or_pretreatment_state_known':False,'ADC_physical_units_verified':False,
        'source_sampling_not_histologic_boundary_resolution':True,'complete_arrays_no_crop':True,'source_sample_changes':False,'source_resampling':False}
    arrays={};images={}
    for role,(suffix,dtype) in ROLES.items():
        name='sub-strokecase0140_ses-0001_'+suffix+'.nii.gz';raw=(OUT/name).read_bytes()
        rec=next(x for x in acquisition['files'] if x['local']==name)
        if sha(raw)!=rec['sha256']:raise ValueError('Pinned original changed: '+role)
        im=nib.load(OUT/name);a=np.asanyarray(im.dataobj)
        if a.dtype!=np.dtype(dtype) or not np.isfinite(a).all():raise ValueError('Original dtype or finite values changed')
        raw_array=a.astype(dtype).tobytes(order='F');arrays[role]=a;images[role]=im
        p=payload(role+'.native.gz',raw_array)
        p.update({'dtype':dtype,'shape':list(a.shape),'affine':im.affine.tolist(),'voxel_sizes_mm':list(map(float,im.header.get_zooms())),
            'axis_codes':list(nib.aff2axcodes(im.affine)),'source_file':BASE+name,'source_file_sha256':sha(raw),'source_file_bytes':len(raw),
            'original_sform_code':int(im.header['sform_code']),'original_qform_code':int(im.header['qform_code']),
            'selected_affine_method':'nibabel best affine; sform when valid','source_units':list(im.header.get_xyzt_units()),
            'slope':float(im.dataobj.slope),'intercept':float(im.dataobj.inter),'min':float(a.min()),'max':float(a.max()),'nonzero':int(np.count_nonzero(a))})
        values=a[a!=0];p['display_window']=[float(np.percentile(values,1)),float(np.percentile(values,99))]
        manifest['arrays'][role]=p
    for role in ('adc','mask'):
        if arrays[role].shape!=arrays['dwi'].shape or not np.array_equal(images[role].affine,images['dwi'].affine):raise ValueError('Diffusion/mask grids differ')
    mask=arrays['mask']==1
    if set(np.unique(arrays['mask']))!={0,1}:raise ValueError('Original binary label IDs changed')
    world,faces,records,voxel=cell_boundary(mask,images['mask'].affine)
    mesh_raw=b'ISV1'+struct.pack('<II',len(world),len(faces))+world.tobytes()+faces.tobytes()
    mesh=payload('expert-mask-cell-boundary.native.gz',mesh_raw)
    components={}
    for connectivity in (1,3):
        lab,n=ndimage.label(mask,ndimage.generate_binary_structure(3,connectivity));counts=np.bincount(lab.ravel())[1:]
        components['6' if connectivity==1 else '26']={'components':int(n),'voxel_counts_descending':sorted(map(int,counts),reverse=True)}
    voxels=int(mask.sum());volume=voxels*abs(np.linalg.det(images['mask'].affine[:3,:3]))
    points=np.argwhere(mask);center=points.mean(0)
    manifest['initial_diffusion_cursor']=points[np.argmin(((points-center)**2).sum(axis=1))].tolist()
    manifest['mesh']={**mesh,'vertices':len(world),'triangles':len(faces),'exposed_original_cell_faces':len(records),
        'positions_dtype':'<f8','indices_dtype':'<u4','world_coordinate_convention':'RAS millimetres from exact selected source affine',
        'boundary_definition':'union of every source mask=1 voxel cell at index +/-0.5; no interpolation/smoothing/decimation or disconnected-component removal',
        'native_mask_voxels':voxels,'label_volume_ml':float(volume/1000),'label_volume_is_pretreatment_core_or_irreversible_tissue':False,
        'voxel_corner_sha256':sha(voxel.astype('<f8').tobytes()),'world_positions_sha256':sha(world.tobytes()),'triangle_indices_sha256':sha(faces.tobytes()),
        'complete_exposed_face_records_sha256':sha(records.tobytes()),'bounds_RAS_mm':[world.min(0).tolist(),world.max(0).tolist()],
        'source_mask_sha256':manifest['arrays']['mask']['source_file_sha256'],'connectivity':components,
        'GPU_display_rounding':'GPU coordinates/normals use float32 only after Float64 source coordinates are verified and retained; this adds no measured resolution',
        'edge_or_corner_contacts_may_be_nonmanifold':'literal closed voxel cells can touch along an edge or point; no artificial healing',
        'clinical_or_named_anatomical_boundary_approval':False}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    proof={'reviewed_at':'2026-10-11','manifest_sha256':sha((OUT/'manifest.json').read_bytes()),'original_files':acquisition['files'],
           'array_voxels':{k:int(a.size) for k,a in arrays.items()},'total_source_values':sum(int(a.size) for a in arrays.values()),
           'mesh':manifest['mesh'],'no_shared_registry_edits':True,'clinical_approval':False}
    (REVIEW/'native-case0140-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({'arrays':proof['array_voxels'],'mesh_vertices':len(world),'mesh_triangles':len(faces),'label_voxels':voxels,'label_volume_ml':volume/1000}))
    return manifest

if __name__=='__main__':build()
