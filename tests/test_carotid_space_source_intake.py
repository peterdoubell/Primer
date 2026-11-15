import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_every_original_master_and_artist_credit_is_retained_without_case_or_anatomy_approval():
    r=json.loads((ROOT/'docs/carotid-space-published-source-review/original-source-review.json').read_text())
    assert r['pmcid']=='PMC6377693' and r['original_article_grant']=='CC BY 4.0'
    assert [x['figure_number'] for x in r['figures']]==list(range(1,24))
    assert all(x['original_decoded_samples_and_ICC_preserved'] and not x['source_pixels_resampled_or_enhanced'] for x in r['figures'])
    assert all(x['numbered_HTML_PDF_thumbnail_RGB_RMS']<1.6 for x in r['figures'])
    assert r['original_author_names']==['Harris U. Chengazi','Alok A. Bhatt']
    assert 'Nadezdha Kiriyak' in r['original_illustration_acknowledgements'] and 'Gwen Mack' in r['original_illustration_acknowledgements']
    assert r['all_23_complete_master_layouts_visually_inspected'] and len(r['visual_review_sheets'])==3
    assert not r['original_anatomical_or_case_approval_granted'] and not r['runtime_promoted'] and not r['structure_coverage_granted']
def test_schematic_layers_and_mixed_modalities_do_not_supply_unacquired_function():
    r=json.loads((ROOT/'docs/carotid-space-published-source-review/original-source-review.json').read_text())['source_role_intake']
    assert r['conceptual_schematic_figures']==[1,6,11,13]
    assert r['mixed_modality_panels']['2']=={'a':'CT','b':'MRI','c':'Projection angiography','d':'Ultrasound'}
    assert r['mixed_modality_panels']['18']=={'a':'Ultrasound','b':'CT'}
    for key in ['source_assay_or_microbiology_labels_are_independent_pixel_proof','static_vocal_fold_medialisation_establishes_function_or_unique_nerve_injury','illustrated_tunica_layers_are_native_patient_wall_geometry','source_stills_are_full_calibrated_dynamic_flow_acquisitions']:assert r[key] is False
