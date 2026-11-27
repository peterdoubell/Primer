"""Record the common hepatic duct part of BodyParts3D 4.3 object FJ3079 and bind it to the requirement its label names.

On 2026-11-24 the biliary reader began to show source object FJ3079 in two parts, divided where the cystic duct meets it
(docs/bp3d-biliary-duct-partition-20261124). The project owner then asked for the two duct parts to be bound.

This pass applies the rules of the body-reader pass (tools/anatomy_sources/bind_body_reader_models.py) unchanged:

- The upper part binds. The source's own label for the object, "Common hepatic duct", fits this part, and one requirement of an
  investigation that shows the reader names the common hepatic duct as a part of its own.
- The lower part does not bind. The source's label does not name it, and every requirement of the two investigations that names
  the common bile duct asks for a segment of it, its lumen, its wall or a margin. A whole is not bound to its parts, and a
  BodyParts3D surface shows neither lumen nor wall alone. The review lists it with that reason.

Coverage is partial. Nothing here is a clinical approval: no radiologist has reviewed the division or the binding.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.anatomy_sources import bind_body_reader_models as body  # noqa: E402
from tools.anatomy_sources import bind_stored_caption_assets_pass2 as second  # noqa: E402

EVIDENCE = body.EVIDENCE
DOCS = ROOT / 'docs/biliary-duct-part-binding-20261124'
REVIEW, RECEIPT = DOCS / 'review.json', DOCS / 'inverse.json'
PARTITION = 'docs/bp3d-biliary-duct-partition-20261124/review.json'
PART = 'bp3d-biliary-4.3/FJ3079-common-hepatic.mesh.gz'
DIVISION = (' The mesh is the part of source object FJ3079 above the cystic duct junction. This project divided the object there on '
            '2026-11-24, to within about 3 mm, without changing a triangle (%s). The source’s label does not fit the part below the '
            'junction, which is not bound. No radiologist has reviewed the division.' % PARTITION)


def plan():
    """The new record, checked by the body-reader pass's own rules against this pass's review."""
    from tools.check_msk_fidelity import inspect_binding, inspect_requirement_coverage
    review = json.loads(REVIEW.read_text())
    if [row['mesh'] for row in review['accepted']] != [PART]:
        raise ValueError('This pass binds one mesh')
    saved = body.REVIEW
    body.REVIEW = REVIEW
    try:
        records = body.plan()
    finally:
        body.REVIEW = saved
    item, = records
    partition = json.loads((ROOT / PARTITION).read_text())
    part = partition['parts']['above']
    if item['local_path'] != 'web/anatomy/bp3d-biliary-4.3/' + part['file'] or item['sha256'] != part['delivered_file_sha256']:
        raise ValueError('The mesh is not the recorded upper part')
    item['geometry']['source_object_part'] = dict(
        object='FJ3079', part='above the cystic duct junction', source_object_sha256=partition['source']['mesh_sha256'],
        division_record=PARTITION, division_tolerance_mm=partition['tolerance_mm'], triangles_of_source_object=partition['source']['triangles'])
    for coverage in item['requirement_coverage'].values():
        coverage['basis'] += DIVISION
    leaves = body.requirement_leaves()[0]
    for row in review['accepted']:
        for investigation in row['investigations']:
            requirement = leaves[row['structure_id']][investigation]
            if inspect_binding(item, requirement) != [] or inspect_requirement_coverage(item, requirement) != ['requirement_coverage_partial']:
                raise ValueError('The checker refuses the binding')
    return [item]


def bind():
    raw = EVIDENCE.read_bytes()
    records = plan()
    after, edits = body.apply(raw, records)
    old, new = json.loads(raw), json.loads(after)
    if new['assets'] != old['assets'] + records or {k: v for k, v in old.items() if k != 'assets'} != {k: v for k, v in new.items() if k != 'assets'}:
        raise ValueError('Unintended change to the evidence file')
    RECEIPT.write_text(json.dumps({
        'path': 'data/radiology/radiology-asset-evidence.json', 'before_sha256': second.sha(raw), 'after_sha256': second.sha(after),
        'edits': edits, 'clinical_approval': False, 'extends_historical_approval': False}, indent=1, ensure_ascii=False) + '\n')
    EVIDENCE.write_bytes(after)
    return records


def before_biliary_duct_part_record(raw):
    """Exact earlier bytes of the evidence file; any other state is returned unchanged."""
    from tools.acute_abdomen_panels_compatibility import before_acute_panel_evidence
    raw = before_acute_panel_evidence(raw)
    receipt = json.loads(RECEIPT.read_text())
    if second.sha(raw) != receipt['after_sha256']:
        return raw
    shift = sum(len(new.encode()) - len(old.encode()) for _, old, new in receipt['edits'])
    for start, old, new in sorted(receipt['edits'], reverse=True):
        shift -= len(new.encode()) - len(old.encode())
        at = start + shift
        if raw[at:at + len(new.encode())] != new.encode():
            raise ValueError('Biliary duct part record literal changed')
        raw = raw[:at] + old.encode() + raw[at + len(new.encode()):]
    if second.sha(raw) != receipt['before_sha256']:
        raise ValueError('Biliary duct part record inverse changed unrelated bytes')
    return raw


if __name__ == '__main__':
    made = bind()
    print(len(made), 'record;', sum(len(item['structure_ids']) for item in made), 'binding')
