"""Curated photographic context and spatial companions for the whole Primer.

The manifests are deliberately separate from authored assessment content. Images
are shared within a field; abstract lessons use explicitly labelled contextual
objects. Neither is represented as an exact depiction of every lesson's concept.
"""

import copy
import json
from functools import lru_cache
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "data"


@lru_cache(maxsize=1)
def model_bindings():
    with (DATA / "module-models.json").open() as source:
        manifest = json.load(source)
    records = manifest["models"]
    bindings = {record["node_id"]: record for record in records}
    if len(bindings) != len(records):
        raise ValueError("Repeated module 3D binding")
    return bindings


@lru_cache(maxsize=1)
def photographs():
    with (DATA / "module-photographs.json").open() as source:
        return json.load(source)["domains"]


def model_props(node):
    record = model_bindings().get(node.get("id"))
    if not record or not isinstance(node.get("title"), str) or not node["title"].strip():
        return None
    return {
        "scenario": "module." + node["id"],
        "family": record["family"],
        "context": record["context"],
        "mode": record["mode"],
        "lesson": node["title"],
    }


def attach_module_media(node):
    """Append companions without replacing precise diagrams or existing labs."""
    media = node["lesson_media"]
    catalog = photographs()
    candidates = catalog.get(node["domain"])
    if not candidates:
        raise ValueError("Missing photograph for field " + node["domain"])
    if isinstance(candidates, dict):
        candidates = [candidates]
    # Introductory and advanced contexts are shared intentionally, rather than
    # silently inventing a photograph for an abstract or unobservable concept.
    advanced_context = node["stage"] >= 3
    if node.get("radiology_reference"):
        # The reference loader normalizes every radiology module to stage 5;
        # its Foundations section is the introductory equipment context.
        advanced_context = node.get("section") != "Foundations"
    photo = copy.deepcopy(candidates[min(int(advanced_context), len(candidates) - 1)])
    if not any(item.get("kind") == "photograph" for item in media):
        media.append(photo)

    if node.get("radiology_reference"):
        reference = node["radiology_reference"]["spatial_model"]
        media.append({
            "id": "module-anatomy-" + node["id"],
            "kind": "model", "renderer": "radiology-anatomy",
            "title": reference["title"],
            "instructions": reference["instructions"],
            "props": {"node_id": node["id"], "family": reference["family"]},
        })
    elif not any(item.get("renderer") == "spatial-3d" for item in media):
        record = model_bindings().get(node["id"])
        if not record:
            raise ValueError("Missing module 3D binding: " + node["id"])
        media.append({
            "id": "module-object-" + node["id"],
            "kind": "model", "renderer": "spatial-3d",
            "title": record["title"], "instructions": record["instructions"],
            "props": model_props(node),
        })
