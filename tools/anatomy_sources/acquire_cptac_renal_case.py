#!/usr/bin/env python3
"""Acquire an explicitly linked original CPTAC renal CT/RTSTRUCT pair and verify publisher MD5."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.anatomy_sources.audit_tcia_series_archive import audit_archive


def validate_selection(selection):
    row = selection['annotation_row']; ct = selection['original_ct_series']; annotation = selection['annotation_series']
    if row['Annotation Type'] != 'Segmentation' or row['Modality'] != 'RTSTRUCT' or ct['Modality'] != 'CT' or annotation['Modality'] != 'RTSTRUCT':
        raise ValueError('Need original CT and actual segmentation, not a seed point or negative assessment')
    if row['ReferencedSeriesInstanceUID'] != ct['SeriesInstanceUID'] or row['SeriesInstanceUID'] != annotation['SeriesInstanceUID']:
        raise ValueError('Annotation reference does not match selected source series')
    if not ct['PatientID'] == annotation['PatientID'] == row['PatientID'] == selection['case_id']:
        raise ValueError('Source case identity differs')
    if not ct['StudyInstanceUID'] == annotation['StudyInstanceUID'] == row['StudyInstanceUID']:
        raise ValueError('Source study identity differs')
    for series in (ct, annotation):
        if series['LicenseURI'] != 'https://creativecommons.org/licenses/by/4.0/' or series['Collection'] != 'CPTAC-CCRCC':
            raise ValueError('Unexpected source licence or collection; review required')
    return [('original-ct', ct), ('annotation', annotation)]


def acquire(selection_path, output):
    selection = json.loads(selection_path.read_text()); pair = validate_selection(selection)
    output.mkdir(parents=True, exist_ok=True)
    for role, series in pair:
        name = selection['case_id'] + '-' + role + '.zip'; path = output/name; partial = output/(name+'.partial')
        if partial.exists(): raise ValueError('Partial archive exists; inspect its original writer before restarting')
        url = 'https://services.cancerimagingarchive.net/nbia-api/services/v1/getImageWithMD5Hash?' + urllib.parse.urlencode({'SeriesInstanceUID':series['SeriesInstanceUID']})
        if not path.exists():
            with urllib.request.urlopen(url, timeout=120) as response, partial.open('xb') as target:
                total = 0
                for chunk in iter(lambda: response.read(1024*1024), b''):
                    target.write(chunk); total += len(chunk)
                    if total // (64*1024*1024) != (total-len(chunk)) // (64*1024*1024): print(role, total, 'bytes received', flush=True)
                expected = response.headers.get('Content-Length')
                if expected is not None and total != int(expected): raise ValueError('Incomplete HTTP archive body')
            partial.rename(path)
        review = audit_archive(path, int(series['ImageCount']), int(series['FileSize']))
        review.update(role=role, source_series_instance_uid=series['SeriesInstanceUID'], download_url=url,
                      source_selection_sha256=hashlib.sha256(selection_path.read_bytes()).hexdigest(),
                      original_image_doi=selection['original_image_doi'], annotation_doi=selection['annotation_doi'],
                      source_values_changed=False, runtime_promoted=False)
        (output/(selection['case_id']+'-'+role+'-archive-audit.json')).write_text(json.dumps(review, indent=2)+'\n')
        print(role, 'verified', review['dicom_count'], 'DICOM objects;', review['dicom_bytes'], 'bytes', flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();acquire(a.selection,a.output)
