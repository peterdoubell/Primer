"""Verify every delivered vertex and source triangle using Blender world transforms.

Run inside Blender on the pinned scene, from this checkout's root:
blender --background --factory-startup --disable-autoexec Startup.blend \
    --python-exit-code 1 --python tools/anatomy_sources/verify_zanatomy_salivary.py -- web/anatomy/zanatomy-salivary

Only this checkout's canonical package is accepted. For scratch reproduction,
use an isolated checkout and run its copy of this tool (see the source README).
"""
import gzip
import hashlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.anatomy_sources.salivary_package_paths import package_directory, package_member


def verify(output):
    package_directory(output)
    source = json.loads(package_member("source.json").read_text())
    assert hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest() == source["sceneSHA256"]
    rows = json.loads(package_member("surfaces.json").read_text())
    assert len(rows) == 18 and len(set(row["sourceObject"] for row in rows)) == len(rows)
    deps = bpy.context.evaluated_depsgraph_get()
    triangle_total, vertex_total, maximum_error = 0, 0, 0
    for row in rows:
        packed = package_member(row["file"]).read_bytes()
        assert hashlib.sha256(packed).hexdigest() == row["packedSHA256"]
        raw = gzip.decompress(packed)
        assert hashlib.sha256(raw).hexdigest() == row["sha256"]
        assert len(raw) == 12 * (row["vertices"] + row["triangles"])
        vertices = np.frombuffer(raw, dtype="<f4", count=row["vertices"] * 3).reshape(-1, 3)
        faces = np.frombuffer(raw, dtype="<u4", offset=vertices.nbytes).reshape(-1, 3)
        obj = bpy.data.objects[row["sourceObject"]].evaluated_get(deps)
        mesh = obj.to_mesh()
        try:
            mesh.calc_loop_triangles()
            assert len(vertices) == len(mesh.vertices) and len(faces) == len(mesh.loop_triangles)
            # Blender's native matrix-vector product is single precision. The packaged coordinates
            # are rounded to float32 after a double-precision transform and conversion to mm.
            expected = np.array([list(obj.matrix_world @ v.co) for v in mesh.vertices]) * 1000
            error = float(np.max(np.abs(vertices - expected)))
            assert error < .0004
            winding = (0, 2, 1) if obj.matrix_world.to_3x3().determinant() < 0 else (0, 1, 2)
            assert np.array_equal(faces, np.array([list(t.vertices) for t in mesh.loop_triangles])[:, winding])
            assert np.array_equal(vertices.min(axis=0), row["bounds"][0])
            assert np.array_equal(vertices.max(axis=0), row["bounds"][1])
            # The paired objects carry source side labels and agree with the scene's midline.
            if row["side"] == "left":
                assert vertices[:, 0].min() >= 0
            if row["side"] == "right":
                assert vertices[:, 0].max() <= 0
            maximum_error = max(maximum_error, error)
            vertex_total += len(vertices)
            triangle_total += len(faces)
        finally:
            obj.to_mesh_clear()
    print(json.dumps({"objects": len(rows), "vertices": vertex_total, "triangles": triangle_total,
                      "max_native_coordinate_error_mm": maximum_error}))


if __name__ == "__main__":
    verify(Path(sys.argv[sys.argv.index("--") + 1]))
