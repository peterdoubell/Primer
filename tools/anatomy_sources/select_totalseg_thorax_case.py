#!/usr/bin/env python3
"""Preserve one complete source CT/mask candidate for native review, no claims."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

NAMES=['lung_upper_lobe_left.nii.gz','lung_lower_lobe_left.nii.gz','lung_upper_lobe_right.nii.gz','lung_middle_lobe_right.nii.gz','lung_lower_lobe_right.nii.gz','trachea.nii.gz']


def extract(root,output,case):
    acquisition=json.loads((root/'acquisition.json').read_text())
    if not acquisition['publisher_checksum_passed']:raise ValueError('Unverified source archive')
    output.mkdir(parents=True,exist_ok=True);rows=[]
    with zipfile.ZipFile(root/acquisition['archive']) as archive:
        meta_raw=archive.read('meta.csv');reader=csv.DictReader(io.StringIO(meta_raw.decode('utf-8-sig')),delimiter=';');all_meta=list(reader)
        print('Metadata columns:',reader.fieldnames)
        matches=[row for row in all_meta if case in row.values()]
        for name in [case+'/ct.nii.gz',*[case+'/segmentations/'+n for n in NAMES]]:
            item=archive.getinfo(name);data=archive.read(name)  # zipfile verifies CRC during read.
            path=output/Path(name).name;path.write_bytes(data)
            rows.append({'source_member':name,'file':path.name,'bytes':len(data),'crc32':f'{item.CRC:08x}','sha256':hashlib.sha256(data).hexdigest()})
    (output/'source-meta-row.json').write_text(json.dumps(matches,indent=2)+'\n')
    record={'case':case,'source_doi':acquisition['doi'],'source_archive_sha256':acquisition['sha256'],'publisher_archive_checksum_passed':True,
            'selection_basis':'First source case with all requested filenames. Contents and full acquired thoracic extent must be inspected before anatomical use; no normality inferred.',
            'metadata_csv_sha256':hashlib.sha256(meta_raw).hexdigest(),'files':rows,'clinical_approval':False,'runtime_promoted':False,'source_data_changed':False}
    (output/'acquisition.json').write_text(json.dumps(record,indent=2)+'\n');print('Preserved source members:',len(rows))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--case',default='s0011');args=parser.parse_args();extract(args.source,args.output,args.case)
