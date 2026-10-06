#!/usr/bin/env python3
"""Match exact original author case filenames/pixels/geometry to CAP images before linking contours."""
import argparse,collections,hashlib,io,json,math,re,struct,warnings
from pathlib import Path
from tools.anatomy_sources.review_sunnybrook_source_parameters import OUT

def sha(raw):return hashlib.sha256(raw).hexdigest()
def verify(root):
    import pydicom
    warnings.filterwarnings('ignore',message='Invalid value for VR UI:.*',category=UserWarning,module='pydicom.valuerep')
    acquisition=json.loads((root/'original-case-acquisition.json').read_text());cap=json.loads((OUT/'native-cine-linkage-review.json').read_text());by_pixels={}
    for row in cap['linked_images']:
        if row['label'].startswith('SA'):
            digest=row['native']['original_pixel_bytes_sha256']
            if digest in by_pixels:raise ValueError('Ambiguous CAP native pixel identity')
            by_pixels[digest]=row
    if len(acquisition['members'])!=240 or len(by_pixels)!=240:raise ValueError('Original/CAP case scope differs')
    original_by_name={};images=[]
    for source in acquisition['members']:
        raw=(root/source['file']).read_bytes()
        if len(raw)!=source['bytes'] or sha(raw)!=source['sha256']:raise ValueError('Acquired original member changed')
        ds=pydicom.dcmread(io.BytesIO(raw));pixels=ds.pixel_array
        if pixels.shape!=(256,256) or str(ds.file_meta.TransferSyntaxUID)!='1.2.840.10008.1.2.1' or ds.PixelRepresentation!=1 or ds.BitsAllocated!=16:raise ValueError('Original native pixel representation differs')
        if tuple(int(v) for v in pixels.ravel())!=struct.unpack('<65536h',ds.PixelData):raise ValueError('Independent original pixel decoding differs')
        digest=sha(ds.PixelData)
        if digest not in by_pixels:raise ValueError('Original case pixel buffer does not match CAP')
        row=by_pixels[digest];native=row['native'];geometry={'image_position_patient':[float(v) for v in ds.ImagePositionPatient],'image_orientation_patient':[float(v) for v in ds.ImageOrientationPatient],'pixel_spacing':[float(v) for v in ds.PixelSpacing]}
        if any(geometry[k]!=native[k] for k in geometry):raise ValueError('Original/CAP source geometry differs')
        number=int(Path(source['file']).stem.split('-')[-1])
        if number!=native['instance_number'] or (number-1)%20!=row['frame']:raise ValueError('Original filename/native phase mapping differs')
        record={'original_member':source['member'],'original_file':source['file'],'original_filename':Path(source['file']).name,'original_file_sha256':source['sha256'],'original_sop_uid':str(ds.SOPInstanceUID),'original_series_uid':str(ds.SeriesInstanceUID),'original_pixel_bytes_sha256':digest,'original_pixels_independently_decoded_equal':True,'CAP_model_label':row['label'],'CAP_model_frame':row['frame'],'CAP_sop_uid':row['sop_uid'],'CAP_native_file':native['member'],'CAP_native_file_sha256':native['sha256'],'original_filename_sequence_number':number,'original_sequence_phase_one_based':(number-1)%20+1,'original_basal_first_slice_number':(number-1)//20+1,'original_and_CAP_geometry_equal':True,**geometry};original_by_name[record['original_filename']]=record;images.append(record)
    source_review=json.loads((OUT/'original-parameter-source-review.json').read_text());contours=[]
    for contour in source_review['source_manual_contours']:
        path=OUT/contour['file'];raw=path.read_bytes()
        if sha(raw)!=contour['sha256']:raise ValueError('Original source contour changed')
        name=path.name;match=re.fullmatch(r'(IM-0001-\d{4})-([iop]\d?contour)-manual\.txt',name)
        if not match or match.group(1)+'.dcm' not in original_by_name:raise ValueError('Original contour image filename has no exact original match')
        image=original_by_name[match.group(1)+'.dcm'];points=[[float(v) for v in line.split()] for line in raw.decode().splitlines() if line.strip()];closed=points+[points[0]];steps=[math.dist(a,b) for a,b in zip(closed,closed[1:])]
        contours.append({'file':contour['file'],'sha256':contour['sha256'],'author_contour_kind':match.group(2),'points':len(points),'original_filename':image['original_filename'],'original_file_sha256':image['original_file_sha256'],'CAP_sop_uid':image['CAP_sop_uid'],'CAP_model_label':image['CAP_model_label'],'CAP_model_frame':image['CAP_model_frame'],'original_phase_one_based':image['original_sequence_phase_one_based'],'original_basal_first_slice_number':image['original_basal_first_slice_number'],'raw_coordinate_bounds':[[min(p[k] for p in points) for k in [0,1]],[max(p[k] for p in points) for k in [0,1]]],'last_to_first_distance_pixels':steps[-1],'maximum_consecutive_or_closure_distance_pixels':max(steps),'original_contour_points_changed_or_repaired':False})
    out={'source_original_case_acquisition':acquisition,'original_case':'SC-HF-I-01','CAP_case':'SCD0000101','original_images':images,'original_contours':contours,'all_240_original_SAX_pixel_buffers_and_geometry_match_CAP':True,'all_33_contours_match_exact_original_filenames':True,'author_contour_kind_counts':dict(collections.Counter(r['author_contour_kind'] for r in contours)),'source_annotation_phases_one_based':sorted({r['original_phase_one_based'] for r in contours}),'model_annotation_frames_zero_based':sorted({r['CAP_model_frame'] for r in contours}),'contour_origin_definition_from_author':'(0,0) at top-left corner, x/y in pixel units','exact_native_pixel_centre_offset_independently_verified':False,'clinical_EF_or_wall_mass_or_complete_anatomy_approved':False,'surface_role_correspondence_not_yet_quantitatively_compared':True,'source_files_or_contours_changed':False,'runtime_promoted':False}
    (OUT/'original-dicom-contour-linkage-review.json').write_text(json.dumps(out,indent=2)+'\n');print('All 240 original SAX images match CAP pixels/geometry; all 33 contours match exact original image filenames.',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);verify(p.parse_args().source_root)
