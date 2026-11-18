"""Bind stored, openly licensed figures to the structures their own published captions name.

These figures were already in the repository with verified licences but bound to nothing. A pair is
bound only when (1) the stored caption or structure note of the figure names the structure, (2) the
figure was looked at and is consistent with that, and (3) the fidelity checker finds no modality or
side conflict for any investigation that shares the structure. Coverage is always partial. Nothing
here is a clinical approval, and no radiologist has reviewed the bindings.

The evidence file is pinned and unevenly formatted, so each record is edited as literal text and the
edits are recorded for an exact inverse.
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
DOCS = ROOT / 'docs/stored-asset-caption-bindings-20261117'
REVIEW, RECEIPT = DOCS / 'review.json', DOCS / 'inverse.json'
PASS2_REVIEW = ROOT / 'docs/stored-asset-caption-bindings-pass2-20261117/review.json'
FINDINGS_REVIEW = ROOT / 'docs/finding-figure-bindings-20261118/review.json'
EMPTY_IDS = re.compile(rb'"structure_ids":\s*\[\s*\]')
EMPTY_COVERAGE = re.compile(rb'"requirement_coverage":\s*\{\s*\}')


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


def quote(entry, name, prefer=None):
    """The sentence of the stored description that names the structure.

    A long sentence is cut to whole words around the name. `prefer` picks the sentence containing
    that text when several name the structure, for example the one about a selected panel.

    The pass merged on 2026-11-17 dropped the first letter of a quote that began its description
    and cut long sentences mid-word. The second pass rewrote those quotes in the evidence file.
    """
    key = re.sub(r'^(right|left)\s+', '', name, flags=re.I)
    for field in ('caption', 'source_caption_full', 'alt', 'structures_visible', 'title'):
        text = ' '.join(str(entry.get(field, '')).split())
        for match in re.finditer(re.escape(key), text, re.I):
            start = text.rfind('. ', 0, match.start())
            start = 0 if start == -1 else start + 2
            end = text.find('. ', match.end())
            end = len(text) if end == -1 else end + 1
            if prefer and prefer not in text[start:end]:
                continue
            if match.start() - start > 160:
                start = text.index(' ', match.start() - 160) + 1
            if end - match.end() > 160:
                end = text.rindex(' ', 0, match.end() + 160)
            return text[start:end].strip()
    return None


def basis(said):
    return ('The stored published description of this figure names the structure: “%s” '
            'One published figure; the full extent is not demonstrated.' % said)


def plan():
    """Per asset: the structure ids and coverage entries to write."""
    from tools.check_msk_fidelity import inspect_binding
    review = json.loads(REVIEW.read_text())
    assets = {item['id']: item for item in json.loads(EVIDENCE.read_text())['assets']}
    described = captions()
    required = {}
    for name in ('msk', 'non-msk'):
        data = json.loads((ROOT / 'data/radiology' / (name + '-structure-requirements.json')).read_text())
        for investigation in data['investigations']:
            for structure in investigation['structures']:
                required.setdefault(structure['id'], []).append(structure)
    out = {}
    for row in review['accepted']:
        asset = assets[row['asset_id']]
        said = quote(described[row['asset_id']], row['name'], row.get('prefer'))
        if not said:
            raise ValueError('No stored caption names %s for %s' % (row['name'], row['asset_id']))
        probe = dict(asset, structure_ids=[row['structure_id']])
        if any(inspect_binding(probe, requirement) for requirement in required[row['structure_id']]):
            raise ValueError('Binding conflict for %s' % row['asset_id'])
        entry = out.setdefault(row['asset_id'], {'structure_ids': [], 'requirement_coverage': {}})
        entry['structure_ids'].append(row['structure_id'])
        entry['requirement_coverage'][row['structure_id']] = {'extent': 'partial', 'basis': basis(said)}
    return out


def only_caption_bindings(asset):
    """True when an asset carries no bindings, or exactly the reviewed caption bindings of the three passes, all partial."""
    wanted = [row['structure_id'] for path in (REVIEW, PASS2_REVIEW, FINDINGS_REVIEW)
              for row in json.loads(path.read_text())['accepted'] if row['asset_id'] == asset['id']]
    return (asset['structure_ids'] == wanted and sorted(asset['requirement_coverage']) == sorted(wanted)
            and all(item['extent'] == 'partial' for item in asset['requirement_coverage'].values()))


def apply(raw, changes):
    """Replace the empty binding fields inside each asset's own record. Returns new bytes and the edits made."""
    edits = []
    for asset_id, change in changes.items():
        marker = raw.find(b'"id": "' + asset_id.encode() + b'"')
        if marker == -1 or raw.find(b'"id": "' + asset_id.encode() + b'"', marker + 1) != -1:
            raise ValueError('Asset record not found exactly once: ' + asset_id)
        following = raw.find(b'"anatomical_review"', marker)
        for pattern, value in ((EMPTY_IDS, json.dumps(change['structure_ids'])),
                               (EMPTY_COVERAGE, json.dumps(change['requirement_coverage'], ensure_ascii=False))):
            match = pattern.search(raw, marker)
            if not match or match.start() > following:
                raise ValueError('Empty binding field not found in record: ' + asset_id)
            key = match.group(0).split(b':')[0]
            edits.append((match.start(), match.group(0), key + b': ' + value.encode()))
    out, done = raw, []
    for start, old, new in sorted(edits, reverse=True):
        out = out[:start] + new + out[start + len(old):]
        done.append([start, old.decode(), new.decode()])
    return out, sorted(done)


def bind():
    raw = EVIDENCE.read_bytes()
    changes = plan()
    after, edits = apply(raw, changes)
    before_view, after_view = json.loads(raw), json.loads(after)
    for old, new in zip(before_view['assets'], after_view['assets']):
        expected = dict(old, **changes.get(old['id'], {}))
        if new != expected:
            raise ValueError('Unintended change in ' + old['id'])
    RECEIPT.write_text(json.dumps({
        'path': 'data/radiology/radiology-asset-evidence.json', 'before_sha256': sha(raw), 'after_sha256': sha(after),
        'edits': edits, 'clinical_approval': False, 'extends_historical_approval': False}, indent=1, ensure_ascii=False) + '\n')
    EVIDENCE.write_bytes(after)
    return changes


def before_stored_caption_bindings(raw):
    """Exact earlier bytes of the evidence file; any other state is returned unchanged."""
    receipt = json.loads(RECEIPT.read_text())
    if sha(raw) != receipt['after_sha256']:
        return raw
    # Offsets are positions in the earlier file, so undo from the last edit to the first.
    shift = sum(len(new.encode()) - len(old.encode()) for _, old, new in receipt['edits'])
    for start, old, new in sorted(receipt['edits'], reverse=True):
        shift -= len(new.encode()) - len(old.encode())
        at = start + shift
        if raw[at:at + len(new.encode())] != new.encode():
            raise ValueError('Stored caption binding literal changed')
        raw = raw[:at] + old.encode() + raw[at + len(new.encode()):]
    if sha(raw) != receipt['before_sha256']:
        raise ValueError('Stored caption binding inverse changed unrelated bytes')
    return raw


if __name__ == '__main__':
    made = bind()
    print(len(made), 'assets;', sum(len(item['structure_ids']) for item in made.values()), 'bindings')
