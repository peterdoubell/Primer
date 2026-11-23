"""Compare the deployed representation with all four uncompressed source NIfTIs.

Usage: python tools/anatomy_sources/verify_segthy_ultrasound.py SOURCE_DIR OUTPUT_DIR
"""
import gzip
import hashlib
import json
import sys
from pathlib import Path

import nibabel as nib
import numpy as np


def unpack(root, row):
    packed = (root / row["file"]).read_bytes()
    assert len(packed) == row["bytes"] and hashlib.sha256(packed).hexdigest() == row["sha256"]
    data = gzip.decompress(packed)
    assert hashlib.sha256(data).hexdigest() == row["decodedSHA256"]
    return data


def verify_case(source_dir, output_dir, case):
    volumes = []
    for role in ("image", "mask"):
        source = source_dir / (case["id"] + "_" + role + ".nii.gz")
        assert hashlib.sha256(gzip.decompress(source.read_bytes())).hexdigest() == case["sources"][role]["payloadSHA256"]
        volume = nib.load(source)
        assert np.array_equal(volume.affine, case["affine"])
        volumes.append(np.asanyarray(volume.dataobj))
    intensity, mask = volumes
    assert intensity.shape == mask.shape == tuple(case["shape"])
    stride = case["brickSize"]
    starts = set()
    for row in case["bricks"]:
        origin = tuple(row["start"])
        assert origin not in starts and all(v % stride == 0 for v in origin)
        starts.add(origin)
        cut = tuple(slice(v, v + stride) for v in origin)
        packed = np.frombuffer(unpack(output_dir, row), dtype=np.uint8).reshape(*reversed(row["size"]), 2)
        for channel, original in enumerate(volumes):
            assert np.array_equal(packed[..., channel].T, original[cut])
    expected = {(i, j, k) for i in range(0, mask.shape[0], stride) for j in range(0, mask.shape[1], stride)
                for k in range(0, mask.shape[2], stride)}
    assert starts == expected
    assert set(np.unique(mask)) == {0, *(label["code"] for label in case["labels"])}
    for label in case["labels"]:
        code = label["code"]
        mesh = label["mesh"]
        assert (mask == code).sum() == label["voxelCount"] and mask[tuple(label["focus"])] == code
        raw = unpack(output_dir, mesh)
        assert len(raw) == 12 * (mesh["vertices"] + mesh["triangles"])
        vertices = np.frombuffer(raw, dtype="<f4", count=mesh["vertices"] * 3).reshape(-1, 3)
        faces = np.frombuffer(raw, offset=vertices.nbytes, dtype="<u4").reshape(-1, 3)
        assert np.isfinite(vertices).all() and faces.max() < len(vertices)
        # Check transition edges and the centre vertices used to triangulate ambiguous cells.
        half = np.rint(2 * vertices / case["spacingMm"]).astype(int)
        assert np.allclose(vertices, half * np.array(case["spacingMm"]) / 2, rtol=0, atol=3e-6)
        fractional_axes = (half % 2).sum(axis=1)
        assert np.isin(fractional_axes, [1, 3]).all()
        edges = half[fractional_axes == 1]
        assert ((mask[tuple((edges // 2).T)] == code) ^ (mask[tuple(((edges + 1) // 2).T)] == code)).all()
        # A Lewiner centre vertex is inside one mixed cube. Every incident face
        # must connect it to that cube's checked edge intersections.
        for vertex in np.flatnonzero(fractional_axes == 3):
            lower = half[vertex] // 2
            cell = mask[tuple(slice(v, v + 2) for v in lower)] == code
            assert cell.any() and not cell.all()
        for axis in range(3):
            is_centre = fractional_axes[faces[:, axis]] == 3
            incident = faces[is_centre]
            if len(incident):
                centre = half[incident[:, axis]]
                adjacent = incident[:, [(axis + 1) % 3, (axis + 2) % 3]]
                assert (fractional_axes[adjacent] == 1).all()
                assert (np.abs(half[adjacent] - centre[:, None, :]) <= 1).all()
        a, b, c = vertices[faces].astype(np.float64).transpose(1, 0, 2)
        signed_volume = np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6
        assert signed_volume > 0
        print(f"{label['name']}: {len(vertices):,} verified boundary vertices, {len(faces):,} triangles")
    print(f"{case['id']}: {intensity.size:,} intensity and label pairs match the native inputs")


if __name__ == "__main__":
    source, output = map(Path, sys.argv[1:])
    for item in json.loads((output / "manifest.json").read_text())["cases"]:
        verify_case(source, output, item)
