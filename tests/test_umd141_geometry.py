"""Guard the source MRI correspondence and unsampled section gaps."""
import gzip
import hashlib
import json
import shutil

import numpy as np
import pytest
from tools import check_umd141_geometry as checker


def test_original_runtime_geometry_matches_acquired_slabs():
    checker.audit()


def test_updated_checksum_cannot_hide_a_triangle_bridging_sections(tmp_path, monkeypatch):
    shutil.copytree(checker.ROOT, tmp_path, dirs_exist_ok=True)
    rows = json.loads((tmp_path / "surfaces.json").read_bytes())
    row = rows[0]
    raw = gzip.decompress((tmp_path / row["file"]).read_bytes())
    vertices = np.frombuffer(raw, "<f4", count=3 * row["vertices"]).reshape(-1, 3)
    faces = np.frombuffer(raw, "<u4", offset=12 * row["vertices"]).reshape(-1, 3).copy()
    grid = json.loads((tmp_path / "grid.json").read_bytes())
    affine = np.asarray(grid["sourceAffine"])
    voxel = np.einsum("ij,kj->ik", vertices.astype(float) - affine[:3, 3], np.linalg.inv(affine[:3, :3]))
    planes = np.rint(voxel[:, 2]).astype(int)
    first_plane = planes[faces[0, 0]]
    replacement = int(np.flatnonzero(planes != first_plane)[0])
    faces[0, 2] = replacement
    changed = vertices.tobytes() + faces.tobytes()
    (tmp_path / row["file"]).write_bytes(gzip.compress(changed, mtime=0))
    row["sha256"] = hashlib.sha256(changed).hexdigest()
    (tmp_path / "surfaces.json").write_text(json.dumps(rows))
    monkeypatch.setattr(checker, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="bridges separate acquired slabs"):
        checker.audit()


def test_updated_checksum_cannot_hide_a_model_shifted_by_one_source_voxel(tmp_path, monkeypatch):
    shutil.copytree(checker.ROOT, tmp_path, dirs_exist_ok=True)
    rows = json.loads((tmp_path / "surfaces.json").read_bytes())
    row = rows[0]
    raw = gzip.decompress((tmp_path / row["file"]).read_bytes())
    vertices = np.frombuffer(raw, "<f4", count=3 * row["vertices"]).reshape(-1, 3).copy()
    grid = json.loads((tmp_path / "grid.json").read_bytes())
    vertices += np.asarray(grid["sourceAffine"])[:3, 0].astype("<f4")
    changed = vertices.tobytes() + raw[row["vertices"] * 12:]
    (tmp_path / row["file"]).write_bytes(gzip.compress(changed, mtime=0))
    row["sha256"] = hashlib.sha256(changed).hexdigest()
    (tmp_path / "surfaces.json").write_text(json.dumps(rows))
    monkeypatch.setattr(checker, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="source annotation boundaries"):
        checker.audit()
