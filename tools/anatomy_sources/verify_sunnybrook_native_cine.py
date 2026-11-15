#!/usr/bin/env python3
"""Link exact original source model references to native cine pixels without resampling or header repairs."""
import argparse,hashlib,io,json,struct,warnings,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/sunnybrook-native-source-review'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def verify(root):
    import pydicom
    # Original source UIDs include leading-zero components; preserve this documented
    # source defect and suppress repetitive parser warnings only, never rewrite UIDs.
    warnings.filterwarnings('ignore',message='Invalid value for VR UI:.*',category=UserWarning,module='pydicom.valuerep')
    review=json.loads((OUT/'original-parameter-source-review.json').read_text());refs=review['source_image_refs'];required={r['sop_uid'] for r in refs};records={};allheaders=[];archive=json.loads((root/'batch1-acquisition.json').read_text());path=root/archive['file']
    if path.stat().st_size!=archive['bytes']:raise ValueError('Original archive changed')
    digest=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):digest.update(chunk)
    if digest.hexdigest()!=archive['sha256']:raise ValueError('Original acquisition archive hash differs')
    with zipfile.ZipFile(path) as z:
        members=[n for n in z.namelist() if n.startswith('SCD0000101/') and n.endswith('.dcm')]
        for name in members:
            raw=z.read(name);ds=pydicom.dcmread(io.BytesIO(raw),stop_before_pixels=True);sop=str(ds.SOPInstanceUID)
            head={'member':name,'sop_uid':sop,'series_uid':str(ds.SeriesInstanceUID),'study_uid':str(ds.StudyInstanceUID),'instance_number':int(ds.InstanceNumber),'folder':name.split('/')[1]};allheaders.append(head)
            if sop not in required:continue
            if sop in records:raise ValueError('Ambiguous original SOP image')
            ds=pydicom.dcmread(io.BytesIO(raw));pixels=ds.pixel_array
            if str(ds.file_meta.TransferSyntaxUID)!='1.2.840.10008.1.2.1' or ds.BitsAllocated!=16 or ds.BitsStored!=16 or ds.PixelRepresentation!=1:raise ValueError('Unsupported original pixel representation')
            scalar=struct.unpack('<'+str(ds.Rows*ds.Columns)+'h',ds.PixelData)
            if pixels.shape!=(ds.Rows,ds.Columns) or tuple(int(v) for v in pixels.ravel())!=scalar:raise ValueError('Independent original pixel decoder differs')
            records[sop]={**head,'sha256':sha(raw),'original_pixel_bytes_sha256':sha(ds.PixelData),'zip_crc_verified':True,'rows':int(ds.Rows),'columns':int(ds.Columns),'pixel_dtype':'signed_int16','bits_stored':int(ds.BitsStored),'photometric_interpretation':str(ds.PhotometricInterpretation),'rescale_slope':float(getattr(ds,'RescaleSlope',1)),'rescale_intercept':float(getattr(ds,'RescaleIntercept',0)),'image_orientation_patient':[float(v) for v in ds.ImageOrientationPatient],'image_position_patient':[float(v) for v in ds.ImagePositionPatient],'pixel_spacing':[float(v) for v in ds.PixelSpacing],'slice_thickness':float(ds.SliceThickness),'spacing_between_slices':float(ds.SpacingBetweenSlices),'trigger_time_ms':float(ds.TriggerTime),'nominal_interval_ms':float(ds.NominalInterval),'cardiac_number_of_images':int(ds.CardiacNumberOfImages),'source_pixels_independently_decoded_equal':True,'source_pixel_range':[int(pixels.min()),int(pixels.max())]}
    if set(records)!=required:raise ValueError('Original model images missing from native archive')
    linked=[]
    for ref in refs:
        r=records[ref['sop_uid']]
        if r['series_uid']!=ref['series_uid']:raise ValueError('Source model/native series linkage differs')
        linked.append({**ref,'native':r})
    groups={}
    for row in linked:groups.setdefault((row['label'],row['slice']),[]).append(row)
    for key,group in groups.items():
        if sorted(r['frame'] for r in group)!=list(range(20)):raise ValueError('Source model phase group incomplete')
        if len({tuple(r['native']['image_orientation_patient']) for r in group})!=1 or len({tuple(r['native']['image_position_patient']) for r in group})!=1:raise ValueError('Source plane geometry changes within phase group')
    phase_groups=[]
    for (label,slice_id),group in sorted(groups.items()):
        ordered=sorted(group,key=lambda r:r['frame']);times=[r['native']['trigger_time_ms'] for r in ordered]
        if any(b<=a for a,b in zip(times,times[1:])):raise ValueError('Original trigger times do not increase')
        phase_groups.append({'label':label,'slice':slice_id,'frames':[r['frame'] for r in ordered],'trigger_times_ms':times,'nominal_intervals_ms':sorted({r['native']['nominal_interval_ms'] for r in ordered}),'distinct_original_pixel_buffers':len({r['native']['original_pixel_bytes_sha256'] for r in ordered}),'image_orientation_patient':ordered[0]['native']['image_orientation_patient'],'image_position_patient':ordered[0]['native']['image_position_patient']})
    allseries={}
    for h in allheaders:allseries.setdefault(h['series_uid'],set()).add(h['folder'])
    folder_records={}
    for h in allheaders:folder_records[h['folder']]=folder_records.get(h['folder'],0)+1
    out={'source_archive':archive,'native_case_dicom_members':len(allheaders),'case_folder_counts':folder_records,'model_image_refs':len(refs),'unique_model_native_sops':len(records),'source_plane_groups':len(groups),'each_model_group_has_20_source_frames':True,'all_original_model_sop_series_links_match':True,'all_referenced_native_pixels_match_scalar_decoder':True,'source_uid_nonconformance_preserved':True,'series_uid_shared_across_folders':[{ 'series_uid':uid,'folders':sorted(folders)} for uid,folders in allseries.items() if len(folders)>1],
        'linked_images':linked,'phase_groups':phase_groups,'all_groups_are_same_simultaneous_heartbeat':False,'source_geometry_declared_by_DICOM':True,'independent_scanner_phantom_calibration_verified':False,'model_transform_basis_in_patient_frame_verified':False,'contour_pixel_index_native_linkage_verified':False,'clinical_quantitative_function_validated':False,'full_anatomical_validation':False,'clinical_approval':False,'runtime_promoted':False,
        'limits':['Original UIDs include non-conformant leading-zero components and one series UID can span multiple folders/planes; do not silently repair or group by series alone.',
            'Model frame index and original TriggerTime/NominalInterval are preserved; normalized model interval is not uncritically treated as milliseconds.',
            'Only exact model-referenced native pixels are independently decoded here; full additional perfusion/tissue acquisitions and their clinical validation remain separate.',
            'Native image linkage does not validate prolate interpolation, patient transform, contour conventions, full tissue/layers or measured EF/flow.']}
    (OUT/'native-cine-linkage-review.json').write_text(json.dumps(out,indent=2)+'\n');print(len(records),'original model-referenced images matched;',len(groups),'20-frame groups; source UID defects retained.')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);verify(p.parse_args().source_root)
