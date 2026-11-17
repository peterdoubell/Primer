"""Second pass: bind stored figures to the structures their own descriptions name.

The first pass (bind_stored_caption_assets.py) matched whole requirement names and could not use a
figure whose record states no side for a left or right requirement. On 2026-11-17 the project
owner relaxed that side rule (tools/check_msk_fidelity.side_unstated), and this pass also matches
requirement names that carry filler words or several parts.

A pair is bound only when all of these hold:

1. a sentence of the figure's published caption, or of its stored source note, names the structure;
2. where the figure has selected panels, that sentence is about a selected panel;
3. the fidelity checker finds no modality or side conflict for any investigation sharing the structure;
4. the figure was looked at and is consistent with the sentence.

Side handling for a left or right requirement whose figure record states no side:

- the sentence states this side, or both sides: the figure is bound to that side;
- the sentence states the other side only: not bound;
- the sentence states no side: bound to each side only where the two sides are mirror images.

Requirements that are findings or diagnoses (haematoma, fracture, thrombus and so on) are not bound
here. Coverage is always partial. Nothing here is a clinical approval, and no radiologist has
reviewed the bindings.

This pass also rewrites first-pass quotes that had lost a first letter or were cut mid-word, and
moves one first-pass quote to the sentence about the figure's selected panels.

The evidence file is pinned and unevenly formatted, so each record is edited as literal text and
the edits are recorded for an exact inverse.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
EVIDENCE = ROOT / 'data/radiology/radiology-asset-evidence.json'
CAPTIONS = ROOT / 'data/radiology/radiology-open-images.json'
DOCS = ROOT / 'docs/stored-asset-caption-bindings-pass2-20261117'
REVIEW, RECEIPT = DOCS / 'review.json', DOCS / 'inverse.json'
PUBLISHED_FIELDS = ('source_caption_full', 'original_caption')
NOTE_FIELDS = ('caption', 'alt', 'structures_visible', 'schematic_structures_visible', 'title', 'figure_title')
SIDES = ('caption_states_side', 'side_not_stated', 'record_states_side', 'not_sided')
# A side is stated by the word itself or by a spelled-out chamber abbreviation (LV, LA, RV, RA).
SIDE_WORDS = {'left': r'\bleft\b|\bL[VA]\b', 'right': r'\bright\b|\bR[VA]\b'}
BOTH_WORDS = r'\b(both|bilateral)\b'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def captions():
    found = {}

    def walk(value):
        if isinstance(value, dict):
            if 'id' in value and ('caption' in value or 'alt' in value):
                found[value['id']] = value
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    walk(json.loads(CAPTIONS.read_text()))
    return found


def descriptions(entry):
    """Each stored description field as one line of text."""
    out = {}
    for field in PUBLISHED_FIELDS + NOTE_FIELDS:
        value = entry.get(field)
        if isinstance(value, (list, tuple)):
            value = '; '.join(str(item) for item in value)
        if value:
            out[field] = ' '.join(str(value).split())
    return out


def requirements():
    """Structure id to every requirement that uses it, and to the investigations that hold it."""
    required, holders = {}, {}
    for name in ('msk', 'non-msk'):
        data = json.loads((ROOT / 'data/radiology' / (name + '-structure-requirements.json')).read_text())
        for investigation in data['investigations']:
            for structure in investigation['structures']:
                required.setdefault(structure['id'], []).append(structure)
                holders.setdefault(structure['id'], set()).add(investigation['investigation_id'])
    return required, holders


def basis(row):
    source = 'published caption' if row['field'] in PUBLISHED_FIELDS else 'stored source note'
    if row['side'] == 'side_not_stated':
        return ('The %s of this figure names the structure without a side: “%s” The figure is used for this '
                'side on the assumption that the paired structure is a mirror image. One published figure; '
                'the full extent is not demonstrated.' % (source, row['quote']))
    return ('The %s of this figure names the structure: “%s” One published figure; the full extent is not '
            'demonstrated.' % (source, row['quote']))


def plan():
    """Per asset: the structure ids and coverage entries to add. Every row is checked first."""
    from tools.check_msk_fidelity import inspect_binding, side_unstated
    review = json.loads(REVIEW.read_text())
    assets = {item['id']: item for item in json.loads(EVIDENCE.read_text())['assets']}
    described = captions()
    required, holders = requirements()
    out, seen = {}, set()
    for row in review['accepted']:
        asset, where = assets[row['asset_id']], '%s -> %s' % (row['asset_id'], row['structure_id'])
        if (row['asset_id'], row['structure_id']) in seen:
            raise ValueError('Repeated row: ' + where)
        seen.add((row['asset_id'], row['structure_id']))
        if not holders[row['structure_id']] & set(asset['investigation_ids']):
            raise ValueError('Structure is not in an investigation of the figure: ' + where)
        if descriptions(described[row['asset_id']]).get(row['field'], '').count(row['quote']) < 1 or len(row['quote']) < 12:
            raise ValueError('Quote is not in the stored description: ' + where)
        selected = (asset.get('source_context') or {}).get('selected_panels')
        if selected:
            known = {str(panel).lower() for panel in selected}
            if not row['panels'] or any(str(panel).lower() not in known for panel in row['panels']):
                raise ValueError('Sentence is not about a selected panel: ' + where)
        probe = dict(asset, structure_ids=[row['structure_id']])
        if any(inspect_binding(probe, requirement) for requirement in required[row['structure_id']]):
            raise ValueError('Binding conflict: ' + where)
        sides = {requirement.get('laterality') for requirement in required[row['structure_id']]} & {'left', 'right'}
        assumed = any(side_unstated(probe, requirement) for requirement in required[row['structure_id']])
        if (row['side'] in ('caption_states_side', 'side_not_stated')) != assumed or row['side'] not in SIDES \
                or (row['side'] == 'not_sided') != (not sides):
            raise ValueError('Side label does not fit the requirement and record: ' + where)
        if row['side'] == 'caption_states_side' and not (
                any(re.search(SIDE_WORDS[side], row['quote'], re.I if side in row['quote'].lower() else 0) for side in sides)
                or re.search(BOTH_WORDS, row['quote'], re.I)):
            raise ValueError('Quote does not state the side: ' + where)
        if row['structure_id'] in asset['structure_ids'] or row['structure_id'] in asset['requirement_coverage']:
            raise ValueError('Already bound: ' + where)
        entry = out.setdefault(row['asset_id'], {'structure_ids': [], 'requirement_coverage': {}, 'corrected': {}})
        entry['structure_ids'].append(row['structure_id'])
        entry['requirement_coverage'][row['structure_id']] = {'extent': 'partial', 'basis': basis(row)}
    for (asset_id, structure_id), text in first_pass_corrections(assets, described).items():
        out.setdefault(asset_id, {'structure_ids': [], 'requirement_coverage': {}, 'corrected': {}})['corrected'][structure_id] = text
    return out


def first_pass_corrections(assets, described):
    """First-pass coverage bases whose quote is rewritten whole-word and about a selected panel."""
    from tools.anatomy_sources import bind_stored_caption_assets as first
    out = {}
    for row in json.loads(first.REVIEW.read_text())['accepted']:
        text = first.basis(first.quote(described[row['asset_id']], row['name'], row.get('prefer')))
        if assets[row['asset_id']]['requirement_coverage'][row['structure_id']]['basis'] != text:
            out[(row['asset_id'], row['structure_id'])] = text
    return out


def merged(old, change):
    """An asset's binding fields after this pass."""
    coverage = {key: dict(value, basis=change['corrected'].get(key, value['basis']))
                for key, value in old['requirement_coverage'].items()}
    return {'structure_ids': old['structure_ids'] + change['structure_ids'],
            'requirement_coverage': dict(coverage, **change['requirement_coverage'])}


def value_span(text, start, key):
    """Character span of the JSON value that follows the first occurrence of a key after start."""
    begin = text.index(':', text.index('"%s"' % key, start)) + 1
    while text[begin] in ' \n\t':
        begin += 1
    return begin, json.JSONDecoder().raw_decode(text, begin)[1]


def apply(raw, changes):
    """Extend the binding fields inside each asset's own record. Returns new bytes and the edits made."""
    text, edits = raw.decode('utf-8'), []
    for asset_id, change in changes.items():
        marker = '"id": "%s"' % asset_id
        if text.count(marker) != 1:
            raise ValueError('Asset record not found exactly once: ' + asset_id)
        start = text.index(marker)
        spans = {key: value_span(text, start, key) for key in ('structure_ids', 'requirement_coverage')}
        new = merged({key: json.loads(text[begin:end]) for key, (begin, end) in spans.items()}, change)
        for key, (begin, end) in spans.items():
            value = json.dumps(new[key], ensure_ascii=False)
            if json.loads(text[begin:end]) != new[key]:
                edits.append((begin, text[begin:end], value))
    out, done = text, []
    for begin, old, new in sorted(edits, reverse=True):
        out = out[:begin] + new + out[begin + len(old):]
        done.append([len(text[:begin].encode('utf-8')), old, new])
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
        'path': 'data/radiology/radiology-asset-evidence.json', 'before_sha256': sha(raw), 'after_sha256': sha(after),
        'edits': edits, 'clinical_approval': False, 'extends_historical_approval': False}, indent=1, ensure_ascii=False) + '\n')
    EVIDENCE.write_bytes(after)
    return changes


def before_stored_caption_bindings_pass2(raw):
    """Exact earlier bytes of the evidence file; any other state is returned unchanged."""
    receipt = json.loads(RECEIPT.read_text())
    if sha(raw) != receipt['after_sha256']:
        return raw
    # Offsets are byte positions in the earlier file, so undo from the last edit to the first.
    shift = sum(len(new.encode()) - len(old.encode()) for _, old, new in receipt['edits'])
    for start, old, new in sorted(receipt['edits'], reverse=True):
        shift -= len(new.encode()) - len(old.encode())
        at = start + shift
        if raw[at:at + len(new.encode())] != new.encode():
            raise ValueError('Second-pass caption binding literal changed')
        raw = raw[:at] + old.encode() + raw[at + len(new.encode()):]
    if sha(raw) != receipt['before_sha256']:
        raise ValueError('Second-pass caption binding inverse changed unrelated bytes')
    return raw


if __name__ == '__main__':
    made = bind()
    print(len(made), 'assets;', sum(len(item['structure_ids']) for item in made.values()), 'bindings;',
          sum(len(item['corrected']) for item in made.values()), 'first-pass quotes rewritten')
