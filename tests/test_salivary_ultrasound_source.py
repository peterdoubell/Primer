"""The real neck report retains a complete licensed photo without invented sides."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
from unittest.mock import patch

import pytest
from PIL import Image
from fastapi.testclient import TestClient
from primer import salivary_ultrasound_reference as source
from primer import source_native_inspectors
from primer import source_raster_integrity
from primer import report_templates
from tools import salivary_ultrasound_compatibility as inverse

ROOT = Path(__file__).resolve().parents[1]


def test_original_publisher_bytes_pixels_and_separate_source_panel_roles():
    figure, = source.figures()
    review = json.loads((ROOT / 'docs/salivary-ultrasound-2025/source-review.json').read_bytes())
    raw = (ROOT / review['file']['path']).read_bytes()
    assert (len(raw), hashlib.sha256(raw).hexdigest()) == (568576, figure['sha256'])
    with Image.open(ROOT / review['file']['path']) as image:
        assert (image.size, image.mode) == ((2056, 685), 'L')
        assert hashlib.sha256(image.tobytes()).hexdigest() == review['file']['decoded_pixels_sha256']
    assert review['file']['original_publisher_bytes_retained'] and not review['file']['source_pixels_changed']
    assert review['article_explicitly_includes_images_unless_other_credit']
    assert review['article_figure3_and_dedicated_figure_page_checked']
    assert not review['figure_specific_credit_or_exclusion_found']
    assert figure['license'] == 'CC BY 4.0'
    assert review['normal_source_panels'] == ['A', 'B']
    assert {row['gland'] for row in review['panels']} == {'parotid', 'submandibular'}
    assert all(row['side'] == row['acquisition_plane'] == 'not reported' for row in review['panels'])
    assert review['representation_bindings_added'] == 0
    assert not review['source_case_registration_to_SegThy']
    assert not review['models_derived_from_still_images']
    assert not review['missing_side_and_plane_assigned_to_reporting_rows']


def test_only_the_actual_neck_report_gets_the_photographs_and_keeps_segthy():
    from primer.server import app
    registered = source_native_inspectors.references()
    assert [row['id'] for row in registered[source.NECK]] == [
        'segthy-001', source.IDENTIFIER, 'zanatomy-salivary',
        'regional-node-us-2026-fig4ab', 'periauricular-node-us-2026-fig14']
    assert [row['id'] for row in registered['ra.ultrasound-thyroid']] == ['segthy-001']
    with TestClient(app) as client:
        ref = client.get('/api/radiology/modules/' + source.NECK).json()['radiology_reference']
        assert ref['descriptor_only'] is True
        assert [row['id'] for row in ref['source_native_inspectors']] == [
        'segthy-001', source.IDENTIFIER, 'zanatomy-salivary',
        'regional-node-us-2026-fig4ab', 'periauricular-node-us-2026-fig14']
        card = ref['source_native_inspectors'][1]
        assert card['modality'] == 'Ultrasound photographs' and card['photographic_figures'] == source.figures()
        assert card['structure_ids'] == card['requirement_coverage'] == []
        assert card['clinical_approval'] is card['current_patient_registration'] is False
        assert 'inline_label' not in card  # A still figure must not acquire a native-volume iframe.
        assert 'salivary-us' not in json.dumps(ref['quick_report'])
        for key in ['Parotid glands', 'Submandibular glands']:
            assert key + ':\n• Normal.' in ref['quick_report']['normal']
        thyroid = client.get('/api/radiology/modules/ra.ultrasound-thyroid').json()['radiology_reference']
        assert source.IDENTIFIER not in {row['id'] for row in thyroid['source_native_inspectors']}
    assert [row['normal'] for row in report_templates.library()[source.NECK]['sections'] if row['heading'] in ['Parotid glands', 'Submandibular glands']] == ['Normal.', 'Normal.']


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    registry = tmp_path / 'data/radiology/salivary-ultrasound-figures.json'
    registry.parent.mkdir(parents=True)
    shutil.copy2(source.REGISTRY, registry)
    image = tmp_path / 'web/reference-media/radiology-open' / source.SRC.rsplit('/', 1)[1]
    image.parent.mkdir(parents=True)
    shutil.copy2(ROOT / 'web' / source.SRC.removeprefix('/app/'), image)
    monkeypatch.setattr(source, 'ROOT', tmp_path)
    monkeypatch.setattr(source, 'REGISTRY', registry)
    source.figures.cache_clear()
    yield registry, image
    source.figures.cache_clear()


@pytest.mark.parametrize('change', ['side', 'plane', 'gland', 'healthy', 'modality', 'coverage', 'license', 'coordinates', 'timeline'])
def test_unreviewed_anatomy_or_source_scope_is_rejected(isolated, monkeypatch, change):
    registry, _ = isolated
    data = json.loads(registry.read_bytes()); figure = data['figures'][0]
    if change == 'side': figure['source_context']['panels'][0]['side'] = 'left'
    elif change == 'plane': figure['source_context']['panels'][0]['acquisition_plane'] = 'longitudinal'
    elif change == 'gland': figure['source_context']['panels'][0]['gland'] = 'thyroid'
    elif change == 'healthy': figure['source_context']['panels'][1]['source_state'] = 'healthy-subject example'
    elif change == 'modality': figure['modality'] = 'MRI'
    elif change == 'coverage': figure['structure_coverage_granted'] = True
    elif change == 'license': figure['license'] = 'CC0'
    elif change == 'coordinates': figure['source_context']['native_coordinates_available'] = True
    else: figure['source_context']['source_time_series'] = True
    raw = (json.dumps(data) + '\n').encode(); registry.write_bytes(raw)
    monkeypatch.setattr(source, 'PIN', hashlib.sha256(raw).hexdigest())
    with pytest.raises(ValueError, match='interpretation'):
        source.figures()


def test_raster_bytes_and_symlinks_are_verified(isolated):
    _, image = isolated
    raw = image.read_bytes(); image.write_bytes(raw + b'foreign')
    with pytest.raises(ValueError, match='changed'):
        source.figures()
    image.unlink(); image.symlink_to(ROOT / 'web' / source.SRC.removeprefix('/app/'))
    with pytest.raises(ValueError, match='regular file'):
        source.figures()


def test_hosted_thin_metadata_and_existing_static_build_route(monkeypatch):
    monkeypatch.setenv('VERCEL', '1')
    image = ROOT / 'web' / source.SRC.removeprefix('/app/')
    original = Path.is_file
    source.figures.cache_clear(); source_raster_integrity._inventory.cache_clear()
    try:
        with patch.object(Path, 'is_file', lambda p: False if p == image else original(p)):
            assert source.figures()[0]['src'] == source.SRC
    finally:
        source.figures.cache_clear(); source_raster_integrity._inventory.cache_clear()
    config = json.loads((ROOT / 'vercel.json').read_bytes())
    assert any(row['src'] == 'web/reference-media/radiology-open/**' and row['use'] == '@vercel/static' for row in config['builds'])
    assert {'src': '/source-media/(.*)', 'dest': '/web/$1'} in config['routes']


def test_authenticated_delivery_retains_exact_bytes_and_the_hosted_static_url(monkeypatch):
    from primer.server import app
    monkeypatch.setenv('PRIMER_ACCESS_USERNAME', 'salivary-fixture')
    monkeypatch.setenv('PRIMER_ACCESS_PASSWORD', 'fixture-only')
    monkeypatch.delenv('VERCEL', raising=False)
    auth = ('salivary-fixture', 'fixture-only')
    with TestClient(app) as client:
        assert client.get(source.SRC).status_code == 401
        result = client.get(source.SRC, auth=auth)
        assert result.status_code == 200 and result.headers['content-type'].startswith('image/png')
        assert hashlib.sha256(result.content).hexdigest() == source.figures()[0]['sha256']
        assert client.get(source.SRC.replace('figure3', 'unknown'), auth=auth).status_code == 404
        monkeypatch.setenv('VERCEL', '1')
        response = client.head(source.SRC, auth=auth, follow_redirects=False)
        assert response.status_code == 307
        assert response.headers['location'] == source.SRC.replace('/app/', '/source-media/', 1)


@pytest.mark.parametrize('change', ['caption', 'duplicate', 'coverage'])
def test_historical_projection_keeps_segthy_and_rejects_an_altered_salivary_card(change):
    current = deepcopy(source_native_inspectors.references())
    before = inverse.before_salivary_bindings(current)
    assert [row['id'] for row in before[source.NECK]] == ['segthy-001']
    assert [row['id'] for row in current[source.NECK]] == [
        'segthy-001', source.IDENTIFIER, 'zanatomy-salivary',
        'regional-node-us-2026-fig4ab', 'periauricular-node-us-2026-fig14']
    card = current[source.NECK][1]
    if change == 'caption': card['caption'] += ' Extent approved.'
    elif change == 'duplicate': current[source.NECK].append(deepcopy(card))
    else: card['requirement_coverage'] = ['invented']
    with pytest.raises(ValueError, match='Unreviewed'):
        inverse.before_salivary_bindings(current)


def test_literal_inverse_restores_shared_parent_files_and_checks_its_proof(tmp_path, monkeypatch):
    proof = inverse.PROOF.read_bytes()
    assert hashlib.sha256(proof).hexdigest() == inverse.PIN
    for name, row in json.loads(proof).items():
        from tools.salivary_surface_compatibility import before_surface_bytes
        raw = before_surface_bytes(name, (ROOT / name).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == row['after']
        restored = inverse.before_salivary_bytes(name, raw)
        assert hashlib.sha256(restored).hexdigest() == row['before']
        assert inverse.before_salivary_bytes(name, restored) == restored
        assert inverse.before_salivary_bytes(name, raw + b'unknown') == raw + b'unknown'
    target = tmp_path / 'proof.json'; target.write_bytes(proof + b'changed')
    monkeypatch.setattr(inverse, 'PROOF', target)
    with pytest.raises(ValueError, match='evidence changed'):
        inverse.before_salivary_bytes('web/app.js', (ROOT / 'web/app.js').read_bytes())
