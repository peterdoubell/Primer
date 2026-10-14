"""Exact original-image bindings preserve source identity and assessment choices."""
import hashlib
from pathlib import Path

import pytest

from primer import thoracic_source_labels as labels
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/thoracic-source-label-review-20261014'


def test_source_locator_resources_equal_the_reviewed_originals():
    assert len(labels.registry()['files']) == 9
    for name, row in labels.registry()['files'].items():
        raw = labels.validate_file(name).read_bytes()
        assert raw == (REVIEW / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row['sha256']


def test_only_the_six_matching_figures_are_bound_without_replacing_source_models():
    c = Curriculum()
    ref = detail(c, resolve('ra.thoracic-ultrasound'))['radiology_reference']
    images = ref['structure_atlas']
    assert len(images) == 16 and len(ref['source_motion_references']) == 6
    assert [item['id'] for item in ref['source_native_inspectors']] == [
        'bp3d-thoracic-original-surfaces', 'totalseg-s0028-lung-native',
        'totalseg-s0028-basal-context', 'totalseg-v1-s0028-cardiac-native']
    bound = [r for r in images if 'source_label_locator' in r]
    assert len(bound) == 6
    assert all(r['source_label_locator']['figure_sha256'] == r['sha256'] for r in bound)
    assert all(not r['source_label_locator'][flag] for r in bound
               for flag in ['clinical_approval', 'tissue_segmentation', 'three_dimensional_registration'])
    assert all(not step['normal'] for step in ref['walkthrough']['steps'])
    original = labels.references()[bound[0]['src']]['dimensions'][:]
    bound[0]['source_label_locator']['dimensions'][0] = 1
    assert labels.references()[bound[0]['src']]['dimensions'] == original


@pytest.mark.parametrize('asset', ['missing.jpg', '../index.html', 'assets%2Ffped-05-00079-g007.jpg'])
def test_unregistered_resources_are_rejected(asset):
    with pytest.raises(ValueError, match='Unknown'):
        labels.validate_file(asset)


def test_present_wrong_or_missing_source_cannot_be_replaced_by_hosted_fallback(tmp_path, monkeypatch):
    labels.registry()
    monkeypatch.setattr(labels, 'ROOT', tmp_path)
    monkeypatch.setenv('VERCEL', '1')
    with pytest.raises(ValueError, match='missing'):
        labels.validate_file('index.html')
    p = tmp_path / 'web/source-labels/thoracic/index.html'
    p.parent.mkdir(parents=True)
    p.write_bytes(b'wrong source')
    with pytest.raises(ValueError, match='changed'):
        labels.validate_file('index.html')


@pytest.mark.parametrize('path', ['primer/server.py', 'primer/radiology_catalog.py', 'web/app.js', 'tools/physics_wave_runtime_compatibility.py'])
def test_inverse_restores_only_the_exact_recorded_changes(path):
    from tools.thoracic_label_runtime_compatibility import before_label_bytes, reviewed
    raw = (ROOT / path).read_bytes()
    restored = before_label_bytes(path, raw)
    assert hashlib.sha256(restored).hexdigest() == reviewed()['files'][path]['before_sha256']
    with pytest.raises(ValueError, match='Unreviewed'):
        before_label_bytes(path, raw + b'changed')
