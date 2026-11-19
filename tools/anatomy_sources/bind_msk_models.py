"""Bind the stored 3D models of the MSK evidence ledger to the structures and parts their source labels name.

The MSK ledger held 636 models, 12 of them bound. On 2026-11-18 the project owner asked for the 3D models to be bound. An
MSK requirement is usually split into parts (requirements_for): a ligament into its attachments and course, a muscle into
its belly and junctions, a bone into regions, cortex and marrow. A model is bound only when its own source label (a
Z-Anatomy, Malaya MRI or Open Knee(s) object name) names the structure, and the requirement is one of:

- the structure itself, when it has no parts;
- the part that is the structure's own body (review ``body_parts``: its course, midsubstance, muscle belly, tendon
  substance, articular surface or bursal boundaries), which a model of the whole structure shows;
- a part that the label names itself (the superficial part of the tibial collateral ligament, an ulnolunate ligament
  of the triangular fibrocartilage complex, a tendon sheath);
- a small named group or a union, of which the label names one member (the trochanteric bursae).

A whole is never bound to a requirement that names its regions, bundles or components, and a part is never bound to its
whole. The requirement must belong to an investigation that lists the model, or whose 3D view shows it (review
``displays``: the atlas regions each investigation's view loads, checked against each atlas manifest). Where the view
shows the model but the record did not list the investigation, the investigation is added to the record.

Every another-name and kind-of pair is listed with its reason in the review record; removing one makes this tool refuse
its rows. Coverage is always partial. Nothing here is a clinical approval, and no radiologist has reviewed the bindings.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.anatomy_sources import bind_stored_caption_assets_pass2 as second  # noqa: E402
from tools.anatomy_sources import bind_unlocked_figures as unlocked  # noqa: E402

EVIDENCE = ROOT / 'data/radiology/msk-asset-evidence.json'
REQUIREMENTS = ROOT / 'data/radiology/msk-structure-requirements.json'
DOCS = ROOT / 'docs/msk-model-bindings-20261118'
REVIEW, RECEIPT = DOCS / 'review.json', DOCS / 'inverse.json'
BASES = ('structure', 'body_part', 'named_part', 'group_member')
EVIDENCE_KINDS = ('own_word', 'another_name', 'kind_of')
UNSIDED = ('examined_side', 'unspecified', 'midline', 'not_applicable')
# Word forms of the earlier passes, and the MSK spellings of the same words.
SAME_WORD = dict(unlocked.SAME_WORD, fibular='fibularis', peroneal='fibularis', peroneus='fibularis', tendons='tendon', bursae='bursa',
                 ligaments='ligament', fibres='fibre')


def words(text):
    text = re.sub(r'(?<=[a-z])-(?=[a-z])', '', text.lower()).replace('_', ' ')
    return [SAME_WORD.get(word, word) for word in re.findall(r"[a-z][a-z0-9']*", text)]


def requirement_leaves():
    """Each requirement leaf (a part, or a structure without parts) per investigation, and its full name."""
    from tools.check_msk_fidelity import requirements_for
    leaves, names = {}, {}
    for investigation in json.loads(REQUIREMENTS.read_text())['investigations']:
        for requirement in requirements_for(investigation):
            leaves.setdefault(requirement['id'], {})[investigation['investigation_id']] = requirement
        for structure in investigation['structures']:
            names[structure['id']] = structure['name']
            for part in structure.get('required_parts') or []:
                names[part['id']] = structure['name'] + ': ' + part['name']
    return leaves, names


def evidence_fits(row, name, pairs):
    """True when the row's stated evidence really is in its label and in the requirement's full name."""
    if row['evidence'] == 'own_word':
        term = words(row.get('term', ''))
        return bool(term) and any(len(word) > 2 for word in term) and all(
            unlocked.named(word, words(row['quote'])) and unlocked.named(word, words(name)) for word in term)
    if row['evidence'] not in ('another_name', 'kind_of'):
        return False
    pair = row[row['evidence']]
    return (pair in pairs.get(row['evidence'], []) and pair['label_word'].lower() in row['quote'].lower()
            and all(unlocked.named(word, words(name)) for word in words(pair['requirement_word'])))


def region_sides(review):
    """For each atlas region of the review's displays: the part ids it loads and the side it shows."""
    out = {}
    for atlas, path in review['atlases'].items():
        manifest = json.loads((ROOT / path).read_text())
        for region, entry in manifest.get('regions', {}).items():
            out[(atlas, region)] = ({part['id'] if isinstance(part, dict) else part for part in entry['parts']}, entry.get('side'))
    return out


def shown_in(asset_id, investigation, review, regions):
    return [regions[tuple(view)][1] for view in review['displays'].get(investigation, [])
            if tuple(view) in regions and asset_id in regions[tuple(view)][0]]


def basis(row):
    if row['evidence'] == 'own_word':
        what = {'named_part': 'this part', 'group_member': 'one of the structures this requirement groups'}.get(row['leaf_basis'], 'the structure')
        text = 'The source label of this model names %s: “%s”.' % (what, row['quote'])
    elif row['evidence'] == 'another_name':
        pair = row['another_name']
        text = 'The source label of this model names “%s”, another name for this requirement’s “%s”: “%s”.' % (
            pair['label_word'], pair['requirement_word'], row['quote'])
    else:
        pair = row['kind_of']
        text = 'The source label of this model names “%s”, one of this requirement’s “%s”: “%s”.' % (
            pair['label_word'], pair['requirement_word'], row['quote'])
    if row['leaf_basis'] == 'body_part':
        text += ' This part is the structure’s own body or surface, which the whole model shows; the model does not delineate the other parts.'
    text += (' The requirement is for the examined side; the model is a %s-side reference, a mirror image for the other side.'
             % row['model_side'])
    return text + ' One source-labelled model; the full extent and boundaries of the named anatomy are not established.'


def plan():
    """Per asset: investigations, structure ids and coverage entries to add. Every row is checked first."""
    from tools.check_msk_fidelity import inspect_binding
    review = json.loads(REVIEW.read_text())
    assets = {item['id']: item for item in json.loads(EVIDENCE.read_text())['assets']}
    leaves, names = requirement_leaves()
    regions = region_sides(review)
    pairs = {'another_name': review['another_name_pairs'], 'kind_of': review['kind_of_pairs']}
    body_parts = set(review['body_parts'])
    out, seen = {}, set()
    for row in review['accepted']:
        asset, leaf = assets[row['asset_id']], row['structure_id']
        where = '%s -> %s' % (row['asset_id'], leaf)
        if (row['asset_id'], leaf) in seen:
            raise ValueError('Repeated row: ' + where)
        seen.add((row['asset_id'], leaf))
        if asset['kind'] != 'model' or asset.get('structure_ids') or asset.get('requirement_coverage'):
            raise ValueError('Not an unbound model: ' + where)
        if leaf not in leaves or row['name'] != names[leaf] or row['kind'] != 'structure':
            raise ValueError('Row does not name a requirement leaf: ' + where)
        listed = set(asset.get('investigation_ids', []))
        sides = {investigation: shown_in(row['asset_id'], investigation, review, regions) for investigation in leaves[leaf]}
        holding = sorted(investigation for investigation in leaves[leaf] if investigation in listed or sides[investigation])
        if not holding or row['investigations'] != holding or row['added_investigations'] != [i for i in holding if i not in listed]:
            raise ValueError('The requirement is not in an investigation that lists or shows the model: ' + where)
        if len(row['quote']) < 4 or row['quote'] not in asset['name']:
            raise ValueError('Label is not in the model record: ' + where)
        if row['evidence'] not in EVIDENCE_KINDS or not evidence_fits(row, names[leaf], pairs):
            raise ValueError('The label does not name the requirement as recorded: ' + where)
        requirement = leaves[leaf][holding[0]]
        is_part = requirement['parent_id'] != leaf
        part = names[leaf].split(': ', 1)[1].lower() if is_part else None
        if row['leaf_basis'] not in BASES or (row['leaf_basis'] == 'structure' and is_part) \
                or (row['leaf_basis'] == 'body_part' and part not in body_parts) or (row['leaf_basis'] == 'named_part' and not is_part):
            raise ValueError('The leaf is not the kind of requirement recorded: ' + where)
        if any(leaves[leaf][investigation]['laterality'] not in UNSIDED for investigation in holding) or row['side'] != 'examined_side':
            raise ValueError('Side does not fit the requirement: ' + where)
        model_sides = {side for investigation in holding for side in sides[investigation]}
        if model_sides and model_sides != {row['model_side']}:
            raise ValueError('The model side differs from its atlas region: ' + where)
        probe = dict(asset, structure_ids=[leaf], investigation_ids=sorted(listed | set(holding)))
        if any(inspect_binding(probe, leaves[leaf][investigation]) for investigation in holding):
            raise ValueError('Binding conflict: ' + where)
        entry = out.setdefault(row['asset_id'], {'investigation_ids': [], 'structure_ids': [], 'requirement_coverage': {}})
        entry['investigation_ids'] += [i for i in row['added_investigations'] if i not in entry['investigation_ids']]
        entry['structure_ids'].append(leaf)
        entry['requirement_coverage'][leaf] = {'extent': 'partial', 'basis': basis(row)}
    return out


def merged(old, change):
    return {'investigation_ids': old.get('investigation_ids', []) + change['investigation_ids'],
            'structure_ids': old.get('structure_ids', []) + change['structure_ids'],
            'requirement_coverage': dict(old.get('requirement_coverage') or {}, **change['requirement_coverage'])}


def apply(raw, changes):
    """Write the binding fields inside each asset's own record as literal edits. Returns new bytes and the edits made."""
    text, edits = raw.decode('utf-8'), []
    for asset_id, change in changes.items():
        marker = '"id": "%s"' % asset_id
        if text.count(marker) != 1:
            raise ValueError('Asset record not found exactly once: ' + asset_id)
        at = text.index(marker)
        begin = text.rindex('{', 0, at)
        record, end = json.JSONDecoder().raw_decode(text, begin)
        indent = text[text.rindex('\n', 0, at) + 1:at]
        new = merged(record, change)
        anchor = None
        for key in ('investigation_ids', 'structure_ids', 'requirement_coverage'):
            found = text.find('\n%s"%s": ' % (indent, key), begin, end)
            if found < 0:
                if key != 'requirement_coverage' or anchor is None:
                    raise ValueError('Binding field not found in record: ' + asset_id)
                edits.append((anchor, '', ',\n%s"requirement_coverage": %s' % (indent, json.dumps(new[key], ensure_ascii=False))))
                continue
            start = found + len('\n%s"%s": ' % (indent, key))
            value, stop = json.JSONDecoder().raw_decode(text, start)
            if value != new[key]:
                edits.append((start, text[start:stop], json.dumps(new[key], ensure_ascii=False)))
            anchor = stop
    out, done = text, []
    for start, old, new in sorted(edits, reverse=True):
        out = out[:start] + new + out[start + len(old):]
        done.append([len(text[:start].encode('utf-8')), old, new])
    return out.encode('utf-8'), sorted(done)


def bind():
    raw = EVIDENCE.read_bytes()
    changes = plan()
    after, edits = apply(raw, changes)
    for old, new in zip(json.loads(raw)['assets'], json.loads(after)['assets']):
        if new != (dict(old, **merged(old, changes[old['id']])) if old['id'] in changes else old):
            raise ValueError('Unintended change in ' + old['id'])
    if {key: value for key, value in json.loads(raw).items() if key != 'assets'} != \
            {key: value for key, value in json.loads(after).items() if key != 'assets'}:
        raise ValueError('Unintended change outside the asset list')
    RECEIPT.write_text(json.dumps({
        'path': 'data/radiology/msk-asset-evidence.json', 'before_sha256': second.sha(raw),
        'after_sha256': second.sha(after), 'edits': edits, 'clinical_approval': False,
        'extends_historical_approval': False}, indent=1, ensure_ascii=False) + '\n')
    EVIDENCE.write_bytes(after)
    return changes


def before_msk_model_bindings(raw):
    """Exact earlier bytes of the MSK evidence file; any other state is returned unchanged."""
    receipt = json.loads(RECEIPT.read_text())
    if second.sha(raw) != receipt['after_sha256']:
        return raw
    # Offsets are byte positions in the earlier file, so undo from the last edit to the first.
    shift = sum(len(new.encode()) - len(old.encode()) for _, old, new in receipt['edits'])
    for start, old, new in sorted(receipt['edits'], reverse=True):
        shift -= len(new.encode()) - len(old.encode())
        at = start + shift
        if raw[at:at + len(new.encode())] != new.encode():
            raise ValueError('MSK model binding literal changed')
        raw = raw[:at] + old.encode() + raw[at + len(new.encode()):]
    if second.sha(raw) != receipt['before_sha256']:
        raise ValueError('MSK model binding inverse changed unrelated bytes')
    return raw


if __name__ == '__main__':
    made = bind()
    print(len(made), 'models;', sum(len(item['structure_ids']) for item in made.values()), 'bindings;',
          sum(len(item['investigation_ids']) for item in made.values()), 'investigations added')
