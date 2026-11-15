#!/usr/bin/env python3
"""Verify original case DICOM inventory and converted T1 voxel/geometry correspondence."""
import argparse
from collections import defaultdict
import hashlib
import io
import json
from pathlib import Path
import zipfile


def audit(root,output):
    import numpy as np
    import nibabel as nib
    import pydicom
    receipt=json.loads((root/'dicoms.zip.acquisition.json').read_text());path=root/'dicoms.zip'
    publisher=json.loads((root/'record.json').read_text());expected=next(e for e in publisher['files'] if e['key']=='dicoms.zip')
    groups=defaultdict(list);members=[]
    # Hash and read the same open descriptor, avoiding a path reopen after verification.
    with path.open('rb') as source:
        md5=hashlib.md5();sha=hashlib.sha256()
        for chunk in iter(lambda:source.read(1024*1024),b''):
            md5.update(chunk);sha.update(chunk)
        if not receipt['publisher_md5_verified'] or 'md5:'+md5.hexdigest()!=expected['checksum'] or sha.hexdigest()!=receipt['sha256']:
            raise ValueError('Original DICOM archive changed')
        source.seek(0)
        with zipfile.ZipFile(source) as z:
            for name in z.namelist():
                if 'TCGA-BC-A3KG' not in name or not name.endswith('.dcm') or name.startswith('__MACOSX/'):continue
                data=z.read(name);d=pydicom.dcmread(io.BytesIO(data));groups[str(d.SeriesInstanceUID)].append(d)
                members.append({'source_member':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'crc_verified':True})
    rows=[];converted=[];case_root=root/'case-BC-A3KG-original-and-derived'
    niftis={name:nib.load(case_root/(name+'.nii.gz')) for name in ['pre','art','pv','del']}
    for uid,images in groups.items():
        first=images[0]
        row={'series_instance_uid':uid,'series_number':int(first.SeriesNumber),'source_description':str(first.SeriesDescription),'images':len(images),
             'rows':int(first.Rows),'columns':int(first.Columns),'pixel_spacing_mm':list(map(float,first.PixelSpacing)),
             'slice_thickness_values_mm':sorted({float(d.SliceThickness) for d in images}),
             'scanning_sequence_values':sorted({str(getattr(d,'ScanningSequence','not_reported')) for d in images}),
             'repetition_times_ms':sorted({float(d.RepetitionTime) for d in images}),
             'echo_numbers':sorted({str(getattr(d,'EchoNumbers','not_reported')) for d in images}),
             'echo_times_ms':sorted({float(d.EchoTime) for d in images}),
             'distinct_positions':len({tuple(d.ImagePositionPatient) for d in images}),
             'sequence_or_disease_identity_clinically_approved':False}
        rows.append(row)
        # Match only by every source voxel and declared physical coordinates; no phase-name guess.
        if len(images)!=88 or row['rows']!=208 or row['columns']!=256:continue
        images.sort(key=lambda d:float(d.ImagePositionPatient[2]))
        if len({tuple(d.ImagePositionPatient) for d in images})!=len(images):raise ValueError('Repeated original phase positions')
        positions=np.asarray([d.ImagePositionPatient for d in images],float)
        if not np.allclose(np.diff(positions,axis=0),[0,0,2.5],atol=1e-6,rtol=0):raise ValueError('Irregular original phase positions')
        if any(list(map(float,d.ImageOrientationPatient))!=[1,0,0,0,1,0] for d in images):raise ValueError('Unsupported original index orientation')
        pixel_spacing=np.asarray(first.PixelSpacing,float)
        if any(not np.array_equal(np.asarray(d.PixelSpacing,float),pixel_spacing) for d in images):raise ValueError('Inconsistent original spacing')
        native=np.stack([d.pixel_array.astype(float)*float(getattr(d,'RescaleSlope',1))+float(getattr(d,'RescaleIntercept',0)) for d in images])
        ras=native.transpose(2,1,0)[::-1,::-1,:]
        origin_lps=positions[0]+np.array([pixel_spacing[1]*(first.Columns-1),pixel_spacing[0]*(first.Rows-1),0])
        affine=np.diag([pixel_spacing[1],pixel_spacing[0],2.5,1]);affine[:3,3]=origin_lps*np.array([-1,-1,1])
        matches=[]
        for name,image in niftis.items():
            data=np.asanyarray(image.dataobj)
            if data.shape==ras.shape and np.array_equal(data,ras):
                difference=float(np.max(np.abs(image.affine-affine)))
                if difference>1e-4:raise ValueError('Matching voxels but source geometry differs')
                matches.append({'source_filename':name+'.nii.gz','exact_rescaled_voxel_match':True,'compared_voxels':int(data.size),
                                'max_source_affine_difference_mm':difference,'source_directions_reindexed_from_lps_to_ras':True})
        if len(matches)!=1:raise ValueError('Original DICOM phase has missing or ambiguous converted correspondence')
        converted.append({'series_instance_uid':uid,'series_number':int(first.SeriesNumber),'matches':matches,
                          'source_frame_of_reference_uids':sorted({str(d.FrameOfReferenceUID) for d in images}),
                          'source_acquisition_times':sorted({str(getattr(d,'AcquisitionTime','not_reported')) for d in images}),
                          'source_contrast_agents':sorted({str(getattr(d,'ContrastBolusAgent','not_reported')) for d in images})})
    if {m['source_filename'] for row in converted for m in row['matches']}!={n+'.nii.gz' for n in niftis}:raise ValueError('Converted original phase set incomplete')
    result={'case_id':'TCGA-BC-A3KG','source_doi':'10.5281/zenodo.8179129','whole_dicom_archive_publisher_md5_verified':True,
            'dicom_archive_sha256':receipt['sha256'],'case_dicom_members':members,'case_series_inventory':rows,
            'original_phase_correspondence':converted,'original_source_values_changed':False,'source_registered_derivatives_used_as_native':False,
            'source_echoes_stacked_as_one_volume':False,'clinical_approval':False,'runtime_promoted':False,
            'limits':['Pixel and geometry correspondence validates conversion, not clinical phase timing/adequacy or anatomical boundary accuracy.',
                      'T2/dual-echo/thick-slab source descriptions and parameters require separate sequence/geometry review before feature credit.',
                      'Both raters and actual clinical eligibility/treatment state remain independent requirements.']}
    output.write_text(json.dumps(result,indent=2)+'\n');print('Case series:',len(rows),'; all four converted phases match source DICOM pixels')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();audit(a.source_root,a.output)
