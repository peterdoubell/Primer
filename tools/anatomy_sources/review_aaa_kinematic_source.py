#!/usr/bin/env python3
"""Preserve original patient CTA/STL identities without treating processed external surfaces as all anatomy."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import struct
import zipfile
from tools.anatomy_sources.review_spl_wall_source import nrrd

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'docs/aaa-kinematic-native-source-review'
ARCHIVE_SHA='036ddd6e13b89e001a8e3d96b06ffb71860eaa80a1a4477e9d5cad1ac94e51c5'
METADATA_SHA='481a51c6ced539d5fd7ff8f4fdb687486b11a835838b7e48cb49121f071282b5'
PAPER_SHA='e2493bd6f7491f6a70988f43a6bc42c545435b466732b5b293af7c100b5a8379'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def stl(raw):
    import numpy as np
    if len(raw)<84:raise ValueError('Truncated binary STL')
    count=struct.unpack_from('<I',raw,80)[0]
    if not count or len(raw)!=84+count*50:raise ValueError('Binary STL facet count/length differs')
    dtype=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attribute','<u2')])
    records=np.frombuffer(raw,dtype,offset=84,count=count)
    if not np.isfinite(records['vertices']).all() or not np.isfinite(records['normal']).all():raise ValueError('Nonfinite original STL samples')
    # Independent scalar stdlib readback preserves even signed-zero bit patterns.
    for row,values in zip(records,struct.iter_unpack('<12fH',raw[84:])):
        if (struct.pack('<3f',*values[:3])!=row['normal'].tobytes()
                or struct.pack('<9f',*values[3:12])!=row['vertices'].tobytes()
                or values[12]!=int(row['attribute'])):
            raise ValueError('Independent scalar STL readback differs')
    return records


def geometry_controls(records):
    import numpy as np
    corners=records['vertices'].astype('float64');vertices,inverse=np.unique(corners.reshape(-1,3),axis=0,return_inverse=True)
    faces=inverse.reshape(-1,3);directed=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]])
    edges,ei,counts=np.unique(np.sort(directed,axis=1),axis=0,return_inverse=True,return_counts=True)
    orientation=np.bincount(ei,weights=np.where(directed[:,0]<directed[:,1],1,-1),minlength=len(edges))
    cross=np.cross(corners[:,1]-corners[:,0],corners[:,2]-corners[:,0]);lengths=np.linalg.norm(cross,axis=1)
    normals=records['normal'].astype('float64');nl=np.linalg.norm(normals,axis=1);valid=(lengths>0)&(nl>0)
    dots=np.einsum('ij,ij->i',cross[valid],normals[valid])/(lengths[valid]*nl[valid])
    parents=list(range(len(vertices)))
    def find(i):
        while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
        return i
    for a,b in edges:
        a,b=find(int(a)),find(int(b))
        if a!=b:parents[b]=a
    return {'facet_count':len(records),'original_corner_count':len(corners)*3,'exact_position_analysis_vertices':len(vertices),
        'facet_vertex_float32_sha256':sha(records['vertices'].tobytes()),'facet_normal_float32_sha256':sha(records['normal'].tobytes()),
        'facet_attribute_uint16_sha256':sha(records['attribute'].tobytes()),'nonzero_attribute_records':int((records['attribute']!=0).sum()),
        'bounds_ras_native_units':[vertices.min(0).tolist(),vertices.max(0).tolist()],
        'zero_area_facets':int((lengths==0).sum()),'zero_stored_normals':int((nl==0).sum()),
        'stored_normal_vs_facet_dot_range':[float(dots.min()),float(dots.max())] if len(dots) else None,
        'boundary_edges':int((counts==1).sum()),'nonmanifold_edges':int((counts>2).sum()),
        'inconsistent_shared_edge_orientation':int(((counts==2)&(orientation!=0)).sum()),
        'exact_position_connected_components':len({find(i) for i in range(len(vertices))}),
        'exact_position_euler_characteristic':int(len(vertices)-len(edges)+len(faces)),
        'signed_volume_native_units_cubed':float(np.einsum('ij,ij->i',corners[:,0],np.cross(corners[:,1],corners[:,2])).sum()/6),
        'independent_scalar_facet_readback_verified':True,
        'analysis_position_deduplication_changes_source':False,'self_intersections_tested':False,
        'closed_topology_is_anatomical_validation':False}


def grid_transform(fields):
    import numpy as np
    if fields['space']!='left-posterior-superior':raise ValueError('Unreviewed source basis')
    vector=lambda s:[float(v) for v in s.strip('()').split(',')]
    directions=re.findall(r'\([^()]+\)',fields['space directions'])
    if len(directions)!=3:raise ValueError('Unreviewed direction axes')
    basis=np.asarray([vector(s) for s in directions]).T;origin=np.asarray(vector(fields['space origin']))
    if not np.isfinite(basis).all() or not np.isfinite(origin).all() or abs(np.linalg.det(basis))<1e-12:raise ValueError('Invalid native spatial matrix')
    return basis,origin


def ras_to_ijk(points,fields):
    import numpy as np
    basis,origin=grid_transform(fields)
    lps=np.asarray(points,dtype='float64')*[-1,-1,1]
    return (lps-origin)@np.linalg.inv(basis).T


def review(root):
    import numpy as np
    metadata_raw=(root/'kinematic-metadata.json').read_bytes();meta=json.loads(metadata_raw)
    archive_path=root/'4DCTA_AAA_Dataset.zip';archive_raw=archive_path.read_bytes()
    if sha(metadata_raw)!=METADATA_SHA or sha(archive_raw)!=ARCHIVE_SHA:raise ValueError('Reviewed source identity differs')
    if meta['metadata']['license']['id']!='cc-by-4.0' or meta['metadata']['access_right']!='open':raise ValueError('Original dataset grant differs')
    if len(meta['files'])!=1 or meta['files'][0]['checksum']!='md5:'+hashlib.md5(archive_raw).hexdigest():raise ValueError('Publisher archive MD5 differs')
    if sha((root/'kinematic-paper.pdf').read_bytes())!=PAPER_SHA:raise ValueError('Reviewed primary paper differs')
    OUTPUT.mkdir(parents=True,exist_ok=True);(OUTPUT/'source-metadata.json').write_bytes(metadata_raw)
    rows=[];members=[];synthetic=[];phase_count=0;voxel_count=0
    with zipfile.ZipFile(archive_path) as z:
        if z.testzip() is not None:raise ValueError('Archive CRC differs')
        for info in z.infolist():
            if info.is_dir():continue
            raw=z.read(info.filename);members.append({'member':info.filename,'bytes':len(raw),'sha256':sha(raw),'crc32':info.CRC})
            if info.filename.startswith('Ground Truth/'):
                synthetic.append({'member':info.filename,'sha256':sha(raw),'is_independent_acquired_anatomy_ground_truth':False,
                                  'is_acquired_systolic_ct':False if 'deformed.nrrd' in info.filename and 'undeformed' not in info.filename else None})
        for patient in range(1,11):
            prefix=f'P{patient}/';names=[i.filename for i in z.infolist() if i.filename.startswith(prefix) and i.filename.endswith('.nrrd')]
            expected=[40,80] if patient in (2,4) else list(range(30,100,10)) if patient in (1,8) else list(range(10,101,10))
            if set(names)!={prefix+str(phase)+'%.nrrd' for phase in expected}:raise ValueError('Incomplete actual phase inventory')
            surface_raw=z.read(prefix+'Wall.stl');records=stl(surface_raw)
            saved=f'P{patient}-original-Wall.stl.gz';(OUTPUT/saved).write_bytes(gzip.compress(surface_raw,mtime=0))
            frames=[]
            for phase in expected:
                member=prefix+str(phase)+'%.nrrd';raw=z.read(member);fields,ct=nrrd(raw);basis,origin=grid_transform(fields)
                ijk=ras_to_ijk(records['vertices'].reshape(-1,3),fields);size=np.asarray(ct.shape[::-1])
                frames.append({'member':member,'cardiac_phase_percent':phase,'nrrd_sha256':sha(raw),'header':fields,
                    'voxel_count':int(ct.size),'original_voxel_int16_sha256':sha(ct.astype('<i2').tobytes()),
                    'stored_value_range':[int(ct.min()),int(ct.max())],'source_matrix_lps':basis.tolist(),'source_origin_lps':origin.tolist(),
                    'surface_corner_ijk_bounds':[ijk.min(0).tolist(),ijk.max(0).tolist()],
                    'surface_corner_records_outside_voxel_cell_extent':int(np.any((ijk<-.5)|(ijk>size-.5),axis=1).sum()),
                    'ct_hu_calibration_verified':False,'physical_space_units_independently_verified':False,
                    'source_voxels_changed':False,'geometry_phase_registration_verified':False})
                phase_count+=1;voxel_count+=int(ct.size)
            rows.append({'patient_source_id':f'P{patient}','surface_member':prefix+'Wall.stl','surface_sha256':sha(surface_raw),
                'preserved_surface_file':saved,'geometry_controls':geometry_controls(records),'frames':frames,
                'review_phase_percent':40 if patient in (2,4) else 30,
                'paper_systolic_phase_typo_affects_case':patient in (2,3),
                'surface_source_basis':'RAS_as_described_in_primary_paper','nrrd_source_basis':'LPS_in_original_header',
                'basis_sign_conversion_is_independent_anatomical_registration':False,
                'delivered_surface_is_external_only':True,'source_segmentation_masks_supplied':False,
                'source_geometry_changed':False,'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False})
    summary={'source_record_url':'https://zenodo.org/records/15477710','source_doi':'10.5281/zenodo.15477710',
        'archive_url':meta['files'][0]['links']['self'],'archive_sha256':sha(archive_raw),'archive_bytes':len(archive_raw),
        'publisher_md5_verified':True,'all_archive_members_crc_verified':True,'source_metadata_sha256':sha(metadata_raw),
        'primary_paper_url':'https://arxiv.org/abs/2505.17647v2','primary_paper_sha256':PAPER_SHA,
        'dataset_license':'CC BY 4.0','dataset_license_url':'https://creativecommons.org/licenses/by/4.0/',
        'attribution':'; '.join(c['name'] for c in meta['metadata']['creators'])+'. '+meta['metadata']['title']+'. DOI 10.5281/zenodo.15477710. CC BY 4.0. No endorsement implied.',
        'patient_count':10,'acquired_ct_frame_count':phase_count,'all_delivered_ct_voxel_count':voxel_count,
        'original_surface_facet_count':sum(r['geometry_controls']['facet_count'] for r in rows),
        'members':members,'records':rows,'synthetic_method_verification_files':synthetic,
        'original_geometry_or_voxels_changed':False,'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False,
        'source_processing':['Automated PRAEVAorta labels combine wall/ILT, calcification and lumen before further processing.',
            'Original study crops masks, removes branches/artifacts, resamples to isotropic grids, smooths, fills holes and remeshes with ACVD before external-surface export.',
            'Internal wall generation in the study pipeline uses assumed thickness; only the processed external surface is delivered in this ten-patient dataset.'],
        'limits':['Cropped external-surface studies do not supply every reportable wall layer, calcification region, thrombus/lumen boundary, vessel branch, access vessel, haemorrhage compartment, fistula or repair component.',
            'Original segmentation labels are not included; coordinate coincidence and normal/topology controls are not independent anatomical boundary review.',
            'NRRD headers explicitly encode LPS while STL is described as RAS; only basis signs are converted for comparison, without fitting or rescaling.',
            'NRRD headers have no explicit physical-space units or HU calibration, and STL is unitless. Native numeric coordinates are retained without inventing independent physical calibration.',
            'The 2025 systolic paragraph includes P2 in its 30% list and omits P3, then says P2/P4 use 40%; the actual phase inventory and typo are retained. Full model phase registration is unverified for all cases.',
            'Synthetic warped method-verification CT/FE outputs are not independent acquired anatomy or clinical systolic ground truth.',
            'Closed/smooth geometry or biomechanical risk maps cannot establish clinical rupture prediction or complete AAA anatomy.']}
    (OUTPUT/'native-source-review.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('Preserved ten original external surfaces;',phase_count,'acquired CT frames;',voxel_count,'unaltered delivered voxels.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    review(p.parse_args().source_root)
