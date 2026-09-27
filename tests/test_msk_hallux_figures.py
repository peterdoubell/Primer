"""Cadaveric MRI, histology, dissection and ultrasound cannot exchange claims."""
import copy
import json
from pathlib import Path

import pytest

from primer import radiology_catalog

ROOT = Path(__file__).resolve().parents[1]


def records():
    images = json.loads((ROOT / 'data/radiology/msk-open-images.json').read_text())['ra.mri-diabetic-foot']
    evidence = json.loads((ROOT / 'data/radiology/msk-asset-evidence.json').read_text())['assets']
    return images, {a['id']: a for a in evidence}


def test_hallux_panels_keep_their_actual_representation_and_population():
    images, evidence = records()
    images = [image for image in images if image.get('anatomical_digit') == 1]
    assert len(images) == 6
    mr = [a for a in images if a['modality'] == 'MRI']
    assert len(mr) == 3
    for image in mr:
        assert 'cadaveric' in image['image_state']
        assert image['anatomical_digit'] == 1
        assert image['clinical_panels'] == ['c', 'd']
        assert image['schematic_panels'] == ['a']
        assert image['ancillary_panels']
        for ancillary in image['ancillary_panels']:
            assert not set(ancillary['panels']).intersection(image['clinical_panels'])
            assert ancillary['kind'] in {'Dissection', 'Histology'}
            assert ancillary['limits']
        clinical = evidence[image['id']]
        schematic = evidence[image['id'] + '-schematic-panels']
        assert clinical['representation_selection']['panels'] == ['c', 'd']
        assert schematic['representation_selection']['panels'] == ['a']
        assert clinical['structures_observed'] == image['structures_visible']
        assert clinical['anatomical_review']['status'] == 'pending'
        assert all('lesser' not in identifier for identifier in clinical['structure_ids'])
    us = [a for a in images if a['modality'] == 'Ultrasound']
    assert {(a['figure_number'], a['source_panel']) for a in us} == {(5, 'c'), (9, 'd')}
    assert all(evidence[a['id']]['structure_ids'] == [] for a in us)


def test_lesser_plate_reference_does_not_inherit_hallux_or_other_digit_coverage():
    import hashlib
    from PIL import Image
    images, evidence = records()
    image = next(a for a in images if a['id'] == 'open-lesser-mtp3-plantar-plate-mri-siddle-fig1')
    asset = evidence[image['id']]
    assert image['anatomical_digit'] == 3
    assert image['clinical_panels'] == asset['representation_selection']['panels'] == ['a', 'b']
    assert asset['source_context']['setting'] == 'in_vivo'
    assert asset['source_context']['anatomical_site']['joint'] == 'mtp3'
    assert asset['requirement_binding_evidence'][0]['site_id'] == 'mtp3'
    assert asset['structure_ids'] == ['diabetic_foot.lesser_mtp_plantar_plates.body']
    assert asset['anatomical_review']['status'] == 'pending'
    path = ROOT / asset['local_path']
    # Independently captured from the encoded PDF DCT stream; convenience
    # ImageFile exports re-encode this JPEG and are not the original bytes.
    assert hashlib.sha256(path.read_bytes()).hexdigest() == '798342c0beebb60fe891b22a98a94afd862830b711aef8ebc8b726b26670796c'
    assert Image.open(path).size == (1420, 2006)


@pytest.mark.parametrize('change', ['kind', 'panels', 'observations', 'limits'])
def test_loader_rejects_ambiguous_ancillary_panel_metadata(monkeypatch, change):
    original_read = radiology_catalog._read
    def altered(name, default=None):
        value = copy.deepcopy(original_read(name, default))
        if name == 'msk-open-images.json':
            image = next(a for a in value['ra.mri-diabetic-foot'] if a['modality'] == 'MRI')
            ancillary = image['ancillary_panels'][0]
            if change == 'kind': ancillary['kind'] = 'MRI'
            if change == 'panels': ancillary['panels'] = []
            if change == 'observations': ancillary['structures_visible'] = 'unstructured claim'
            if change == 'limits': ancillary['limits'] = ''
        return value
    monkeypatch.setattr(radiology_catalog, '_read', altered)
    radiology_catalog._structure_atlases.cache_clear()
    try:
        with pytest.raises(ValueError, match='Dissection and histology'):
            radiology_catalog._structure_atlases()
    finally:
        radiology_catalog._structure_atlases.cache_clear()
