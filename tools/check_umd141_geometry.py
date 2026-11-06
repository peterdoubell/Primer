"""Audit acquired annotation slabs and lossless MRI transport for UMD case 141."""
from pathlib import Path
import gzip
import hashlib
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1] / "web/anatomy/umd-141"


def decoded(file, expected):
    raw = gzip.decompress((ROOT / file).read_bytes())
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("Source buffer checksum differs")
    return raw



def source_face_centres(selected, origin):
    """Encode each source boundary by doubled XY, source section and slab side."""
    locations = np.argwhere(selected) + origin
    caps = []
    for side in [-1, 1]:
        caps.append(np.column_stack((2 * locations[:, :2], locations[:, 2], np.full(len(locations), side))))
    for axis in [0, 1]:
        for direction in [-1, 1]:
            neighbour = np.roll(selected, -direction, axis=axis)
            boundary = [slice(None)] * 3
            boundary[axis] = -1 if direction > 0 else 0
            neighbour[tuple(boundary)] = False
            cells = np.argwhere(selected & ~neighbour) + origin
            xy = 2 * cells[:, :2]
            xy[:, axis] += direction
            caps.append(np.column_stack((xy, cells[:, 2], np.zeros(len(cells), dtype=int))))
    return np.unique(np.concatenate(caps), axis=0)

def audit():
    grid = json.loads((ROOT / "grid.json").read_bytes())
    full = json.loads((ROOT / "full-mri.json").read_bytes())
    rows = json.loads((ROOT / "surfaces.json").read_bytes())
    mask = np.frombuffer(decoded("mask.gz", grid["decodedSHA256"]["mask"]), "u1").reshape(grid["shape"], order="F")
    sources = json.loads((ROOT / "sources.json").read_bytes())
    proof_raw = (ROOT / sources["sourcePixelGeometryProofFile"]).read_bytes()
    if hashlib.sha256(proof_raw).hexdigest() != sources["sourcePixelGeometryProofSHA256"]:
        raise ValueError("Original DICOM geometry proof changed")
    proof = json.loads(proof_raw)
    if (proof["allFramesVerified"] is not True
            or proof["frames"] != full["shape"][2]
            or proof["matchingSourcePixels"] != int(np.prod(full["shape"]))
            or proof["maxPositionErrorVoxels"] >= .001):
        raise ValueError("Original DICOM/NIfTI correspondence is incomplete")
    frames = proof["framesSourceIdentities"]
    if sorted(frame["index"] for frame in frames) != list(range(full["shape"][2])):
        raise ValueError("Original DICOM frame coverage differs")
    for frame in frames:
        if frame["sliceThicknessMM"] != grid["sliceThicknessMM"]:
            raise ValueError("Acquired slice thickness changed")
        if abs(frame["spacingBetweenSlicesMM"] - grid["spacing"][2]) > .00001:
            raise ValueError("Acquired slice spacing changed")
    next_plane = 0
    for chunk in full["chunks"]:
        raw = decoded(chunk["file"], chunk["sha256"])
        if chunk["firstPlane"] != next_plane or len(raw) != chunk["decodedBytes"]:
            raise ValueError("Missing or reordered acquired MRI sections")
        if len(raw) != full["shape"][0] * full["shape"][1] * chunk["planes"] * 2:
            raise ValueError("MRI chunk extent differs")
        next_plane += chunk["planes"]
    if next_plane != full["shape"][2] or next_plane != 25:
        raise ValueError("Acquired MRI extent incomplete")
    affine = np.asarray(grid["sourceAffine"])
    spacing = np.asarray(grid["spacing"])
    thickness = grid["sliceThicknessMM"]
    if not 0 < thickness < spacing[2]:
        raise ValueError("Acquired slab gap differs")
    if {row["label"] for row in rows} != {1, 2, 3, 4} or len(rows) != 4:
        raise ValueError("Missing or duplicated source label")
    for row in rows:
        raw = decoded(row["file"], row["sha256"])
        vertices = np.frombuffer(raw, "<f4", count=3 * row["vertices"]).reshape(-1, 3)
        faces = np.frombuffer(raw, "<u4", offset=12 * row["vertices"]).reshape(-1, 3)
        if not np.isfinite(vertices).all() or faces.max() >= len(vertices) or len(faces) != row["triangles"]:
            raise ValueError("Invalid slab mesh")
        voxel = np.einsum("ij,kj->ik", vertices.astype(float) - affine[:3, 3], np.linalg.inv(affine[:3, :3]))
        plane = np.rint(voxel[:, 2]).astype(int)
        np.testing.assert_allclose(voxel[:, :2] * 2, np.rint(voxel[:, :2] * 2), atol=.0002)
        np.testing.assert_allclose(np.abs((voxel[:, 2] - plane) * spacing[2]), thickness / 2, atol=.0001)
        if not np.all(plane[faces] == plane[faces[:, :1]]):
            raise ValueError("A triangle bridges separate acquired slabs")
        pairs = faces.reshape(-1, 6)
        if not np.all(pairs[:, 0] == pairs[:, 3]) or not np.all(pairs[:, 2] == pairs[:, 4]):
            raise ValueError("Annotation face triangulation changed")
        quad_ids = pairs[:, [0, 1, 2, 5]]
        centres = voxel[quad_ids].mean(axis=1)
        xy = np.rint(2 * centres[:, :2]).astype(int)
        section = np.rint(centres[:, 2]).astype(int)
        slab_offset = (centres[:, 2] - section) * spacing[2]
        side = np.rint(slab_offset / (thickness / 2)).astype(int)
        np.testing.assert_allclose(2 * centres[:, :2], xy, atol=.0002)
        np.testing.assert_allclose(slab_offset, side * thickness / 2, atol=.0001)
        actual, occurrences = np.unique(np.column_stack((xy, section, side)), axis=0, return_counts=True)
        expected_centres = source_face_centres(mask == row["label"], np.asarray(grid["origin"]))
        if not np.all(occurrences == 1) or not np.array_equal(actual, expected_centres):
            raise ValueError("Model faces differ from source annotation boundaries")
        count = int(np.count_nonzero(mask == row["label"]))
        if count != row["sourceVoxels"]:
            raise ValueError("Label voxels omitted from model")
        tri = vertices[faces].astype(float)
        measured = np.einsum("ij,ij->i", tri[:, 0], np.cross(tri[:, 1], tri[:, 2])).sum() / 6
        expected = count * abs(np.linalg.det(affine[:3, :3])) * thickness / spacing[2]
        if abs(measured - expected) > .05:
            raise ValueError("Sampled slab volume differs from source annotation")
    print("25 MRI sections and four annotation models verified; acquired slab gaps retained.")


if __name__ == "__main__":
    audit()
