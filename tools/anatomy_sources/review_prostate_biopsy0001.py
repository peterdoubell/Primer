#!/usr/bin/env python3
"""Audit original MRI/STL/SEG/US objects without fitting or approving anatomy."""
import collections
import gzip
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
import pydicom
from tools.anatomy_sources.native_dicom_geometry import validate_geometry
from tools.anatomy_sources.package_laryngeal_phonation_reference import canonical_gzip

SOURCE = Path('/Users/peter/Documents/ChatGPT/Primer/.research/prostate-native-source')
OUT = ROOT/'docs/prostate-native-source-review/case0001'
CASE = 'Prostate-MRI-US-Biopsy-0001'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def decode_scalar(ds):
    """Independently read the complete uncompressed scalar source payload."""
    if str(ds.file_meta.TransferSyntaxUID)!='1.2.840.10008.1.2.1':
        raise ValueError('Only observed explicit little-endian originals are supported')
    if ds.SamplesPerPixel!=1 or ds.PhotometricInterpretation!='MONOCHROME2' or ds.PixelRepresentation!=0:
        raise ValueError('Unexpected scalar source representation')
    shape=(int(getattr(ds,'NumberOfFrames',1)),int(ds.Rows),int(ds.Columns))
    count=int(np.prod(shape));raw=ds.PixelData
    if ds.BitsAllocated==1:
        if ds.BitsStored!=1 or ds.HighBit!=0:raise ValueError('Unexpected source bit field')
        result=np.unpackbits(np.frombuffer(raw,dtype=np.uint8),bitorder='little')[:count]
        meaningful=(count+7)//8
    elif ds.BitsAllocated in [8,16]:
        if ds.HighBit!=ds.BitsStored-1:raise ValueError('Unexpected source high bit')
        dtype='<u2' if ds.BitsAllocated==16 else 'u1';meaningful=count*(ds.BitsAllocated//8)
        result=np.frombuffer(raw[:meaningful],dtype=dtype)
        # The observed originals have zero unused high bits. Do not mask or alter them.
        if np.any(result >= 2**int(ds.BitsStored)):raise ValueError('Nonzero unused source high bits')
    else:
        raise ValueError('Unexpected allocation')
    if len(raw)!=meaningful+(meaningful%2) or any(raw[meaningful:]):
        raise ValueError('Unexpected source payload length or padding')
    result=result.reshape(shape)
    expected=ds.pixel_array.reshape(shape)
    if not np.array_equal(result,expected):raise ValueError('Independent source scalar decode disagrees')
    return result

def binary_stl(raw):
    if len(raw)<84:raise ValueError('Truncated binary STL')
    count=struct.unpack_from('<I',raw,80)[0]
    if not count or len(raw)!=84+count*50:raise ValueError('Incomplete original STL faces')
    dtype=np.dtype([('normal','<f4',3),('vertices','<f4',(3,3)),('attribute','<u2')])
    triangles=np.frombuffer(raw,offset=84,dtype=dtype,count=count)
    if not np.isfinite(triangles['vertices']).all() or not np.isfinite(triangles['normal']).all():
        raise ValueError('Non-finite original STL value')
    return triangles

def topology(corners):
    # Deduplication here measures adjacency only; original ordered face corners remain untouched.
    vertices,inverse=np.unique(corners.reshape(-1,3),axis=0,return_inverse=True)
    faces=inverse.reshape(-1,3);parent=list(range(len(vertices)))
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]];x=parent[x]
        return x
    edges=collections.Counter()
    for a,b,c in faces:
        for x,y in [(a,b),(b,c),(c,a)]:
            edges[tuple(sorted((int(x),int(y))))]+=1
            x,y=find(int(x)),find(int(y));parent[y]=x
    counts=collections.Counter(find(int(f[0])) for f in faces)
    cross=np.cross(corners[:,1]-corners[:,0],corners[:,2]-corners[:,0])
    return {'unique_coordinate_vertices_for_analysis_only':len(vertices),'triangles':len(faces),
            'component_triangle_counts':sorted(counts.values(),reverse=True),
            'boundary_edges':sum(v==1 for v in edges.values()),'nonmanifold_edges':sum(v>2 for v in edges.values()),
            'zero_area_faces':int(np.sum(np.linalg.norm(cross,axis=1)==0))}

def frame_geometry(ds):
    return {'orientation':list(ds.ImageOrientationPatient),'position_mm':list(ds.ImagePositionPatient),
            'pixel_spacing_mm':list(ds.PixelSpacing),'rows':int(ds.Rows),'columns':int(ds.Columns)}

def review():
    OUT.mkdir(parents=True,exist_ok=True)
    acquisition=json.loads((SOURCE/'original-case0001-acquisition.json').read_text())
    groups=collections.defaultdict(list);records=[];decoded={};total=0
    for row in acquisition['objects']:
        raw=(SOURCE/row['file']).read_bytes()
        if sha(raw)!=row['sha256'] or hashlib.md5(raw).hexdigest()!=row['object_etag']:
            raise ValueError('Original object changed')
        ds=pydicom.dcmread(SOURCE/row['file'])
        if ds.PatientID!=CASE or str(ds.SeriesInstanceUID)!=row['series_uid'] or ds.Modality!=row['modality']:
            raise ValueError('Source identity disagrees with publisher index')
        groups[row['series_uid']].append(ds)
        record={**row,'SOPInstanceUID':str(ds.SOPInstanceUID),'SOPClassUID':str(ds.SOPClassUID),
                'FrameOfReferenceUID':str(getattr(ds,'FrameOfReferenceUID','')),'StudyInstanceUID':str(ds.StudyInstanceUID)}
        if hasattr(ds,'PixelData'):
            array=decode_scalar(ds);total+=array.size;decoded[str(ds.SOPInstanceUID)]=array
            record.update(stored_samples=int(array.size),shape=list(array.shape),dtype=array.dtype.str,
                          independently_decoded_samples_sha256=sha(array.tobytes()),PixelData_sha256=sha(ds.PixelData),
                          stored_scalar_minimum=int(array.min()),stored_scalar_maximum=int(array.max()),
                          source_bits_stored=int(ds.BitsStored),source_rescale_slope=getattr(ds,'RescaleSlope',None),
                          source_rescale_intercept=getattr(ds,'RescaleIntercept',None),
                          source_WindowCenter=str(getattr(ds,'WindowCenter','')),
                          source_WindowWidth=str(getattr(ds,'WindowWidth','')),
                          source_VOILUTFunction=str(getattr(ds,'VOILUTFunction','')))
        records.append(record)
    if len(records)!=106:raise ValueError('Original selected case object inventory changed')
    mri=[];t2=None;t2_sets=None
    for uid,frames in groups.items():
        if frames[0].Modality!='MR':continue
        geometry=validate_geometry([frame_geometry(ds) for ds in frames])
        ordered=[frames[i] for i in geometry['source_frame_order']]
        array=np.stack([decoded[str(ds.SOPInstanceUID)][0] for ds in ordered])
        role='T2' if str(frames[0].SeriesDescription).startswith('t2') else 'producer_ADC' if 'ADC' in str(frames[0].SeriesDescription) else 'producer_calculated_DWI'
        (SOURCE/(role+'-original-u16.bin')).write_bytes(array.astype('<u2',copy=False).tobytes())
        info={'role':role,'SeriesInstanceUID':uid,'SeriesDescription':str(frames[0].SeriesDescription),
              'SOPInstanceUIDs_in_source_plane_order':[str(ds.SOPInstanceUID) for ds in ordered],
              'geometry':geometry,'stored_samples':int(array.size),'stored_samples_sha256':sha(array.astype('<u2',copy=False).tobytes()),
              'ImageType':list(frames[0].ImageType),'source_AcquisitionTime':str(getattr(frames[0],'AcquisitionTime','')),
              'source_has_declared_rescale_or_physical_ADC_units':False,
              'source_DCE_supplied':False,'source_spatial_sampling_is_effective_fine_tissue_resolution':False}
        if frames[0].get((0x0019,0x100c)) is not None:
            info['source_private_0019_100c_value']=str(frames[0][0x0019,0x100c].value)
            info['source_private_creator_0019_0010']=str(frames[0].get((0x0019,0x0010)).value)
        mri.append(info)
        if role=='T2':t2=info;t2_sets={str(ds.SOPInstanceUID):ds for ds in ordered}
    if len(mri)!=3 or t2 is None:raise ValueError('Original MRI source roles changed')
    segmentations=[]
    for frames in groups.values():
        ds=frames[0]
        if ds.Modality!='SEG':continue
        if len(frames)!=1 or ds.SegmentationType!='BINARY' or len(ds.SegmentSequence)!=1:raise ValueError('Unexpected source SEG')
        shared=ds.SharedFunctionalGroupsSequence[0];orientation=list(shared.PlaneOrientationSequence[0].ImageOrientationPatient)
        spacing=list(shared.PixelMeasuresSequence[0].PixelSpacing)
        mask=decoded[str(ds.SOPInstanceUID)];frames_in_order=[];position_errors=[]
        for index,frame in enumerate(ds.PerFrameFunctionalGroupsSequence):
            sources=frame.DerivationImageSequence[0].SourceImageSequence
            if len(sources)!=1:raise ValueError('Ambiguous source SEG frame reference')
            sop=str(sources[0].ReferencedSOPInstanceUID)
            if sop not in t2_sets:raise ValueError('Source SEG refers to an unacquired/different MRI')
            source=t2_sets[sop];position=list(frame.PlanePositionSequence[0].ImagePositionPatient)
            position_errors.append(float(np.max(np.abs(np.array(position,float)-np.array(source.ImagePositionPatient,float)))))
            frames_in_order.append({'orientation':orientation,'position_mm':position,'pixel_spacing_mm':spacing,'rows':int(ds.Rows),'columns':int(ds.Columns)})
        seg_geometry=validate_geometry(frames_in_order)
        if set(str(f.DerivationImageSequence[0].SourceImageSequence[0].ReferencedSOPInstanceUID) for f in ds.PerFrameFunctionalGroupsSequence)!=set(t2_sets):raise ValueError('Source SEG does not refer to every T2 image')
        if str(ds.FrameOfReferenceUID)!=t2_sets[next(iter(t2_sets))].FrameOfReferenceUID:raise ValueError('Different source frame of reference')
        ordered=mask[seg_geometry['source_frame_order']]
        segment=ds.SegmentSequence[0];name='prostate' if str(segment.SegmentLabel)=='Prostate' else 'suspicious_target1'
        if name=='suspicious_target1' and str(segment.SegmentLabel)!='Lesion 1':raise ValueError('Unexpected source label')
        (SOURCE/(name+'-derived-SEG-u8.bin')).write_bytes(ordered.tobytes())
        p=OUT/(name+'-original-SEG.dcm');p.write_bytes((SOURCE/next(r['file'] for r in records if r['SOPInstanceUID']==str(ds.SOPInstanceUID))).read_bytes())
        segmentations.append({'role':name,'SOPInstanceUID':str(ds.SOPInstanceUID),'SeriesInstanceUID':str(ds.SeriesInstanceUID),
                              'original_SEG_file':p.name,'original_SEG_sha256':sha(p.read_bytes()),'SegmentLabel':str(segment.SegmentLabel),
                              'SegmentDescription':str(segment.SegmentDescription),'SegmentAlgorithmType':str(segment.SegmentAlgorithmType),
                              'SegmentAlgorithmName':str(getattr(segment,'SegmentAlgorithmName','')),'geometry':seg_geometry,
                              'stored_samples':int(ordered.size),'stored_samples_sha256':sha(ordered.tobytes()),'foreground_samples':int(np.sum(ordered)),
                              'all_60_T2_SOP_references_exactly_verified':True,'maximum_referenced_T2_plane_position_difference_mm':max(position_errors),
                              'derived_rasterization_is_original_manual_voxel_segmentation':False,
                              'clinical_tumour_boundary_or_all_prostate_tissues_approved':False})
    surfaces=[]
    for frames in groups.values():
        ds=frames[0]
        if ds.Modality!='M3D':continue
        raw=ds.EncapsulatedDocument;length=int(ds.EncapsulatedDocumentLength)
        if len(raw)!=length+(length%2) or any(raw[length:]):raise ValueError('Unexpected encapsulated STL padding')
        raw=raw[:length];triangles=binary_stl(raw);corners=triangles['vertices'];name='prostate' if ds.SeriesDescription=='STL surface of prostate' else 'suspicious_target1'
        if name=='suspicious_target1' and ds.SeriesDescription!='STL surface of lesion 1':raise ValueError('Unexpected original mesh role')
        (OUT/(name+'-original.stl')).write_bytes(raw)
        corners_raw=corners.astype('<f4').tobytes();(OUT/(name+'-original-face-corners.f32.gz')).write_bytes(canonical_gzip(corners_raw))
        stat=topology(corners);model={'role':name,'SOPInstanceUID':str(ds.SOPInstanceUID),'SeriesInstanceUID':str(ds.SeriesInstanceUID),
                'source_STL_sha256':sha(raw),'source_STL_header_hex':raw[:80].hex(),'source_face_corners_sha256':sha(corners_raw),
                'original_normals_sha256':sha(triangles['normal'].astype('<f4').tobytes()),
                'original_attributes_sha256':sha(triangles['attribute'].astype('<u2').tobytes()),'bounds':[corners.min((0,1)).tolist(),corners.max((0,1)).tolist()],
                'FrameOfReferenceUID':str(ds.FrameOfReferenceUID),'source_MRI_same_FrameOfReferenceUID':str(ds.FrameOfReferenceUID)==t2_sets[next(iter(t2_sets))].FrameOfReferenceUID,
                'source_STL_contains_explicit_coordinate_space_header':b'SPACE=' in raw[:80],
                'source_positions_normals_faces_or_attributes_changed':False,'native_US_registration_verified':False,
                'clinical_fine_anatomical_or_histological_boundary_approval':False,**stat}
        surfaces.append(model)
    us=[]
    for frames in groups.values():
        ds=frames[0]
        if ds.Modality!='US':continue
        creator=ds.get((0x1129,0x0010));voxel=ds.get((0x1129,0x1016))
        us.append({'SOPInstanceUID':str(ds.SOPInstanceUID),'SeriesInstanceUID':str(ds.SeriesInstanceUID),
                   'stored_samples':int(decoded[str(ds.SOPInstanceUID)].size),'source_pixel_spacing':list(ds.PixelSpacing),
                   'private_creator':str(creator.value) if creator else None,'private_voxel_size':str(voxel.value) if voxel else None,
                   'standard_ImagePositionPatient_present':hasattr(ds,'ImagePositionPatient'),
                   'standard_ImageOrientationPatient_present':hasattr(ds,'ImageOrientationPatient'),
                   'physical_axes_or_native_MRI_US_registration_verified':False})
    result={'schema_version':1,'case':CASE,'source_collection_url':'https://www.cancerimagingarchive.net/collection/prostate-mri-us-biopsy/',
            'license':'CC BY 4.0','source_acquisition_sha256':sha((SOURCE/'original-case0001-acquisition.json').read_bytes()),
            'objects':records,'original_objects_verified':len(records),'original_scalar_samples_independently_decoded':int(total),
            'source_age':'064Y','source_sex':'M','MRI_series':mri,'derived_segmentations':segmentations,'original_surfaces':surfaces,'original_US_series':us,
            'prostate_outline_is_every_prostate_zone_capsule_nerve_vessel_or_duct':False,
            'source_ROI_is_proven_tumour_or_current_patient_histology':False,
            'source_likert_score_is_current_PI_RADS_v2_1':False,
            'actor_resampling_fitting_smoothing_capping_component_removal_or_decimation':False,
            'clinical_anatomical_or_full_reporting_approval_granted':False,'runtime_promoted':False}
    (OUT/'original-source-review.json').write_text(json.dumps(result,indent=2)+'\n')
    (OUT/'original-acquisition.json').write_text(json.dumps(acquisition,indent=2)+'\n')
    print(len(records),'original objects;',int(total),'independently decoded original scalar samples')
    print([(r['role'],r['triangles'],r['component_triangle_counts']) for r in surfaces])
    return result

if __name__=='__main__':
    review()
