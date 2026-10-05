#!/usr/bin/env python3
"""Export every native renal CT voxel from one acquisition with exact reversible HU encoding."""
import argparse,gzip,hashlib,json
from pathlib import Path


def export(root,output):
    import numpy as np
    from tools.anatomy_sources.review_cptac_renal_contours import verified_objects
    from tools.anatomy_sources.acquire_cptac_renal_case import validate_selection
    selection_path=root/'C3N-03018-selection.json';selection=json.loads(selection_path.read_text());validate_selection(selection)
    all_objects=verified_objects(root,'original-ct');images=[d for d in all_objects if str(d.AcquisitionNumber)=='1']
    images.sort(key=lambda d:float(d.ImagePositionPatient[2]))
    if len(all_objects)!=850 or len(images)!=417:raise ValueError('Original acquisition counts differ')
    positions=np.asarray([d.ImagePositionPatient for d in images],float)
    if not np.array_equal(np.diff(positions,axis=0),np.tile([0,0,.625],(416,1))):raise ValueError('Native source position steps differ')
    shape=(417,512,512);volume=np.empty(shape,dtype='<i2');frames=[]
    for index,d in enumerate(images):
        if (list(map(float,d.ImageOrientationPatient))!=[1,0,0,0,1,0] or str(d.AcquisitionTime)!='104940.737882'
            or int(d.Rows)!=512 or int(d.Columns)!=512 or float(d.RescaleSlope)!=1 or float(d.RescaleIntercept)!=-1024
            or str(d.RescaleType)!='HU' or list(map(float,d.PixelSpacing))!=[.976562,.976562]
            or float(d.SliceThickness)!=.625 or float(d.SpacingBetweenSlices)!=2.5):raise ValueError('Native source geometry/scale differs')
        stored=d.pixel_array;hu=stored.astype(np.int32)-1024
        if hu.min()<-32768 or hu.max()>32767:raise ValueError('Native HU cannot be preserved in signed 16-bit format')
        volume[index]=hu
        if not np.array_equal(volume[index].astype(np.int32)+1024,stored.astype(np.int32)):raise ValueError('Exact source stored-value round trip differs')
        frames.append({'index':index,'source_sop_instance_uid':str(d.SOPInstanceUID),'source_position_lps_mm':positions[index].tolist(),
                       'hu_plane_sha256':hashlib.sha256(volume[index].tobytes()).hexdigest()})
    output.mkdir(parents=True,exist_ok=True);raw=volume.tobytes();compressed=gzip.compress(raw,compresslevel=6,mtime=0)
    if gzip.decompress(compressed)!=raw:raise ValueError('Lossless volume encoding differs')
    path=output/'volume.int16le.bin.gz';path.write_bytes(compressed)
    probes=[]
    for z,y,x in [(0,0,0),(416,511,511),(208,256,256),(275,250,175),(100,100,100)]:probes.append({'index_xyz':[x,y,z],'hu':int(volume[z,y,x])})
    geometry_path=Path('docs/cptac-renal-source-review/C3N-03018-original-geometry-review.json')
    result={'schema_version':1,'case_id':selection['case_id'],'dataset_doi':selection['original_image_doi'],'license':'CC BY 4.0',
      'license_url':'https://creativecommons.org/licenses/by/4.0/','attribution':'CPTAC-CCRCC, The Cancer Imaging Archive. Original imaging DOI '+selection['original_image_doi']+'. CC BY 4.0. Derivative: acquisition-separated, reversible integer HU encoding; no source voxel resampling.',
      'source_ct_archive_sha256':json.loads((root/'C3N-03018-original-ct-archive-audit.json').read_text())['archive_sha256'],
      'source_selection_sha256':hashlib.sha256(selection_path.read_bytes()).hexdigest(),'source_geometry_review_sha256':hashlib.sha256(geometry_path.read_bytes()).hexdigest(),
      'selected_acquisition_number':1,'selected_acquisition_frames':417,'other_acquisition_frames_retained_in_source_archive':433,
      'source_shape_zyx':list(shape),'texture_shape_xyz':[512,512,417],'source_spacing_xyz_mm':[.976562,.976562,.625],
      'origin_lps_mm':positions[0].tolist(),'image_orientation_patient':[1,0,0,0,1,0],
      'declared_spacing_between_slices_mm':2.5,'observed_interplane_step_mm':.625,'slice_thickness_mm':.625,
      'binary_dtype':'signed_int16_little_endian','binary_index_order':'Z,Y,X; native X fastest','source_rescale_slope':1,'source_rescale_intercept':-1024,
      'file':path.name,'uncompressed_bytes':len(raw),'compressed_bytes':len(compressed),'uncompressed_sha256':hashlib.sha256(raw).hexdigest(),'compressed_sha256':hashlib.sha256(compressed).hexdigest(),
      'minimum_hu':int(volume.min()),'maximum_hu':int(volume.max()),'probes':probes,'frames':frames,
      'source_stored_values_round_trip_verified':True,'source_value_encoding_changed':True,'source_information_changed':False,
      'source_voxels_resampled_cropped_or_dropped':False,'source_acquisitions_interleaved_or_deduplicated':False,
      'annotation_or_segmentation_included':False,'named_phase_verified':False,'whole_kidney_or_fine_anatomy_verified':False,
      'clinical_approval':False,'model_coverage_granted':False,
      'limitations':['Original 2.5 mm spacing tag and observed 0.625 mm plane step remain separate; no tag is overwritten or used to fit geometry.',
                     'An oncological source case is not a normal renal atlas or a trauma case; collection/source labels do not independently establish phase, histology or every structure.',
                     'The viewer displays source voxel data, not a segmented organ model; transfer functions and projections cannot establish tissue identity, perfusion, viability or complete clinical interpretation.']}
    (output/'volume.provenance.json').write_text(json.dumps(result,indent=2)+'\n');print('Preserved',volume.size,'native voxels;',len(compressed),'compressed bytes',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();export(a.source_root,a.output)
