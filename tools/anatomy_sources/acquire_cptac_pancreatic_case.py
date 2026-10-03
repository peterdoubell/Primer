#!/usr/bin/env python3
"""Acquire paired source-labelled original CPTAC pancreatic CT and RTSTRUCT objects without inferring phase or anatomy."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.anatomy_sources.audit_tcia_series_archive import audit_archive


def validate_selection(selection):
    if not re.fullmatch(r'C3[NL]-\d{5}',selection['case_id']):raise ValueError('Unexpected source case identifier')
    pairs=selection['source_pairs']
    if len(pairs)!=2 or {p['role'] for p in pairs}!={'arterial-labelled','venous-labelled'}:raise ValueError('Need both explicitly identified source CT references')
    tracking=set();studies=set();ct_ids=set();annotation_ids=set();objects=[]
    for pair in pairs:
        row=pair['annotation_row'];ct=pair['original_ct_series'];annotation=pair['annotation_series']
        if row['Annotation Type']!='Segmentation' or row['Modality']!='RTSTRUCT' or row['ReferencedSeriesModality']!='CT' or ct['Modality']!='CT' or annotation['Modality']!='RTSTRUCT':raise ValueError('Seed, negative assessment or modality cannot substitute for a CT segmentation pair')
        if row['ClinicalTrialTimePointID']!='Pre-Dose':raise ValueError('Source treatment time point differs')
        if row['ReferencedSeriesInstanceUID']!=ct['SeriesInstanceUID'] or row['SeriesInstanceUID']!=annotation['SeriesInstanceUID']:raise ValueError('Source reference differs')
        if not ct['PatientID']==annotation['PatientID']==row['PatientID']==selection['case_id']:raise ValueError('Source case identities differ')
        if not ct['StudyInstanceUID']==annotation['StudyInstanceUID']==row['StudyInstanceUID']:raise ValueError('Source study identities differ')
        for s in (ct,annotation):
            if s['Collection']!='CPTAC-PDA' or s['LicenseURI']!='https://creativecommons.org/licenses/by/4.0/':raise ValueError('Source collection or current selected-series licence differs')
        tracking.add(row['Tracking UID']);studies.add(row['StudyInstanceUID']);ct_ids.add(ct['SeriesInstanceUID']);annotation_ids.add(annotation['SeriesInstanceUID'])
        objects.extend([(pair['role']+'-ct',ct),(pair['role']+'-annotation',annotation)])
    if len(tracking)!=1 or len(studies)!=1 or len(ct_ids)!=2 or len(annotation_ids)!=2:raise ValueError('Source observation/study correspondence or distinct references unresolved')
    return objects


def acquire(selection_path,output):
    selection=json.loads(selection_path.read_text());objects=validate_selection(selection);output.mkdir(parents=True,exist_ok=True)
    for role,series in objects:
        name=selection['case_id']+'-'+role+'.zip';path=output/name;partial=output/(name+'.partial')
        if partial.exists():raise ValueError('Existing partial file requires inspecting its original writer; do not restart blindly')
        url='https://services.cancerimagingarchive.net/nbia-api/services/v1/getImageWithMD5Hash?'+urllib.parse.urlencode({'SeriesInstanceUID':series['SeriesInstanceUID']})
        if not path.exists():
            with urllib.request.urlopen(url,timeout=120) as response,partial.open('xb') as target:
                count=0
                for chunk in iter(lambda:response.read(1024*1024),b''):
                    target.write(chunk);count+=len(chunk)
                    if count//(64*1024*1024)!=(count-len(chunk))//(64*1024*1024):print(role,count,'bytes received',flush=True)
                expected=response.headers.get('Content-Length')
                if expected is not None and count!=int(expected):raise ValueError('Incomplete source archive body')
            partial.rename(path)
        report=audit_archive(path,int(series['ImageCount']),int(series['FileSize']))
        report.update(source_case=selection['case_id'],role=role,source_series_instance_uid=series['SeriesInstanceUID'],download_url=url,
                      original_image_doi=selection['original_image_doi'],annotation_doi=selection['annotation_doi'],
                      source_selection_sha256=hashlib.sha256(selection_path.read_bytes()).hexdigest(),source_values_changed=False,runtime_promoted=False)
        (output/(selection['case_id']+'-'+role+'-archive-audit.json')).write_text(json.dumps(report,indent=2)+'\n')
        print(role,'publisher MD5/CRC verified',report['dicom_count'],'objects;',report['dicom_bytes'],'DICOM bytes',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--selection',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();acquire(a.selection,a.output)
