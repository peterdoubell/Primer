"""Nominal acquisition facts and study-specific names cannot silently calibrate delivered images."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from tools.anatomy_sources.review_cvh5_specimen_metadata import paragraph_columns

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/cvh5-specimen-metadata-review'


def test_exact_source_table_and_all_model_term_links_are_retained():
    r=json.loads((REVIEW/'specimen-and-terminology-review.json').read_text())
    assert r['source_table_sha256']==hashlib.sha256((REVIEW/'original-specimen-table.docx').read_bytes()).hexdigest()
    assert r['source_table_publisher_md5_verified'] and r['source_terminology_count']==47
    source=ROOT/'docs/cvh5-pelvic-source-review/original-model-inventory.json';inv=json.loads(source.read_text())
    assert r['source_model_inventory_sha256']==hashlib.sha256(source.read_bytes()).hexdigest()
    assert {row['source_model_node_name'] for row in r['source_terminology_rows']}=={n['name'] for n in inv['model_nodes']}
    assert sum(row['spelling_alias_applied'] for row in r['source_terminology_rows'])==1
    assert all(not row['textual_link_is_anatomical_validation'] for row in r['source_terminology_rows'])


def test_table_tabs_preserve_taxonomy_columns_without_using_paragraph_style_tabs():
    p=ET.fromstring('<w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:pPr><w:tabs><w:tab w:val="left"/></w:tabs></w:pPr><w:r><w:t>Study name </w:t><w:tab/><w:t>TA name</w:t></w:r></w:p>')
    assert paragraph_columns(p)==['Study name ','TA name']


def test_donor_context_and_acquisition_are_not_delivered_spacing_or_registration():
    r=json.loads((REVIEW/'specimen-and-terminology-review.json').read_text())
    assert r['source_specimen']=='CVH5' and r['source_sex_label']=='female' and r['source_age_years']==25
    assert r['source_height_mm']==1700 and r['source_weight_kg']==59
    assert r['source_sectioning_direction']=='transverse' and r['nominal_acquired_section_thickness_mm']==.2
    assert r['reported_original_image_resolution']==[4064,2704]
    assert r['delivered_section_count']==93 and r['delivered_pdf_image_dimensions']==[466,530]
    assert r['delivered_plane_spacing_mm'] is None and r['delivered_inplane_spacing_mm'] is None
    assert r['delivered_crop_resize_transform'] is None and not r['section_model_registration_verified']
    assert not r['delivered_pages_are_consecutive_acquired_planes_verified']
    assert not r['cohort_table_is_individual_CVH5_measurement_control']
    assert [i['cell_union_span_if_93_uniform_planes_mm'] for i in r['hypothetical_depth_comparisons']]==[18.6,186.0]
    assert all(not i['is_source_verified_delivered_spacing'] for i in r['hypothetical_depth_comparisons'])


def test_source_eas_and_urethral_terms_do_not_grant_whole_structure_coverage():
    r=json.loads((REVIEW/'specimen-and-terminology-review.json').read_text())
    rows={i['study_name']:i for i in r['source_terminology_rows']}
    assert rows['External anal sphincter']['source_terminologia_anatomica_column']=='Subcutaneous layer external anal sphincter'
    assert 'Deep layer external anal sphincter' in rows['Puborectal muscle (deep part)']['source_terminologia_anatomica_column']
    assert rows['Puborectal muscle (superficial part)']['source_terminologia_anatomica_column']=='Superficial layer external anal sphincter'
    assert rows['Urethral sphincter proper']['source_terminologia_anatomica_column']=='External urethral sphincter'
    assert not r['whole_EAS_coverage_from_named_EAS_model_granted'] and not r['terminology_mapping_is_universal_taxonomy']
    assert not r['caption_count_discrepancy_author_confirmed_resolved']
    assert not r['clinical_approval'] and not r['runtime_promoted'] and not r['structure_coverage_granted']
