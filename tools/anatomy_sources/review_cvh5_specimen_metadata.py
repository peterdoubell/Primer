#!/usr/bin/env python3
"""Bind published specimen/terminology facts without assigning unreported image calibration."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
OUTPUT=Path(__file__).resolve().parents[2]/'docs/cvh5-specimen-metadata-review'


def text(element):return ''.join(n.text or '' for n in element.iter(W+'t'))


def paragraph_columns(paragraph):
    parts=['']
    for run in paragraph.iter(W+'r'):
        for n in run:
            if n.tag==W+'t':parts[-1]+=n.text or ''
            elif n.tag==W+'tab':parts.append('')
    return parts


def review(table,source,candidates):
    output=OUTPUT
    raw=table.read_bytes();meta=json.loads((source/'source-metadata.json').read_text())
    expected=next(u.split('md5=')[1] for u in meta['media_urls'] if '/pone.0132226.s009.docx?' in u)
    if hashlib.md5(raw).hexdigest()!=expected:raise ValueError('Original specimen table differs')
    with zipfile.ZipFile(table) as z:
        if z.testzip() is not None:raise ValueError('Source DOCX CRC differs')
        document_raw=z.read('word/document.xml');doc=ET.fromstring(document_raw)
    tables=[]
    for t in doc.iter(W+'tbl'):
        tables.append([[text(c) for c in row.findall(W+'tc')] for row in t.findall(W+'tr')])
    if len(tables)!=3:raise ValueError('Source table topology differs')
    first=tables[0];column=first[0].index('CVH5');facts={row[0]:row[column] for row in first[1:]}
    if facts['Age']!='25' or facts['Section thickness (mm)']!='0.2' or re.sub(r'\s+','',facts['Image Resolution'])!='4064×2704':raise ValueError('Reviewed specimen facts differ')
    active=False;terms=[]
    for paragraph in doc.iter(W+'p'):
        s=text(paragraph)
        if s.startswith('S1 Table C.'):active=True;continue
        if s.startswith('S1 Table D.'):break
        if not active or not s.strip() or s.startswith('Name used in present study'):continue
        columns=paragraph_columns(paragraph)
        terms.append({'study_name_raw':columns[0],'study_name':columns[0].strip(),
                      'source_terminologia_anatomica_column':columns[1].strip() if len(columns)>1 else '',
                      'textual_link_is_anatomical_validation':False})
    inv_raw=(source/'original-model-inventory.json').read_bytes();inv=json.loads(inv_raw)
    nodes={n['name'].strip():n for n in inv['model_nodes']};alias={'Denonvilliers’ fascia':'Denonvillier’s fascia'}
    if len(terms)!=47:raise ValueError('Incomplete source terminology list')
    for row in terms:
        key=alias.get(row['study_name'],row['study_name'])
        if key not in nodes:raise ValueError('Unmatched source term: '+row['study_name'])
        row['source_model_node_name']=nodes[key]['name'];row['source_resource_name']=nodes[key]['resource_name']
        row['spelling_alias_applied']=key!=row['study_name']
    if {r['source_model_node_name'] for r in terms}!={n['name'] for n in inv['model_nodes']}:raise ValueError('Incomplete model-name linkage')
    section_raw=(source/'source-review.json').read_bytes();sections=json.loads(section_raw)
    candidate_raw=(candidates/'candidate-geometry-review.json').read_bytes();candidate=json.loads(candidate_raw)
    skin=next(r for r in candidate['resources'] if any(n['name']=='Skin' for n in r['source_model_nodes']))
    lo,hi=skin['candidate_bounds_native_units'];extent=[b-a for a,b in zip(lo,hi)];count=len(sections['sections'])
    comparisons=[]
    for spacing in [.2,2.0]:
        comparisons.append({'hypothetical_uniform_page_spacing_mm':spacing,
                            'centre_to_centre_span_if_93_consecutive_planes_mm':(count-1)*spacing,
                            'cell_union_span_if_93_uniform_planes_mm':count*spacing,
                            'is_source_verified_delivered_spacing':False})
    output.mkdir(parents=True,exist_ok=True)
    (output/'original-specimen-table.docx').write_bytes(raw)
    report={'source_table_sha256':hashlib.sha256(raw).hexdigest(),'source_table_publisher_md5_verified':True,
            'source_document_xml_sha256':hashlib.sha256(document_raw).hexdigest(),
            'source_model_inventory_sha256':hashlib.sha256(inv_raw).hexdigest(),'source_sections_review_sha256':hashlib.sha256(section_raw).hexdigest(),
            'candidate_geometry_review_sha256':hashlib.sha256(candidate_raw).hexdigest(),
            'source_specimen':'CVH5','source_sex_label':facts[''],'source_age_years':25,
            'source_height_mm':1700,'source_weight_kg':59,'source_sectioning_direction':facts['Sectioning direction'],
            'nominal_acquired_section_thickness_mm':.2,'reported_original_image_resolution':[4064,2704],
            'source_table_cells':tables,'source_terminology_rows':terms,'source_terminology_count':len(terms),
            'encoded_model_node_count':len(inv['model_nodes']),'source_caption_structure_count':46,
            'caption_count_discrepancy_author_confirmed_resolved':False,
            'delivered_section_count':count,'delivered_pdf_image_dimensions':[466,530],
            'delivered_pages_are_consecutive_acquired_planes_verified':False,'delivered_plane_spacing_mm':None,
            'delivered_inplane_spacing_mm':None,'delivered_crop_resize_transform':None,'section_model_registration_verified':False,
            'candidate_skin_extent_native_units':extent,'candidate_unit_scale_to_metres':candidate['declared_unit_scale_to_metres'],
            'hypothetical_depth_comparisons':comparisons,'cohort_table_is_individual_CVH5_measurement_control':False,
            'whole_EAS_coverage_from_named_EAS_model_granted':False,'terminology_mapping_is_universal_taxonomy':False,
            'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False,
            'limits':['Source nominal section thickness is not automatically spacing of the 93 published PDF images.',
                      'Image dimensions do not establish physical in-plane spacing, crop transform or acquired-master availability.',
                      'The source EAS name describes the study subcutaneous portion; full EAS/other taxonomy requires separate review.',
                      'Combined lumen/vessel model names do not independently resolve every reportable substructure or branch.',
                      'Cohort means must not replace individual specimen measurements or calibration.']}
    (output/'specimen-and-terminology-review.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Linked 47 source terms; retained CVH5 biometry and unreported delivery calibration as unknown.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--table',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--candidates',type=Path,required=True)
    a=p.parse_args();review(a.table,a.source,a.candidates)
