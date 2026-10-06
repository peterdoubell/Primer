#!/usr/bin/env python3
"""Verify every original R6 DICOM slice before assigning source units, HU or upstream attribution."""
import argparse
import hashlib
import json
from pathlib import Path
from tools.anatomy_sources.review_avt_r6_source import ROOT,CT_SHA,MASK_SHA,META_SHA,read_nrrd

OUTPUT=ROOT/'docs/avt-r6-dicom-linkage-review'
MANIFEST_SHA='749770a09558e74bb51bd8ae2700b9ab946f208441eebf8b75e1b34ad300cd1a'
INDEX_SHA='94ff95473e68843682c1fa1a7889daca178b4fc5280ef839c4acd0b0535fa571'
SERIES='1.3.6.1.4.1.9328.50.17.321375527633491919048584720362415649934'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def verify(root):
    import numpy as np
    import pydicom
    manifest_raw=(root/'r6-matched-dicom-objects.json').read_bytes();manifest=json.loads(manifest_raw)
    metadata_raw=(root/'figshare-metadata.json').read_bytes();metadata=json.loads(metadata_raw)
    if sha(metadata_raw)!=META_SHA or metadata['license']['name']!='CC BY 4.0' or sha((root/'R6.seg.nrrd').read_bytes())!=MASK_SHA:
        raise ValueError('Original mask identity or producer grant differs')
    if sha(manifest_raw)!=MANIFEST_SHA or manifest['series']['SeriesInstanceUID']!=SERIES:raise ValueError('Pinned original series differs')
    if manifest['series']['source_DOI']!='10.7937/k9/tcia.2015.ofip7tvm' or manifest['series']['license_short_name']!='CC BY 3.0':raise ValueError('Source DOI/grant differs')
    index=root/'idc-24.2.2/idc_index.parquet'
    if sha(index.read_bytes())!=INDEX_SHA:raise ValueError('Publisher index differs')
    if len(manifest['objects'])!=1064 or len({e['key'] for e in manifest['objects']})!=1064:raise ValueError('Incomplete original source manifest')
    raw=(root/'R6.nrrd').read_bytes()
    if sha(raw)!=CT_SHA:raise ValueError('Original derivative CT differs')
    fields,ct=read_nrrd(raw);rows=[]
    for item in manifest['objects']:
        path=root/'r6-matched-dicom'/Path(item['key']).name;raw=path.read_bytes()
        if len(raw)!=item['bytes'] or hashlib.md5(raw).hexdigest()!=item['etag'].strip('"'):raise ValueError('Original object identity differs')
        d=pydicom.dcmread(path)
        if str(d.SeriesInstanceUID)!=SERIES:raise ValueError('Original series differs')
        position=np.asarray(d.ImagePositionPatient,dtype='float64');offset=(position[2]+655.375)/.625
        if abs(offset-round(offset))>1e-8 or not 0<=round(offset)<1064:raise ValueError('Original plane location differs')
        k=int(round(offset));pixels=d.pixel_array
        if not np.array_equal(pixels,ct[k]):raise ValueError('Original source pixels differ at '+str(k))
        if (not np.array_equal(position,[-185.5,-185.5,-655.375+k*.625])
                or list(map(float,d.PixelSpacing))!=[.724609,.724609]
                or list(map(float,d.ImageOrientationPatient))!=[1,0,0,0,1,0]
                or (int(d.Rows),int(d.Columns))!=(512,512)):
            raise ValueError('Exact original source geometry differs')
        if (float(d.RescaleSlope),float(d.RescaleIntercept),str(d.RescaleType),int(d.PixelPaddingValue))!=(1,-1024,'HU',-2000):raise ValueError('Original intensity interpretation differs')
        if (int(d.BitsAllocated),int(d.BitsStored),int(d.PixelRepresentation))!=(16,16,1):raise ValueError('Original sample interpretation differs')
        rows.append({'voxel_k':k,'object_key':item['key'],'dicom_sha256':sha(raw),'dicom_etag_md5_verified':True,
            'SOPInstanceUID':str(d.SOPInstanceUID),'ImagePositionPatient_mm':position.tolist(),
            'PixelSpacing_mm':list(map(float,d.PixelSpacing)),'ImageOrientationPatient':list(map(float,d.ImageOrientationPatient)),
            'Rows':int(d.Rows),'Columns':int(d.Columns),'BitsAllocated':16,'BitsStored':16,'PixelRepresentation':1,
            'RescaleSlope':1.0,'RescaleIntercept':-1024.0,'RescaleType':'HU','PixelPaddingValue':-2000,
            'TransferSyntaxUID':str(d.file_meta.TransferSyntaxUID),'stored_pixel_int16_sha256':sha(pixels.astype('<i2').tobytes()),
            'all_source_slice_pixels_equal_nrrd':True})
    if {r['voxel_k'] for r in rows}!=set(range(1064)) or len({r['SOPInstanceUID'] for r in rows})!=1064:raise ValueError('Missing or duplicate original slice')
    # Pixel padding remains excluded from intensity interpretation, not edited out of the original volume.
    valid=ct!= -2000;values=ct[valid].astype('int32')-1024
    DOI=json.loads((root/'rider-pet-ct-doi.json').read_text())['data']['attributes']
    if DOI['doi'].lower()!='10.7937/k9/tcia.2015.ofip7tvm' or not any(r.get('rightsIdentifier')=='cc-by-3.0' for r in DOI['rightsList']):raise ValueError('Original DOI/grant differs')
    license_rows=json.loads((root/'rider-pet-ct-license-rows.json').read_text())
    if not any('https://creativecommons.org/licenses/by/3.0/' in r['license_urls'] for r in license_rows['rows']):raise ValueError('Official collection grant differs')
    OUTPUT.mkdir(parents=True,exist_ok=True)
    for source,target in [('r6-matched-dicom-objects.json','original-dicom-object-manifest.json'),
        ('rider-pet-ct-doi.json','original-source-doi-metadata.json'),('rider-pet-ct-license-rows.json','original-collection-license-rows.json'),
        ('idc-geometry-candidates.json','original-index-candidate-rows.json'),('candidate-sample-geometry.json','original-candidate-sample-geometries.json')]:
        (OUTPUT/target).write_bytes((root/source).read_bytes())
    summary={'source_record_url':'https://www.cancerimagingarchive.net/collection/rider-lung-pet-ct/',
        'source_doi':'10.7937/k9/tcia.2015.ofip7tvm','source_dataset_title':DOI['titles'][0]['title'],
        'original_mask_sha256':MASK_SHA,'original_mask_producer_metadata_sha256':META_SHA,'mask_producer_license':'CC BY 4.0',
        'creators_as_recorded_in_original_doi_metadata':DOI['creators'],'source_license':'CC BY 3.0',
        'source_license_url':'https://creativecommons.org/licenses/by/3.0/','source_doi_metadata_sha256':sha((root/'rider-pet-ct-doi.json').read_bytes()),
        'official_collection_license_rows_sha256':sha((root/'rider-pet-ct-license-rows.json').read_bytes()),
        'publisher_idc_index_release':'24.2.2','publisher_idc_index_sha256':INDEX_SHA,'source_object_manifest_sha256':MANIFEST_SHA,
        'source_series':manifest['series'],'original_ct_sha256':CT_SHA,'original_ct_voxel_sha256':sha(ct.tobytes()),
        'original_dicom_instance_count':1064,'verified_original_pixel_count':int(ct.size),'records':sorted(rows,key=lambda r:r['voxel_k']),
        'all_source_slices_and_pixels_match':True,'source_physical_space_units_verified':'mm_from_original_DICOM',
        'source_hu_transform_verified':{'slope':1,'intercept':-1024,'unit':'HU'},'original_padding_stored_value':-2000,
        'original_padding_voxel_count':int((~valid).sum()),'nonpadding_hu_range':[int(values.min()),int(values.max())],
        'original_volume_modified':False,'source_ct_and_mask_commercial_reuse_grants_verified':True,
        'original_avt_export_tcia_release_version_verified':False,'bolus_timing_or_arterial_phase_verified':False,
        'highest_resolution_acquired_master_verified':False,'case_diagnosis_independently_confirmed':False,
        'mask_boundary_or_branch_identity_independently_reviewed':False,'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False,
        'limits':['The AVT publication cites RIDER Lung CT; exact original-source pixels identify this R6 volume in RIDER Lung PET-CT instead. Preserve the original citation and record the verified case-specific correction.',
            'The rejected same-count RIDER series has different spacing/origin and mismatched source pixels; shape/count matches do not establish case identity.',
            'Current original-series linkage and rights are verified; the historical AVT export release and processing workflow provenance are not inferred from an IDC import version.',
            'Original CT units/intensity calibration do not approve semantic masks, wall/lumen boundaries, complete branch anatomy, phase, diagnosis or clinical measurements.',
            'Padding is a source sentinel rather than tissue HU; all original voxel values remain untouched.']}
    (OUTPUT/'complete-dicom-linkage-review.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('All 1,064 original DICOM slices/278,921,216 pixels match; original mm/HU and case-specific CC BY 3.0 attribution verified.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    verify(p.parse_args().source_root)
