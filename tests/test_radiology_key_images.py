"""Real teaching figures, attribution and narrow external-image boundaries."""
import copy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from primer import radiology


@pytest.mark.parametrize('source', [
    'https://radiologyassistant.nl/assets/example.jpg',
    'https://radiologyassistant.nl/img/containers/main/example.jpg/cache.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/1/12/Example.png',
    '/app/illustrations/forest/radiology/rad-5-coronary-ct-800.webp',
])
def test_known_image_origins_and_existing_local_plates_are_allowed(source):
    radiology.validate_image_source(source)


@pytest.mark.parametrize('source', [
    'https://example.com/image.jpg',
    'https://radiologyassistant.nl.evil.example/assets/image.jpg',
    'https://radiologyassistant.nl/private/image.jpg',
    'https://radiologyassistant.nl/assets/../private/image.jpg',
    'https://radiologyassistant.nl/assets/%2e%2e/private/image.jpg',
    'https://radiologyassistant.nl/assets/image.svg',
    'https://radiologyassistant.nl/assets/image.html',
    'https://radiologyassistant.nl/assets/image.jpg#fragment',
    'http://radiologyassistant.nl/assets/image.jpg',
    'https://user:password@radiologyassistant.nl/assets/image.jpg',
    'https://radiologyassistant.nl:8443/assets/image.jpg',
    'https://upload.wikimedia.org/private/image.jpg',
    '/app/illustrations/../../.env.local',
    '/app/illustrations/%2e%2e/secret.webp',
    '/app/illustrations/does-not-exist.webp',
    'data:image/svg+xml,<svg/>',
    '//radiologyassistant.nl/assets/example.jpg',
    None,
])
def test_image_paths_cannot_expand_into_arbitrary_fetches(source):
    with pytest.raises(ValueError):
        radiology.validate_image_source(source)


def test_every_slot_is_backed_by_one_curated_figure():
    from primer.curriculum import Curriculum
    curriculum = Curriculum()
    nodes = [node for node in curriculum.nodes.values()
             if node['domain'] == 'radiology' and node['id'].startswith('rad.')]
    images = [image for node in nodes for image in node['radiology_reference']['key_images']]
    assert len(images) == 298
    assert len({image['id'] for image in images}) == len(images)
    for node in nodes:
        entries = node['radiology_reference']['key_images']
        assert all(entry['src'] and entry['caption'] and entry['alt'] and entry['attribution'] for entry in entries)
        assert all(entry['source_url'].startswith(('https://', '/app/illustrations/')) for entry in entries)
        for entry in entries:
            if entry['src'].startswith('https://upload.wikimedia.org/'):
                assert entry['license'] and entry['license_url']
            if entry['src'].startswith('/app/'):
                assert entry['image_type'] == 'diagram'
    # These two exemplar reports must show genuine scan examples and their
    # source references, not a repeated generic course plate in every slot.
    for identifier in ('rad.5.coronary-ct', 'rad.5.prostate-mri'):
        entries = curriculum.node(identifier)['radiology_reference']['key_images']
        assert len({image['src'] for image in entries}) == 8
        assert sum(image['image_type'] == 'clinical' for image in entries) >= 5


def test_catalog_missing_a_slot_fails_closed(monkeypatch):
    real_read = radiology._read
    def missing(filename):
        value = copy.deepcopy(real_read(filename))
        if filename == radiology.IMAGE_CATALOGS[0]:
            value.pop(next(iter(value)))
        return value
    monkeypatch.setattr(radiology, '_read', missing)
    nodes = json.loads((ROOT / 'data/curriculum/11-radiology.json').read_text())['nodes']
    with pytest.raises(ValueError, match='cover every report slot'):
        radiology.attach_references(nodes)


def test_ultrasound_key_diagram_uses_full_resolution_source():
    from PIL import Image
    from primer.curriculum import Curriculum

    node = Curriculum().node('rad.5.ultrasound-physics')
    image = next(entry for entry in node['radiology_reference']['key_images']
                 if entry['id'] == 'ultrasound-physics-image-3')
    assert image['src'].endswith('/rad-5-ultrasound-physics-1600.webp')
    assert image['source_url'] == image['src']
    with Image.open(ROOT / 'web' / image['src'].removeprefix('/app/')) as raster:
        assert raster.size == (image['width'], image['height']) == (1600, 1000)


def test_browser_policy_allows_the_curated_image_paths_only(tmp_path, monkeypatch):
    monkeypatch.setenv('PRIMER_DB', str(tmp_path / 'image-policy.db'))
    from primer.server import CSP
    directive = next(part.strip() for part in CSP.split(';') if part.strip().startswith('img-src '))
    assert set(directive.split()[1:]) == {
        "'self'", 'data:', 'https://radiologyassistant.nl/assets/',
        'https://radiologyassistant.nl/img/', 'https://upload.wikimedia.org/wikipedia/commons/',
    }
    assert "connect-src 'self'" in CSP
