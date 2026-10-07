"""Original thyroid case screening must not convert absent/cropped annotations into normality."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/thyroid-native-source-review'
def test_all_subset_cases_and_extent_exclusions_are_preserved():
    r=json.loads((OUT/'subset-thyroid-screen.json').read_text())
    assert r['case_count']==len(r['cases'])==102 and r['publisher_full_archive_MD5_verified']
    assert r['actual_dataset_license']['id']=='cc-by-4.0'
    assert len(r['empty_cases'])==26 and len(r['boundary_touching_cases'])==30
    assert len(r['nonempty_not_boundary_touching_cases'])==46
    assert set(r['empty_cases'])|set(r['boundary_touching_cases'])|set(r['nonempty_not_boundary_touching_cases'])=={x['case'] for x in r['cases']}
    assert not(set(r['empty_cases'])&set(r['boundary_touching_cases']))
    case=next(x for x in r['cases'] if x['case']=='s0011')
    assert case['touches_volume_axes']==[2] and case['source_bounds_xyz_inclusive'][2][1]==case['shape'][2]-1
    assert r['nonempty_not_boundary_touching_cases'][0]=='s0358'
    assert all(not x['source_components_or_labels_modified'] for x in r['cases'])
    assert not r['source_boundary_containment_is_full_anatomical_approval']
    assert not r['source_1_5mm_sampling_is_adequate_for_all_reported_tiny_tissues']
    assert not r['clinical_approval'] and not r['runtime_promoted']
