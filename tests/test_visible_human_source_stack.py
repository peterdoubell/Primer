import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/visible-human-source-review'
def test_complete_stack_preserves_all_original_samples_without_alignment_inference():
    r=json.loads((OUT/'ordered-source-stack-review.json').read_text());a=json.loads((OUT/'female-head-original-acquisition.json').read_text())
    assert r['original_acquisition_sha256']==hashlib.sha256((OUT/'female-head-original-acquisition.json').read_bytes()).hexdigest()
    assert r['source_grid_zyx_RGB']==[855,1216,2048,3] and r['source_stack_bytes']==6387793920
    assert r['all_855_original_frame_RGB_samples_written_and_read_back_exactly']
    assert [x['decoded_RGB_sha256'] for x in r['source_frame_checks']]==[x['decoded_RGB_sha256'] for x in a['records']]
    assert r['identical_decoded_frame_groups']==[]
    assert len(r['adjacent_frame_photometric_checks'])==854
    for i,pair in enumerate(r['adjacent_frame_photometric_checks']):
        assert (pair['first_frame'],pair['second_frame'])==(a['records'][i]['frame'],a['records'][i+1]['frame'])
        assert 0<=pair['mean_absolute_RGB_difference']<=255 and not pair['metric_is_anatomical_registration_or_distance']
    for key in ['ordering_is_independent_physical_alignment_or_registration','source_sample_resampling_fitting_gap_filling_or_enhancement','source_anatomical_labels_or_full_tissue_boundary_approval','clinical_approval','runtime_promoted','structure_coverage_granted']:assert r[key] is False

def test_reviewed_index_planes_are_exact_unregistered_source_sections():
    r=json.loads((OUT/'source-index-plane-review.json').read_text());stack=json.loads((OUT/'ordered-source-stack-review.json').read_text())
    assert r['source_stack_sha256']==stack['source_stack_sha256'] and r['source_stack_rehashed_before_render']
    assert [(x['axis'],x['index']) for x in r['planes']]==[('source_y',500),('source_y',650),('source_y',800),('source_x',900),('source_x',1050),('source_x',1200)]
    assert [x['dimensions'] for x in r['planes']]==[[855,2048,3]]*3+[[855,1216,3]]*3
    assert not r['pixels_interpolated_or_source_frames_fitted']
    assert not r['source_index_planes_are_independently_registered_patient_planes']
    assert not r['clinical_approval'] and not r['runtime_promoted']
