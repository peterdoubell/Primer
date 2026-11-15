#!/usr/bin/env python3
"""Separate explicit HCC CT acquisitions; never infer phase identity from a title."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.anatomy_sources.review_tcia_lung_case import read_series


def acquisition_groups(images):
    groups=defaultdict(list)
    for image in images:
        if not hasattr(image,'AcquisitionNumber'):
            raise ValueError('Missing acquisition number; phase/volume partition unresolved')
        groups[str(image.AcquisitionNumber)].append(image)
    for group in groups.values():
        positions=[tuple(map(float,d.ImagePositionPatient)) for d in group]
        if len(positions)!=len(set(positions)):
            raise ValueError('Repeated positions within one acquisition; further partition needed')
        sops=[str(d.SOPInstanceUID) for d in group]
        if len(sops)!=len(set(sops)):raise ValueError('Repeated source instance')
        group.sort(key=lambda d:float(d.ImagePositionPatient[2]))
    return dict(groups)


def audit(root,output):
    import numpy as np
    contrast=root/'hcc-003-multiphase.zip';pre=root/'hcc-003-pre.zip';seg_path=root/'hcc-003-seg.zip'
    images=read_series(contrast);groups=acquisition_groups(images);seg=read_series(seg_path)[0]
    by_sop={str(d.SOPInstanceUID):(number,d) for number,group in groups.items() for d in group}
    refs={str(d.ReferencedSOPInstanceUID) for d in seg.ReferencedSeriesSequence[0].ReferencedInstanceSequence}
    if not refs<=set(by_sop):raise ValueError('SEG source instances unavailable')
    referred_acquisitions={by_sop[sop][0] for sop in refs}
    # Mixed references must be preserved as unresolved derivation scope, not collapsed
    # into a guessed single phase or silently rewritten.
    mixed_references = len(referred_acquisitions) != 1
    descriptors={int(d.SegmentNumber):d for d in seg.SegmentSequence};raw=seg.pixel_array
    frame_records=[];counts={k:0 for k in descriptors}
    for index,frame in enumerate(seg.PerFrameFunctionalGroupsSequence):
        label=int(frame.SegmentIdentificationSequence[0].ReferencedSegmentNumber)
        source=frame.DerivationImageSequence[0].SourceImageSequence
        if not source:raise ValueError('Missing per-frame derivation source')
        source_rows=[]
        for item in source:
            sop=str(item.ReferencedSOPInstanceUID)
            if sop not in by_sop:raise ValueError('SEG frame source unavailable')
            image=by_sop[sop][1];position=np.asarray(frame.PlanePositionSequence[0].ImagePositionPatient,float)
            ct_direction=np.asarray(image.ImageOrientationPatient,float).reshape(2,3)
            seg_direction=np.asarray(seg.SharedFunctionalGroupsSequence[0].PlaneOrientationSequence[0].ImageOrientationPatient,float).reshape(2,3)
            signs=[]
            for ct_axis,seg_axis in zip(ct_direction,seg_direction):
                if np.array_equal(ct_axis,seg_axis):signs.append(1)
                elif np.array_equal(ct_axis,-seg_axis):signs.append(-1)
                else:raise ValueError('SEG axis correspondence needs separate review')
            spacing=np.asarray(image.PixelSpacing,float)
            seg_spacing=np.asarray(seg.SharedFunctionalGroupsSequence[0].PixelMeasuresSequence[0].PixelSpacing,float)
            if not np.array_equal(spacing,seg_spacing):raise ValueError('Source/SEG sampling differs')
            expected=np.asarray(image.ImagePositionPatient,float).copy()
            if signs[0]<0:expected+=ct_direction[0]*spacing[1]*(image.Columns-1)
            if signs[1]<0:expected+=ct_direction[1]*spacing[0]*(image.Rows-1)
            delta=float(np.max(np.abs(position-expected)))
            if not (np.allclose(position,expected,atol=1e-9,rtol=0) or np.allclose(position,np.round(expected,4),atol=1e-9,rtol=0)):
                raise ValueError('SEG/source grid origin does not match declared index directions or documented decimal precision')
            source_rows.append({'source_sop':sop,'source_acquisition':by_sop[sop][0],
                                'corresponding_grid_origin_difference_mm':delta,'in_plane_axis_signs':signs,
                                'included_in_declared_series_references':sop in refs})
        counts[label]+=int(np.count_nonzero(raw[index]))
        frame_records.append({'seg_frame':index,'segment_number':label,'derivation_sources':source_rows})
    frame_source_sops={item['source_sop'] for f in frame_records for item in f['derivation_sources']}
    frame_source_acquisitions={item['source_acquisition'] for f in frame_records for item in f['derivation_sources']}
    rows=[]
    for number,group in sorted(groups.items()):
        positions=np.asarray([d.ImagePositionPatient for d in group],float)
        if any(d.PatientID!='HCC_003' or d.SeriesInstanceUID!=group[0].SeriesInstanceUID for d in group):
            raise ValueError('Source identity/frame differs')
        rows.append({'acquisition_number':number,'source_images':len(group),'distinct_positions':len(positions),
          'source_sops':[str(d.SOPInstanceUID) for d in group],'position_bounds_lps':[positions.min(0).tolist(),positions.max(0).tolist()],
          'observed_slice_steps_mm':sorted(set(np.diff(positions[:,2]).tolist())),
          'pixel_spacing_mm':list(map(float,group[0].PixelSpacing)),
          'frame_of_reference_uids':sorted({str(d.FrameOfReferenceUID) for d in group}),
          'slice_thickness_values':sorted({str(getattr(d,'SliceThickness','not_reported')) for d in group}),
          'phase_name':None,'phase_identity_verified':False})
    pre_images=read_series(pre)
    result={'case_id':'HCC_003','source_doi':'10.7937/TCIA.5FNA-0924',
      'contrast_archive_sha256':hashlib.sha256(contrast.read_bytes()).hexdigest(),'pre_archive_sha256':hashlib.sha256(pre.read_bytes()).hexdigest(),
      'seg_archive_sha256':hashlib.sha256(seg_path.read_bytes()).hexdigest(),'combined_contrast_images':len(images),
      'combined_distinct_positions':len({tuple(d.ImagePositionPatient) for d in images}),
      'acquisitions':rows,'seg_referenced_acquisition':None if mixed_references else next(iter(referred_acquisitions)),
      'seg_source_acquisition_counts':{number:sum(by_sop[sop][0]==number for sop in refs) for number in sorted(referred_acquisitions)},
      'status':'held_unreconciled_multi_acquisition_derivation',
      'per_frame_source_acquisitions':sorted(frame_source_acquisitions),
      'per_frame_unique_source_images':len(frame_source_sops),
      'per_frame_sources_not_in_declared_series_references':len(frame_source_sops-refs),
      'seg_referenced_source_images':len(refs),'seg_frames':len(frame_records),'per_frame_references':frame_records,
      'segments':[{'source_segment_number':k,'source_label':str(d.SegmentLabel),'source_algorithm_type':str(d.SegmentAlgorithmType),
                   'source_positive_voxels':counts[k],'clinical_boundary_approval':False} for k,d in descriptors.items()],
      'pre_images':len(pre_images),'pre_slice_thickness_values':sorted({str(getattr(d,'SliceThickness','not_reported')) for d in pre_images}),
      'acquisition_time_values':sorted({str(getattr(d,'AcquisitionTime','not_reported')) for d in images}),
      'contrast_agent_values':sorted({str(getattr(d,'ContrastBolusAgent','not_reported')) for d in images}),
      'seg_frame_of_reference_uid':str(seg.FrameOfReferenceUID),
      'ct_frame_of_reference_uids':sorted({str(d.FrameOfReferenceUID) for d in images}),
      'seg_ct_frame_of_reference_identity_match':all(d.FrameOfReferenceUID==seg.FrameOfReferenceUID for d in images),
      'phase_names_assigned':False,'source_acquisitions_merged':False,'registration_fitted':False,'source_values_changed':False,
      'clinical_approval':False,'runtime_promoted':False,
      'limits':['Explicit acquisition number separates source volumes; it does not establish arterial/portal/delayed phase identity.',
                'Identical grids do not prove breath-hold alignment or cross-phase lesion correspondence.',
                'SEMIAUTOMATIC source labels are not automatically clinically accurate or complete anatomy.',
                'Source PRE LIVER title and thickness do not provide fine precontrast morphology or prove treatment state.']}
    output.write_text(json.dumps(result,indent=2)+'\n');print('Acquisitions',[(r['acquisition_number'],r['source_images']) for r in rows],'; SEG references',result['seg_referenced_acquisition'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();audit(a.source_root,a.output)
