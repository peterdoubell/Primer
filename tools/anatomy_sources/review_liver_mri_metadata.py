#!/usr/bin/env python3
"""Preserve source MRI readings without counting repeated headers or implying eligibility."""
import argparse
import hashlib
import json
from pathlib import Path


def readings(headers,rows):
    result=[];repeated=[];empty=[];section_headers=[]
    for number,row in enumerate(rows,2):
        if not any(x is not None for x in row):empty.append(number);continue
        if row[0]==headers[0]:
            if len(row)!=len(headers) or any(value is not None and value!=header for header,value in zip(headers,row)):
                raise ValueError('Ambiguous header-like source row')
            repeated.append(number);section_headers.append({'source_row':number,'header_values':list(row),
                'source_columns_omitted':[header for header,value in zip(headers,row) if value is None]});continue
        value=dict(zip(headers,row))
        if not isinstance(value.get('PatientID'),str) or not value['PatientID'].startswith('TCGA-'):
            raise ValueError('Unexpected source case identity')
        date=value.get('StudyDate')
        value['StudyDate']=date.isoformat() if hasattr(date,'isoformat') else date
        result.append({'source_row':number,'source_values':value,'diagnostic_eligibility_verified':False,'clinical_approval':False})
    return {'source_readings':result,'repeated_header_rows':repeated,'empty_source_rows':empty,
            'source_patient_ids':sorted({r['source_values']['PatientID'] for r in result}),
            'source_section_headers':section_headers}


def review(path,output):
    import openpyxl
    workbook=openpyxl.load_workbook(path,read_only=True,data_only=True)
    sheet=workbook['Sheet1'];rows=sheet.values;headers=next(rows);record=readings(headers,rows);workbook.close()
    record.update({'source_file':path.name,'source_workbook_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                   'source_doi':'10.5281/zenodo.8179129','source_version':'1.1','source_workbook_modified':False,
                   'tumour_size_unit_independently_verified':False,'source_category_labels_recomputed':False,
                   'phase_or_sequence_coverage_verified':False,'clinical_approval':False,
                   'limits':['Preserve source size values without assuming millimetres or applying a category rule.',
                             'Treat comments, residual/treatment context and eligible patient risk as review requirements.',
                             'A hepatobiliary-specific agent label does not itself establish hepatobiliary phase acquisition.',
                             'Do not treat missing risk context or a dataset category as a new clinical eligibility/diagnosis decision.']})
    output.write_text(json.dumps(record,indent=2)+'\n');print('Unique source patients',len(record['source_patient_ids']),'source readings',len(record['source_readings']),'repeated headers',record['repeated_header_rows'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('metadata',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();review(a.metadata,a.output)
