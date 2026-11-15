"""Source modality, mixed panels and known caption corrections stay explicit."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def records():
    images = json.loads((ROOT / 'data/radiology/msk-open-images.json').read_text())['ra.mri-ankle']
    evidence = json.loads((ROOT / 'data/radiology/msk-asset-evidence.json').read_text())['assets']
    return {a['id']: a for a in images}, {a['id']: a for a in evidence}


def test_ultrasound_examples_cannot_be_presented_as_mri_requirement_evidence():
    images, evidence = records()
    ultrasound = [a for a in images.values() if a['modality'] == 'Ultrasound']
    assert len(ultrasound) == 3
    for image in ultrasound:
        assert image['kind'] == 'clinical-image'
        assert not image.get('contains_schematic_panels')
        asset = evidence[image['id']]
        assert asset['modality'] == 'Ultrasound'
        assert asset['structure_ids'] == []
        assert asset['anatomical_review']['status'] == 'pending'


def test_spring_mri_and_schematic_have_distinct_pixel_panel_claims():
    images, evidence = records()
    identifier = 'open-ankle-spring-components-szaro-fig2'
    image = images[identifier]
    assert image['clinical_panels'] == ['a'] and image['schematic_panels'] == ['b']
    assert image['contains_schematic_panels']
    assert 'Tibialis posterior tendon' in image['structures_visible']
    assert 'Tibialis posterior tendon' not in image['schematic_structures_visible']
    assert evidence[identifier]['representation_selection']['panels'] == ['a']
    assert evidence[identifier + '-schematic-panels']['representation_selection']['panels'] == ['b']


def test_pathology_and_published_foot_caption_typo_are_not_hidden():
    images, evidence = records()
    mixed = images['open-ankle-tendon-compartments-fig4']
    assert 'mixed' in mixed['image_state'].lower()
    assert 'tenosynovitis' in mixed['limits'].lower()
    peroneal = images['open-ankle-peroneal-course-bianchi-fig1']
    assert 'fifth metatarsal' in peroneal['caption'].lower()
    assert 'fifth metacarpal' not in peroneal['caption'].lower()
    assert 'fifth metacarpal' in peroneal['source_caption_full'].lower()
    assert 'typo' in peroneal['limits'].lower()
    assert evidence[peroneal['id']]['limitations'] == peroneal['limits']
