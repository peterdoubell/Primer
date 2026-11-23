"""Export the published salivary scene through Blender's evaluated mesh API.

Run from the checkout root:
blender --background --factory-startup --disable-autoexec Startup.blend \
    --python-exit-code 1 --python tools/anatomy_sources/export_zanatomy_salivary.py -- web/anatomy/zanatomy-salivary

Only this checkout's canonical package is accepted. For scratch reproduction,
use an isolated checkout and run its copy of this tool (see the source README).
"""
import gzip
import hashlib
import io
import json
import re
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.anatomy_sources.salivary_package_paths import package_directory, package_member


SCENE_SHA = "9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd"
ARCHIVE_REV = "ded1a55381328f3f242426f0e8e711c5fca62c14"
PAIRS = (
    ("Parotid gland", "gland", (235, 168, 105)),
    ("Submandibular gland", "gland", (117, 194, 171)),
    ("Sublingual gland", "gland", (157, 157, 226)),
    ("Parotid duct", "duct", (255, 219, 139)),
    ("Submandibular duct", "duct", (176, 238, 204)),
    ("Mylohyoid muscle", "landmark", (200, 112, 100)),
    ("Superficial part of masseter", "landmark", (189, 104, 124)),
    ("Deep part of masseter", "landmark", (164, 111, 133)),
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def export(output):
    output = package_directory(output)
    scene = bpy.context.scene
    if sha(Path(bpy.data.filepath).read_bytes()) != SCENE_SHA or scene.unit_settings.system != "METRIC":
        raise ValueError("Unexpected Z-Anatomy source file or unit system")
    millimetres = scene.unit_settings.scale_length * 1000
    objects = [(name + suffix, side, kind, color) for name, kind, color in PAIRS
               for side, suffix in (("left", ".l"), ("right", ".r"))]
    objects += [(name, None, "landmark", (221, 211, 181)) for name in ("Mandible", "Hyoid bone")]
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    deps = bpy.context.evaluated_depsgraph_get()
    for source_name, side, kind, color in objects:
        obj = bpy.data.objects[source_name]
        evaluated = obj.evaluated_get(deps)
        mesh = evaluated.to_mesh()
        try:
            mesh.calc_loop_triangles()
            vertices = np.empty(3 * len(mesh.vertices), dtype=np.float32)
            mesh.vertices.foreach_get("co", vertices)
            matrix = np.asarray(evaluated.matrix_world, dtype=np.float64)
            world = np.einsum("vi,ji->vj", vertices.reshape(-1, 3), matrix[:3, :3]) + matrix[:3, 3]
            positions = np.ascontiguousarray(world * millimetres, dtype="<f4")
            indices = np.empty(3 * len(mesh.loop_triangles), dtype="<i4")
            mesh.loop_triangles.foreach_get("vertices", indices)
            faces = indices.reshape(-1, 3)
            reversed_winding = bool(np.linalg.det(matrix[:3, :3]) < 0)
            if reversed_winding:
                faces = faces[:, [0, 2, 1]]
            triangles = np.ascontiguousarray(faces, dtype="<u4")
            if not positions.size or not triangles.size or not np.isfinite(positions).all() or triangles.max() >= len(positions):
                raise ValueError("Invalid source geometry for " + source_name)
            packed = io.BytesIO()
            raw = positions.tobytes() + triangles.tobytes()
            with gzip.GzipFile(fileobj=packed, mode="wb", compresslevel=9, mtime=0) as stream:
                stream.write(raw)
            base = source_name.rsplit(".", 1)[0] if side else source_name
            label = ((side + "-") if side else "") + base.lower().replace(" ", "-")
            filename = label + ".mesh.gz"
            package_member(filename).write_bytes(packed.getvalue())
            rows.append({
                "label": label, "name": (side.title() + " " + base.lower()) if side else base,
                "side": side, "group": kind, "sourceObject": source_name, "sourceData": obj.data.name,
                "sourceType": obj.type, "worldMatrix": matrix.tolist(), "handednessReversed": reversed_winding,
                "sourceModifiers": [m.type for m in obj.modifiers], "file": filename,
                "vertices": len(positions), "triangles": len(triangles), "color": color,
                "bounds": [positions.min(axis=0).tolist(), positions.max(axis=0).tolist()],
                "sha256": sha(raw), "packedSHA256": sha(packed.getvalue()),
            })
        finally:
            evaluated.to_mesh_clear()
    package_member("surfaces.json").write_text(json.dumps(rows, indent=2) + "\n")
    provenance = {"source": "Z-Anatomy, Models of human anatomy", "revision": ARCHIVE_REV,
                  "sourceURL": f"https://github.com/Z-Anatomy/Models-of-human-anatomy/tree/{ARCHIVE_REV}",
                  "sceneSHA256": SCENE_SHA, "archiveSHA256": "e029688545627bd0214b269e1063143abb580aad72b2c2445d6d8a9a0d9da736",
                  "blenderVersion": bpy.app.version_string, "worldUnitToMillimetres": millimetres,
                  "license": "CC BY-SA 4.0", "baselineCredit": "BodyParts3D © Database Center for Life Science, CC BY-SA 2.1 Japan",
                  "scope": "Atlas gross gland bodies, author-modelled ducts, muscles and bony landmarks. The left/right objects share geometry in this authored atlas. No same-person registration to the thyroid sweeps or published salivary ultrasound panels."}
    package_member("source.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n")
    page = package_member("index.html")
    if page.is_file():
        text, count = re.subn(r'data-surfaces-sha256="[0-9a-f]{64}"',
                              'data-surfaces-sha256="' + sha(package_member("surfaces.json").read_bytes()) + '"',
                              page.read_text())
        if count != 1 or re.findall(r'class="layer" type="checkbox" value="([^"]+)"', text) != [r["label"] for r in rows]:
            raise ValueError("Reader layer order differs from the source objects")
        page.write_text(text)
        members = {"index.html", "view.css", "controls.js", "planes.mjs", "LICENSE.txt", "surfaces.json", "source.json"}
        files = {}
        for name in sorted(members | {r["file"] for r in rows}):
            content = package_member(name).read_bytes()
            files[name] = {"bytes": len(content), "sha256": sha(content)}
        package_member("delivery.json").write_text(json.dumps({"files": files}, indent=2) + "\n")
    print("Exported", len(rows), "scene objects and", sum(row["triangles"] for row in rows), "triangles")


if __name__ == "__main__":
    export(Path(sys.argv[sys.argv.index("--") + 1]))
