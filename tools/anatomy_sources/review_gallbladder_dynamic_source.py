#!/usr/bin/env python3
"""Preserve source clip identity and every decoded timestamp without inventing clinical dynamics."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def review(root, output):
    metadata_path=root/'commons-original-metadata.json';metadata=json.loads(metadata_path.read_text())
    source=next(iter(metadata['query']['pages'].values()))['imageinfo'][0]
    clip=root/'Gallbladder_Ultrasound.webm';raw=clip.read_bytes()
    if len(raw)!=source['size'] or hashlib.sha1(raw).hexdigest()!=source['sha1']:
        raise ValueError('Original provider clip size/hash differs')
    rights=source['extmetadata']
    if rights['LicenseShortName']['value']!='CC BY-SA 4.0' or rights['LicenseUrl']['value']!='https://creativecommons.org/licenses/by-sa/4.0':
        raise ValueError('Selected source grant differs')
    probe=json.loads((root/'commons-ffprobe.json').read_text())
    frames=json.loads((root/'commons-original-frames.json').read_text())['frames']
    lines=[l for l in (root/'commons-original-framemd5.txt').read_text().splitlines() if l and not l.startswith('#')]
    header=[l for l in (root/'commons-original-framemd5.txt').read_text().splitlines() if l.startswith('#tb')]
    if len(frames)!=len(lines) or len(probe['streams'])!=1 or probe['streams'][0]['codec_type']!='video':
        raise ValueError('Original frame/stream decode accounting differs')
    timeline=[]
    for frame,line in zip(frames,lines):
        fields=[v.strip() for v in line.split(',')]
        timeline.append({'source_timestamp_seconds':frame['best_effort_timestamp_time'],'key_frame':frame['key_frame'],
                         'decoded_frame_md5':fields[-1],'framemd5_pts':int(fields[2]),'decoded_frame_bytes':int(fields[4])})
    times=[float(f['source_timestamp_seconds']) for f in timeline]
    if any(b<=a for a,b in zip(times,times[1:])):raise ValueError('Original timeline is not strictly ordered')
    slots={round(t*30) for t in times};absent=sorted(set(range(max(slots)+1))-slots)
    output.mkdir(parents=True,exist_ok=True);target=output/'original-gallbladder-ultrasound.webm';shutil.copyfile(clip,target)
    result={'source_file_url':source['url'],'source_page_url':'https://commons.wikimedia.org/wiki/File:Gallbladder_Ultrasound.webm',
        'file':target.name,'bytes':len(raw),'publisher_sha1':source['sha1'],'publisher_sha1_verified':True,'sha256':hashlib.sha256(raw).hexdigest(),
        'provider_metadata_sha256':hashlib.sha256(metadata_path.read_bytes()).hexdigest(),'source_timestamp':source['timestamp'],
        'source_rights_metadata':{k:v['value'] for k,v in rights.items() if k in ['LicenseShortName','LicenseUrl','Artist','Credit','ImageDescription']},
        'codec':probe['streams'][0]['codec_name'],'coded_width':source['width'],'coded_height':source['height'],
        'nominal_frame_rate':probe['streams'][0]['r_frame_rate'],'duration_seconds':float(probe['format']['duration']),
        'decoded_frames':timeline,'decoded_frame_count':len(timeline),'decoded_frame_hashes_are_review_decode_not_native_acquisition':True,
        'framemd5_time_base_headers':header,'source_frame_time_base':probe['streams'][0]['time_base'],
        'unrepresented_nominal_30fps_slots':absent,'nominal_slots_are_not_asserted_missing_clinical_acquisition_frames':True,
        'original_frame_intervals_preserved_without_interpolation':True,'original_encoded_clip_altered':False,
        'source_displayed_position_label':'GALLBLADDER LLD','actual_patient_position_independently_verified':False,
        'stone_mobility_verified':False,'compression_response_verified':False,'tenderness_response_verified':False,'doppler_flow_verified':False,
        'native_acquisition_resolution_verified':False,'clinical_diagnosis_verified':False,'clinical_approval':False,'runtime_promoted':False,
        'access_holds':[{'source':'https://doi.org/10.3390/diagnostics16183023','article_identity_primary_source':'https://pubmed.ncbi.nlm.nih.gov/42793808/',
            'publisher_page_http_status':403,'publisher_pdf_http_status':403,'publisher_supplement_http_status':403,
            'source_media_or_grant_acquired':False,'indefinite_unavailability_inferred':False}],
        'limits':['The original uploader licence/description and encoded-file integrity do not prove clinical diagnosis, complete scan coverage or particular dynamic observations.',
            'Changes across source frames may reflect different 2D views, respiration or probe movement; no 3D correspondence or stone mobility is inferred.',
            'LLD is a displayed source label, not independent evidence of performed repositioning. No probe-pressure or clinical tenderness record is supplied.',
            'Coded 1920x1080 video dimensions do not establish native ultrasound resolution, calibration or full wall-layer fidelity.']}
    (output/'original-cine-source-review.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Original clip identity and all decoded frame timestamps preserved.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();review(args.source_root,args.output)
