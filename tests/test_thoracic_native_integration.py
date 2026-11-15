"""Curated source geometry is bound without replacing clinical examples or granting coverage."""
import hashlib
import json
from pathlib import Path
import pytest
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from primer import thoracic_native_inspectors as native

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/thoracic-native-anatomy-review-20261013'


def test_reference_and_shared_lesson_preserve_clinical_images_and_cine():
    curriculum = Curriculum()
    ref = detail(curriculum, resolve('ra.thoracic-ultrasound'))['radiology_reference']
    assert len(ref['structure_atlas']) == 16 and len(ref['source_motion_references']) == 6
    assert [item['id'] for item in ref['source_native_inspectors']] == [
        'bp3d-thoracic-original-surfaces', 'totalseg-s0028-lung-native',
        'totalseg-s0028-basal-context', 'totalseg-v1-s0028-cardiac-native', 'bp3d-cardiac-original-context', 'baskaran-2020-cardiac-comparisons']
    item = ref['source_native_inspectors'][0]
    assert item['modality'] == 'Curated 3D anatomy'
    assert item['clinical_approval'] is item['fine_anatomical_approval'] is False
    assert not item['current_patient_registration'] and not item['complete_reporting_anatomy_approved']
    assert all(not step['normal'] for step in ref['walkthrough']['steps'])
    media = [m for m in curriculum.node('rad.5.pleura')['lesson_media'] if m['kind'] == 'source-native-inspectors']
    assert len(media) == 1 and media[0]['investigation_ids'] == ['ra.thoracic-ultrasound']
    assert 'curated' in media[0]['instructions'] and 'probabilities' not in media[0]['instructions']
    models = [m for m in curriculum.node('rad.5.pleura')['lesson_media'] if m['kind'] == 'model']
    assert len(models) == 1 and models[0]['props']['source_native_only'] is True
    assert models[0]['props']['native_inspectors'] == ref['source_native_inspectors']


def test_all_source_payloads_remain_identical_to_reviewed_originals_and_transports():
    data = native.registry()
    assert len(data['files']) == 28
    for name, identity in data['files'].items():
        path = native.validate_file(name)
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == identity['sha256']
        if name.startswith(('originals/', 'transport/')):
            assert raw == (REVIEW / name).read_bytes()
    ref = native.references()['ra.thoracic-ultrasound'][0]
    assert ref['manifest_sha256'] == data['files']['manifest.json']['sha256']


@pytest.mark.parametrize('name', ['../manifest.json', 'originals/../reference.js', 'unknown.bin.gz', '/reference.html', 'transport/FJ3131.bin.gz?other'])
def test_unregistered_or_escaped_source_paths_fail_closed(name):
    with pytest.raises(ValueError, match='Unknown'):
        native.validate_file(name)


def test_present_corrupt_payload_cannot_fall_back_to_hosted_metadata(tmp_path, monkeypatch):
    root = tmp_path
    target = root / 'web/anatomy/bp3d-thoracic-4.3/transport/FJ3131.bin.gz'
    target.parent.mkdir(parents=True)
    target.write_bytes(b'corrupt')
    native.registry()  # Preserve the genuine pinned registry before redirecting payload lookup.
    monkeypatch.setattr(native, 'ROOT', root)
    monkeypatch.setenv('VERCEL', '1')
    with pytest.raises(ValueError, match='bytes changed'):
        native.validate_file('transport/FJ3131.bin.gz')


def test_hosted_only_payloads_require_hosted_environment(tmp_path, monkeypatch):
    native.registry()
    monkeypatch.setattr(native, 'ROOT', tmp_path)
    monkeypatch.delenv('VERCEL', raising=False)
    with pytest.raises(ValueError, match='missing'):
        native.validate_file('transport/FJ3131.bin.gz')
    monkeypatch.setenv('VERCEL', '1')
    native.validate_file('transport/FJ3131.bin.gz')
    with pytest.raises(ValueError, match='missing'):
        native.validate_file('reference.html')


@pytest.mark.parametrize('path', ['primer/server.py','primer/module_media.py','primer/source_native_inspectors.py','web/app.js','vercel.json'])
def test_native_integration_inverse_is_exact_and_rejects_other_edits(path):
    from tools.thoracic_native_runtime_compatibility import reviewed, previous_runtime_bytes
    raw = (ROOT / path).read_bytes()
    record = reviewed()['files'][path]
    restored = previous_runtime_bytes(path, raw)
    assert hashlib.sha256(restored).hexdigest() == record['before_sha256']
    with pytest.raises(ValueError, match='Unreviewed'):
        previous_runtime_bytes(path, raw + b'\n')
