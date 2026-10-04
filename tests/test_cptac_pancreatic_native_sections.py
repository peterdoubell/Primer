"""Native selection and archive binding must not manufacture anatomical alignment."""
import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from tools.anatomy_sources.render_cptac_pancreatic_native_reference import native_region, verified_objects


def test_physical_margin_and_per_role_midpoint_preserve_native_indices():
    np = pytest.importorskip('numpy')
    points = np.array([[10., 20., 30.], [12., 24., 32.]])
    centre, start, stop = native_region(points, np.zeros(3), [1., 2., .5], [100, 100, 100], margin_mm=2)
    assert centre.tolist() == [11, 11, 62]
    assert start.tolist() == [8, 9, 56]
    assert stop.tolist() == [15, 14, 69]
    moved = native_region(points + [3, 0, 0], np.zeros(3), [1., 2., .5], [100, 100, 100], margin_mm=2)[0]
    assert moved.tolist() == [14, 11, 62]  # own source location; no fit back to the first acquisition


def test_crop_clips_only_display_extent_and_rejects_outside_source():
    np = pytest.importorskip('numpy')
    centre, start, stop = native_region([[0, 0, 0], [1, 1, 1]], np.zeros(3), [1, 1, 1], [4, 4, 4], margin_mm=25)
    assert start.tolist() == [0, 0, 0] and stop.tolist() == [4, 4, 4]
    with pytest.raises(ValueError, match='outside native grid'):
        native_region([[0, 0, 0], [5, 1, 1]], np.zeros(3), [1, 1, 1], [4, 4, 4])
    with pytest.raises(ValueError, match='sampling'):
        native_region([[0, 0, 0]], np.zeros(3), [1, 0, 1], [4, 4, 4])


def test_archive_must_match_geometry_receipt_before_decoding(tmp_path):
    pytest.importorskip('pydicom')
    case, role = 'C3L-02112', 'arterial-labelled-ct'
    archive = tmp_path / (case + '-' + role + '.zip')
    with zipfile.ZipFile(archive, 'w') as z:
        z.writestr('unchanged.txt', 'original')
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    receipt = tmp_path / (case + '-' + role + '-archive-audit.json')
    receipt.write_text(json.dumps({'archive_sha256': digest, 'members': []}))
    with pytest.raises(ValueError, match='Receipt differs'):
        verified_objects(tmp_path, case, role, '0' * 64)
    archive.write_bytes(b'changed')
    with pytest.raises(ValueError, match='archive changed'):
        verified_objects(tmp_path, case, role, digest)


def test_actual_figures_bind_separate_acquisitions_and_unresolved_limits():
    root = Path(__file__).resolve().parents[1]
    folder = root / 'docs/cptac-pancreatic-native-sections'
    receipt = json.loads((folder / 'C3L-02112-native-sections.provenance.json').read_text())
    assert receipt['clinical_approval'] is False and receipt['runtime_promoted'] is False
    assert receipt['tracking_identity_reconciled'] is False and receipt['phase_adequacy_verified'] is False
    assert receipt['source_voxels_resampled'] is False
    records = receipt['records']
    assert [r['source_role'] for r in records] == ['arterial-labelled', 'venous-labelled']
    assert [r['source_shape_zyx'][0] for r in records] == [365, 713]
    assert len({r['ct_archive_sha256'] for r in records}) == 2
    assert len({r['axial_source_sop_instance_uid'] for r in records}) == 2
    for r in records:
        assert hashlib.sha256((folder / r['figure']).read_bytes()).hexdigest() == r['figure_sha256']
        assert r['native_sections_registered_between_roles'] is False
        assert r['annotation_is_location_aid_only'] is True
        assert [p['axis_zyx'] for p in r['planes']] == [0, 1, 2]
        assert all(p['resampling'] is False for p in r['planes'])
