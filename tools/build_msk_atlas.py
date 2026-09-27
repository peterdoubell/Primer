#!/usr/bin/env python3
"""Package inspected Z-Anatomy exports without changing native geometry.

Consumes the staging manifest produced by anatomy_sources/stage_z_anatomy.py.
All transforms are already evaluated in the source coordinate frame. Surface
material regions remain surfaces; this never manufactures cartilage thickness.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import struct

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "web/anatomy/msk-atlas"
COLORS = {"bone": "#dfd1b0", "ligament": "#d6c89a", "muscle": "#b77075",
          "nerve": "#f0c45e", "tendon": "#e5dac7", "capsule": "#98b8c5",
          "bursa": "#7aabb9", "labrum": "#72b8bd", "meniscus": "#91bbc7",
          "fat": "#e5c46c", "fibrocartilage": "#9abcd0", "tendon-sheath": "#b5c2b1", "fascia": "#c0bdab",
          "cartilage-surface": "#80c4cf", "tendon-surface": "#ece1c7"}
LABELS = {"bone": "Bones", "ligament": "Ligaments", "muscle": "Muscles", "nerve": "Nerves",
          "tendon": "Tendons", "capsule": "Capsules", "bursa": "Bursae", "labrum": "Labrum",
          "meniscus": "Menisci", "cartilage-surface": "Cartilage surfaces",
          "fat": "Fat pads", "fibrocartilage": "Articular discs", "tendon-sheath": "Tendon sheaths", "fascia": "Fascia",
          "tendon-surface": "Tendon surfaces"}


def copy_mesh(record, identifier, source_root):
    path = Path(record["file"]).resolve()
    if not path.is_relative_to(source_root.resolve()):
        raise ValueError("Staged mesh leaves its source directory")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != record["sha256"]:
        raise ValueError("Staged mesh fingerprint changed: " + identifier)
    magic, vertices, indices = struct.unpack("<4sII", data[:12])
    if magic != b"BP3D" or len(data) != 12 + vertices * 24 + indices * 4 or indices % 3:
        raise ValueError("Invalid staged geometry: " + identifier)
    target = DEST / (identifier + ".bin")
    target.write_bytes(data)
    return {"file": "/app/anatomy/msk-atlas/" + target.name,
            "vertices": vertices, "triangles": indices // 3, "bytes": len(data)}


def build(staged):
    source = json.loads((staged / "manifest.json").read_text())
    coordinates = source["coordinate_system"]
    if (coordinates["units"], coordinates["x_positive"], coordinates["y_positive"], coordinates["z_positive"]) != (
            "centimeters", "patient left", "superior", "anterior"):
        raise ValueError("Unreviewed coordinate frame; do not guess registration")
    DEST.mkdir(parents=True, exist_ok=True)
    parts = {}
    surfaces = {}
    for identifier, original in source["parts"].items():
        part = copy.deepcopy(original)
        part.update(copy_mesh(original, identifier, staged))
        part["color"] = COLORS[part["layer"]]
        part["fidelity_review"] = "pending"
        # Absolute staging locations are build inputs, never runtime URLs.
        material_groups = part.pop("material_submeshes", [])
        parts[identifier] = part
        surfaces[identifier] = []
        for group in material_groups:
            material = group["name"].split(".")[0].lower()
            if material not in ("cartilage", "tendon"):
                continue
            sid = identifier + "-material-" + str(group["material_index"])
            layer = material + "-surface"
            surface = {"id": sid, "name": original["name"].removesuffix(".r") + " · " + material + " surface",
                       "layer": layer, "color": COLORS[layer], "surface_overlay": True,
                       "sha256": group["sha256"], "source_part_id": identifier,
                       "source_material": group["name"], "source_model_id": original["source_model_id"],
                       "source_geometry_id": original["source_geometry_id"],
                       "source_sha256": original["source_sha256"], "source_file": original["source_file"],
                       "bounds": group["bounds"], "regions": original["regions"],
                       "fidelity_review": "pending", "license": source["license"],
                       "limitations": "Source-assigned outer surface only; tissue thickness, defects and internal architecture are not represented."}
            surface.update(copy_mesh(group, sid, staged))
            parts[sid] = surface
            surfaces[identifier].append(sid)
    regions = {}
    for key, region in source["regions"].items():
        identifiers = [entry for identifier in region["parts"] for entry in [identifier, *surfaces[identifier]]]
        low, high = region["focus_bounds"]
        margin = {"shoulder": 10, "elbow": 10, "wrist": 9, "hip": 10, "knee": 9, "ankle": 10}[key]
        layers = {parts[identifier]["layer"] for identifier in identifiers}
        regions[key] = {"title": region["title"], "side": region["side"],
                        "parts": [{"id": identifier, "layer": parts[identifier]["layer"]} for identifier in identifiers],
                        "layers": [[layer, LABELS[layer]] for layer in LABELS if layer in layers],
                        "source_up_range": [low[1] - margin, high[1] + margin],
                        "focus_bounds": region["focus_bounds"],
                        "focus_bounds_source_objects": region["focus_bounds_source_objects"]}
    manifest = {k: copy.deepcopy(v) for k, v in source.items()
                if k not in ("parts", "regions", "source_license_file")}
    manifest["coordinate_system"]["display_basis"] = "native-x-left-y-superior-z-anterior"
    manifest.update({"parts": parts, "regions": regions,
                     "status": "Expanded adult reference anatomy; clinical fidelity review incomplete",
                     "source_url": "https://github.com/LluisV/Z-Anatomy/tree/" + source["source_commit"],
                     "viewer_notes": [
                         "Adult right-sided reference anatomy. Bone, joint, muscle and nerve surfaces retain their shared source coordinates; no fitting to a different atlas was performed.",
                         "Region view crops long structures for orientation. Full structures removes the crop; Isolate shows the complete selected source object.",
                         "Cartilage and tendon surface layers are the source artist's material regions, not tissue volumes. They cannot establish thickness or grade a tear. Some small ligament meshes are coarse; this atlas is not yet a complete clinically validated representation of every reporting structure.",
                         "BodyParts3D, The Database Center for Life Science (source lineage); Z-Anatomy contributors. Adapted meshes and surface regions are distributed under CC BY-SA 4.0."
                     ]})
    (DEST / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    shutil.copyfile(source["source_license_file"], DEST / "SOURCE-LICENSE.txt")
    attribution = "# Z-Anatomy MSK reference surfaces\n\n" + "\n\n".join(manifest["viewer_notes"]) + "\n\n"
    attribution += "Source commit: `" + source["source_commit"] + "`.\n\n"
    attribution += "Source: " + manifest["source_url"] + "\n\nLicense: " + source["license_url"] + "\n\n"
    attribution += source["adaptations"] + "\n\nThe manifest retains source model/geometry IDs, transforms, original-file hashes and derived-file hashes. No clinical approval is implied by source attribution.\n"
    (DEST / "ATTRIBUTION.md").write_text(attribution)
    print("Packaged", len(parts), "source parts/surface regions in", len(regions), "registered regions")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged", type=Path, required=True)
    build(parser.parse_args().staged.resolve())
