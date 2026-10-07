import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_original_pdf_page_bindings_preserve_three_distinct_cases_and_sequences():
    r=json.loads((ROOT/'docs/parotid-MRI-published-source-review/original-source-review.json').read_text())
    assert r['pmcid']=='PMC11719534' and r['original_article_grant']=='CC BY 4.0'
    assert [(x['figure_number'],x['source_PDF_object'],x['source_PDF_page']) for x in r['figures']]==[(1,107,7),(2,140,8),(3,175,8)]
    assert all(x['original_decoded_samples_and_ICC_preserved'] and not x['source_pixels_resampled_or_enhanced'] for x in r['figures'])
    assert all(x['explicit_original_PDF_page_binding_visually_reviewed'] and x['original_HTML_and_PDF_encoded_contrast_differ'] for x in r['figures'])
    assert r['source_case_contexts']['1']['age_years']==54 and r['source_case_contexts']['1']['laterality']=='left'
    assert r['source_case_contexts']['2']['age_years']==65 and r['source_case_contexts']['2']['sex']=='female'
    assert r['source_case_contexts']['3']['age_years']==15 and r['source_case_contexts']['3']['laterality']=='right'
    assert r['source_panel_roles']['d']=='MRI DWI' and r['source_panel_roles']['e']=='MRI ADC map'
    assert r['source_panel_roles']['f']=='Derived DCE signal-intensity/time plot'
    assert not r['source_algorithm_is_independently_validated_current_patient_classifier']
    assert not r['source_dynamic_curve_is_native_3D_or_full_DCE_acquisition'] and not r['normalized_signal_values_are_new_independent_patient_measurements']
    assert len(r['nonclinical_source_figures_held'])==3
    assert not r['original_anatomical_or_case_approval_granted'] and not r['runtime_promoted'] and not r['structure_coverage_granted']
