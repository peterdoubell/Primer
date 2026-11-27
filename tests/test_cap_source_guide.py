"""Check both report formats, named anatomy and actual rendered source selectors."""
from collections import Counter
from copy import deepcopy
from urllib.parse import parse_qs, urlsplit

import pytest

from tools.anatomy_sources import build_cap_inventory as cap


def test_every_current_source_field_and_quick_report_row_is_traced():
    item = cap.validate(cap.read(cap.ROOT, cap.OUTPUT))
    fast = cap.read(cap.ROOT, cap.FAST)['templates'][cap.EXAM]
    assert [s['quick_report'] for s in item['sections']] == [fast['technique'], *fast['sections']]
    assert [s['id'] for s in item['sections']] == list(cap.NOTES)
    fields = {f['id']: f for f in item['evidence_requirements']}
    assert len(fields) == 44
    assert set(fields) == {f for row in item['sections'] for f in row['source_field_ids']}
    assert all(not f['required_representations'] for f in fields.values())
    assert fields[cap.EXAM + ':thoracic-lymph-nodes:size']['axis'] == 'short_axis'
    assert fields[cap.EXAM + ':liver:size']['axis'] == 'not_specified_in_field'
    assert fields[cap.EXAM + ':target-lesions:response']['requires_any'] == [cap.EXAM + ':target-lesions:measurable']
    assert set(fields[cap.EXAM + ':target-lesions:response']['evidence']) >= {'baseline_and_nadir', 'non_target_disease', 'new_lesions'}
    assert not any(t['source_section_id'] == 'target-lesions' for t in item['anatomical_requirements'])
    changed = deepcopy(item)
    changed['anatomical_requirements'][0]['laterality'] = 'left'
    with pytest.raises(ValueError):
        cap.validate(changed)


def test_partial_views_bind_only_occupied_source_objects_at_real_CT_positions():
    item = cap.build()
    targets = {t['id']: t for t in item['anatomical_requirements']}
    assert len(targets) == len(item['anatomical_requirements']) == 122
    links = [link for link in cap.references(item) if link['source_id'] == 'ct-torso-s0028']
    manifest = cap.read(cap.ROOT, cap.ATLAS + '/manifest.json')
    labels = {l['sourceLabel']: l for l in manifest['labels']}
    assert Counter(l['representation'] for l in links) == {k: 67 for k in cap.KINDS}
    assert len({(l['requirement_id'], l['representation']) for l in links}) == len(links)
    for link in links:
        t = targets[link['requirement_id']]
        source = labels[t['source_label']]
        url = urlsplit(link['href'])
        assert url.path == '/app/anatomy/ct-torso-s0028/index.html'
        assert url.fragment == cap.ANCHORS[link['representation']]
        assert parse_qs(url.query) == {'exam': [cap.EXAM], 'row': [t['source_section_id']],
            'label': [source['sourceLabel']], 'representation': [link['representation']]}
        assert link['side'] == t['laterality']
        assert link['focus'] == source['focus'] and source['voxelCount'] > 0
        assert link['mask_sha256'] == source['sourceSHA256']
        assert link['reaches_grid_edge'] is source['touchesGridEdge']
        assert link['source_id'] == 'ct-torso-s0028' and link['status'] == 'partial'
        assert not any(link[k] for k in ('complete_extent', 'current_patient_registration', 'clinical_approval'))


def test_unlabelled_regions_empty_mask_and_comparison_cases_remain_distinct():
    item = cap.build()
    guide = cap.viewer_guide(item, cap.references(item))
    assert guide == cap.read(cap.ROOT, cap.GUIDE)
    rows = {r['name']: r for s in guide.values() for r in s['targets']}
    assert rows['Lingula']['state'] == rows['Segment I (caudate lobe)']['state'] == 'unlabelled'
    assert rows['Prostate']['state'] == 'empty'
    assert rows['Left proximal humerus']['links'] == rows['Left pleura']['links'] == {}
    assert rows['Left kidney']['sourceLabel'] == 'kidney_left'
    assert rows['Right adrenal gland']['sourceLabel'] == 'adrenal_gland_right'
    assert sum(name.startswith(('Right rib ', 'Left rib ')) for name in rows) == 24
    assert guide['target-lesions']['targets'] == []
    assert guide['target-lesions']['comparison']['href'].endswith('/recist-pelvic-023/comparison.html')
    assert guide['liver']['comparison']['href'].endswith('/liver-regions-mri/index.html')


def test_each_mri_comparison_selects_its_named_segment_and_a_verified_occupied_section():
    item = cap.build()
    links = cap.liver_segment_links(item)
    assert len(links) == 16
    assert Counter(row['representation'] for row in links) == {'schematic': 8, 'model': 8}
    by_number = {1: (44,1988), 2: (52,12782), 3: (49,11814), 4: (52,7506),
                 5: (48,10159), 6: (48,11063), 7: (49,10281), 8: (50,12780)}
    for link in links:
        region = int(link['source_label'].rsplit('_', 1)[1])
        assert link['requirement_id'] == 'cap.liver_segment_' + str(region)
        assert (link['slice_index'], link['source_section_pixels']) == by_number[region]
        assert link['source_case'] == 'a1B8NQX1CHIcaQqs' and link['source_modality'] == 'MRI'
        params = parse_qs(urlsplit(link['href']).query)
        assert params == {'region': [str(region)], 'slice': [str(link['slice_index'])],
                          'from': [cap.EXAM], 'representation': [link['representation']]}
        assert link['status'] == 'partial' and not link['current_patient_registration']
    guide = cap.read(cap.ROOT, cap.GUIDE)['liver']['targets']
    segments = [t for t in guide if t.get('separateMRI')]
    assert len(segments) == 8 and all(t['state'] == 'unlabelled' and not t['links'] for t in segments)


def test_comparison_ct_preserves_separate_iv_components_and_exact_source_focus():
    links = cap.ct_segment_links(cap.build())
    assert len(links) == 27
    labels = cap.read(cap.ROOT, 'web/anatomy/medseg-liver-001/manifest.json')['labels']
    sources = {row['segment']: row for row in labels}
    for link in links:
        label = sources[link['segment']]
        assert link['source_code'] == label['code'] and link['source_label'] == label['sourceName']
        assert link['focus'] == label['focus'] and link['source_voxels'] == label['voxelCount']
        assert link['source_modality'] == 'CT' and link['status'] == 'partial'
        assert not any(link[key] for key in ('complete_extent','clinical_approval','current_patient_registration'))
    fourth = [link for link in links if link['requirement_id'] == 'cap.liver_segment_4']
    assert len(fourth) == 6 and {link['segment'] for link in fourth} == {'4a','4b'}
    assert {link['target_relation'] for link in fourth} == {'named_subregion'}
    guide = cap.read(cap.ROOT, cap.GUIDE)['liver']['targets']
    compared = [t for t in guide if 'separateCT' in t]
    assert len(compared) == 8 and sum(len(t['separateCT']) for t in compared) == 9
    assert all(t['state'] == 'unlabelled' and not t['links'] for t in compared)
    assert {u['name'] for t in compared for u in t['separateCT']} == {row['sourceName'] for row in labels}
