"""Exact processed source preservation is separate from clinical anatomy approval."""
import collections
import gzip
import hashlib
import json
import math
import shutil
import struct
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / 'docs/wt9fc-tongue-source-review'
ATLAS = 'wt9fc-sub007'
OUT = ROOT / 'web/anatomy' / ATLAS


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def test_original_dataset_grant_and_case_storage_are_preserved_separately():
    node = json.loads((PROOF / 'osf-node.json').read_text())
    licence = json.loads((PROOF / 'osf-license.json').read_text())
    evidence = json.loads((PROOF / 'dataset-licence-evidence.json').read_text())
    assert node['data']['relationships']['license']['data']['id'] == licence['data']['id']
    assert licence['data']['attributes']['name'] == 'CC0 1.0 Universal'
    assert evidence['node_sha256'] == sha((PROOF / 'osf-node.json').read_bytes())
    assert evidence['licence_sha256'] == sha((PROOF / 'osf-license.json').read_bytes())
    assert evidence['article_licence'] == 'CC-BY-NC-ND 4.0'
    assert not evidence['article_graphics_or_captions_reused']
    acquisition = json.loads((PROOF / 'acquisition.json').read_text())
    for row in acquisition['files']:
        raw = (PROOF / row['filename']).read_bytes()
        assert len(raw) == row['bytes']
        assert sha(raw) == row['sha256']
        assert hashlib.md5(raw).hexdigest() == row['md5']
    report = json.loads((PROOF / 'independent-grid-and-surface-review.json').read_text())
    for name, row in report['sample_checks'].items():
        raw = gzip.decompress((PROOF / name).read_bytes())
        assert struct.unpack_from('<8h', raw, 40)[1:4] == (64, 320, 320)
        assert row['samples'] == 6553600
        assert row['original_raw_samples_independently_equal']
        assert row['scaled_samples_independently_equal']
        assert row['raw_header_sform_independently_equal_nibabel']
        assert tuple(struct.unpack_from('<12f', raw, 280)) == tuple(v for line in row['affine'][:3] for v in line)
        assert list(struct.unpack_from('<2f', raw, 112)) == row['scale_slope_intercept']
    assert not report['image_mask_affine_identical']
    assert report['max_image_mask_grid_corner_distance_mm'] < 0.00008
    assert report['case_context_from_source_spreadsheet']['age.at.scan'] == 33.12
    assert report['case_context_from_source_spreadsheet']['sex'] == 'Female'
    assert report['source_health_context']['subject_specific_diagnosis_not_provided']
    assert not report['source_health_context']['independent_normal_anatomy_or_swallowing_function_proven']


def test_every_source_face_and_component_survives_transport_without_repairs():
    manifest = json.loads((OUT / 'manifest.json').read_text())
    report = json.loads((PROOF / 'independent-grid-and-surface-review.json').read_text())
    total = 0
    for row in report['labels']:
        value = row['label_value']
        part = next(p for p in manifest['parts'].values() if p['source_label'] == value)
        encoded = (ROOT / 'web' / part['file'].removeprefix('/app/')).read_bytes()
        assert sha(encoded) == part['sha256']
        decoded = gzip.decompress(encoded)
        assert sha(decoded) == part['decoded_sha256']
        magic, vertices, indices = struct.unpack_from('<4sII', decoded)
        assert magic == b'BP3D' and vertices == row['surface_vertices']
        assert indices == row['surface_triangles'] * 3
        original_faces = gzip.decompress((PROOF / f'label-{value}-triangles.u32le.bin.gz').read_bytes())
        faces = decoded[12 + vertices * 24:]
        assert faces == original_faces
        assert sha(faces) == part['source_triangles_sha256']
        positions = gzip.decompress((PROOF / f'label-{value}-positions.f64le.bin.gz').read_bytes())
        assert sha(positions) == part['source_positions_sha256']
        for i, (coordinate,) in enumerate(struct.iter_unpack('<d', positions)):
            transported = struct.unpack_from('<f', decoded, 12 + i * 4)[0]
            assert math.isfinite(transported) and abs(coordinate - transported) <= 4e-5
        edges = collections.Counter()
        parent = list(range(vertices))

        def find(v):
            while v != parent[v]:
                parent[v] = parent[parent[v]]
                v = parent[v]
            return v

        used = set()
        for a, b, c in struct.iter_unpack('<III', faces):
            assert max(a, b, c) < vertices
            used.update((a, b, c))
            for x, y in [(a, b), (b, c), (c, a)]:
                edges[tuple(sorted((x, y)))] += 1
                parent[find(x)] = find(y)
        assert all(count == 2 for count in edges.values())
        assert len({find(v) for v in used}) == part['source_components']
        total += indices // 3
    assert total == manifest['total_triangles'] == 67508
    inferior = next(p for p in manifest['parts'].values() if p['source_label'] == 3)
    assert inferior['name'].startswith('inferior longitudinal') and inferior['source_components'] == 2
    genio = next(p for p in manifest['parts'].values() if p['source_label'] == 4)
    assert genio['name'].startswith('genioglossus')
    assert manifest['source_image_affine'] != manifest['source_label_affine']
    assert manifest['distributed_source_processed'] and not manifest['unmodified_native_acquisition']
    assert not manifest['source_movie_registration'] and not manifest['clinical_approval']
    assert not manifest['anatomical_approval'] and not manifest['complete_swallowing_geometry_verified']


def test_reference_and_preview_do_not_grant_normality_or_functional_coverage():
    entry = json.loads((PROOF / 'reader-reference-entry.json').read_text())
    assert entry['atlas'] == ATLAS and entry['family'] == 'tongue-source'
    assert entry['initial_cropped'] is False
    assert sha((OUT / 'manifest.json').read_bytes()) == entry['manifest_sha256']
    image = entry['source_image']
    raw = (ROOT / 'web' / image['src'].removeprefix('/app/')).read_bytes()
    assert sha(raw) == image['sha256']
    assert struct.unpack_from('>II', raw, 16) == (image['width'], image['height']) == (1020, 800)
    display = json.loads((PROOF / 'source-display-review.json').read_text())
    assert not display['source_samples_changed'] and not display['extra_anatomical_data_removed']
    assert display['display_pixel_repeat_factor'] == 3 and not display['interpolation_applied']
    assert not display['extra_display_resolution_claimed']
    assert all(crop['all_nonzero_plane_samples_retained'] for crop in display['display_zero_margin_crops'])
    full = ROOT / 'web/reference-media' / ATLAS / 'full-source-index-planes.png'
    assert sha(full.read_bytes()) == display['full_source_plane_sha256']
    assert display['original_publisher_ROI_masking_preserved']
    assert not display['source_patient_anatomical_planes_independently_verified']
    note = entry['population_note']
    assert 'publisher 1 mm Gaussian smoothing' in note and 'not an unmodified native acquisition' in note
    assert 'no diagnosis field' in note and 'no registration to published swallowing movies' in note
    assets = json.loads((PROOF / 'reader-asset-entries.json').read_text())
    assert len(assets) == 5
    assert sum(a['kind'] == 'model' for a in assets) == 4
    for asset in assets:
        assert asset['investigation_ids'] == ['ra.swallowing']
        assert not asset['structure_ids'] and not asset['requirement_coverage']
        assert asset['anatomical_review']['status'] == 'pending'
        grant = asset['source']['license']
        assert grant['name'] == 'CC0 1.0 Universal' and grant['commercial_use'] and grant['redistribution']
        assert sha((ROOT / grant['evidence_path']).read_bytes()) == grant['evidence_sha256']


def test_default_build_reproduces_geometry_without_touching_global_registries(tmp_path):
    pytest.importorskip('numpy')
    pytest.importorskip('PIL')
    from tools.anatomy_sources.package_wt9fc_tongue_reference import package
    result = package(PROOF, root=tmp_path)
    assert not result['global_registry_applied']
    assert not (tmp_path / 'data/radiology/source-anatomy-references.json').exists()
    assert not (tmp_path / 'data/radiology/radiology-asset-evidence.json').exists()
    for old in OUT.glob('*.bin.gz'):
        assert old.read_bytes() == (tmp_path / 'web/anatomy' / ATLAS / old.name).read_bytes()
    source_image = ROOT / 'web/reference-media' / ATLAS / 'source-MRI-label-context.png'
    assert source_image.read_bytes() == (tmp_path / source_image.relative_to(ROOT)).read_bytes()
    full = ROOT / 'web/reference-media' / ATLAS / 'full-source-index-planes.png'
    assert full.read_bytes() == (tmp_path / full.relative_to(ROOT)).read_bytes()


def test_preview_repeats_exact_full_plane_pixels_without_smoothing():
    Image = pytest.importorskip('PIL.Image')
    folder = ROOT / 'web/reference-media' / ATLAS
    full = Image.open(folder / 'full-source-index-planes.png').convert('RGB')
    display = Image.open(folder / 'source-MRI-label-context.png').convert('RGB')
    proof = json.loads((PROOF / 'source-display-review.json').read_text())
    for crop in proof['display_zero_margin_crops']:
        axis = crop['source_index_axis']
        low_y, low_x = crop['transposed_plane_low_inclusive']
        high_y, high_x = crop['transposed_plane_high_exclusive']
        assert crop['all_nonzero_label_samples_retained']
        for row in range(2):
            x, y = axis * 340 + 10, 50 + row * 365 + 20
            source = full.crop((x + low_x, y + low_y, x + high_x, y + high_y))
            width, height = source.width * 3, source.height * 3
            expected = source.resize((width, height), resample=Image.Resampling.NEAREST)
            assert display.crop((x, y, x + width, y + height)).tobytes() == expected.tobytes()


def test_surface_proofs_match_reextraction_from_original_distributed_mask():
    np = pytest.importorskip('numpy')
    measure = pytest.importorskip('skimage.measure')
    raw = gzip.decompress((PROOF / 'sub-007_segID-001_T2w_labels.nii.gz').read_bytes())
    labels = np.frombuffer(raw, '<u2', offset=352).reshape((64, 320, 320), order='F')
    affine = np.array(struct.unpack_from('<12f', raw, 280)).reshape(3, 4)
    for value in range(1, 5):
        vertices, faces, _, _ = measure.marching_cubes((labels == value).astype(np.float32),
                                                      level=0.5, method='lewiner', allow_degenerate=True)
        source_positions = np.dot(vertices, affine[:, :3].T) + affine[:, 3]
        expected_positions = gzip.decompress((PROOF / f'label-{value}-positions.f64le.bin.gz').read_bytes())
        expected_faces = gzip.decompress((PROOF / f'label-{value}-triangles.u32le.bin.gz').read_bytes())
        assert source_positions.astype('<f8').tobytes() == expected_positions
        assert faces.astype('<u4').tobytes() == expected_faces


def test_packager_rejects_swapped_muscle_labels_in_source_review(tmp_path):
    pytest.importorskip('numpy')
    pytest.importorskip('PIL')
    from tools.anatomy_sources.package_wt9fc_tongue_reference import package
    copied = tmp_path / 'changed-source'
    shutil.copytree(PROOF, copied)
    path = copied / 'independent-grid-and-surface-review.json'
    report = json.loads(path.read_text())
    report['labels'][2]['source_name'] = 'genioglossus'
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match='muscle mapping'):
        package(copied, root=tmp_path / 'output')
