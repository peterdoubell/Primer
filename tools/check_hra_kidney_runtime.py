"""Verify published kidney geometry against the original source inventories."""
from pathlib import Path
import gzip
import hashlib
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "web/anatomy/hra-kidney-interior"
REVIEW = ROOT / "docs/hra-renal-source-review"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def audit():
    rows = json.loads((ASSETS / "surfaces.json").read_bytes())
    expected = {}
    for identifier in ["kidney-female-right-v1.3", "ureter-female-right-v1.2"]:
        inventory = json.loads((REVIEW / (identifier + "-geometry-inventory.json")).read_bytes())
        for record in inventory["records"]:
            key = (identifier, record["node_name"])
            if key in expected:
                raise ValueError("Duplicate source primitive identity")
            expected[key] = (inventory["source_glb_sha256"], record)
    seen = set()
    boundary_edges = 0
    degenerate_faces = 0
    triangles = 0
    for row in rows:
        key = (row["source"], row["id"])
        if key in seen or key not in expected:
            raise ValueError("Unknown or duplicated runtime primitive")
        seen.add(key)
        source_sha, record = expected[key]
        raw = gzip.decompress((ASSETS / row["file"]).read_bytes())
        if digest(raw) != row["sha256"] or row["sourceGLBSHA256"] != source_sha:
            raise ValueError("Runtime or source identity changed")
        if len(raw) != 12 * (row["vertices"] + row["triangles"]):
            raise ValueError("Buffer extent changed")
        vertices = np.frombuffer(raw, "<f4", count=row["vertices"] * 3).reshape(-1, 3)
        faces = np.frombuffer(raw, "<u4", offset=row["vertices"] * 12).reshape(-1, 3)
        if not np.isfinite(vertices).all() or faces.max() >= len(vertices):
            raise ValueError("Invalid geometry buffer")
        if digest(vertices.tobytes()) != record["position_accessor_sha256"]:
            raise ValueError("Source positions changed")
        source_index_hashes = {digest(faces.tobytes())}
        if faces.max() <= 65535:
            source_index_hashes.add(digest(faces.astype("<u2").tobytes()))
        if record["indices_accessor_sha256"] not in source_index_hashes:
            raise ValueError("Source indices changed")
        if (row["name"], row["ontology"]) != (record["source_label"], record["source_ontology_id"]):
            raise ValueError("Source anatomical label changed")
        np.testing.assert_array_equal(vertices.min(axis=0), row["bounds"][0])
        np.testing.assert_array_equal(vertices.max(axis=0), row["bounds"][1])
        edges = np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1)
        _, counts = np.unique(edges, axis=0, return_counts=True)
        boundary = int(np.count_nonzero(counts == 1))
        nonmanifold = int(np.count_nonzero(counts > 2))
        points = vertices[faces].astype(np.float64)
        cross = np.cross(points[:, 1] - points[:, 0], points[:, 2] - points[:, 0])
        degenerate = int(np.count_nonzero(np.all(cross == 0, axis=1)))
        if boundary != record["indexed_boundary_edges"] or nonmanifold != record["indexed_nonmanifold_edges"]:
            raise ValueError("Source boundary topology changed")
        if degenerate != record["zero_area_triangles"]:
            raise ValueError("Source degenerate-face count changed")
        if row["originalBoundaryEdges"] != boundary or row["originalZeroAreaTriangles"] != degenerate:
            raise ValueError("Runtime source-limit metadata changed")
        boundary_edges += boundary
        degenerate_faces += degenerate
        triangles += len(faces)
    if seen != set(expected) or len(seen) != 39 or triangles != 107454:
        raise ValueError("Source primitive inventory incomplete")
    metadata = json.loads((ASSETS / "sources.json").read_bytes())
    if (metadata["retainedIndexedBoundaryEdges"] != boundary_edges
            or metadata["retainedZeroAreaTriangles"] != degenerate_faces
            or metadata["independentAnatomicalReviewComplete"] is not False):
        raise ValueError("Source limit or review status changed")
    return {
        "source_primitives": len(seen),
        "triangles": triangles,
        "retained_boundary_edges": boundary_edges,
        "retained_degenerate_faces": degenerate_faces,
        "source_positions_indices_and_labels_exact": True,
        "independent_anatomical_approval": False,
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
