"""Spine coverage and sensory/motor distinctions in the shared teaching map."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_spine_mri_and_trauma_modules_share_the_same_parent():
    investigations = json.loads((ROOT / 'data/radiology/reference-investigations.json').read_text())['investigations']
    spine = {row['id'] for row in investigations if row['module_id'] == 'rad.4.spine-imaging'}
    assert spine == {'ra.thoracolumbar-fractures', 'ra.cervical-spine-injury',
                     'ra.mri-lumbar-disc', 'ra.mri-myelopathy', 'ra.thoracolumbar-injury'}


def test_map_keeps_key_muscles_distinct_from_sensory_landmarks():
    data = json.loads((ROOT / 'data/radiology/spine-neurology-map.json').read_text())
    levels = {row['root']: row for row in data['levels']}
    assert len(levels) == len(data['levels']) == 28
    assert set(levels) == ({'C' + str(i) for i in range(2, 9)} |
                           {'T' + str(i) for i in range(1, 13)} |
                           {'L' + str(i) for i in range(1, 6)} | {'S1', 'S2', 'S3', 'S4–5'})
    assert levels['L4']['sensory'] == 'Medial malleolus'
    assert levels['L4']['motor'] == 'Ankle dorsiflexion'
    assert levels['L5']['motor'] == 'Great toe extension'
    assert levels['C8']['motor'] == 'Distal finger flexion'
    assert levels['S4–5']['view'] == 'posterior'
    assert {key for key, row in levels.items() if 'motor_point' in row} == {
        'C5', 'C6', 'C7', 'C8', 'T1', 'L2', 'L3', 'L4', 'L5', 'S1'}
    assert 'overlap' in data['limits'] and 'C1' in data['limits']
    assert 'traversing L5' in ' '.join(data['mri_notes'])
    assert any(row['url'] == 'https://njpaintherapy.com/blog/what-are-dermatomes/' for row in data['sources'])
    for row in levels.values():
        assert row['view'] in {'anterior', 'posterior'}
        for x, y in [row['point']] + ([row['motor_point']] if 'motor_point' in row else []):
            assert 0 < x < 300 and 0 < y < 470
