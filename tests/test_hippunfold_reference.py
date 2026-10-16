"""The registered hippocampal reference preserves source values and labelled cells.

These tests establish source identity and delivery, not clinical completeness.
"""
import gzip
import hashlib
import json
import struct
from pathlib import Path

import numpy as np
import pytest

from primer import hippunfold_reference as hipp
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/hippunfold-epilepsy-review-20261016'
ASSETS = ROOT / 'web/anatomy' / hipp.ATLAS


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def original_nifti(row):
    """Read the original stored float64 samples without a medical image library."""
    packed = (REVIEW / 'originals' / row['sourceFile']).read_bytes()
    assert sha(packed) == row['sourceSHA256']
    raw = gzip.decompress(packed)
    assert struct.unpack_from('<i', raw)[0] == 348
    assert raw[344:348] == b'n+1\0'
    dims = struct.unpack_from('<8h', raw, 40)
    assert dims == (3, 128, 256, 128, 1, 1, 1, 1)
    assert struct.unpack_from('<2h', raw, 70) == (64, 64)
    offset, slope, intercept = struct.unpack_from('<3f', raw, 108)
    assert (offset, slope, intercept) == (352, 1, 0)
    assert raw[123] & 7 == 2  # Source length units are millimetres.
    assert struct.unpack_from('<h', raw, 254)[0] > 0
    affine = np.eye(4)
    affine[:3] = np.asarray(struct.unpack_from('<12f', raw, 280)).reshape(3, 4)
    samples = np.frombuffer(raw, dtype='<f8', offset=int(offset))
    assert len(samples) == 128 * 256 * 128 and np.isfinite(samples).all()
    return samples, affine


def decoded(row):
    packed = (ASSETS / row['file']).read_bytes()
    assert sha(packed) == row['gzipSHA256']
    raw = gzip.decompress(packed)
    assert sha(raw) == row['decodedSHA256']
    assert len(raw) == row['byteLength']
    return raw


@pytest.fixture(scope='module')
def manifest():
    return json.loads((ASSETS / 'manifest.json').read_text())


def test_every_runtime_asset_matches_the_registry_and_is_regular():
    records = hipp.registry()['files']
    assert len(records) == 25
    assert set(records) == {p.name for p in ASSETS.iterdir() if p.is_file()}
    for name, record in records.items():
        path = hipp.validate_file(name)
        assert path.is_file() and not path.is_symlink()
        raw = path.read_bytes()
        assert len(raw) == record['bytes'] and sha(raw) == record['sha256']


def test_all_source_samples_recover_original_float64_bits_and_affines(manifest):
    checked = 0
    assert manifest['storageOrder'] == 'F'
    for hemisphere in manifest['hemispheres']:
        for row in hemisphere['arrays']:
            original, affine = original_nifti(row)
            restored = np.frombuffer(decoded(row), dtype=row['dtype']).astype('<f8')
            np.testing.assert_array_equal(restored.view('<u8'), original.view('<u8'))
            np.testing.assert_array_equal(affine, hemisphere['affine'])
            checked += len(original)
        assert np.linalg.det(affine[:3, :3]) < 0
    assert checked == 16777216


@pytest.mark.parametrize('side', ['L', 'R'])
def test_every_mesh_triangle_is_a_complete_outward_source_voxel_face(side, manifest):
    hemisphere = next(h for h in manifest['hemispheres'] if h['name'] == side)
    label_row = next(r for r in hemisphere['arrays'] if r['modality'] == 'lbl')
    source, affine = original_nifti(label_row)
    shape = tuple(manifest['shape'])
    labels = source.reshape(shape, order='F')
    assert set(np.unique(labels)) == set(range(9))
    shape_array = np.asarray(shape)
    total = 0
    for row in [m for m in manifest['meshes'] if m['sourceHemisphereName'] == side]:
        raw = decoded(row)
        assert struct.unpack_from('<4sIII', raw) == (b'HVX1', row['vertexCount'], row['triangleCount'], 0)
        split = 16 + 12 * row['vertexCount']
        positions_raw, indices_raw = raw[16:split], raw[split:]
        assert sha(positions_raw) == row['positionByteSHA256']
        assert sha(indices_raw) == row['indexByteSHA256']
        points = np.frombuffer(positions_raw, '<f4').reshape(-1, 3).astype('<f8')
        triangles = np.frombuffer(indices_raw, '<u4').reshape(-1, 3)
        assert len(triangles) == row['triangleCount']
        assert np.isfinite(points).all() and np.all(points * 2 == np.round(points * 2))
        assert triangles.max() < len(points)
        np.testing.assert_array_equal(row['sourceAffine'], affine)
        corners = points[triangles]
        cross = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
        # Each original triangle covers half a unit voxel face. Handedness is
        # checked in physical source coordinates, whose affine determinant is negative.
        assert np.all(np.sum(cross * cross, axis=1) == 1)
        outward = cross * np.sign(np.linalg.det(affine[:3, :3]))
        axes = np.argmax(abs(outward), axis=1)
        signs = outward[np.arange(len(outward)), axes].astype(int)
        assert np.all(np.count_nonzero(outward, axis=1) == 1)
        owning = np.rint(corners.mean(axis=1) - outward * .25).astype(int)
        assert np.all((owning >= 0) & (owning < shape_array))
        assert np.all(labels[tuple(owning.T)] == row['label'])
        neighbour = owning + outward.astype(int)
        within = np.all((neighbour >= 0) & (neighbour < shape_array), axis=1)
        assert np.all(labels[tuple(neighbour[within].T)] != row['label'])
        flat = np.ravel_multi_index(tuple(owning.T), shape)
        keys = flat * 6 + axes * 2 + (signs > 0)
        order = np.argsort(keys, kind='stable')
        keys = keys[order]
        unique, counts = np.unique(keys, return_counts=True)
        assert np.all(counts == 2)
        # The pair must meet along the square diagonal, rather than duplicate
        # a triangle or overlap across one square edge.
        pairs = corners[order].reshape(-1, 2, 3, 3)
        common = (pairs[:, 0, :, None, :] == pairs[:, 1, None, :, :]).all(axis=-1).any(axis=-1)
        assert np.all(common.sum(axis=1) == 2)
        shared = pairs[:, 0][common].reshape(-1, 2, 3)
        assert np.all(np.sum((shared[:, 0] - shared[:, 1]) ** 2, axis=1) == 2)
        mask = labels == row['label']
        expected = []
        # Scan independently for all six occupied-to-unoccupied transitions,
        # including crop faces; no source component may be discarded.
        padded = np.pad(mask, 1)
        for axis in range(3):
            for sign in [-1, 1]:
                slices = [slice(1, n + 1) for n in shape]
                slices[axis] = slice(1 + sign, shape[axis] + 1 + sign)
                owner_flat = np.flatnonzero((mask & ~padded[tuple(slices)]).ravel())
                expected.append(owner_flat * 6 + axis * 2 + (sign > 0))
        np.testing.assert_array_equal(unique, np.sort(np.concatenate(expected)))
        world = corners @ affine[:3, :3].T + affine[:3, 3]
        world_cross = np.cross(world[:, 1] - world[:, 0], world[:, 2] - world[:, 0])
        inverse = np.linalg.inv(affine[:3, :3])
        expected_normal = np.stack([sum(outward[:, j] * inverse[j, k] for j in range(3))
                                    for k in range(3)], axis=1)
        assert np.all(np.sum(world_cross * expected_normal, axis=1) > 0)
        total += len(triangles)
    assert total == sum(m['triangleCount'] for m in manifest['meshes'] if m['sourceHemisphereName'] == side)


def test_only_two_reports_and_lessons_bind_the_partial_registered_reference():
    curriculum = Curriculum()
    refs = hipp.references()
    assert set(refs) == {'ra.mri-epilepsy', 'ra.mri-dementia'}
    for identifier, lesson_id in [('ra.mri-epilepsy', 'rad.5.epilepsy-mri'), ('ra.mri-dementia', 'rad.5.dementia')]:
        ref = detail(curriculum, resolve(identifier))['radiology_reference']
        item = next(i for i in ref['source_native_inspectors'] if i['id'] == hipp.IDENTIFIER)
        assert item == refs[identifier][0]
        assert all(item[flag] is False for flag in hipp.APPROVAL_FLAGS)
        assert item['coordinate_context'] == 'published-registered-training-grid'
        assert item['modality'] == 'Registered T2 MRI and categorical surfaces'
        assert item['license'] == 'CC BY 4.0'
        assert ref['reporting']['checklist'] and ref['report_templates'] and ref['walkthrough']['steps']
        assert not ref.get('source_native_only', False)
        gallery = next(m for m in curriculum.node(lesson_id)['lesson_media']
                       if m['kind'] == 'source-native-inspectors' and identifier in m['investigation_ids'])
        assert 'registered' in (gallery['title'] + gallery['instructions']).lower()


@pytest.mark.parametrize('asset', ['../index.html', 'L%2FT2w.bin.gz', '../L-T2w.bin.gz', '/index.html', 'absent.bin.gz', ''])
def test_unregistered_paths_are_rejected(asset):
    with pytest.raises(ValueError, match='Unknown'):
        hipp.validate_file(asset)


@pytest.mark.parametrize('asset', ['L-T2w.bin.gz', 'index.html'])
def test_corrupt_and_nonregular_files_never_use_hosted_fallback(asset, tmp_path, monkeypatch):
    hipp.registry()
    monkeypatch.setattr(hipp, 'ROOT', tmp_path)
    monkeypatch.setenv('VERCEL', '1')
    path = tmp_path / 'web/anatomy' / hipp.ATLAS / asset
    path.parent.mkdir(parents=True)
    path.write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='bytes changed'):
        hipp.validate_file(asset)
    path.unlink()
    path.mkdir()
    with pytest.raises(ValueError, match='regular'):
        hipp.validate_file(asset)
    path.rmdir()
    path.symlink_to(ASSETS / asset)
    with pytest.raises(ValueError, match='regular'):
        hipp.validate_file(asset)


def test_only_missing_registered_payloads_can_use_vercel_static_hosting(tmp_path, monkeypatch):
    hipp.registry()
    monkeypatch.setattr(hipp, 'ROOT', tmp_path)
    monkeypatch.delenv('VERCEL', raising=False)
    with pytest.raises(ValueError, match='missing'):
        hipp.validate_file('L-T2w.bin.gz')
    monkeypatch.setenv('VERCEL', '1')
    assert hipp.validate_file('L-T2w.bin.gz') == tmp_path / 'web/anatomy' / hipp.ATLAS / 'L-T2w.bin.gz'
    for name in hipp.AUTHORED:
        with pytest.raises(ValueError, match='missing'):
            hipp.validate_file(name)
