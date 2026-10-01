import hashlib
from pathlib import Path
import zipfile

import pytest

from tools.anatomy_sources.audit_tcia_series_archive import audit_archive
from tools.anatomy_sources.review_tcia_lung_case import match_native_planes


def make_archive(path, data=b'original-source', manifest=None):
    if manifest is None:
        manifest = 'Filename,MD5Hash\nimage.dcm,' + hashlib.md5(data).hexdigest() + '\n'
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('image.dcm', data)
        z.writestr('md5hashes.csv', manifest)
    return path


def test_complete_publisher_manifest_verifies_exact_source_bytes(tmp_path):
    result = audit_archive(make_archive(tmp_path / 'source.zip'), 1, len(b'original-source'))
    assert result['publisher_per_file_md5_verified']
    assert result['archive_sha256'] == hashlib.sha256((tmp_path / 'source.zip').read_bytes()).hexdigest()
    assert result['members'][0]['sha256'] == hashlib.sha256(b'original-source').hexdigest()
    assert not result['clinical_approval']


def test_changed_source_or_missing_manifest_entry_is_rejected(tmp_path):
    archive = make_archive(tmp_path / 'changed.zip', b'edited-source',
        'Filename,MD5Hash\nimage.dcm,' + hashlib.md5(b'original-source').hexdigest() + '\n')
    with pytest.raises(ValueError, match='MD5 mismatch'):
        audit_archive(archive, 1)
    archive = make_archive(tmp_path / 'missing.zip', manifest='Filename,MD5Hash\n')
    with pytest.raises(ValueError, match='membership'):
        audit_archive(archive, 1)


def test_count_and_publisher_uncompressed_size_are_independent_checks(tmp_path):
    archive = make_archive(tmp_path / 'source.zip')
    with pytest.raises(ValueError, match='membership'):
        audit_archive(archive, 2)
    with pytest.raises(ValueError, match='bytes differ'):
        audit_archive(archive, 1, 1)


def test_seg_plane_order_is_matched_by_native_position_without_fitting():
    pytest.importorskip('numpy')
    ct = [[10, 20, -3], [10, 20, -2], [10, 20, -1]]
    assert match_native_planes(ct, [ct[2], ct[0], ct[1]]) == [2, 0, 1]
    with pytest.raises(ValueError, match='native plane'):
        match_native_planes(ct, [[10.01, 20, -3], ct[1], ct[2]])
    with pytest.raises(ValueError, match='Repeated'):
        match_native_planes(ct, [ct[0], ct[0], ct[2]])
