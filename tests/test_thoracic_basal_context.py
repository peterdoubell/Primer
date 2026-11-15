"""Basal context retains complete same-case organs without inferred tissue layers."""
import gzip
import hashlib
import json
from pathlib import Path

import nibabel as nib
import numpy as np
from skimage.measure import marching_cubes

from tools.anatomy_sources.review_hvsmr2_pat7_source import read_nifti

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/thoracic-basal-context-review-s0028'


def test_all_seven_same_case_labels_and_original_ct_are_preserved():
    proof = json.loads((REVIEW / 'source-review.json').read_text())
    assert [r.get('label') for r in proof['records'][1:]] == [
        'lung_upper_lobe_left', 'lung_lower_lobe_left', 'lung_upper_lobe_right',
        'lung_middle_lobe_right', 'lung_lower_lobe_right', 'liver', 'spleen']
    assert not proof['clinical_approval'] and not proof['structure_coverage_granted']
    assert not proof['source_masks_relabelled_or_components_deleted']
    for row in proof['records']:
        path = REVIEW / row['file']
        encoded = path.read_bytes()
        assert hashlib.sha256(encoded).hexdigest() == row['sha256']
        independent, affine, _ = read_nifti(path)
        image = nib.load(path)
        assert np.array_equal(independent, image.dataobj.get_unscaled())
        assert np.array_equal(affine, image.affine)
        assert list(independent.shape) == [299, 299, 394]
        assert affine.tolist() == row['affine'] == proof['records'][0]['affine']
    acquisition = json.loads((REVIEW / 'basal-context-acquisition.json').read_text())
    assert acquisition['member_CRCs_verified']
    assert acquisition['publisher_archive_identity_unchanged_before_after']
    assert [r['label'] for r in acquisition['members']] == ['liver', 'spleen']
    assert proof['records'][6]['component_voxels_6'] == [398757, 2]
    assert proof['records'][7]['component_voxels_6'] == [28223, 1]


def test_every_original_label_interface_and_display_position_is_retained():
    proof = json.loads((REVIEW / 'source-review.json').read_text())
    manifest = json.loads((REVIEW / 'viewer-manifest.json').read_text())
    assert len(manifest['parts']) == 7
    origin = np.asarray(manifest['mesh_origin_source_mm'])
    for row, part in zip(proof['records'][1:], manifest['parts']):
        image = nib.load(REVIEW / row['file'])
        vertices, faces, _, _ = marching_cubes(np.asarray(image.dataobj.get_unscaled()), level=.5, allow_degenerate=True)
        vertices = vertices.astype(np.float64)
        a = image.affine
        world = np.column_stack([vertices[:, 0]*a[i, 0] + vertices[:, 1]*a[i, 1] + vertices[:, 2]*a[i, 2] + a[i, 3] for i in range(3)]).astype('<f8')
        assert gzip.decompress((REVIEW / row['surfaces']['positions.f64.gz']['file']).read_bytes()) == world.tobytes()
        assert gzip.decompress((REVIEW / row['surfaces']['triangles.u32.gz']['file']).read_bytes()) == faces.astype('<u4').tobytes()
        raw = gzip.decompress((REVIEW / part['buffer_file']).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == part['buffer_decoded_sha256']
        positions = np.frombuffer(raw[:len(vertices)*12], dtype='<f4').reshape(-1, 3)
        assert np.array_equal(positions, (world-origin).astype('<f4'))
        triangles = world[faces]
        face_normals = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
        normals = np.zeros_like(world)
        for corner in range(3):
            np.add.at(normals, faces[:, corner], face_normals)
        lengths = np.linalg.norm(normals, axis=1)
        normals[lengths > 0] /= lengths[lengths > 0, None]
        assert raw[len(vertices)*12:len(vertices)*24] == normals.astype('<f4').tobytes()
        assert raw[len(vertices)*24:] == faces.astype('<u4').tobytes()
        assert part['triangles'] == len(faces)


def test_viewer_keeps_acoustic_path_and_tissue_layer_limits_explicit():
    html = (REVIEW / 'index.html').read_text()
    assert 'All seven source parts' in html
    assert 'do not establish an ultrasound acoustic path' in html
    assert 'A label interface is not a tissue capsule' in html
    assert 'clinical approval' in html


def test_browser_and_gpu_evidence_covers_every_part_at_both_widths():
    proof = json.loads((REVIEW / 'viewer-browser-proof.json').read_text())
    assert len(proof['rows']) == 126 and not proof['errors']
    assert {(r['width'], r['label'], r['axis']) for r in proof['rows']} == {
        (width, part, axis) for width in [1440, 390] for part in range(7) for axis in range(3)}
    assert all(r['source_sample_and_display_exact'] for r in proof['rows'])
    for name, digest in proof['implementation_file_sha256'].items():
        assert hashlib.sha256((REVIEW / name).read_bytes()).hexdigest() == digest
    gpu = json.loads((REVIEW / 'viewer-gpu-proof.json').read_text())
    manifest = json.loads((REVIEW / 'viewer-manifest.json').read_text())
    expected = {r['id']: r['triangles'] for r in manifest['parts']}
    assert {(r['width'], r['id']) for r in gpu['rows']} == {(w, i) for w in [1440, 390] for i in expected}
    assert all(r['all_uploaded_buffers_exact'] and r['drawn_source_triangles'] == expected[r['id']] for r in gpu['rows'])
