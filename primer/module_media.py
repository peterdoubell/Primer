"""Spatial companions for the whole Primer.

The manifest is deliberately separate from authored assessment content. Abstract
lessons use explicitly labelled contextual objects; a model is not represented as
an exact depiction of every lesson's concept.
"""

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


@lru_cache(maxsize=1)
def radiology_source_bindings():
    """Match original local figures to their existing investigation/lesson IDs."""
    from . import radiology_catalog
    atlases = radiology_catalog._structure_atlases()
    bindings = {}
    for investigation in radiology_catalog.catalogue()['investigations']:
        if atlases.get(investigation['id']):
            bindings.setdefault(investigation['module_id'], []).append(investigation['id'])
    return {key: tuple(values) for key, values in bindings.items()}


def attach_source_gallery(node):
    """Expose existing source evidence without replacing authored companions."""
    media = node['lesson_media']
    covered = {identifier for item in media if item.get('kind') == 'source-gallery'
               for identifier in item.get('investigation_ids', [])}
    missing = [identifier for identifier in radiology_source_bindings().get(node['id'], ())
               if identifier not in covered]
    if not missing:
        return
    # Every current matching lesson has at most three source readers. Keep the
    # existing bounded gallery schema and include all readers if it grows.
    for start in range(0, len(missing), 4):
        suffix = '' if start == 0 else '-' + str(start // 4 + 1)
        media.append({
            'id': 'module-source-figures-' + node['id'] + suffix,
            'kind': 'source-gallery',
            'title': 'Original source figures',
            'instructions': ('Read the complete source captions and case context. Published imaging, '
                             'drawings, specimens and processed displays retain their separate evidence roles. '
                             'Selected figures do not replace a complete examination or establish every anatomical boundary.'),
            'investigation_ids': missing[start:start + 4],
        })


def attach_module_media(node):
    """Append companions without replacing precise diagrams or existing labs."""
    media = node["lesson_media"]
    if node.get("radiology_reference"):
        attach_source_gallery(node)
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
