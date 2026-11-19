"""Bind the stored 3D models of the radiology ledger to the structures their own source labels name.

Until 2026-11-18, 142 of the 148 models in the radiology evidence ledger had no binding. On 2026-11-18 the project owner
asked for the 3D models to be bound. A model has no caption; what it shows is fixed by its source label: an HRA
ontology label, a BodyParts3D concept name, a TotalSegmentator, NasalSeg or HVSMR-2.0 class, or an OpenEar, WT9FC or
prostate-biopsy structure name. The record's name carries that label. A model is bound to a requirement only when all of
these hold:

1. the label names the structure the requirement names, or one of the structures a combined requirement names
   ("left atrium and venous ostia"). A label that names a whole is never bound to a requirement that names its parts
   (the aorta to the aortic arch), and a part is never bound to its whole;
2. the requirement is in an investigation of the model;
3. the fidelity checker finds no conflict for any investigation sharing the requirement;
4. for a sided requirement, the side is stated by the label or the record and agrees with where the mesh lies, or the
   mesh lies on both sides of the midline, or, for a specimen of unrecorded side, the two sides are mirror images.

"Names" is recorded per row as one of three kinds of evidence:

- own_word: the label and the requirement share the words that name the structure (``term``);
- another_name: the label names the structure by another name or a standard abbreviation of its source's class list;
- kind_of: the label names something that is by definition a kind of what the requirement names (the genioglossus is an
  extrinsic muscle of the tongue).

Every another_name and kind_of pair is listed with its reason in the review record; removing a pair makes this tool
refuse its rows. Where the label states a side, the tool reads the stored mesh and checks that it lies on that side of
the midline, in the axes its source declares (review ``frames``). Coverage is always partial. Nothing here is a
clinical approval, and no radiologist has reviewed the bindings.
"""
import gzip
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.anatomy_sources import bind_finding_figures as findings  # noqa: E402
from tools.anatomy_sources import bind_stored_caption_assets_pass2 as second  # noqa: E402
from tools.anatomy_sources import bind_unlocked_figures as unlocked  # noqa: E402

EVIDENCE = second.EVIDENCE
DOCS = ROOT / 'docs/model-bindings-20261118'
REVIEW, RECEIPT = DOCS / 'review.json', DOCS / 'inverse.json'
SIDES = ('label_states_side', 'record_states_side', 'mesh_spans_both_sides', 'side_not_stated', 'not_sided')
# Sides that the checker sees as unstated by the record (side_unstated): the side rests on the label or the mesh.
SIDE_NOT_IN_RECORD = ('label_states_side', 'mesh_spans_both_sides', 'side_not_stated')
EVIDENCE_KINDS = ('own_word', 'another_name', 'kind_of')
KINDS = ('structure',)
BOTH_WORDS = findings.BOTH_WORDS
# Spelling variants and word forms of the earlier passes, and four adjective forms that model labels and requirements use.
SAME_WORD = dict(unlocked.SAME_WORD, tubal='tube', uterine='uterus', venous='vein', ovarian='ovary')


def words(text):
    return [SAME_WORD.get(word.lower(), word.lower()) for word in re.findall(r"[A-Za-z][A-Za-z0-9']*", text.replace('_', ' '))]


def named(word, other_words):
    return unlocked.named(word, other_words)


def in_label(phrase, quote):
    return re.search(r'(?<![A-Za-z])%s(?![A-Za-z])' % re.escape(phrase), quote, re.I) is not None


def evidence_fits(row, requirements, pairs):
    """True when the row's stated evidence really is in its label and in the requirement."""
    quote, name = row['quote'], requirements[0]['name']
    if row['evidence'] == 'own_word':
        term = words(row.get('term', ''))
        return bool(term) and any(len(word) > 2 for word in term) and all(
            named(word, words(quote)) and named(word, words(name)) for word in term)
    if row['evidence'] not in ('another_name', 'kind_of'):
        return False
    pair = row[row['evidence']]
    return (pair in pairs.get(row['evidence'], []) and in_label(pair['label_word'], quote)
            and all(named(word, words(name)) for word in words(pair['requirement_word'])))


def states_both(row):
    return re.search(BOTH_WORDS, row['quote'], re.I) is not None


def basis(row):
    if row['evidence'] == 'own_word':
        text = 'The source label of this model names the structure: “%s”.' % row['quote']
    elif row['evidence'] == 'another_name':
        pair = row['another_name']
        text = 'The source label of this model names “%s”, another name for this requirement’s “%s”: “%s”.' % (
            pair['label_word'], pair['requirement_word'], row['quote'])
    else:
        pair = row['kind_of']
        text = 'The source label of this model names “%s”, which this requirement covers under “%s”: “%s”.' % (
            pair['label_word'], pair['requirement_word'], row['quote'])
    if row['side'] == 'label_states_side':
        if states_both(row):
            text += ' The label states both sides, and the mesh has separate parts on the left and the right.'
        elif row.get('side_quote'):
            text += ' The source node name states the side: “%s”; the mesh lies on that side.' % row['side_quote']
        else:
            text += ' The label states the side, and the mesh lies on that side.'
    elif row['side'] == 'record_states_side':
        text += ' The model record states the side.'
    elif row['side'] == 'mesh_spans_both_sides':
        text += ' The label states no side; the mesh lies on both sides of the midline, so it is used for each side.'
    elif row['side'] == 'side_not_stated':
        text += (' Neither the label nor the record states a side; the model is used for this side on the assumption that '
                 'the two sides are mirror images.')
    return text + ' One source-labelled model; the full extent and boundaries of the named anatomy are not established.'


def mesh(asset):
    """Vertex positions and triangle indices of a stored model (BP3D transport: header, float32 positions and normals, uint32 indices)."""
    raw = gzip.decompress((ROOT / asset['local_path']).read_bytes())
    magic, count, size = struct.unpack('<4sII', raw[:12])
    if magic != b'BP3D':
        raise ValueError('Not a stored model mesh: ' + asset['id'])
    positions = list(struct.iter_unpack('<3f', raw[12:12 + 12 * count]))
    indices = struct.unpack_from('<%dI' % size, raw, 12 + 24 * count)
    return positions, [indices[at:at + 3] for at in range(0, size, 3)]


def parts(positions, triangles):
    """Mean X of each connected part of a mesh, largest part first."""
    parent = list(range(len(positions)))

    def root(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node
    for a, b, c in triangles:
        parent[root(b)] = root(a)
        parent[root(c)] = root(a)
    groups = {}
    for node in {node for triangle in triangles for node in triangle}:
        groups.setdefault(root(node), []).append(positions[node][0])
    return [sum(xs) / len(xs) for xs in sorted(groups.values(), key=len, reverse=True)]


def side_position(asset_id, frames, assets, cache=None):
    """Where a mesh lies relative to its source's midline, in the source's own axes (positive toward the body's left).

    Returns the frame, the offset of the mesh's mean from the midline, and the shares of its vertices beyond the margin
    on the left and on the right. For a source with no midline structure, returns the left-right spread of its two
    largest connected parts instead."""
    cache = {} if cache is None else cache
    prefix = [key for key in frames if asset_id.startswith(key)]
    if len(prefix) != 1:
        raise ValueError('No side frame for ' + asset_id)
    frame = frames[prefix[0]]

    def load(identifier):
        if identifier not in cache:
            cache[identifier] = mesh(assets[identifier])
        return cache[identifier]
    positions, triangles = load(asset_id)
    sign = 1 if frame['left'] == '+x' else -1
    if not frame['midline']:
        xs = parts(positions, triangles)[:2]
        return frame, None, (abs(xs[0] - xs[1]) if len(xs) == 2 else 0.0)
    middles = [sum(point[0] for point in load(identifier)[0]) / len(load(identifier)[0]) for identifier in frame['midline']]
    midline = sum(middles) / len(middles)
    toward_left = [sign * (point[0] - midline) for point in positions]
    offset = sum(toward_left) / len(toward_left)
    left = sum(value > frame['margin'] for value in toward_left) / len(toward_left)
    right = sum(value < -frame['margin'] for value in toward_left) / len(toward_left)
    return frame, offset, (left, right)


def side_fits_mesh(row, sides, frames, assets, cache=None):
    """A stated or two-sided binding must agree with where the mesh lies."""
    frame, offset, spread = side_position(row['asset_id'], frames, assets, cache)
    both = row['side'] == 'mesh_spans_both_sides' or states_both(row)
    if offset is None:
        return both and spread >= frame['margin']
    if both:
        return min(spread) >= 0.15
    (side,) = sides
    return offset > frame['margin'] if side == 'left' else offset < -frame['margin']


def plan():
    """Per asset: the structure ids and coverage entries to add. Every row is checked first."""
    from tools.check_msk_fidelity import inspect_binding, side_unstated
    review = json.loads(REVIEW.read_text())
    assets = {item['id']: item for item in json.loads(EVIDENCE.read_text())['assets']}
    required, holders = second.requirements()
    pairs = {'another_name': review['another_name_pairs'], 'kind_of': review['kind_of_pairs']}
    out, seen, cache = {}, set(), {}
    for row in review['accepted']:
        asset, where = assets[row['asset_id']], '%s -> %s' % (row['asset_id'], row['structure_id'])
        if (row['asset_id'], row['structure_id']) in seen:
            raise ValueError('Repeated row: ' + where)
        seen.add((row['asset_id'], row['structure_id']))
        if asset['kind'] != 'model':
            raise ValueError('Not a model: ' + where)
        if not holders[row['structure_id']] & set(asset['investigation_ids']):
            raise ValueError('Requirement is not in an investigation of the model: ' + where)
        if row['name'] != required[row['structure_id']][0]['name'] or row['kind'] not in KINDS:
            raise ValueError('Row does not name its requirement: ' + where)
        if len(row['quote']) < 2 or row['quote'] not in asset['name'] or row.get('side_quote', row['quote']) not in asset['name']:
            raise ValueError('Label is not in the model record: ' + where)
        probe = dict(asset, structure_ids=[row['structure_id']])
        if any(inspect_binding(probe, requirement) for requirement in required[row['structure_id']]):
            raise ValueError('Binding conflict: ' + where)
        if row['evidence'] not in EVIDENCE_KINDS or not evidence_fits(row, required[row['structure_id']], pairs):
            raise ValueError('The label does not name the requirement as recorded: ' + where)
        sides = {requirement.get('laterality') for requirement in required[row['structure_id']]} & {'left', 'right'}
        assumed = any(side_unstated(probe, requirement) for requirement in required[row['structure_id']])
        if row['side'] not in SIDES or (row['side'] in SIDE_NOT_IN_RECORD) != assumed or (row['side'] == 'not_sided') != (not sides):
            raise ValueError('Side label does not fit the requirement and record: ' + where)
        stated = (row['quote'] + ' ' + row.get('side_quote', '')).replace('_', ' ')
        if row['side'] == 'label_states_side' and not (
                any(re.search(second.SIDE_WORDS[side], stated, re.I if side in stated.lower() else 0) for side in sides)
                or re.search(BOTH_WORDS, stated, re.I)):
            raise ValueError('Label does not state the side: ' + where)
        if row['side'] == 'record_states_side' and (asset.get('source_context') or {}).get('laterality') not in sides:
            raise ValueError('Record does not state the side: ' + where)
        if ('side_quote' in row) and row['side'] != 'label_states_side':
            raise ValueError('A side quote is recorded for a binding whose label states no side: ' + where)
        if row['side'] in ('label_states_side', 'mesh_spans_both_sides') and not side_fits_mesh(row, sides, review['frames'], assets, cache):
            raise ValueError('The mesh does not lie on the stated side: ' + where)
        if row['structure_id'] in asset['structure_ids'] or row['structure_id'] in asset['requirement_coverage']:
            raise ValueError('Already bound: ' + where)
        entry = out.setdefault(row['asset_id'], {'structure_ids': [], 'requirement_coverage': {}, 'corrected': {}})
        entry['structure_ids'].append(row['structure_id'])
        entry['requirement_coverage'][row['structure_id']] = {'extent': 'partial', 'basis': basis(row)}
    return out


def bind():
    raw = EVIDENCE.read_bytes()
    changes = plan()
    after, edits = second.apply(raw, changes)
    for old, new in zip(json.loads(raw)['assets'], json.loads(after)['assets']):
        if new != (dict(old, **second.merged(old, changes[old['id']])) if old['id'] in changes else old):
            raise ValueError('Unintended change in ' + old['id'])
    if {key: value for key, value in json.loads(raw).items() if key != 'assets'} != \
            {key: value for key, value in json.loads(after).items() if key != 'assets'}:
        raise ValueError('Unintended change outside the asset list')
    RECEIPT.write_text(json.dumps({
        'path': 'data/radiology/radiology-asset-evidence.json', 'before_sha256': second.sha(raw),
        'after_sha256': second.sha(after), 'edits': edits, 'clinical_approval': False,
        'extends_historical_approval': False}, indent=1, ensure_ascii=False) + '\n')
    EVIDENCE.write_bytes(after)
    return changes


def before_model_bindings(raw):
    """Exact earlier bytes of the evidence file; any other state is returned unchanged."""
    receipt = json.loads(RECEIPT.read_text())
    if second.sha(raw) != receipt['after_sha256']:
        return raw
    # Offsets are byte positions in the earlier file, so undo from the last edit to the first.
    shift = sum(len(new.encode()) - len(old.encode()) for _, old, new in receipt['edits'])
    for start, old, new in sorted(receipt['edits'], reverse=True):
        shift -= len(new.encode()) - len(old.encode())
        at = start + shift
        if raw[at:at + len(new.encode())] != new.encode():
            raise ValueError('Model binding literal changed')
        raw = raw[:at] + old.encode() + raw[at + len(new.encode()):]
    if second.sha(raw) != receipt['before_sha256']:
        raise ValueError('Model binding inverse changed unrelated bytes')
    return raw


if __name__ == '__main__':
    made = bind()
    print(len(made), 'models;', sum(len(item['structure_ids']) for item in made.values()), 'bindings')
