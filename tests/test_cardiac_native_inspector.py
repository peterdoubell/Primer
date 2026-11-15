"""Cardiac source inspection preserves originals, complete interfaces and explicit limits."""
import gzip
import hashlib
import json
import subprocess
import shutil
from pathlib import Path

import numpy as np
import pytest

from primer import cardiac_native_inspector as cardiac
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/cardiac-native-source-review-v1-s0028'


@pytest.mark.skipif(shutil.which('node') is None, reason='Node.js is required')
def test_lossless_mask_storage_restores_every_source_value_with_bounded_resident_buffers():
    result = subprocess.run(['node', 'tools/check_cardiac_mask_storage.cjs'], cwd=ROOT,
                            capture_output=True, text=True, check=True, timeout=30)
    proof = json.loads(result.stdout)
    assert proof['originalMaskSamplesChecked'] == 176119970
    assert proof['packedMaskBytes'] == 22015000
    assert proof['residentSourceVoxelBuffersBytes'] == 162911328


def test_every_runtime_file_is_the_exact_reviewed_source_or_declared_display_adaptation():
    data = cardiac.registry()
    assert len(data['files']) == 17
    for name, record in data['files'].items():
        raw = cardiac.validate_file(name).read_bytes()
        assert raw == (REVIEW / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == record['sha256']
        assert len(raw) == record['bytes']


def test_original_int32_CT_and_all_masks_preserve_samples_and_full_interfaces():
    manifest = json.loads((REVIEW / 'viewer-manifest.json').read_text())
    source = json.loads((REVIEW / 'source-review.json').read_text())
    assert hashlib.sha256((REVIEW / 'source-review.json').read_bytes()).hexdigest() == manifest['source_review_sha256']
    assert manifest['ct_sample_kind'] == 'signed_int32' and manifest['ct_sample_bytes'] == 4
    count = int(np.prod(manifest['shape']))
    original_ct = gzip.decompress((REVIEW / manifest['ct_file']).read_bytes())
    samples = original_ct[manifest['ct_voxel_offset']:]
    assert len(samples) == count * 4
    assert hashlib.sha256(samples).hexdigest() == manifest['ct_payload_sha256']
    assert manifest['ct_file_sha256'] != 'd11b8acbf137277d157930f7d0cb3a5f259364a5e5af18dafcd3cac0ecf4168c'
    assert manifest['source_xyzt_units'] == 0 and manifest['source_original_published_grid_not_scanner_DICOM']
    assert sum(part['triangles'] for part in manifest['parts']) == 86072
    origin = np.array(manifest['sform_origin'])
    by_label = {record['source_label']: record for record in source['records'][1:]}
    for part in manifest['parts']:
        record = by_label[part['id']]
        decoded = gzip.decompress((REVIEW / part['mask_file']).read_bytes())
        mask = decoded[part['mask_voxel_offset']:]
        assert len(mask) == count and set(mask) == {0, 1}
        assert hashlib.sha256(mask).hexdigest() == part['mask_payload_sha256']
        assert np.count_nonzero(np.frombuffer(mask, dtype='u1')) == record['foreground_voxels']
        raw = gzip.decompress((REVIEW / part['buffer_file']).read_bytes())
        n = part['vertices']
        assert len(raw) == n * 24 + part['triangles'] * 12
        positions = np.frombuffer(raw[:n * 12], dtype='<f4').reshape(-1, 3).astype('<f8') + origin
        normals = np.frombuffer(raw[n * 12:n * 24], dtype='<f4').reshape(-1, 3)
        indices = raw[n * 24:]
        assert hashlib.sha256(positions.astype('<f8').tobytes()).hexdigest() == part['source_position_payload_sha256']
        assert hashlib.sha256(indices).hexdigest() == part['source_triangle_payload_sha256']
        assert np.isfinite(normals).all() and np.max(np.abs(np.linalg.norm(normals, axis=1) - 1)) < 2e-7
        assert record['components_6_connected'] == 1


def test_four_bound_reports_and_shared_lessons_keep_source_meaning_and_clinical_limits():
    curriculum = Curriculum()
    for identifier, entries in cardiac.references().items():
        ref = detail(curriculum, resolve(identifier))['radiology_reference']
        item = next(v for v in ref['source_native_inspectors'] if v['id'] == cardiac.IDENTIFIER)
        assert item == entries[0]
        assert all(item[flag] is False for flag in cardiac.APPROVAL_FLAGS)
        assert 'RV/atrial myocardial walls' in item['caption']
        assert item['license'] == 'CC BY 4.0'
        media = next(v for v in curriculum.node(ref['investigation']['module_id'])['lesson_media']
                     if v['kind'] == 'source-native-inspectors')
        assert identifier in media['investigation_ids']
        assert 'probabilities' not in media['instructions']


@pytest.mark.parametrize('asset', ['../index.html', 'originals%2Fct.nii.gz', 'originals/../viewer.css', 'missing.nii.gz', '/index.html'])
def test_unregistered_source_paths_are_rejected(asset):
    with pytest.raises(ValueError, match='Unknown'):
        cardiac.validate_file(asset)


def test_corrupt_present_source_and_nonregular_payload_never_use_hosted_fallback(tmp_path, monkeypatch):
    cardiac.registry()
    monkeypatch.setattr(cardiac, 'ROOT', tmp_path)
    monkeypatch.setenv('VERCEL', '1')
    p = tmp_path / 'web/anatomy' / cardiac.ATLAS / 'originals/ct.nii.gz'
    p.parent.mkdir(parents=True)
    p.write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='bytes changed'):
        cardiac.validate_file('originals/ct.nii.gz')
    p.unlink()
    p.mkdir()
    with pytest.raises(ValueError, match='regular'):
        cardiac.validate_file('originals/ct.nii.gz')


def test_absent_original_is_allowed_only_for_registered_hosted_payloads(tmp_path, monkeypatch):
    cardiac.registry()
    monkeypatch.setattr(cardiac, 'ROOT', tmp_path)
    monkeypatch.delenv('VERCEL', raising=False)
    with pytest.raises(ValueError, match='missing'):
        cardiac.validate_file('originals/ct.nii.gz')
    monkeypatch.setenv('VERCEL', '1')
    cardiac.validate_file('originals/ct.nii.gz')
    with pytest.raises(ValueError, match='missing'):
        cardiac.validate_file('index.html')
